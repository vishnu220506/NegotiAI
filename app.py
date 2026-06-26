import os
import gradio as gr
from google import genai
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-2.5-flash"


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
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return response.text
    except Exception as e:
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


app = gr.Interface(
    fn=generate_strategy,
    inputs=[
        gr.Dropdown(
            choices=[
                "Internship / Salary Negotiation",
                "Product Sales Negotiation",
                "Real Estate / Property Investment Negotiation"
            ],
            label="Choose Negotiation Scenario"
        ),
        gr.Textbox(
            label="Describe your negotiation situation",
            placeholder="Example: I am buying a property listed for AED 1,500,000 and want to negotiate the price down.",
            lines=6
        )
    ],
    outputs=gr.Markdown(label="NegotiAI Strategy"),
    title="NegotiAI",
    description="Adaptive AI Negotiation & Sales Preparation Platform"
)

app.launch()