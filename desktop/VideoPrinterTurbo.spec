"""Build with desktop/build.ps1 or desktop/build_macos.sh; models and user credentials are never bundled."""
import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

root = Path(SPECPATH).parent
ffmpeg = Path(os.environ['VPT_FFMPEG_DIR'])
datas = [(str(root / 'front' / 'dist'), 'front/dist'),
         (str(root / 'server' / 'resources'), 'server/resources'),
         (str(root / 'config.yaml'), '.'),
         (str(root / 'downloader.json'), '.'),
         (str(root / 'i18n.json'), '.')]
tool_names = ('ffmpeg.exe', 'ffprobe.exe') if sys.platform == 'win32' else ('ffmpeg', 'ffprobe')
binaries = [(str(ffmpeg / name), 'bin') for name in tool_names]
# Analysis follows Mach-O dependencies (including Homebrew dylibs) and rewrites
# their install names for the extracted bundle; do not copy them as plain data.
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
          debug=False, strip=False, upx=False, console=True,
          **({'codesign_identity': os.environ.get('VPT_CODESIGN_IDENTITY') or None}
             if sys.platform == 'darwin' else {}))
