"""Windows/macOS single-file entry point. No Node/Python installation needed at runtime."""
import argparse
import atexit
import asyncio
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser


def acquire_instance(data, no_browser):
    """Hold an OS lock so double-clicks during startup cannot share a database."""
    handle = (data / "desktop.lock").open("a+b")
    if handle.tell() == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        print("An existing instance is starting or running.", flush=True)
        for _ in range(150):
            try:
                port = json.loads((data / "desktop.json").read_text())["port"]
                url = f"http://127.0.0.1:{port}"
                with urllib.request.urlopen(url + "/desktop_health", timeout=1) as response:
                    if json.load(response).get("app") == "VideoPrinterTurbo":
                        if not no_browser:
                            webbrowser.open(url)
                        return False
            except Exception:
                time.sleep(0.2)
        print("Existing instance is not ready; inspect its console or logs.", flush=True)
        return False
    # The registered bound method retains the handle for the entire process.
    atexit.register(handle.close)
    return True


def prepare():
    resource = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    base = (Path.home() / "Library" / "Application Support" if sys.platform == "darwin"
            else Path(os.environ.get("LOCALAPPDATA", Path.home())))
    data = Path(os.environ.get("VPT_DATA_DIR", base / "VideoPrinterTurbo")).expanduser().resolve()
    data.mkdir(parents=True, exist_ok=True)
    os.environ.update(VPT_DESKTOP="1", VPT_DATA_DIR=str(data), VPT_RESOURCE_DIR=str(resource))
    model_dir = (Path("/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/models/faster_whisper")
                 if sys.platform == "darwin" else data / "models" / "faster_whisper")
    os.environ.setdefault("VPT_MODEL_DIR", str(model_dir))
    for directory in ("db", "logs", "storage", "output"):
        (data / directory).mkdir(exist_ok=True)
    for name in ("config.yaml", "downloader.json"):
        if not (data / name).exists():
            shutil.copyfile(resource / name, data / name)
    os.environ["PATH"] = str(resource / "bin") + os.pathsep + os.environ.get("PATH", "")
    # Legacy relative SQLite URLs resolve here; application storage uses VPT_DATA_DIR.
    os.chdir(data)
    sys.path.insert(0, str(resource / "server"))
    return resource, data



def migrate_legacy_models():
    """Copy the old macOS model cache while preserving source and existing files."""
    if sys.platform != "darwin":
        return
    legacy = Path.home() / "Library" / "Application Support" / "VideoPrinterTurbo" / "models"
    if not legacy.is_dir():
        return
    destination = Path("/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/models")

    def copy_missing(source, target):
        target = Path(target)
        if target.exists() or target.is_symlink():
            return str(target)
        try:
            return shutil.copy2(source, target)
        except Exception:
            # A failed copy must not be mistaken for a complete file on retry.
            target.unlink(missing_ok=True)
            raise

    print(f"Copying legacy models: {legacy} -> {destination}", flush=True)
    shutil.copytree(legacy, destination, dirs_exist_ok=True, copy_function=copy_missing)
    print("Legacy model copy complete; source files preserved.", flush=True)


def build_app(resource):
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    from app import app as backend

    application = FastAPI(lifespan=backend.router.lifespan_context)
    application.mount("/api", backend)
    dist = resource / "front" / "dist"
    application.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @application.get("/desktop_health")
    async def health():
        return {"app": "VideoPrinterTurbo", "ready": True}

    @application.get("/{path:path}")
    async def page(path: str):
        candidate = (dist / path).resolve()
        if not candidate.is_relative_to(dist.resolve()):
            raise HTTPException(404)
        return FileResponse(candidate if candidate.is_file() else dist / "index.html")

    return application


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-binaries", action="store_true", help="Verify bundled FFmpeg/ffprobe and exit")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=18080)
    args = parser.parse_args()
    if args.check_binaries:
        resource = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
        suffix = ".exe" if os.name == "nt" else ""
        for name in ("ffmpeg", "ffprobe"):
            subprocess.run([str(resource / "bin" / (name + suffix)), "-version"], check=True)
        return
    resource, data = prepare()
    if not acquire_instance(data, args.no_browser):
        return
    migrate_legacy_models()
    # Keep the socket reserved through server startup, preventing port races.
    listener = socket.socket()
    try:
        listener.bind(("127.0.0.1", args.port))
    except OSError:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{args.port}/desktop_health", timeout=2) as response:
                existing = json.load(response)
            if existing.get("app") == "VideoPrinterTurbo":
                if not args.no_browser:
                    webbrowser.open(f"http://127.0.0.1:{args.port}")
                return
        except Exception:
            pass
        listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    port = listener.getsockname()[1]
    (data / "desktop.json").write_text(json.dumps({"port": port}), encoding="utf-8")
    url = f"http://127.0.0.1:{port}"
    import uvicorn
    application = build_app(resource)
    server = uvicorn.Server(uvicorn.Config(application, host="127.0.0.1", port=port, log_config=None))

    def open_when_ready():
        while not server.started and not server.should_exit:
            time.sleep(0.2)
        if server.started and not args.no_browser:
            webbrowser.open(url)

    threading.Thread(target=open_when_ready, daemon=True).start()
    print(f"VideoPrinterTurbo: {url}\nData: {data}\nPress Ctrl+C to exit.", flush=True)
    try:
        asyncio.run(server.serve(sockets=[listener]))
    finally:
        listener.close()


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
