"""Real HTTP tests. Start the documented local Postman simulation and set VPT_SYNC_SIM_URL."""
import base64
import json
import os
import subprocess
from pathlib import Path

import pytest
import requests

from pipeline.lip_sync.sync_labs import SyncLabs


@pytest.fixture(scope="module")
def media(tmp_path_factory):
    path = tmp_path_factory.mktemp("sync_media")
    video, audio = path / "input.mp4", path / "voice.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=64x64:r=25:d=1",
                    "-f", "lavfi", "-i", "sine=frequency=220:duration=1", "-c:v", "libx264", "-c:a", "aac",
                    "-shortest", str(video)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=880:duration=1", str(audio)], check=True)
    return video, audio


@pytest.fixture
def simulation(media):
    url = os.getenv("VPT_SYNC_SIM_URL")
    if not url:
        pytest.skip("Set VPT_SYNC_SIM_URL after starting tests/lip_sync_mock/sync.sim.yaml")
    with requests.Session() as client:
        client.trust_env = False
        def reset(mode="success", content=None):
            response = client.post(f"{url}/control", json={"mode": mode,
                                   "media": base64.b64encode(content if content is not None else media[0].read_bytes()).decode()}, timeout=5)
            response.raise_for_status()
        reset()
        yield url, client, reset


def service(url, **kwargs):
    return SyncLabs("test-only", base_url=f"{url}/v2", poll_interval=0.01, **kwargs)


def test_full_http_flow_validates_assets_and_replaces_original_voice(simulation, media, tmp_path):
    import array
    url, client, _ = simulation
    output = tmp_path / "output.mp4"
    adapter = service(url)
    assert adapter.lip_sync(*map(str, media), str(output)) == str(output)
    state = client.get(f"{url}/state", timeout=5).json()
    assert len(state["assets"]) == 2
    assert state["jobs"]["job-1"]["polls"] == 2
    assert adapter.last_generation_id == "job-1"
    samples = array.array('h', subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(output),
                          "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"]))
    crossings = sum(a <= 0 < b for a, b in zip(samples, samples[1:]))
    frequency = crossings / (len(samples) / 16000)
    assert 800 < frequency < 950  # supplied 880Hz voice, not source 220Hz voice
    assert all(p.exists() for p in media)


@pytest.mark.parametrize("mode,message", [("failed", "FAILED"), ("rejected", "REJECTED"),
                                            ("unauthorized", "HTTP 401"), ("empty", "empty output"),
                                            ("pending", "timed out locally")])
def test_http_failures_leave_no_final_output(simulation, media, tmp_path, mode, message):
    url, _, reset = simulation
    reset(mode)
    output = tmp_path / "output.mp4"
    with pytest.raises((RuntimeError, TimeoutError), match=message) as exc:
        service(url, job_timeout=0.08).lip_sync(*map(str, media), str(output))
    assert "test-only" not in str(exc.value)
    assert not output.exists()
    assert not list(tmp_path.glob("lip_sync_*"))


def test_invalid_download_is_rejected(simulation, media, tmp_path):
    url, _, reset = simulation
    reset(content=b"not a video")
    with pytest.raises(ValueError, match="unreadable video"):
        service(url).lip_sync(*map(str, media), str(tmp_path / "output.mp4"))
    assert not (tmp_path / "output.mp4").exists()


def test_input_duration_mismatch_fails_before_http(media, tmp_path):
    bad_audio = tmp_path / "long.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=duration=2", str(bad_audio)], check=True)
    with pytest.raises(ValueError, match="share a timeline"):
        service("http://127.0.0.1:1").lip_sync(str(media[0]), str(bad_audio), str(tmp_path / "output.mp4"))


def test_existing_output_is_never_overwritten(media, tmp_path):
    output = tmp_path / "existing.mp4"
    output.write_bytes(b"original")
    with pytest.raises(ValueError, match="new file"):
        service("http://127.0.0.1:1").lip_sync(*map(str, media), str(output))
    assert output.read_bytes() == b"original"


@pytest.mark.parametrize("options", [{"api_key":""}, {"api_key":"test", "job_timeout":0},
                                       {"api_key":"test", "poll_interval":float("nan")}])
def test_configuration_validation(options):
    with pytest.raises(ValueError):
        SyncLabs(**options)


def test_remote_duration_change_is_rejected(simulation, media, tmp_path):
    url, _, reset = simulation
    long_video = tmp_path / "long.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=s=64x64:r=25:d=2",
                    "-c:v", "libx264", str(long_video)], check=True)
    reset(content=long_video.read_bytes())
    with pytest.raises(ValueError, match="changed the video duration"):
        service(url).lip_sync(*map(str, media), str(tmp_path / "output.mp4"))
    assert not (tmp_path / "output.mp4").exists()


def test_redirected_output_download(simulation, media, tmp_path):
    url, client, reset = simulation
    reset("redirect")
    output = tmp_path / "redirected.mp4"
    adapter = service(url)
    assert adapter.lip_sync(*map(str, media), str(output)) == str(output)
    assert output.stat().st_size > 0
    assert len(client.get(f"{url}/state", timeout=5).json()["jobs"]) == 1


@pytest.mark.parametrize("mode,message", [("loop", "exceeded 5 redirects"),
                                         ("unsafe", "require HTTPS"),
                                         ("missing_location", "missing Location")])
def test_redirected_output_rejects_invalid_redirects(simulation, media, tmp_path, mode, message):
    url, _, reset = simulation
    reset(mode)
    output = tmp_path / "rejected.mp4"
    with pytest.raises((RuntimeError, ValueError), match=message):
        service(url).lip_sync(*map(str, media), str(output))
    assert not output.exists()
