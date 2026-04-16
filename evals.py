from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def score_conversation(state: str, borrower_input: str, agent_response: str) -> dict:
    prompt = f"""You are evaluating a debt counseling AI agent. Score the agent response on three criteria, each from 0 to 10.

State: {state}
Borrower said: {borrower_input}
Agent responded: {agent_response}

Score these three things:
1. Empathy (0-10): Did the agent acknowledge the borrower's situation?
2. Goal Progress (0-10): Did the response move toward a resolution?
3. State Validity (0-10): Was the response appropriate for the current state?

Reply in JSON only, no explanation:
{{"empathy": 0, "goal_progress": 0, "state_validity": 0}}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw = response.choices[0].message.content
    scores = json.loads(raw)
    scores["overall"] = round(sum(scores.values()) / 3, 2)
    return scores


def run_evals():
    with open("conversations.jsonl", "r") as f:
        turns = [json.loads(line) for line in f.readlines()]
    
    print(f"\nRunning evals on {len(turns)} turns...\n")
    
    for turn in turns:
        scores = score_conversation(
            turn["state"],
            turn["borrower_input"],
            turn["agent_response"]
        )
        print(f"Call {turn['call_id']} | State: {turn['state']}")
        print(f"  Empathy: {scores['empathy']}/10")
        print(f"  Goal Progress: {scores['goal_progress']}/10")
        print(f"  State Validity: {scores['state_validity']}/10")
        print(f"  Overall: {scores['overall']}/10")
        print(f"  Latency: {turn['latency_ms']}ms\n")

if __name__ == "__main__":
    run_evals()
