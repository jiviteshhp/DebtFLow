import pyaudio
import asyncio
import os
import json
import time
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from dotenv import load_dotenv

load_dotenv()

RATE = 16000
CHUNK = 512

def _find_input_device(audio: pyaudio.PyAudio, preferred_rate: int) -> int | None:
    for i in range(audio.get_device_count()):
        d = audio.get_device_info_by_index(i)
        if d["maxInputChannels"] < 1:
            continue
        try:
            audio.is_format_supported(
                preferred_rate, input_device=i,
                input_channels=1, input_format=pyaudio.paInt16
            )
            return i
        except Exception:
            continue
    return None

async def connect_deepgram(callback):
    deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))
    connection = deepgram.listen.asynclive.v("1")

    async def on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if not transcript.strip():
            return
        # only fire on final transcript, not partials
        if result.is_final:
            await callback(transcript)

    connection.on(LiveTranscriptionEvents.Transcript, on_message)

    options = LiveOptions(
        model="nova-2",
        language="en-IN",
        smart_format=True,
        encoding="linear16",
        sample_rate=RATE,
        interim_results=True,  # get partials so endpointing works faster
        endpointing=500,
    )

    await connection.start(options)
    return connection

async def start_listening(connection, is_muted_fn=None):
    import sys
    import io

    # suppress ALSA/JACK noise that prints during PyAudio init
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    os.dup2(devnull_fd, 2)
    os.close(devnull_fd)

    audio = pyaudio.PyAudio()
    device_index = _find_input_device(audio, RATE)

    open_kwargs = dict(
        format=pyaudio.paInt16, channels=1, rate=RATE,
        input=True, frames_per_buffer=CHUNK
    )
    if device_index is not None:
        open_kwargs["input_device_index"] = device_index

    stream = audio.open(**open_kwargs)

    # restore stderr now that mic is open — errors are done
    os.dup2(old_stderr, 2)
    os.close(old_stderr)

    print("Listening... speak now.")

    try:
        keepalive_msg = json.dumps({"type": "KeepAlive"})
        last_keepalive = time.time()

        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)

            if is_muted_fn is None or not is_muted_fn():
                await connection.send(data)
            else:
                # send KeepAlive every 5s while muted so Deepgram doesn't close
                if time.time() - last_keepalive > 5:
                    await connection.send(keepalive_msg)
                    last_keepalive = time.time()

            await asyncio.sleep(0)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        await connection.finish()

async def listen_and_transcribe(callback):
    connection = await connect_deepgram(callback)
    await start_listening(connection)
