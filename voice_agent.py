import asyncio
import os
import subprocess
from state_machine import DebtFlowSM
from agent import get_agent_response
from tts import text_to_speech
from logger import log_turn
from stt import listen_and_transcribe
import time

sm = DebtFlowSM()
call_id = "live_call_1"
current_playback = None
agent_speaking = False
last_agent_finished = 0
SILENCE_AFTER_SPEECH = 3  # ignore transcripts for 3s after agent finishes

async def handle_transcript(transcript: str):
    global current_playback, agent_speaking, last_agent_finished

    # block transcripts while agent is speaking or just finished
    if agent_speaking:
        return
    if time.time() - last_agent_finished < SILENCE_AFTER_SPEECH:
        return
    # ignore very short transcripts — likely noise
    if len(transcript.split()) < 2:
        return

    print(f"\nYou: {transcript}")

    start = time.time()
    sm.transition(transcript)
    response = get_agent_response(sm.current_state, transcript)
    latency_ms = (time.time() - start) * 1000

    print(f"Priya ({sm.current_state.value}): {response}")
    print(f"Latency: {round(latency_ms)}ms\n")

    log_turn(call_id, sm.current_state.value, transcript, response, latency_ms)
    text_to_speech(response, "response.mp3")

    agent_speaking = True
    current_playback = subprocess.Popen(
        ["mpg123", "-q", "response.mp3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    # wait for playback to finish in background
    await asyncio.get_event_loop().run_in_executor(None, current_playback.wait)
    agent_speaking = False
    last_agent_finished = time.time()

if __name__ == "__main__":
    print("DebtFlow Voice Agent starting...")
    asyncio.run(listen_and_transcribe(handle_transcript))
