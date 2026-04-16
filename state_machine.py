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
            if borrower_input == "cant_pay":
                self.current_state = State.CANT_PAY
            elif borrower_input == "wont_pay":
                self.current_state = State.WONT_PAY
            elif borrower_input == "will_pay":
                self.current_state = State.WILL_PAY
        elif (self.current_state == State.CANT_PAY or self.current_state == State.WONT_PAY or self.current_state == State.WILL_PAY):
            self.current_state = State.END
    
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




        