from gtts import gTTS

def text_to_speech(text: str, output_file: str = "response.mp3"):
    tts = gTTS(text=text, lang="en")
    tts.save(output_file)
    return output_file
