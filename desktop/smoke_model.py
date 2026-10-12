"""Opt-in real download and offline CPU inference smoke check."""
import argparse
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from service.whisper_model_manager import WhisperModelManager

parser = argparse.ArgumentParser()
parser.add_argument("--cache", required=True)
parser.add_argument("--audio")
args = parser.parse_args()
manager = WhisperModelManager(args.cache)
path = manager.ensure("tiny")
print(manager.status("tiny"), flush=True)
from faster_whisper import WhisperModel
import numpy as np

with patch("huggingface_hub.HfApi.model_info", side_effect=AssertionError("Offline check contacted network")), patch("huggingface_hub.hf_hub_download", side_effect=AssertionError("Offline check attempted download")):
    assert WhisperModelManager(args.cache).ensure("tiny") == path
    model = WhisperModel(str(path), device="cpu", compute_type="int8", local_files_only=True)
    segments, info = model.transcribe(args.audio or np.zeros(16000, dtype=np.float32), language="en")
    print("Offline transcription:", " ".join(segment.text for segment in segments), flush=True)
print("Offline CPU inference OK", flush=True)
