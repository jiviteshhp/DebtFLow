import asyncio
import os
from state_machine import DebtFlowSM
from agent import get_agent_response
from tts import text_to_speech
from logger import log_turn
import time

async def run_conversation(call_id: str, user_text: str):
    sm = DebtFlowSM()
    
    start = time.time()
    sm.transition(user_text)
    response_text = get_agent_response(sm.current_state, user_text)
    latency_ms = (time.time() - start) * 1000
    
    audio_file = text_to_speech(response_text)
    log_turn(call_id, sm.current_state.value, user_text, response_text, latency_ms)
    
    return {
        "call_id": call_id,
        "state": sm.current_state.value,
        "response": response_text,
        "audio": audio_file,
        "latency_ms": round(latency_ms, 2)
    }

if __name__ == "__main__":
    result = asyncio.run(run_conversation("test_call", "cant_pay"))
    print(f"State: {result['state']}")
    print(f"Response: {result['response']}")
    print(f"Audio: {result['audio']}")
    print(f"Latency: {result['latency_ms']}ms")
