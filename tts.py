import os
import subprocess
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

VOICE_ID = "RXe6OFmxoC0nlSWpuCDy"

def text_to_speech(text: str, output_file: str = "response.mp3"):
    audio_stream = client.text_to_speech.stream(
        text=text,
        voice_id=VOICE_ID,
        model_id="eleven_turbo_v2_5",
        output_format="mp3_44100_128",
        voice_settings={
            "stability": 0.75,
            "similarity_boost": 0.85,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    )
    with open(output_file, "wb") as f:
        for chunk in audio_stream:
            if chunk:
                f.write(chunk)
    return output_file

if __name__ == "__main__":
    text_to_speech("Namaste, main Priya hoon. Kaise hain aap aaj?")
    subprocess.run(["mpg123", "-q", "response.mp3"])
    print("TTS test done")
