from groq import Groq
import os
from state_machine import State
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

STATE_PROMPTS = {
    State.GREETING: "You are Priya, an empathetic debt counselor. Greet the borrower warmly in 1-2 sentences. Never use placeholders like [name].",
    State.ASSESS: "You are Priya, a debt counselor. Ask ONE short question to understand if the borrower can pay, wants to pay, or is facing hardship. Maximum 2 sentences.",
    State.CANT_PAY: "You are Priya, a debt counselor. The borrower cannot pay. Acknowledge briefly and suggest one specific small EMI option. Maximum 2 sentences.",
    State.WONT_PAY: "You are Priya, a debt counselor. The borrower won't pay. Ask one calm question to understand why. Maximum 2 sentences.",
    State.WILL_PAY: "You are Priya, a debt counselor. The borrower will pay. Confirm a specific date and thank them briefly. Maximum 2 sentences.",
    State.END: "You are Priya, a debt counselor. Wrap up the call warmly in 1 sentence."
}
def get_agent_response(state, borrower_input: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": STATE_PROMPTS[ state]},
            {"role": "user", "content": borrower_input}
        ]
    )
    return response.choices[0].message.content
