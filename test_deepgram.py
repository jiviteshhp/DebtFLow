import asyncio
import os
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from dotenv import load_dotenv

load_dotenv()

async def test():
    deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))
    connection = deepgram.listen.asynclive.v("1")

    async def on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        print(f"Transcript: '{transcript}'")

    async def on_error(self, error, **kwargs):
        print(f"Error: {error}")

    connection.on(LiveTranscriptionEvents.Transcript, on_message)
    connection.on(LiveTranscriptionEvents.Error, on_error)

    options = LiveOptions(
        model="nova-2",
        language="en-IN",
        smart_format=True,
        encoding="linear16",
        sample_rate=16000,
        interim_results=True,
    )

    await connection.start(options)
    print("Connected to Deepgram")
    
    import pyaudio
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        input_device_index=10,
        frames_per_buffer=1024
    )

    print("Speak now...")
    for _ in range(200):
        data = stream.read(1024, exception_on_overflow=False)
        await connection.send(data)
        await asyncio.sleep(0.01)

    stream.close()
    audio.terminate()
    await connection.finish()
    print("Done")

asyncio.run(test())
