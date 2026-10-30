param(
    [string]$Python = "$PSScriptRoot/../server/.venv/Scripts/python.exe",
    [string]$FFmpegDirectory = ""
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path "$PSScriptRoot/..").Path
if (!$FFmpegDirectory) { $FFmpegDirectory = Split-Path (Get-Command ffmpeg.exe -ErrorAction Stop).Source }
foreach ($binary in @('ffmpeg.exe', 'ffprobe.exe')) {
    if (!(Test-Path -LiteralPath (Join-Path $FFmpegDirectory $binary))) { throw "Missing $binary in $FFmpegDirectory" }
}
$env:VPT_FFMPEG_DIR = (Resolve-Path $FFmpegDirectory).Path
$Python = (Resolve-Path $Python).Path
Push-Location "$repo/front"
$previousApi = $env:VITE_API_BASE_URL
try {
    $env:VITE_API_BASE_URL = '/api'
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
} finally {
    $env:VITE_API_BASE_URL = $previousApi
    Pop-Location
}
Push-Location $repo
try {
    & $Python -m PyInstaller --noconfirm --clean desktop/VideoPrinterTurbo.spec
    if ($LASTEXITCODE -ne 0) { throw 'EXE build failed' }
    & "$repo/dist/VideoPrinterTurbo.exe" --check-binaries
    if ($LASTEXITCODE -ne 0) { throw 'Bundled FFmpeg/ffprobe check failed' }
} finally { Pop-Location }
