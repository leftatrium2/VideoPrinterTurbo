@echo off
rem Usage: start.bat [--mode auto^|cpu^|cuda] [--check] [--reinstall]
rem Python payload is shared with start.sh; keep both copies identical.
setlocal DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 (
    echo ERROR: Cannot access the project directory.
    exit /b 1
)
where uv >nul 2>nul
if errorlevel 1 (
    echo ERROR: uv is required. Install uv and add it to PATH.
    pause
    exit /b 1
)
set "VPT_LAUNCHER_FILE=%~f0"
uv run --no-project --no-python-downloads --python ">=3.11,<3.13" python -c "import os; from pathlib import Path; p=Path(os.environ['VPT_LAUNCHER_FILE']); exec(compile(p.read_text(encoding='utf-8').split('\n# VPT_PYTHON_START\n',1)[1],str(p),'exec'))" %*
set "VPT_EXIT_CODE=%ERRORLEVEL%"
if not "%VPT_EXIT_CODE%"=="0" if not "%VPT_EXIT_CODE%"=="130" (
    echo ERROR: Startup failed. Review the output above and the service logs.
    pause
)
exit /b %VPT_EXIT_CODE%
# VPT_PYTHON_START
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import socket
import subprocess
import sys
import time
import tomllib
import urllib.request
import urllib.error

ROOT = Path.cwd()
WINDOWS = sys.platform == 'win32'
TORCH = '2.10.0'
VISION = '0.25.0'
ORT = '1.26.0'


def info(message):
    print(message, flush=True)


def run(command, *, cwd=ROOT, env=None, capture=False):
    result = subprocess.run([str(x) for x in command], cwd=cwd, env=env,
                            text=True, capture_output=capture)
    if result.returncode:
        if capture:
            info(result.stdout.strip())
            info(result.stderr.strip())
        raise RuntimeError(f'Command failed (exit {result.returncode}): {command[0]}')
    return result.stdout.strip() if capture else None


def select_mode(requested):
    system = platform.system()
    arch = platform.machine().lower()
    if system not in ('Darwin', 'Linux', 'Windows'):
        raise RuntimeError(f'Unsupported operating system: {system}')
    apple = system == 'Darwin' and arch == 'arm64'
    nvidia = shutil.which('nvidia-smi')
    gpu = False
    if nvidia and system != 'Darwin':
        result = subprocess.run([nvidia, '--query-gpu=name', '--format=csv,noheader'],
                                capture_output=True, text=True, timeout=15)
        gpu = result.returncode == 0 and bool(result.stdout.strip())
        if not gpu and requested == 'auto':
            raise RuntimeError('NVIDIA driver detection failed. Repair the driver or use --mode cpu.')
    mode = ('mac' if apple else 'cuda' if gpu else 'cpu') if requested == 'auto' else requested
    if mode == 'mac' and not apple:
        raise RuntimeError('Mac acceleration requires native ARM64 Python on Apple Silicon. Do not use Rosetta.')
    if mode == 'cuda' and (not gpu or arch not in ('amd64', 'x86_64')):
        raise RuntimeError('CUDA mode requires a working NVIDIA driver and an x86_64 Linux or Windows system.')
    if system == 'Darwin' and not apple:
        raise RuntimeError('This launcher supports native Apple Silicon macOS only. Use ARM64 Python.')
    return mode


def check_port(port):
    with socket.socket() as sock:
        if not WINDOWS:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('127.0.0.1', port))
        except OSError as exc:
            raise RuntimeError(f'Port {port} is unavailable. Stop the existing service or choose another port.') from exc


def base_env():
    env = os.environ.copy()
    # Keep user uv project/venv settings from redirecting launcher installations.
    for key in ('VIRTUAL_ENV', 'PYTHONHOME', 'PYTHONPATH', 'UV_PROJECT_ENVIRONMENT', 'UV_PYTHON'):
        env.pop(key, None)
    env.update(PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1', UV_PYTHON_DOWNLOADS='never')
    return env


def accelerated_env(python, mode):
    env = base_env()
    if mode == 'cpu':
        env['CUDA_VISIBLE_DEVICES'] = ''
    if mode == 'cuda':
        site = Path(run([python, '-c', 'import sysconfig; print(sysconfig.get_path("purelib"))'], env=env, capture=True))
        dirs = [site / 'torch' / 'lib']
        for package in ('cublas', 'cudnn', 'cuda_runtime', 'cufft', 'curand', 'cuda_nvrtc'):
            dirs.extend([site / 'nvidia' / package / 'lib', site / 'nvidia' / package / 'bin'])
        dirs = [str(p) for p in dirs if p.is_dir()]
        key = 'PATH' if WINDOWS else 'LD_LIBRARY_PATH'
        env[key] = os.pathsep.join(dirs + [env.get(key, '')])
    if mode == 'mac':
        env['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
    env['AUDIO_SEPARATOR_MODEL_DIR'] = str(ROOT / 'storage' / 'models' / 'audio_separator')
    return env


VERIFY = r'''
import os, platform
from pathlib import Path
import torch
mode = os.environ['VPT_MODE']
if mode == 'cuda':
    if platform.system() == 'Windows':
        handles = [os.add_dll_directory(p) for p in os.environ['PATH'].split(os.pathsep) if p and Path(p).is_dir()]
    assert torch.version.cuda == '12.8', 'Expected CUDA 12.8 PyTorch.'
    assert torch.cuda.is_available(), 'CUDA is unavailable. Check the NVIDIA driver (CUDA 12.8 compatible).'
    x = torch.ones(4, device='cuda'); assert x.sum().item() == 4
    import ctranslate2
    assert ctranslate2.get_cuda_device_count() > 0, 'CTranslate2 cannot access CUDA.'
    assert 'float16' in ctranslate2.get_supported_compute_types('cuda'), 'Faster Whisper FP16 is unsupported.'
    import onnxruntime as ort
    ort.preload_dlls(directory='')
    if platform.system() == 'Windows':
        import ctypes
        ctypes.WinDLL(str(Path(ort.__file__).parent / 'capi' / 'onnxruntime_providers_cuda.dll'))
    else:
        import ctypes
        ctypes.CDLL('libcublas.so.12'); ctypes.CDLL('libcudnn.so.9')
        ctypes.CDLL(str(Path(ort.__file__).parent / 'capi' / 'libonnxruntime_providers_cuda.so'))
    assert 'CUDAExecutionProvider' in ort.get_available_providers(), 'ONNX Runtime CUDA provider is unavailable.'
    print('CUDA initialized: ' + torch.cuda.get_device_name(0))
elif mode == 'mac':
    assert torch.backends.mps.is_available(), 'MPS is unavailable. Check macOS and native ARM64 Python.'
    x = torch.ones(4, device='mps'); assert x.sum().item() == 4
    import mlx.core as mx
    assert mx.metal.is_available(), 'MLX Metal is unavailable.'
    mx.eval(mx.ones((4,)))
    import mlx_whisper
    # The existing backend uses this exact condition to enable MLX ASR.
    assert platform.processor() == 'arm', 'The backend does not recognize this Python as Apple Silicon.'
    print('Apple Silicon initialized: MPS and MLX Metal are available.')
else:
    assert torch.version.cuda is None, 'Expected CPU-only PyTorch.'
    print('CPU environment initialized.')
import torchvision, whisper, faster_whisper
from audio_separator.separator import Separator
'''


def initialize(mode, args, uv, npm):
    cache = ROOT / 'storage' / 'launcher'
    cache.mkdir(parents=True, exist_ok=True)
    venv = ROOT / '.venv' / ('launcher-' + mode)
    python = venv / ('Scripts/python.exe' if WINDOWS else 'bin/python')
    env = base_env()
    project = tomllib.loads((ROOT / 'server' / 'pyproject.toml').read_text(encoding='utf-8'))
    dependencies = [d for d in project['project']['dependencies'] if mode == 'mac' or not d.startswith('mlx-whisper')]
    if platform.system() == 'Darwin':
        # Resolve Apple's newer baseline with torchvision and all application dependencies.
        dependencies.extend(['torch>=2.13,<3', 'torchvision'])
    if mode == 'cuda':
        dependencies = [d.replace('audio-separator[cpu]', 'audio-separator[gpu]') for d in dependencies]
        dependencies.extend(['ctranslate2==4.6.0', f'onnxruntime=={ORT}', f'onnxruntime-gpu=={ORT}'])
    signature = hashlib.sha256(json.dumps([dependencies, mode, sys.version, platform.machine(),
                                          TORCH, VISION, ORT, VERIFY], sort_keys=True).encode()).hexdigest()
    stamp = cache / (mode + '.json')
    old = json.loads(stamp.read_text()) if stamp.exists() else {}
    if args.reinstall or not python.is_file() or old.get('signature') != signature:
        if not python.is_file():
            run([uv, 'venv', '--python', sys.executable, str(venv)], env=env)
        requirements = cache / (mode + '-requirements.txt')
        constraints = cache / (mode + '-constraints.txt')
        requirements.write_text('\n'.join(dependencies) + '\n', encoding='utf-8')
        command = [uv, 'pip', 'install', '--python', str(python)]
        info(f'Installing Python dependencies for {mode}. The first run may take several minutes.')
        version_command = [python, '-c', 'from importlib.metadata import version; print("torch==" + version("torch")); print("torchvision==" + version("torchvision"))']
        if platform.system() == 'Darwin':
            # audio-separator requires torch >=2.13 on Apple Silicon. Resolve the
            # matching torchvision together instead of imposing CUDA Docker pins.
            run(command + ['--requirements', str(requirements)], env=env)
            constraints.write_text(run(version_command, env=env, capture=True) + '\n', encoding='utf-8')
        else:
            torch_args = [f'torch=={TORCH}', f'torchvision=={VISION}', '--index-url',
                          'https://download.pytorch.org/whl/' + ('cu128' if mode == 'cuda' else 'cpu')]
            run(command + torch_args, env=env)
            constraints.write_text(run(version_command, env=env, capture=True) + '\n', encoding='utf-8')
            run(command + ['--constraint', str(constraints), '--requirements', str(requirements)], env=env)
        if mode == 'cuda':
            # CPU/GPU ORT distributions share the same import package. Install GPU files last.
            run(command + ['--no-deps', '--reinstall-package', 'onnxruntime-gpu', f'onnxruntime-gpu=={ORT}'], env=env)
        run([uv, 'pip', 'check', '--python', str(python)], env=env)
        env = accelerated_env(python, mode)
        env['VPT_MODE'] = mode
        run([python, '-c', VERIFY], env=env)
        stamp.write_text(json.dumps({'signature': signature}), encoding='utf-8')
    else:
        env = accelerated_env(python, mode)
        env['VPT_MODE'] = mode
        run([python, '-c', VERIFY], env=env)
    lock = ROOT / 'front' / 'package-lock.json'
    npm_stamp = cache / 'frontend.sha256'
    npm_signature = hashlib.sha256(lock.read_bytes() + (ROOT / 'front' / 'package.json').read_bytes() +
                                   run([shutil.which('node'), '--version'], capture=True).encode() + platform.system().encode()).hexdigest()
    npm_command = [npm]
    if WINDOWS:
        npm_cli = Path(npm).parent / 'node_modules' / 'npm' / 'bin' / 'npm-cli.js'
        if not npm_cli.is_file():
            raise RuntimeError('Cannot locate npm-cli.js next to npm.cmd. Install a standard Node.js distribution.')
        npm_command = [shutil.which('node'), str(npm_cli)]
    if args.reinstall or not (ROOT / 'front' / 'node_modules' / 'vite').is_dir() or not npm_stamp.exists() or npm_stamp.read_text() != npm_signature:
        run(npm_command + ['ci', '--no-audit', '--no-fund'], cwd=ROOT / 'front', env=env)
        npm_stamp.write_text(npm_signature)
    for target, source in [('config.yaml', 'config.yaml.sample'), ('downloader.json', 'downloader.json.sample.json')]:
        if not (ROOT / target).exists():
            shutil.copyfile(ROOT / source, ROOT / target)
            info(f'Created {target} from the sample.')
    for folder in ('server/db', 'storage', 'output', 'storage/models/audio_separator'):
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    return python, env, cache


BACKEND = r'''
import os, runpy, sys
if os.environ['VPT_MODE'] == 'cuda':
    if sys.platform == 'win32':
        handles = [os.add_dll_directory(p) for p in os.environ['PATH'].split(os.pathsep) if p and os.path.isdir(p)]
    import torch
    import onnxruntime
    onnxruntime.preload_dlls(directory='')
sys.argv = ['uvicorn'] + sys.argv[1:]
runpy.run_module('uvicorn', run_name='__main__')
'''


def stop(process):
    if process.poll() is not None:
        return
    if WINDOWS:
        # taskkill /T is scoped to this launcher child, never to a port or executable name.
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        if not WINDOWS:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def serve(python, env, cache, args):
    children = []
    logs = []
    creation = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if WINDOWS else {'start_new_session': True}
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    if WINDOWS:
        signal.signal(signal.SIGBREAK, interrupted)
    try:
        front_env = env.copy()
        front_env['VITE_API_BASE_URL'] = f'http://127.0.0.1:{args.backend_port}'
        commands = [([str(python), '-c', BACKEND, 'app:app', '--host', '127.0.0.1', '--port', str(args.backend_port)], ROOT / 'server', env, 'backend'),
                    ([shutil.which('node'), str(ROOT / 'front' / 'node_modules' / 'vite' / 'bin' / 'vite.js'), '--host', '0.0.0.0', '--port', str(args.frontend_port), '--strictPort'], ROOT / 'front', front_env, 'frontend')]
        for command, cwd, child_env, name in commands:
            log = open(cache / (name + '.log'), 'w', encoding='utf-8')
            logs.append(log)
            children.append(subprocess.Popen(command, cwd=cwd, env=child_env, stdout=log, stderr=subprocess.STDOUT, **creation))
        urls = [f'http://127.0.0.1:{args.backend_port}/openapi.json', f'http://127.0.0.1:{args.frontend_port}/']
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        pending = set(urls)
        deadline = time.monotonic() + 120
        while pending:
            if any(p.poll() is not None for p in children):
                raise RuntimeError(f'A service exited during startup. See logs in {cache}.')
            if time.monotonic() > deadline:
                raise RuntimeError(f'Service startup timed out. See logs in {cache}.')
            for url in list(pending):
                try:
                    with opener.open(url, timeout=1) as response:
                        if response.status == 200:
                            pending.remove(url)
                except urllib.error.HTTPError as exc:
                    exc.close()
                except (OSError, ValueError):
                    pass
            time.sleep(0.3)
        info(f'VideoPrinterTurbo is ready: {urls[1]}')
        info(f'Logs: {cache}\nPress Ctrl+C to stop both services.')
        while True:
            if any(p.poll() is not None for p in children):
                raise RuntimeError(f'A service stopped unexpectedly. See logs in {cache}.')
            time.sleep(0.5)
    finally:
        for child in reversed(children):
            try:
                stop(child)
            except (OSError, subprocess.TimeoutExpired) as exc:
                info(f'WARNING: Could not stop process {child.pid}: {exc}')
        for log in logs:
            log.close()


def main():
    parser = argparse.ArgumentParser(description='Initialize and start VideoPrinterTurbo locally.')
    parser.add_argument('--mode', choices=('auto', 'cpu', 'cuda', 'mac'), default='auto')
    parser.add_argument('--check', action='store_true', help='Check prerequisites without installing or starting services.')
    parser.add_argument('--reinstall', action='store_true', help='Run dependency installation again.')
    parser.add_argument('--backend-port', type=int, default=8080)
    parser.add_argument('--frontend-port', type=int, default=5173)
    args = parser.parse_args()
    if not (3, 11) <= sys.version_info[:2] < (3, 13):
        raise RuntimeError('Python 3.11 or 3.12 is required.')
    if args.backend_port == args.frontend_port or not all(1 <= p <= 65535 for p in (args.backend_port, args.frontend_port)):
        raise RuntimeError('Choose two different ports between 1 and 65535.')
    tools = {name: shutil.which(name) for name in ('uv', 'node', 'npm', 'ffmpeg', 'ffprobe')}
    missing = [name for name, path in tools.items() if not path]
    if missing:
        raise RuntimeError('Missing required commands: ' + ', '.join(missing) + '. Install them and add them to PATH.')
    for name in ('server/pyproject.toml', 'front/package.json', 'front/package-lock.json', 'config.yaml.sample', 'downloader.json.sample.json'):
        if not (ROOT / name).is_file():
            raise RuntimeError(f'Required project file is missing: {name}')
    mode = select_mode(args.mode)
    for port in (args.backend_port, args.frontend_port):
        check_port(port)
    info(f'Platform: {platform.system()} {platform.machine()}; Python: {platform.python_version()}; mode: {mode}')
    info('Prerequisite checks passed.')
    if args.check:
        info('Acceleration will be verified after dependency installation during a normal start.')
        return
    python, env, cache = initialize(mode, args, tools['uv'], tools['npm'])
    info("aaa")
    sys.exit(0)
    serve(python, env, cache, args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        info('Stopped.')
        sys.exit(130)
    except Exception as exc:
        info(f'ERROR: {exc}')
        sys.exit(1)
