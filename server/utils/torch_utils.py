import platform

import torch

from utils import const


def load_asr_model():
    if torch.cuda.is_available():
        from faster_whisper import WhisperModel
        return "faster_whisper", WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
    elif platform.processor() == "arm" and torch.backends.mps.is_available():
        # Apple Silicon
        import mlx_whisper
        return "mlx", None  # mlx loaded at invocation time
    else:
        import whisper
        return "whisper", whisper.load_model("large-v3", device="cpu")


# Check if whisper settings are reasonable for the current platform
def check_asr_platform(asr_server: int):
    if asr_server == const.TASK_CONFIG_ASR_FASTER_WHISPER:
        # Requires CUDA 12 support
        if torch.cuda.is_available():
            return True
        return False
    if asr_server == const.TASK_CONFIG_ASR_MLX_WHISPER:
        if platform.processor() == "arm" and torch.backends.mps.is_available():
            return True
        return False
    return True
