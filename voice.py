import asyncio
import os
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from dotenv import load_dotenv

load_dotenv()

deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))

async def transcribe_stream(audio_callback):
    connection = deepgram.listen.asynclive.v("1")
    
    async def on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if transcript:
            await audio_callback(transcript)
    
    connection.on(LiveTranscriptionEvents.Transcript, on_message)
    
    options = LiveOptions(
        model="nova-2",
        language="hi-en",  # Hindi + English code switching
        smart_format=True,
        interim_results=False
    )
    
    await connection.start(options)
    return connection
