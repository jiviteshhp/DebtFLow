import json
import os
from datetime import datetime

LOG_FILE = "conversations.jsonl"

def log_turn(call_id: str, state: str, borrower_input: str, agent_response: str, latency_ms: float):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "call_id": call_id,
        "state": state,
        "borrower_input": borrower_input,
        "agent_response": agent_response,
        "latency_ms": latency_ms
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
