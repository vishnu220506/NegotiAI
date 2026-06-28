import os
import json
import time
import gradio as gr
from google import genai
from google.genai import types
from dotenv import load_dotenv
from prompts import PRACTICE_PERSONAS
from prompts import SYSTEM_PROMPT
from prompts import FEEDBACK_SYSTEM_PROMPT

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-2.5-flash-lite"

SCENARIOS = [
    "Internship / Salary Negotiation",
    "Product Sales Negotiation",
    "Real Estate / Property Investment Negotiation",
]

SCENARIO_EXAMPLES = {
    "Internship / Salary Negotiation": "Example: I have an internship offer for AED 3,000 per month and want to negotiate for AED 4,500.",
    "Product Sales Negotiation": "Example: I am selling a software subscription for AED 12,000 per year and the customer wants a discount.",
    "Real Estate / Property Investment Negotiation": "Example: I am buying a property listed for AED 1,500,000 and want to negotiate the price down.",
}


def update_prep_placeholder(scenario):
    return gr.update(placeholder=SCENARIO_EXAMPLES.get(scenario, ""))


def call_with_retry(api_call, max_attempts=3, delay_seconds=5):
    """
    Calls a Gemini API function and retries only for temporary 503/unavailable errors.
    Quota errors, API key errors, and real code errors are not retried repeatedly.
    """
    last_error = None

    for attempt in range(max_attempts):
        try:
            return api_call()
        except Exception as e:
            last_error = e
            error_text = str(e).lower()

            if "503" in error_text or "unavailable" in error_text or "overloaded" in error_text:
                time.sleep(delay_seconds)
                continue

            raise

    raise last_error


def friendly_api_error(error):
    """
    Converts technical Gemini/API errors into short, professional messages.
    This prevents raw API errors from appearing in the demo UI.
    """
    error_text = str(error)
    lower_text = error_text.lower()

    if "429" in error_text or "resource_exhausted" in lower_text or "quota" in lower_text:
        return (
            "AI service is temporarily unavailable because the free Gemini API limit "
            "has been reached. Please try again later."
        )

    if "503" in error_text or "unavailable" in lower_text or "overloaded" in lower_text:
        return "AI service is temporarily busy. Please wait a moment and try again."

    if "api_key" in lower_text or "permission" in lower_text or "unauthenticated" in lower_text:
        return "AI service is not configured correctly. Please check the API key setup."

    return "AI service is temporarily unavailable. Please try again later."


def generate_strategy(scenario, user_details):
    if not scenario:
        return "Please choose a negotiation scenario first."

    if not user_details.strip():
        return "Please describe your negotiation situation first."

    prompt = f"""
{SYSTEM_PROMPT}

Scenario: {scenario}

User situation:
{user_details}

Provide a structured negotiation preparation plan with:
1. Situation summary
2. Best strategy
3. Likely objections
4. Suggested responses
5. Walk-away point
6. Confidence tips
"""

    try:
        response = call_with_retry(
            lambda: client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
        )
        return response.text

    except Exception as e:
        return f"""
## Unable to generate strategy

{friendly_api_error(e)}
"""


def start_practice_session(scenario):
    """
    Starts a new Gemini chat session using the persona for the chosen scenario.
    """
    persona_prompt = PRACTICE_PERSONAS[scenario]

    chat = client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=persona_prompt,
            temperature=0.8,
        ),
    )

    return chat


def practice_reply(chat, user_message):
    """
    Sends the user's message into an existing Gemini chat session.
    """
    try:
        response = call_with_retry(lambda: chat.send_message(user_message))
        return response.text

    except Exception as e:
        return friendly_api_error(e)


def generate_feedback_report(history):
    """
    Scores the user's Practice Mode conversation.
    """
    history = history or []
    lines = []

    for turn in history:
        role = turn.get("role")
        content = turn.get("content", "")

        if role == "user":
            lines.append(f"User: {content}")
        elif role == "assistant":
            lines.append(f"AI Persona: {content}")

    transcript = "\n".join(lines)

    if not transcript.strip():
        return {"error": "No conversation to evaluate yet. Practice a negotiation first."}

    try:
        response = call_with_retry(
            lambda: client.models.generate_content(
                model=MODEL_NAME,
                contents=transcript,
                config=types.GenerateContentConfig(
                    system_instruction=FEEDBACK_SYSTEM_PROMPT,
                    temperature=0.3,
                ),
            )
        )

        raw_text = response.text.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`").replace("json\n", "", 1)

        return json.loads(raw_text)

    except Exception as e:
        return {"error": friendly_api_error(e)}


CATEGORY_LABELS = {
    "confidence": "Confidence",
    "persuasion": "Persuasion",
    "objection_handling": "Objection Handling",
    "communication": "Communication",
    "emotional_control": "Emotional Control",
    "closing_effectiveness": "Closing Effectiveness",
}


def render_scorecard_html(feedback):
    """
    Turns the feedback dictionary into an HTML scorecard.
    """
    if "error" in feedback:
        return f"""
        <div style="padding:14px; background:#2b1d1d; border:1px solid #e74c3c; border-radius:8px;">
            <strong style="color:#ffb3b3;">Feedback unavailable</strong>
            <p style="color:#f2f2f2; margin-top:8px;">{feedback['error']}</p>
        </div>
        """

    scores = feedback.get("scores", {})
    notes = feedback.get("notes", {})

    rows_html = ""

    for key, label in CATEGORY_LABELS.items():
        score = scores.get(key, 0)
        note = notes.get(key, "")
        percent = score * 10

        if score <= 4:
            color = "#e74c3c"
        elif score <= 7:
            color = "#f39c12"
        else:
            color = "#27ae60"

        rows_html += f"""
        <div style="margin-bottom:14px;">
            <div style="display:flex; justify-content:space-between; font-weight:600;">
                <span>{label}</span><span>{score}/10</span>
            </div>
            <div style="background:#333; border-radius:6px; height:10px; overflow:hidden;">
                <div style="background:{color}; width:{percent}%; height:100%;"></div>
            </div>
            <div style="font-size:0.85em; color:#aaa; margin-top:4px;">{note}</div>
        </div>
        """

    summary = feedback.get("overall_summary", "")

    return f"""
    <div style="font-family:sans-serif;">
        {rows_html}
        <div style="margin-top:16px; padding:12px; background:#222; border-radius:8px;">
            <strong>Overall:</strong> {summary}
        </div>
    </div>
    """


def handle_feedback(history):
    feedback = generate_feedback_report(history)
    return render_scorecard_html(feedback)


def handle_start(scenario):
    """
    Starts Practice Mode safely. If Gemini cannot start, the app shows a short
    professional message instead of crashing or showing raw technical errors.
    """
    if not scenario:
        history = [{
            "role": "assistant",
            "content": "Please choose a negotiation scenario first."
        }]
        return (
            None,
            gr.update(value=history, visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
        )

    try:
        chat = start_practice_session(scenario)

    except Exception as e:
        history = [{
            "role": "assistant",
            "content": friendly_api_error(e)
        }]
        return (
            None,
            gr.update(value=history, visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
        )

    history = [{
        "role": "system",
        "content": "Session started. Describe your real situation below, including your offer, target, and background, to begin the negotiation."
    }]

    return (
        chat,
        gr.update(value=history, visible=True),
        gr.update(visible=True),
        gr.update(visible=True),
    )


def handle_send(chat, user_message, history):
    """
    Sends a user message in Practice Mode and appends the AI persona reply.
    """
    history = history or []

    if chat is None:
        history = history + [
            {"role": "assistant", "content": "Please click Start Practice Session first."}
        ]
        return history, gr.update(value="")

    if not user_message.strip():
        return history, gr.update(value="")

    reply = practice_reply(chat, user_message)

    history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]

    return history, gr.update(value="")


with gr.Blocks(title="NegotiAI") as app:
    gr.Markdown("# NegotiAI\nAdaptive AI Negotiation & Sales Preparation Platform")

    with gr.Tabs():
        with gr.Tab("Prepare"):
            with gr.Row():
                with gr.Column():
                    prep_scenario = gr.Dropdown(
                        choices=SCENARIOS,
                        label="Choose Negotiation Scenario",
                        value=SCENARIOS[0],
                    )
                    prep_details = gr.Textbox(
                        label="Describe your negotiation situation",
                        placeholder=SCENARIO_EXAMPLES[SCENARIOS[0]],
                        lines=6,
                    )
                    prep_button = gr.Button("Generate Strategy", variant="primary")

                with gr.Column():
                    prep_output = gr.Markdown(label="NegotiAI Strategy")

            prep_scenario.change(
                fn=update_prep_placeholder,
                inputs=prep_scenario,
                outputs=prep_details,
            )

            prep_button.click(
                fn=generate_strategy,
                inputs=[prep_scenario, prep_details],
                outputs=prep_output,
            )

        with gr.Tab("Practice"):
            practice_scenario = gr.Dropdown(
                choices=SCENARIOS,
                label="Choose Negotiation Scenario",
                value=SCENARIOS[0],
            )
            start_button = gr.Button("Start Practice Session", variant="primary")

            chatbot = gr.Chatbot(label="Practice Conversation", visible=False)
            msg_box = gr.Textbox(
                label="Your message",
                placeholder="Type your response and press Enter...",
                visible=False,
            )
            send_button = gr.Button("Send", visible=False)

            chat_state = gr.State(None)

            start_button.click(
                fn=handle_start,
                inputs=practice_scenario,
                outputs=[chat_state, chatbot, msg_box, send_button],
            )

            send_button.click(
                fn=handle_send,
                inputs=[chat_state, msg_box, chatbot],
                outputs=[chatbot, msg_box],
            )

            msg_box.submit(
                fn=handle_send,
                inputs=[chat_state, msg_box, chatbot],
                outputs=[chatbot, msg_box],
            )

        with gr.Tab("Feedback"):
            gr.Markdown("Complete a Practice session first, then generate your scorecard here.")
            feedback_button = gr.Button("Get Feedback Report", variant="primary")
            feedback_output = gr.HTML()

            feedback_button.click(
                fn=handle_feedback,
                inputs=chatbot,
                outputs=feedback_output,
            )


if __name__ == "__main__":
    app.launch()