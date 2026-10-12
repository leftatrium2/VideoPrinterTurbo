"""Persistent, resumable model downloads shared by the API and transcription worker."""
import hashlib
import json
import os
import shutil
from pathlib import Path
import threading

from config.config import get_current_path


class WhisperModelManager:
    models = ("tiny", "base", "small", "medium", "large-v3")
    required = ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")

    def __init__(self, root=None):
        self.root = Path(root or os.environ.get("VPT_MODEL_DIR", Path(get_current_path()) / "models" / "faster_whisper"))
        self._lock = threading.RLock()
        self._states = {}
        self._threads = {}

    def _path(self, model):
        if model not in self.models:
            raise ValueError("Unsupported Whisper model")
        return self.root / model

    def _required(self, model):
        if model == "large-v3":
            return self.required[:3] + ("vocabulary.json", "preprocessor_config.json")
        return self.required

    def _ready(self, model):
        path = self._path(model)
        try:
            manifest = json.loads((path / "ready.json").read_text(encoding="utf-8"))
            return all((path / name).stat().st_size == manifest[name] > 0 for name in self._required(model))
        except (OSError, ValueError, KeyError, TypeError):
            return False

    def status(self, model):
        path = self._path(model)
        with self._lock:
            state = dict(self._states.get(model, {}))
        if self._ready(model):
            state.update(state="ready", completed_files=len(self._required(model)), error="")
        else:
            if state.get("state") == "ready":
                state["state"] = "missing"
            state.setdefault("state", "missing")
        return {
            "model": model, "path": str(path), "total_files": len(self._required(model)),
            "completed_files": 0, "error": "", **state,
        }

    def _update(self, model, **state):
        with self._lock:
            self._states.setdefault(model, {}).update(state)

    def start(self, model):
        self._path(model)
        with self._lock:
            if self._ready(model):
                return self.status(model)
            thread = self._threads.get(model)
            if thread is None or not thread.is_alive():
                self._update(model, state="downloading", completed_files=0, error="")
                thread = threading.Thread(target=self._download, args=(model,), daemon=True)
                self._threads[model] = thread
                thread.start()
            return self.status(model)

    def _download(self, model):
        try:
            from huggingface_hub import HfApi, hf_hub_download
            path = self._path(model)
            path.mkdir(parents=True, exist_ok=True)
            (path / "ready.json").unlink(missing_ok=True)
            repo = f"Systran/faster-whisper-{model}"
            info = HfApi().model_info(repo, files_metadata=True)
            files = {item.rfilename: item for item in info.siblings}
            needed = sum(max(0, (files[name].size or 0) - ((path / name).stat().st_size if (path / name).exists() else 0)) for name in self._required(model))
            if shutil.disk_usage(path).free < needed + 64 * 1024 * 1024:
                raise RuntimeError("Insufficient disk space for Whisper model")
            manifest = {}
            for index, name in enumerate(self._required(model)):
                item = files[name]
                local = Path(hf_hub_download(repo, name, revision=info.sha, local_dir=path))
                if not item.size or local.stat().st_size != item.size:
                    raise RuntimeError(f"Incomplete model file: {name}")
                if item.lfs and item.lfs.sha256:
                    self._update(model, state="verifying")
                    with local.open("rb") as stream:
                        digest = hashlib.file_digest(stream, "sha256").hexdigest()
                    if digest != item.lfs.sha256:
                        local.unlink()
                        raise RuntimeError(f"Model checksum mismatch: {name}; retry download")
                manifest[name] = item.size
                self._update(model, state="downloading", completed_files=index + 1)
            # Only a fully verified snapshot is eligible for offline loading.
            temporary = path / "ready.tmp"
            temporary.write_text(json.dumps(manifest), encoding="utf-8")
            temporary.replace(path / "ready.json")
            self._update(model, state="ready", error="")
        except Exception as exc:
            self._update(model, state="failed", error=str(exc))

    def ensure(self, model):
        self.start(model)
        with self._lock:
            thread = self._threads.get(model)
        if thread is not None:
            thread.join()
        state = self.status(model)
        if state["state"] != "ready":
            raise RuntimeError(state["error"] or "Whisper model download failed")
        return self._path(model)


model_manager = WhisperModelManager()
