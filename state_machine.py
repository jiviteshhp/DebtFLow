from enum import Enum

class State(Enum):
    GREETING = "greeting"
    ASSESS = "assess"
    CANT_PAY = "cant_pay"
    WONT_PAY = "wont_pay"
    WILL_PAY = "will_pay"
    END = "end"

class DebtFlowSM:
    def __init__(self):
        self.current_state = State.GREETING

    def transition(self, borrower_input: str):
        if self.current_state == State.GREETING:
            self.current_state = State.ASSESS

        elif self.current_state == State.ASSESS:
            intent = classify_intent(borrower_input)
            intent = intent.strip().lower()
            if "cant" in intent:
                self.current_state = State.CANT_PAY
            elif "wont" in intent or "won" in intent:
                self.current_state = State.WONT_PAY
            elif "will" in intent:
                self.current_state = State.WILL_PAY

        elif self.current_state in [State.CANT_PAY, State.WONT_PAY, State.WILL_PAY]:
            self.current_state = State.END

        elif self.current_state == State.END:
            pass  # conversation over, do nothing

        
    
if __name__ == "__main__":
    sm = DebtFlowSM()
    print(sm.current_state)
    
    sm.transition("")
    print(sm.current_state)
    
    sm.transition("cant_pay")
    print(sm.current_state)
    
    sm.transition("")
    print(sm.current_state)
                


def get_response(self):
    responses = {
        State.GREETING: "Hi, I'm calling about your outstanding loan. Is this a good time?",
        State.ASSESS: "I understand. Can you tell me your current situation with the payment?",
        State.CANT_PAY: "I understand you're going through a tough time. Let's work out a plan that fits you.",
        State.WONT_PAY: "I hear you. Can you help me understand your concerns about the payment?",
        State.WILL_PAY: "That's great. When would you be able to make the payment?",
        State.END: "Thank you for your time. We'll follow up as discussed."
    }
    return responses[self.current_state]




def classify_intent(borrower_input: str) -> str:
    from groq import Groq
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user",
            "content": f"""Classify this borrower statement into exactly one of: cant_pay, wont_pay, will_pay, unclear

Borrower said: "{borrower_input}"

Reply with only one word: cant_pay, wont_pay, will_pay, or unclear"""
        }]
    )
    return response.choices[0].message.content.strip().lower()        
