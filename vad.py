import torch
import numpy as np

model, utils = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
    force_reload=False
)

def is_speech(audio_chunk: bytes, sample_rate: int = 16000) -> bool:
    audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
    
    # silero requires exactly 512 samples at 16000Hz
    required = 512
    if len(audio_np) < required:
        return False
    
    # use exactly 512 samples
    audio_tensor = torch.from_numpy(audio_np[:required])
    confidence = model(audio_tensor, sample_rate).item()
    return confidence >  0.3
