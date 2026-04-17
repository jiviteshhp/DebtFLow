import requests
import random
import time

BASE_URL = "http://localhost:8000"

scenarios = [
    ["hello", "cant_pay", "lost my job last month"],
    ["hi there", "will_pay", "yes I can pay next week"],
    ["hello", "wont_pay", "I dont think this loan is valid"],
    ["hi", "cant_pay", "medical emergency drained my savings"],
    ["hello", "will_pay", "I have money ready"],
    ["hi", "wont_pay", "the interest rate is too high"],
    ["hello", "cant_pay", "my business failed"],
    ["hi there", "will_pay", "I will pay on friday"],
    ["hello", "wont_pay", "I need to talk to my lawyer first"],
    ["hi", "cant_pay", "I have no income right now"],
]

for i, scenario in enumerate(scenarios * 3):
    call_id = f"sim_{i+1}"
    
    requests.post(f"{BASE_URL}/start/{call_id}")
    
    for message in scenario:
        requests.post(
            f"{BASE_URL}/transition/{call_id}",
            params={"borrower_input": message}
        )
        time.sleep(0.5)
    
    print(f"Simulated call {call_id}")

print("Done — refresh your dashboard")
