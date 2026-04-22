import asyncio
import os
import subprocess
from state_machine import DebtFlowSM
from agent import get_agent_response
from tts import text_to_speech
from logger import log_turn
from stt import connect_deepgram, start_listening
import time

sm = DebtFlowSM()
call_id = "live_call_1"
current_playback = None
agent_speaking = False   # True while mpg123 is playing
processing = False       # True while LLM is generating

GREETING_TEXT = "Hello, this is Priya calling from the bank's loan recovery team. Am I speaking with the account holder? Is this a good time to talk?"

def is_muted():
    """Deepgram should not receive audio while agent is speaking or LLM is running."""
    return agent_speaking or processing

async def speak(text: str, state: str):
    global current_playback, agent_speaking
    print(f"Priya ({state}): {text}\n")
    # run blocking ElevenLabs API call in a thread so event loop stays free
    await asyncio.to_thread(text_to_speech, text, "response.mp3")
    agent_speaking = True
    current_playback = subprocess.Popen(
        ["mpg123", "-q", "response.mp3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    await asyncio.get_event_loop().run_in_executor(None, current_playback.wait)
    agent_speaking = False

async def handle_transcript(transcript: str):
    global processing

    if processing:
        return
    if len(transcript.split()) < 2:
        return

    processing = True
    try:
        print(f"\nYou: {transcript}")
        start = time.time()
        sm.transition(transcript)
        # run blocking Groq API call in a thread so event loop stays free
        response = await asyncio.to_thread(get_agent_response, sm.current_state, transcript)
        latency_ms = (time.time() - start) * 1000
        print(f"Latency: {round(latency_ms)}ms")
        log_turn(call_id, sm.current_state.value, transcript, response, latency_ms)
        await speak(response, sm.current_state.value)
    finally:
        processing = False

async def main():
    from state_machine import State

    # connect Deepgram and init mic first — this flushes all ALSA/JACK errors
    # before any meaningful output appears on screen
    greeting_done = False

    def _is_muted():
        # mute until greeting finishes, then use normal mute logic
        return (not greeting_done) or is_muted()

    connection = await connect_deepgram(handle_transcript)
    # start_listening suppresses ALSA errors internally during mic init
    listen_task = asyncio.create_task(
        start_listening(connection, is_muted_fn=_is_muted)
    )
    # small yield so start_listening runs up to "Listening... speak now."
    await asyncio.sleep(0.3)

    # now play greeting — terminal is clean at this point
    print(f"\nPriya (greeting): {GREETING_TEXT}\n")
    await asyncio.to_thread(text_to_speech, GREETING_TEXT, "response.mp3")
    p = subprocess.Popen(
        ["mpg123", "-q", "response.mp3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    await asyncio.get_event_loop().run_in_executor(None, p.wait)

    sm.current_state = State.ASSESS
    greeting_done = True  # unmute — mic now live

    await listen_task

if __name__ == "__main__":
    print("DebtFlow Voice Agent starting...")
    asyncio.run(main())
