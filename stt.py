import pyaudio
import asyncio
import os
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from dotenv import load_dotenv

load_dotenv()

RATE = 16000
CHUNK = 1024

async def listen_and_transcribe(callback):
    deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))
    connection = deepgram.listen.asynclive.v("1")

    async def on_message(self, result, **kwargs):
        print("Message received")
        transcript = result.channel.alternatives[0].transcript
        if transcript.strip():
            print(f"You said: {transcript}")
            await callback(transcript)

    connection.on(LiveTranscriptionEvents.Transcript, on_message)

    options = LiveOptions(
        model="nova-2",
        language="en-IN",
        smart_format=True,
        encoding="linear16",
        sample_rate=RATE,
        interim_results=False,
    )

    await connection.start(options)
    print("Connected to Deepgram")

    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        input_device_index=10,
        frames_per_buffer=CHUNK
    )

    print("Listening... speak now.")

    try:
        for _ in range(500):
            data = stream.read(CHUNK, exception_on_overflow=False)
            await connection.send(data)
            await asyncio.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        await connection.finish()
