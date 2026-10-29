"""Real HTTP tests against the documented local Postman fal simulation."""
import array
import base64
import os
import subprocess

import pytest
import requests

from pipeline.lip_sync.fal_latentsync import FalLatentSync
from test_sync_labs import media  # shared real one-second video/audio fixture


@pytest.fixture
def simulation(media):
    url=os.getenv("VPT_FAL_SIM_URL")
    if not url:
        pytest.skip("Set VPT_FAL_SIM_URL after starting tests/lip_sync_mock/fal.sim.yaml")
    with requests.Session() as client:
        client.trust_env=False
        def reset(mode="success", content=None):
            client.post(f"{url}/control", json={"mode":mode,"media":base64.b64encode(
                content if content is not None else media[0].read_bytes()).decode()},timeout=5).raise_for_status()
        reset()
        yield url,client,reset


def service(url,**kwargs):
    return FalLatentSync("test-only",queue_base_url=url,storage_base_url=url,poll_interval=0.01,**kwargs)


def test_real_upload_queue_result_and_final_voice(simulation,media,tmp_path):
    url,client,_=simulation
    adapter=service(url,seed=123,guidance_scale=1.5)
    output=tmp_path/"output.mp4"
    assert adapter.lip_sync(*map(str,media),str(output))==str(output)
    state=client.get(f"{url}/state",timeout=5).json()
    assert state["submitted"]==1 and state["polls"]==3
    assert state["arguments"]["seed"]==123
    assert state["arguments"]["guidance_scale"]==1.5
    assert adapter.last_request_id=="request-1"
    samples=array.array('h',subprocess.check_output(["ffmpeg","-v","error","-i",str(output),"-vn",
                                                    "-ac","1","-ar","16000","-f","s16le","-"]))
    frequency=sum(a<=0<b for a,b in zip(samples,samples[1:]))/(len(samples)/16000)
    assert 800<frequency<950
    assert all(p.exists() for p in media)


@pytest.mark.parametrize("mode,message",[("failed","no face"),("unknown","unknown status"),
    ("pending","timed out locally"),("unauthorized","HTTP 401"),("empty","empty video"),
    ("missing_video","missing video"),("result_error","HTTP 422"),("foreign_url","outside the configured")])
def test_real_http_errors_leave_no_output(simulation,media,tmp_path,mode,message):
    url,client,reset=simulation
    reset(mode)
    adapter=service(url,job_timeout=0.1)
    with pytest.raises((RuntimeError,ValueError,TimeoutError),match=message) as exc:
        adapter.lip_sync(*map(str,media),str(tmp_path/"out.mp4"))
    assert "test-only" not in str(exc.value)
    assert not (tmp_path/"out.mp4").exists()
    assert not list(tmp_path.glob("fal_lip_sync_*"))
    assert client.get(f"{url}/state",timeout=5).json()["submitted"]<=1


def test_invalid_output_and_remote_retime_are_rejected(simulation,media,tmp_path):
    url,_,reset=simulation
    for content,match in [(b"not a video","unreadable video")]:
        reset(content=content)
        with pytest.raises(ValueError,match=match):
            service(url).lip_sync(*map(str,media),str(tmp_path/"out.mp4"))
    long=tmp_path/"long.mp4"
    subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","color=s=64x64:r=25:d=2","-c:v","libx264",str(long)],check=True)
    reset(content=long.read_bytes())
    with pytest.raises(ValueError,match="changed the video duration"):
        service(url).lip_sync(*map(str,media),str(tmp_path/"out.mp4"))


def test_preflight_does_not_call_service(media,tmp_path):
    output=tmp_path/"existing.mp4"
    output.write_bytes(b"keep")
    with pytest.raises(ValueError,match="new file"):
        service("http://127.0.0.1:1").lip_sync(*map(str,media),str(output))
    assert output.read_bytes()==b"keep"
    long=tmp_path/"long.wav"
    subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","sine=duration=2",str(long)],check=True)
    with pytest.raises(ValueError,match="must not exceed"):
        service("http://127.0.0.1:1").lip_sync(str(media[0]),str(long),str(tmp_path/"out.mp4"))


@pytest.mark.parametrize("kwargs",[{"api_key":""},{"api_key":"test","seed":True},
    {"api_key":"test","guidance_scale":0},{"api_key":"test","job_timeout":float('nan')}])
def test_config(kwargs):
    with pytest.raises(ValueError): FalLatentSync(**kwargs)


def test_queue_and_logs_reach_progress_callback(simulation, media, tmp_path):
    url, client, _ = simulation
    events = []
    service(url, on_progress=events.append).lip_sync(*map(str, media), str(tmp_path / 'progress.mp4'))
    assert any(event['stage'] == 'queued' and event['queue_position'] == 3 for event in events)
    assert any(event['stage'] == 'running' and event['detail'] == 'Model running' for event in events)
    assert client.get(f'{url}/state', timeout=5).json()['logsRequested']
    assert events[-1]['stage'] == 'completed'
