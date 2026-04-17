from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv

load_dotenv()

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

audio = client.text_to_speech.convert(
    text="Hello, I am Priya, your debt counselor. How are you doing today?",
    voice_id="21m00Tcm4TlvDq8ikWAM",
    model_id="eleven_multilingual_v2"
)

with open("test_eleven.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)

print("Done - play test_eleven.mp3")
