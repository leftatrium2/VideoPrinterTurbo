import json
from datetime import timedelta

import pytest
import srt
from pydub.generators import Sine

from pipeline.tts.duration_controller import build_dubbing_timeline as _build_dubbing_timeline
from utils import const


def build_dubbing_timeline(*args, **kwargs):
    # Existing cases assert the bounded natural-first policy.
    kwargs.setdefault("dubbing_strategy", const.DUBBING_STRATEGY_NATURAL_FIRST)
    return _build_dubbing_timeline(*args, **kwargs)


def sub(start=0, end=1000, text="hello"):
    return srt.Subtitle(1, timedelta(milliseconds=start), timedelta(milliseconds=end), text)


def synthesizer(durations, calls):
    def synth(text, out_path, **kwargs):
        calls.append(text)
        Sine(440).to_audio_segment(duration=durations[text]).export(out_path, format="wav")
    return synth


def test_short_speech_keeps_speed_and_absolute_position(tmp_path):
    calls = []
    timeline = build_dubbing_timeline([sub(1000, 2000)], synthesizer({"hello": 400}, calls), {},
                                     tmp_path, video_duration_ms=3000)
    assert len(timeline) == 3000
    assert timeline[:1000].rms == 0
    assert timeline[1000:1400].rms > 0
    assert timeline[1450:].rms == 0
    assert json.loads((tmp_path / "alignment.json").read_text())[0]["status"] == "short"


def test_rewrite_and_audio_are_reused_and_subtitle_matches(tmp_path):
    calls, rewrites = [], []
    synth = synthesizer({"hello": 1800, "short": 900}, calls)
    def shorten(*args):
        rewrites.append(args)
        return "short"
    out = tmp_path / "final.srt"
    options = dict(shorten=shorten, final_subtitle_path=out, video_duration_ms=2000)
    build_dubbing_timeline([sub()], synth, {}, tmp_path, **options)
    build_dubbing_timeline([sub()], synth, {}, tmp_path, **options)
    assert calls == ["hello", "short"]
    assert len(rewrites) == 1
    assert list(srt.parse(out.read_text()))[0].content == "short"
    build_dubbing_timeline([sub()], synth, {"voice": "new"}, tmp_path, **options)
    assert len(calls) == 4


def test_borrow_is_limited_and_does_not_cross_next_sentence(tmp_path):
    calls = []
    timeline = build_dubbing_timeline([sub(), sub(1400, 2400, "next")],
        synthesizer({"hello": 1300, "next": 500}, calls), {}, tmp_path,
        video_duration_ms=3000, final_subtitle_path=tmp_path / "final.srt")
    final = list(srt.parse((tmp_path / "final.srt").read_text()))
    assert final[0].end == timedelta(milliseconds=1300)
    assert timeline[1320:1400].rms == 0


def test_retries_are_bounded_and_failure_recorded(tmp_path):
    calls, rewrites = [], []
    def shorten(*args):
        rewrites.append(args)
        return "hello"
    with pytest.raises(ValueError, match="manual editing"):
        build_dubbing_timeline([sub()], synthesizer({"hello": 3000}, calls), {},
                               tmp_path, shorten=shorten, video_duration_ms=2000)
    assert len(rewrites) == 2
    assert json.loads((tmp_path / "alignment.json").read_text())[0]["status"] == "too_long"


@pytest.mark.parametrize("subs", [[sub(0, 0)], [sub(0, 2000)], [sub(), sub(500, 1000)]])
def test_invalid_windows_fail_before_synthesis(tmp_path, subs):
    calls = []
    with pytest.raises(ValueError):
        build_dubbing_timeline(subs, synthesizer({}, calls), {}, tmp_path, video_duration_ms=1000)
    assert calls == []


def test_mild_speedup_uses_real_ffmpeg(tmp_path):
    timeline = build_dubbing_timeline([sub()], synthesizer({"hello": 1080}, []), {},
                                     tmp_path, video_duration_ms=1000)
    assert len(timeline) == 1000
    row = json.loads((tmp_path / "alignment.json").read_text())[0]
    assert row["tempo"] == pytest.approx(1.08)


def test_task_beans_are_independent():
    from pipeline.bean.pipeline_data import PipeLineData
    first, second = PipeLineData(), PipeLineData()
    first.tts_bean.final_subtitle_path = "first.srt"
    assert second.tts_bean.final_subtitle_path == ""


def test_no_llm_still_enforces_speed_limit(tmp_path):
    with pytest.raises(ValueError, match="manual editing"):
        build_dubbing_timeline([sub()], synthesizer({"hello": 2000}, []), {}, tmp_path,
                               video_duration_ms=1000)


def test_empty_text_does_not_call_provider(tmp_path):
    calls = []
    timeline = build_dubbing_timeline([sub(text="")], synthesizer({}, calls), {}, tmp_path)
    assert not calls
    assert timeline.rms == 0


def test_silent_synthesis_is_rejected_and_not_cached(tmp_path):
    from pydub import AudioSegment
    def synth(text, out_path):
        AudioSegment.silent(duration=500).export(out_path, format="wav")
    with pytest.raises(ValueError, match="empty TTS"):
        build_dubbing_timeline([sub()], synth, {}, tmp_path)
    assert not list(tmp_path.glob("*.audio"))
    assert json.loads((tmp_path / "alignment.json").read_text())[0]["status"] == "failed"


def test_dubbing_prompt_is_opt_in_and_preserves_timing(monkeypatch):
    from pipeline.llm.llm_utils import LLMUtils
    instructions = []
    def rewrite(client, model, texts, instruction):
        instructions.append(instruction)
        return ["translated"]
    monkeypatch.setattr(LLMUtils, "rewrite_batch", rewrite)
    original = [{"index": "1", "start": "00:00:00,000", "end": "00:00:01,000", "text": "source"}]
    normal = LLMUtils.rewrite_srt(None, "model", original, "translate")
    dubbing = LLMUtils.rewrite_srt(None, "model", original, "translate", dubbing=True)
    assert instructions[0] == "translate"
    assert "软约束" in instructions[1] and "00:00:01,000" in instructions[1]
    assert dubbing == normal
    assert original[0]["text"] == "source"


def test_prompt_contains_valid_input_json():
    from pipeline.llm.llm_utils import LLMUtils
    _, prompt = LLMUtils.build_rewrite_prompt(["one", "two"], "translate")
    payload = json.loads(prompt[prompt.index("[{\""):])
    assert [item["id"] for item in payload] == [0, 1]


@pytest.mark.parametrize("provider_name,class_name,init", [
    ("azure_tts_v1", "AzureTTSV1", {}),
    ("azure_tts_v2", "AzureTTSV2", {"api_key": "test", "region": "test"}),
    ("siliconflow_tts", "SiliconFlowTTS", {"api_key": "test"}),
    ("google_gemini_tts", "GoogleGeminiTTS", {"api_key": "test"}),
])
def test_all_providers_forward_alignment_options(tmp_path, monkeypatch, provider_name, class_name, init):
    import importlib
    from pydub import AudioSegment
    from utils.tts_utils import TTSUtils
    module = importlib.import_module(f"pipeline.tts.{provider_name}")
    async def output_dir():
        return str(tmp_path)
    monkeypatch.setattr(module, "get_tts_rewrite_path", output_dir)
    received = []
    def build(subs, synth, kwargs, temporary, **options):
        received.append(options)
        return AudioSegment.silent(duration=1000)
    monkeypatch.setattr(TTSUtils, "build_timeline", build)
    monkeypatch.setattr(TTSUtils, "export_timeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(AudioSegment, "export", lambda *args, **kwargs: None)
    source = tmp_path / "input.srt"
    source.write_text(srt.compose([sub()]))
    getattr(module, class_name)(**init).rewrite(str(source), "en-US", "voice",
                                              cache_dir=str(tmp_path / "cache"), video_duration_ms=2000)
    assert received == [{"cache_dir": str(tmp_path / "cache"), "video_duration_ms": 2000}]


@pytest.mark.parametrize("duration,accepted", [(1332, True), (1353, True)])
def test_output_time_tolerance_boundary(tmp_path, duration, accepted):
    synth = synthesizer({"hello": duration}, [])
    if not accepted:
        with pytest.raises(ValueError, match="30ms tolerance"):
            build_dubbing_timeline([sub(end=1200)], synth, {}, tmp_path, video_duration_ms=1200)
        return
    timeline = build_dubbing_timeline([sub(end=1200)], synth, {}, tmp_path, video_duration_ms=1200)
    assert len(timeline) == 1200
    row = json.loads((tmp_path / "alignment.json").read_text())[0]
    assert row["tempo"] == pytest.approx(duration / 1200)
    assert row["tolerance_ms"] <= 30


@pytest.mark.parametrize("duration,accepted", [(2244, True), (2280, True), (2281, False)])
def test_fallback_speedup_has_hard_limit(tmp_path, caplog, duration, accepted):
    synth = synthesizer({"hello": duration}, [])
    if not accepted:
        with pytest.raises(ValueError, match="fallback limit 1.2x"):
            build_dubbing_timeline([sub(end=1900)], synth, {}, tmp_path, video_duration_ms=1900)
        return
    timeline = build_dubbing_timeline([sub(end=1900)], synth, {}, tmp_path, video_duration_ms=1900)
    assert len(timeline) == 1900
    row = json.loads((tmp_path / "alignment.json").read_text())[0]
    assert row["status"] == "fallback_speedup"
    assert row["tempo"] <= 1.2
    assert "speech=" in caplog.text and "target=1900ms" in caplog.text


def test_fallback_only_after_rewrites_and_before_next_speech(tmp_path):
    rewrites = []
    def shorten(*args):
        rewrites.append(args)
        return "short"
    build_dubbing_timeline([sub(), sub(1100, 2100, "next")],
        synthesizer({"hello": 2000, "short": 1300, "next": 500}, []), {}, tmp_path,
        shorten=shorten, video_duration_ms=2100)
    assert len(rewrites) == 2
    row = json.loads((tmp_path / "alignment.json").read_text())[0]
    assert row["status"] == "fallback_speedup"
    assert row["borrowed_ms"] == 100
    assert row["tempo"] == pytest.approx(1300 / 1100)


def test_all_overlong_segments_are_reported_and_audio_reused(tmp_path, caplog):
    calls = []
    synth = synthesizer({"first": 1700, "okay": 800, "last": 1600}, calls)
    subs = [sub(0, 1000, "first"), sub(1000, 2000, "okay"), sub(2000, 3000, "last")]
    output = tmp_path / "final.srt"
    for _ in range(2):
        with pytest.raises(ValueError, match="2/3 subtitles too long") as error:
            build_dubbing_timeline(subs, synth, {}, tmp_path,
                                   video_duration_ms=3000, final_subtitle_path=output)
        assert "Subtitle 1" in str(error.value) and "Subtitle 3" in str(error.value)
    assert calls == ["first", "okay", "last"]
    rows = json.loads((tmp_path / "alignment.json").read_text())
    assert [r["status"] for r in rows] == ["too_long", "accepted", "too_long"]
    assert rows[0]["final_text"] == "first"
    assert rows[0]["required_tempo"] == pytest.approx(1.7)
    assert rows[2]["available_ms"] == 1000
    assert "continuing remaining subtitles" in caplog.text
    assert not output.exists()


def test_default_timeline_strategy_fits_and_warns(tmp_path, caplog):
    final = tmp_path / "final.srt"
    timeline = _build_dubbing_timeline([sub()], synthesizer({"hello": 2100}, []), {}, tmp_path,
                                      video_duration_ms=1000, final_subtitle_path=final)
    assert len(timeline) == 1000
    row = json.loads((tmp_path / "alignment.json").read_text())[0]
    assert row["dubbing_strategy"] == const.DUBBING_STRATEGY_TIMELINE_FIRST
    assert row["status"] == "forced_speedup" and row["tempo"] == pytest.approx(2.1)
    assert "forced speedup" in caplog.text
    assert list(srt.parse(final.read_text()))[0].content == "hello"


def test_strategy_switch_reuses_audio_but_rechecks_limits(tmp_path):
    calls = []
    synth = synthesizer({"hello": 2100}, calls)
    _build_dubbing_timeline([sub()], synth, {}, tmp_path, video_duration_ms=1000)
    with pytest.raises(ValueError, match="too long"):
        _build_dubbing_timeline([sub()], synth, {}, tmp_path, video_duration_ms=1000,
                                dubbing_strategy=const.DUBBING_STRATEGY_NATURAL_FIRST)
    assert calls == ["hello"]
    assert json.loads((tmp_path / "alignment.json").read_text())[0]["status"] == "too_long"


def test_best_candidate_survives_worse_last_retry(tmp_path):
    rewrites = iter(["better", "worse"])
    synth = synthesizer({"hello": 2000, "better": 1150, "worse": 1600}, [])
    final = tmp_path / "final.srt"
    build_dubbing_timeline([sub()], synth, {}, tmp_path, video_duration_ms=1000,
                          shorten=lambda *args: next(rewrites), final_subtitle_path=final)
    row = json.loads((tmp_path / "alignment.json").read_text())[0]
    assert row["selected_attempt"] == 1
    assert row["duration_ms"] == 1150
    assert row["tempo"] == pytest.approx(1.15)
    assert list(srt.parse(final.read_text()))[0].content == "better"


@pytest.mark.parametrize("strategy", [0, 3, "timeline_first", "1", 1.0, True, None])
def test_invalid_strategy_rejected_at_public_entry(strategy):
    from pipeline.utils.pipeline_tts_utils import tts_from_subtitle
    with pytest.raises(ValueError, match="Unsupported dubbing_strategy"):
        tts_from_subtitle("unused", "missing.srt", "voice", "en", dubbing_strategy=strategy)


@pytest.mark.parametrize("strategy", [const.DUBBING_STRATEGY_TIMELINE_FIRST,
                                      const.DUBBING_STRATEGY_NATURAL_FIRST])
@pytest.mark.parametrize("name,engine", [
    ("AzureTTSV1", const.TTS_LIST_AZURE_TTS_V1_VAL),
    ("AzureTTSV2", const.TTS_LIST_AZURE_TTS_V2_VAL),
    ("SiliconFlowTTS", const.TTS_LIST_SILICON_FLOW_TTS_VAL),
    ("GoogleGeminiTTS", const.TTS_LIST_GOOGLE_GEMINI_TTS_VAL),
])
def test_public_entry_passes_strategy_to_each_provider(monkeypatch, strategy, name, engine):
    from unittest.mock import MagicMock
    from pipeline.utils import pipeline_tts_utils as module
    provider = MagicMock()
    monkeypatch.setattr(module, name, provider)
    module.tts_from_subtitle(engine, "input.srt", "voice", "en", api_key="test", region="test",
                             dubbing_strategy=strategy)
    provider.return_value.rewrite.assert_called_once_with(
        "input.srt", "en", "voice", dubbing_strategy=strategy)
