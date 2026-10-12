"""Build with desktop/build.ps1; models and user credentials are never bundled."""
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

root = Path(SPECPATH).parent
ffmpeg = Path(os.environ['VPT_FFMPEG_DIR'])
datas = [(str(root / 'front' / 'dist'), 'front/dist'),
         (str(root / 'server' / 'resources'), 'server/resources'),
         (str(root / 'config.yaml.sample'), '.'),
         (str(root / 'downloader.json.sample.json'), '.'),
         (str(root / 'i18n.json'), '.')]
binaries = [(str(ffmpeg / name), 'bin') for name in ('ffmpeg.exe', 'ffprobe.exe')]
# Include FFmpeg shared libraries when using a shared rather than static build.
binaries += [(str(path), 'bin') for path in ffmpeg.glob('*.dll')]
hidden = ['app', 'aiosqlite', 'sqlalchemy.dialects.sqlite.aiosqlite',
          'uvicorn.logging', 'uvicorn.loops.auto', 'uvicorn.protocols.http.auto',
          'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan.on']
for package in ('faster_whisper', 'ctranslate2', 'tokenizers', 'av', 'huggingface_hub', 'azure.cognitiveservices.speech'):
    package_data, package_bins, package_hidden = collect_all(package)
    datas += package_data
    binaries += package_bins
    hidden += package_hidden
hidden += collect_submodules('pipeline.downloader')
a = Analysis([str(root / 'desktop' / 'launcher.py')], pathex=[str(root / 'server')],
             binaries=binaries, datas=datas, hiddenimports=hidden,
             excludes=['mlx', 'mlx_whisper', 'whisper', 'streamlit', 'pytest', 'tkinter'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='VideoPrinterTurbo',
          debug=False, strip=False, upx=False, console=True)
