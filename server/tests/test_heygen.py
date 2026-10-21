"""HeyGen v3 contract tests over actual HTTP using the local Postman simulation."""
import array
import base64
import os
import subprocess

import pytest
import requests

from pipeline.lip_sync.heygen import HeyGen
from test_sync_labs import media


@pytest.fixture
def simulation(media):
    url = os.getenv("VPT_HEYGEN_SIM_URL")
    if not url:
        pytest.skip("Start heygen.sim.yaml and set VPT_HEYGEN_SIM_URL")
    with requests.Session() as client:
        client.trust_env = False
        def reset(mode="success", content=None):
            client.post(f"{url}/control", json={"mode":mode,"media":base64.b64encode(
                content if content is not None else media[0].read_bytes()).decode()}, timeout=5).raise_for_status()
        reset()
        yield url, client, reset


def service(url, **kwargs):
    return HeyGen("test-only", base_url=f"{url}/v3", poll_interval=0.01, **kwargs)


@pytest.mark.parametrize("mode", ["precision", "speed"])
def test_full_http_flow_and_original_voice_replacement(simulation, media, tmp_path, mode):
    url, client, _ = simulation
    adapter = service(url, mode=mode)
    output = tmp_path / "output.mp4"
    assert adapter.lip_sync(*map(str, media), str(output)) == str(output)
    state = client.get(f"{url}/state", timeout=5).json()
    assert state['submitted'] == 1 and state['polls'] == 3
    assert all(x['uploaded'] and x['completed'] for x in state['assets'].values())
    assert state['arguments']['mode'] == mode
    assert state['arguments']['enable_dynamic_duration'] is False
    assert adapter.last_lipsync_id == 'ls-1'
    samples = array.array('h', subprocess.check_output(["ffmpeg","-v","error","-i",str(output),
                          "-vn","-ac","1","-ar","16000","-f","s16le","-"]))
    frequency = sum(a<=0<b for a,b in zip(samples,samples[1:]))/(len(samples)/16000)
    assert 800 < frequency < 950
    assert all(p.exists() for p in media)


@pytest.mark.parametrize("mode,message", [("failed","face not found"),("unknown","unknown status"),
    ("pending","timed out locally"),("unauthorized","HTTP 401"),("empty","empty output"),
    ("missing_headers","upload_headers"),("size_limit","upload size limit"),
    ("complete_error","HTTP 422"),("missing_id","missing lipsync_id"),("missing_url","missing video_url")])
def test_real_http_failures_clean_up(simulation, media, tmp_path, mode, message):
    url, client, reset = simulation
    reset(mode)
    output = tmp_path / "out.mp4"
    adapter = service(url, job_timeout=0.1)
    with pytest.raises((ValueError,RuntimeError,TimeoutError), match=message) as exc:
        adapter.lip_sync(*map(str,media),str(output))
    assert "test-only" not in str(exc.value)
    assert not output.exists() and not list(tmp_path.glob('heygen_lip_sync_*'))
    assert client.get(f"{url}/state", timeout=5).json()['submitted'] <= 1


def test_m4a_tts_input_is_converted_to_wav(simulation, media, tmp_path):
    url, client, _ = simulation
    m4a = tmp_path / "tts.m4a"
    subprocess.run(["ffmpeg","-v","error","-i",str(media[1]),"-c:a","aac",str(m4a)],check=True)
    service(url).lip_sync(str(media[0]),str(m4a),str(tmp_path/'out.mp4'))
    assets = client.get(f"{url}/state",timeout=5).json()['assets']
    assert assets['2']['content_type'] == 'audio/wav'
    assert assets['2']['filename'].endswith('.wav')
    assert m4a.exists()


def test_bad_downloads_and_changed_timeline_rejected(simulation, media, tmp_path):
    url, _, reset = simulation
    reset(content=b'invalid video')
    with pytest.raises(ValueError,match='unreadable video'):
        service(url).lip_sync(*map(str,media),str(tmp_path/'out.mp4'))
    long = tmp_path/'long.mp4'
    subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","color=s=64x64:r=25:d=2","-c:v","libx264",str(long)],check=True)
    reset(content=long.read_bytes())
    with pytest.raises(ValueError,match='changed the video duration'):
        service(url).lip_sync(*map(str,media),str(tmp_path/'out.mp4'))


def test_preflight_keeps_existing_files(media, tmp_path):
    output=tmp_path/'existing.mp4'; output.write_bytes(b'keep')
    with pytest.raises(ValueError,match='new file'):
        service('http://127.0.0.1:1').lip_sync(*map(str,media),str(output))
    assert output.read_bytes()==b'keep'


@pytest.mark.parametrize('options',[{'api_key':''},{'api_key':'test','mode':'other'},
    {'api_key':'test','job_timeout':0},{'api_key':'test','poll_interval':float('nan')}])
def test_config_validation(options):
    with pytest.raises(ValueError): HeyGen(**options)
