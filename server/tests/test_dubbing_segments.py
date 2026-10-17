import json
from datetime import timedelta

import pytest
import srt
from pydub.generators import Sine

from pipeline.tts.dubbing_segments import group_subtitles, as_rewrite_subtitles
from pipeline.tts.duration_controller import build_dubbing_timeline


def cue(index, start, end, text):
    return srt.Subtitle(index, timedelta(milliseconds=start), timedelta(milliseconds=end), text)


def test_complete_sentence_groups_fragmented_cues_without_mutation():
    subs = [cue(3, 0, 1000, "These people"), cue(4, 1000, 2000, "use AI"),
            cue(5, 2000, 3000, "when stuck."), cue(6, 3000, 4000, "Next sentence.")]
    grouped, mappings = group_subtitles(subs)
    assert mappings == [[3, 4, 5], [6]]
    assert grouped[0].content == "These people use AI when stuck."
    assert grouped[0].start == subs[0].start and grouped[0].end == subs[2].end
    assert subs[0].content == "These people"
    assert as_rewrite_subtitles(grouped)[0]["end"] == "00:00:03,000"


@pytest.mark.parametrize("next_start,next_text", [(1200, "continuation"), (1000, "- Another speaker"),
                                                   (1000, "[Alice] Hello"), (1000, "Bob: Hello")])
def test_pauses_and_speaker_markers_are_boundaries(next_start, next_text):
    _, ids = group_subtitles([cue(1, 0, 1000, "unfinished"), cue(2, next_start, 2000, next_text)])
    assert ids == [[1], [2]]


def test_sentence_and_size_boundaries():
    _, ids = group_subtitles([cue(i + 1, i * 1000, (i + 1) * 1000, "word") for i in range(8)])
    assert ids == [list(range(1, 7)), [7, 8]]
    _, ids = group_subtitles([cue(1, 0, 6000, "long phrase"), cue(2, 6000, 11000, "continuation")])
    assert ids == [[1], [2]]
    _, ids = group_subtitles([cue(1, 0, 1000, "结束。"), cue(2, 1000, 2000, "下一句")])
    assert ids == [[1], [2]]


def test_grouping_preserves_pause_in_actual_timeline(tmp_path):
    subs = [cue(1, 0, 700, "part"), cue(2, 700, 2000, "two."), cue(3, 2500, 3500, "Next.")]
    calls = []
    def synth(text, out_path, **kwargs):
        calls.append(text)
        Sine(440).to_audio_segment(duration=1000 if text == "part two." else 800).export(out_path, format="wav")
    final = tmp_path / "final.srt"
    timeline = build_dubbing_timeline(subs, synth, {}, tmp_path, group_for_dubbing=True,
                                     final_subtitle_path=final, video_duration_ms=4000)
    assert calls == ["part two.", "Next."]
    assert timeline[2000:2500].rms == 0
    assert timeline[2500:3000].rms > 0
    output = list(srt.parse(final.read_text()))
    assert [s.content for s in output] == calls
    rows = json.loads((tmp_path / "alignment.json").read_text())
    assert [r["source_subtitle_ids"] for r in rows] == [[1, 2], [3]]


def test_unmatched_source_windows_are_rejected_before_synthesis(tmp_path):
    with pytest.raises(ValueError, match="time windows mismatch"):
        build_dubbing_timeline([cue(1, 0, 1000, "translation")], None, {}, tmp_path,
                               source_subs=[cue(1, 0, 900, "source")])


def test_llm_receives_grouped_source_before_translation(tmp_path, monkeypatch):
    import pipeline.llm.openai_provider as module
    source = tmp_path / "source.srt"
    destination = tmp_path / "translated.srt"
    source.write_text(srt.compose([cue(1, 0, 1000, "Hello"), cue(2, 1000, 2000, "world.")]))
    monkeypatch.setattr(module, "OpenAI", lambda **kwargs: object())
    received = []
    def rewrite(client, model, subtitles, prompt, **options):
        received.extend(subtitles)
        return [dict(sub, text="你好世界。") for sub in subtitles]
    monkeypatch.setattr(module.LLMUtils, "rewrite_srt", rewrite)
    assert module.OpenAIProvider("test", "https://example.test", "model").rewrite(
        "translate", str(source), str(destination), dubbing=True)
    assert [s["text"] for s in received] == ["Hello world."]
    assert list(srt.parse(destination.read_text()))[0].end == timedelta(seconds=2)
