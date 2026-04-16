from fastapi import FastAPI
from state_machine import DebtFlowSM
from agent import get_agent_response
import time
from logger import log_turn
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
sessions = {}  # call_id -> DebtFlowSM instance

from evals import score_conversation
from changelog import log_change


@app.post("/start/{call_id}")
def start_call(call_id: str):
    sessions[call_id] = DebtFlowSM()
    return {"call_id": call_id, "state": sessions[call_id].current_state.value}


@app.post("/transition/{call_id}")
def transition(call_id: str, borrower_input: str):
    if call_id not in sessions:
        return {"error": "call not found"}
    
    start = time.time()
    sessions[call_id].transition(borrower_input)
    current_state = sessions[call_id].current_state
    response = get_agent_response(current_state, borrower_input)
    latency_ms = (time.time() - start) * 1000

    log_turn(call_id, current_state.value, borrower_input, response, latency_ms)
    
    return {
        "state": current_state.value,
        "response": response,
        "latency_ms": round(latency_ms, 2)
    }

@app.get("/evals")
def run_evals():
    with open("conversations.jsonl", "r") as f:
        turns = [json.loads(line) for line in f.readlines()]
    
    results = []
    for turn in turns:
        scores = score_conversation(
            turn["state"],
            turn["borrower_input"],
            turn["agent_response"]
        )
        scores["call_id"] = turn["call_id"]
        scores["state"] = turn["state"]
        scores["latency_ms"] = turn["latency_ms"]
        results.append(scores)
    
    return {"evals": results}

@app.get("/changelog")
def get_changelog():
    with open("changelog.jsonl", "r") as f:
        entries = [json.loads(line) for line in f.readlines()]
    return {"changelog": entries}