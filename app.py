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

# Example placeholder text shown in the Prepare tab, matched to whichever
# scenario is selected — instead of always showing the real estate example
# regardless of the dropdown choice.
SCENARIO_EXAMPLES = {
    "Internship / Salary Negotiation": "Example: I have an internship offer for AED 3,000 per month and want to negotiate for AED 4,500.",
    "Product Sales Negotiation": "Example: I am selling a software subscription for AED 12,000 per year and the customer wants a discount.",
    "Real Estate / Property Investment Negotiation": "Example: I am buying a property listed for AED 1,500,000 and want to negotiate the price down.",
}


def update_prep_placeholder(scenario):
    """Runs when the Prepare dropdown changes, so the example text always
    matches the currently selected scenario."""
    return gr.update(placeholder=SCENARIO_EXAMPLES.get(scenario, ""))


def call_with_retry(api_call, max_attempts=3, delay_seconds=5):
    """
    Calls a Gemini API function and automatically retries if it fails with
    a 503 "model overloaded" error — these are short-lived spikes on
    Google's side, not bugs in our code, so a brief wait usually succeeds.
    Any other kind of error is raised immediately, since retrying a bad
    key or a real bug wouldn't help.
    """
    last_error = None
    for attempt in range(max_attempts):
        try:
            return api_call()
        except Exception as e:
            last_error = e
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                time.sleep(delay_seconds)
                continue
            raise
    raise last_error


def generate_strategy(scenario, user_details):
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
        response = call_with_retry(lambda: client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        ))
        return response.text
    except Exception as e:
        print(e)
        return f"""
## NegotiAI Strategy Report

### 1. Situation Summary
You are preparing for a {scenario}. Your goal is to negotiate professionally while protecting your target outcome.

### 2. Recommended Strategy
Start by showing respect for the other party's position, then explain your reasoning clearly. Focus on value, evidence, and alternatives rather than pressure.

### 3. Likely Objections
- "The price or offer is fixed."
- "There are other interested buyers or candidates."
- "This is already the best available offer."

### 4. Suggested Responses
- "I understand your position. Based on my budget and market comparison, I would like to explore whether there is flexibility."
- "I am serious about moving forward, but I need the final terms to make financial sense."
- "If the price cannot move, could we discuss added value, payment terms, or other concessions?"

### 5. Walk-Away Point
Define the maximum price, minimum salary, or minimum acceptable terms before entering the negotiation. Do not decide emotionally during the discussion.

### 6. Confidence Tips
- Stay calm.
- Ask questions before making concessions.
- Do not accept immediately.
- Use silence strategically.
- Be ready to walk away politely.
"""


def start_practice_session(scenario):
    """
    Starts a new Gemini chat session using the persona for the chosen
    scenario. Unlike generate_strategy() above (one isolated call), a chat
    session remembers every message sent through it — that's what lets the
    AI stay consistent as a character across a back-and-forth negotiation.
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
    Sends the user's message into an existing chat session and returns the
    persona's reply. Because `chat` already holds everything said earlier,
    Gemini sees the full conversation, not just this one message.
    """
    try:
        response = call_with_retry(lambda: chat.send_message(user_message))
        return response.text
    except Exception as e:
        return f"Something went wrong: {e}"


def generate_feedback_report(history):
    """
    Takes a Practice Mode conversation (the same list of dicts the Chatbot
    component uses) and asks Gemini to score the USER's negotiation
    performance. Returns a plain Python dictionary parsed from Gemini's
    JSON response — ready for the UI to turn into a scorecard.
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
        response = call_with_retry(lambda: client.models.generate_content(
            model=MODEL_NAME,
            contents=transcript,
            config=types.GenerateContentConfig(
                system_instruction=FEEDBACK_SYSTEM_PROMPT,
                temperature=0.3,
            ),
        ))
        raw_text = response.text.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`").replace("json\n", "", 1)

        return json.loads(raw_text)

    except Exception as e:
        return {"error": f"Something went wrong: {e}"}


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
    Turns the dictionary from generate_feedback_report() into an HTML
    scorecard: one labeled, colored bar per category, plus an overall
    coaching summary. This is what makes Feedback Mode look like a real
    report instead of another wall of text.
    """
    if "error" in feedback:
        return f"<p style='color:#e74c3c;'>{feedback['error']}</p>"

    scores = feedback.get("scores", {})
    notes = feedback.get("notes", {})

    rows_html = ""
    for key, label in CATEGORY_LABELS.items():
        score = scores.get(key, 0)
        note = notes.get(key, "")
        percent = score * 10  # 1-10 scale -> 0-100%

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
    """
    Runs when 'Get Feedback Report' is clicked. Scores the current Practice
    Mode transcript and renders it as a scorecard.
    """
    feedback = generate_feedback_report(history)
    return render_scorecard_html(feedback)


def handle_start(scenario):
    """
    Runs when 'Start Practice Session' is clicked. Creates a new chat
    session, shows a system note confirming it's ready, and reveals the
    chat box + message input + Send button. Those three stay hidden until
    this point on purpose — there's nothing to type into before a session
    actually exists, so a stray message can never get sent into a void.
    """
    chat = start_practice_session(scenario)
    history = [{
        "role": "system",
        "content": "Session started. Describe your real situation below (your offer, your target, your background) to begin the negotiation."
    }]
    return (
        chat,
        gr.update(value=history, visible=True),
        gr.update(visible=True),
        gr.update(visible=True),
    )


def handle_send(chat, user_message, history):
    """
    Runs when 'Send' is clicked (or Enter is pressed). Sends the user's
    message into the active session and appends both sides of the exchange
    to the visible chat history.
    """
    if chat is None:
        history = history + [
            {"role": "assistant", "content": "Please click **Start Practice Session** first."}
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
                    prep_scenario = gr.Dropdown(choices=SCENARIOS, label="Choose Negotiation Scenario")
                    prep_details = gr.Textbox(
                        label="Describe your negotiation situation",
                        placeholder=SCENARIO_EXAMPLES[SCENARIOS[0]],
                        lines=6,
                    )
                    prep_button = gr.Button("Generate Strategy", variant="primary")
                with gr.Column():
                    prep_output = gr.Markdown(label="NegotiAI Strategy")

            prep_scenario.change(fn=update_prep_placeholder, inputs=prep_scenario, outputs=prep_details)
            prep_button.click(fn=generate_strategy, inputs=[prep_scenario, prep_details], outputs=prep_output)

        with gr.Tab("Practice"):
            practice_scenario = gr.Dropdown(choices=SCENARIOS, label="Choose Negotiation Scenario")
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
            send_button.click(fn=handle_send, inputs=[chat_state, msg_box, chatbot], outputs=[chatbot, msg_box])
            msg_box.submit(fn=handle_send, inputs=[chat_state, msg_box, chatbot], outputs=[chatbot, msg_box])

        with gr.Tab("Feedback"):
            gr.Markdown("Complete a Practice session first, then generate your scorecard here.")
            feedback_button = gr.Button("Get Feedback Report", variant="primary")
            feedback_output = gr.HTML()

            feedback_button.click(fn=handle_feedback, inputs=chatbot, outputs=feedback_output)


if __name__ == "__main__":
    app.launch()