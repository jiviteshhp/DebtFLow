from enum import Enum


class State(Enum):
    GREETING  = "greeting"
    ASSESS    = "assess"
    CANT_PAY  = "cant_pay"
    NEGOTIATE = "negotiate"
    WONT_PAY  = "wont_pay"
    OBJECTION = "objection"
    WILL_PAY  = "will_pay"
    END       = "end"


class DebtFlowSM:
    def __init__(self):
        self.current_state = State.GREETING
        self.turn_count = 0

    def transition(self, borrower_input: str):
        if not borrower_input.strip():
            return

        self.turn_count += 1

        if self.current_state == State.GREETING:
            self.current_state = State.ASSESS

        elif self.current_state == State.ASSESS:
            # short responses are just acknowledgments — stay in ASSESS
            if len(borrower_input.split()) < 4:
                pass
            else:
                intent = classify_intent(borrower_input)
                if intent == "cant_pay":
                    self.current_state = State.CANT_PAY
                elif intent == "wont_pay":
                    self.current_state = State.WONT_PAY
                # will_pay from ASSESS means nothing yet — no amount, no date
                # keep in ASSESS so Priya can ask about their situation first

        elif self.current_state == State.CANT_PAY:
            intent = classify_intent(borrower_input)
            if intent == "will_pay":
                self.current_state = State.WILL_PAY
            else:
                self.current_state = State.NEGOTIATE

        elif self.current_state == State.NEGOTIATE:
            intent = classify_intent(borrower_input)
            if intent == "will_pay":
                self.current_state = State.WILL_PAY
            elif intent == "wont_pay":
                self.current_state = State.WONT_PAY
            # cant_pay or unclear: stay in NEGOTIATE, try different offer

        elif self.current_state == State.WONT_PAY:
            intent = classify_intent(borrower_input)
            if intent == "will_pay":
                self.current_state = State.WILL_PAY
            else:
                self.current_state = State.OBJECTION

        elif self.current_state == State.OBJECTION:
            intent = classify_intent(borrower_input)
            if intent == "will_pay":
                self.current_state = State.WILL_PAY
            elif self.turn_count > 10:
                self.current_state = State.END
            # else stay in OBJECTION and keep addressing concerns

        elif self.current_state == State.WILL_PAY:
            self.current_state = State.END

        # END: no transition


def classify_intent(borrower_input: str) -> str:
    from groq import Groq
    import os
    from dotenv import load_dotenv
    load_dotenv()

    from groq import Groq
    import os
    from dotenv import load_dotenv
    load_dotenv()

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "system",
                "content": "You are a classifier. Reply with exactly one word only: cant_pay, wont_pay, will_pay, or unclear. No explanation.",
            }, {
                "role": "user",
                "content": f"""Classify the borrower's intent from their statement.

cant_pay  = they want to pay but genuinely cannot right now (no money, job loss, emergency)
wont_pay  = they are refusing or disputing the payment (don't want to, claim fraud, already paid)
will_pay  = they explicitly agree to pay a specific amount or on a specific date
unclear   = vague or cannot determine intent

Examples:
"I lost my job last month" -> cant_pay
"Medical bills have drained me" -> cant_pay
"2000 per month works for me" -> will_pay
"I will pay on the 15th" -> will_pay
"Yes I can pay next week" -> will_pay
"Yes" -> will_pay
"Sure" -> will_pay
"Ok, agreed" -> will_pay
"I refuse to pay this" -> wont_pay
"This loan is fraudulent" -> wont_pay
"Maybe, I'll think about it" -> unclear
"I don't know" -> unclear

Borrower said: "{borrower_input}"

Reply with one word:"""
            }],
            max_tokens=5,
            temperature=0.0,
            timeout=5.0,  # fail fast — 5s max, don't hang the conversation
        )
        result = response.choices[0].message.content.strip().lower()
        for label in ["cant_pay", "wont_pay", "will_pay", "unclear"]:
            if label in result:
                return label
        return "unclear"
    except Exception as e:
        print(f"[classify_intent] failed: {e} — defaulting to unclear")
        return "unclear"


if __name__ == "__main__":
    tests = [
        ("hello", State.ASSESS),
        ("I lost my job, I cannot pay", State.CANT_PAY),
        ("2000 per month works for me", State.WILL_PAY),
        ("I will pay on the 15th", State.CONFIRM),
        ("confirmed", State.END),
    ]
    sm = DebtFlowSM()
    print(f"Start: {sm.current_state.value}")
    for inp, expected in tests:
        sm.transition(inp)
        status = "OK" if sm.current_state == expected else f"FAIL (expected {expected.value})"
        print(f"  '{inp}' -> {sm.current_state.value} {status}")
