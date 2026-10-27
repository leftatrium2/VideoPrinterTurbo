"""Bounded dubbing alignment shared by all speech providers."""
import hashlib
import json
import logging
from datetime import timedelta
from pathlib import Path

import srt
from pydub import AudioSegment
from pydub.silence import detect_leading_silence

from utils import const

logger = logging.getLogger(__name__)
MAX_TEMPO = 1.1
FALLBACK_MAX_TEMPO = 1.2
MAX_REWRITES = 2
MAX_BORROW_MS = 500
# Allow a small output-time tolerance, then fit the complete speech to the window.
BOUNDARY_TOLERANCE_MS = 30


def validate_dubbing_strategy(strategy):
    if type(strategy) is not int or strategy not in (
            const.DUBBING_STRATEGY_TIMELINE_FIRST, const.DUBBING_STRATEGY_NATURAL_FIRST):
        raise ValueError(f"Unsupported dubbing_strategy: {strategy!r}")


def fits_window(duration_ms, window_ms):
    return duration_ms / MAX_TEMPO <= window_ms + BOUNDARY_TOLERANCE_MS


def build_dubbing_timeline(subs, synth_fn, synth_kwargs, cache_dir, *,
                           shorten=None, source_subs=None, video_duration_ms=None,
                           final_subtitle_path=None, rewrite_context="",
                           source_subtitle_ids=None, group_for_dubbing=False,
                           dubbing_strategy: int = const.DUBBING_STRATEGY_TIMELINE_FIRST):
    from utils.tts_utils import TTSUtils

    validate_dubbing_strategy(dubbing_strategy)
    if not subs:
        raise ValueError("No subtitles for dubbing")
    total = video_duration_ms or max(TTSUtils.timedelta_to_ms(s.end) for s in subs)
    for i, sub in enumerate(subs):
        start, end = map(TTSUtils.timedelta_to_ms, (sub.start, sub.end))
        if start < 0 or end <= start or end > total:
            raise ValueError(f"Subtitle {i + 1}: invalid time window")
        if i and sub.start < subs[i - 1].end:
            raise ValueError(f"Subtitle {i + 1}: overlapping time window")
    if group_for_dubbing:
        from pipeline.tts.dubbing_segments import group_subtitles
        subs, source_subtitle_ids = group_subtitles(subs)
    if source_subtitle_ids is None:
        source_subtitle_ids = [[sub.index] for sub in subs]
    if len(source_subtitle_ids) != len(subs):
        raise ValueError("Dubbing segment/source subtitle mapping mismatch")
    if source_subs is not None and (len(source_subs) != len(subs) or any(
            source.start != sub.start or source.end != sub.end
            for source, sub in zip(source_subs, subs))):
        raise ValueError("Dubbing segment/source time windows mismatch")
    logger.info("Dubbing: %s segments from %s source subtitles", len(subs),
                sum(len(ids) for ids in source_subtitle_ids))
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    timeline = AudioSegment.silent(duration=total, frame_rate=48000)
    final, report = [], []
    safe_params = {k: v for k, v in synth_kwargs.items()
                   if k not in {"key", "api_key", "proxy"}}
    source_digest = hashlib.sha256(json.dumps(
        [s.content for s in source_subs] if source_subs else [], ensure_ascii=False
    ).encode()).hexdigest()
    try:
        for i, sub in enumerate(subs):
            start, end = map(TTSUtils.timedelta_to_ms, (sub.start, sub.end))
            target = end - start
            next_start = TTSUtils.timedelta_to_ms(subs[i + 1].start) if i + 1 < len(subs) else total
            available = target + min(MAX_BORROW_MS, max(0, next_start - end))
            text = sub.content.strip()
            if not text:
                final.append(sub)
                report.append({"index": i + 1, "status": "empty", "dubbing_strategy": dubbing_strategy,
                               "source_subtitle_ids": source_subtitle_ids[i],
                               "start_ms": start, "end_ms": end})
                continue
            row = {"index": i + 1, "dubbing_strategy": dubbing_strategy, "source_subtitle_ids": source_subtitle_ids[i],
                   "source_text": source_subs[i].content if source_subs is not None else sub.content,
                   "start_ms": start, "end_ms": end,
                   "target_ms": target, "status": "processing", "attempts": []}
            report.append(row)
            rewrite_identity = {"version": 2, "text": text, "params": safe_params,
                                "provider": synth_fn.__qualname__, "target": target,
                                "context": rewrite_context,
                                "sources": source_digest}
            rewrite_key = hashlib.sha256(json.dumps(rewrite_identity, sort_keys=True).encode()).hexdigest()
            rewrite_file = cache / f"{rewrite_key}.json"
            rewrites = json.loads(rewrite_file.read_text()) if rewrite_file.exists() else {}
            clip = None
            fallback_used = False
            forced_used = False
            best = None
            for attempt in range(MAX_REWRITES + 1):
                identity = {"version": 1, "provider": synth_fn.__qualname__,
                            "text": text, "params": safe_params}
                key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
                raw = cache / f"{key}.audio"
                if not raw.exists():
                    pending = cache / f"{key}.pending"
                    synth_fn(text, out_path=str(pending), **synth_kwargs)
                    audio = AudioSegment.from_file(pending)
                    if not len(audio) or audio.rms == 0:
                        raise ValueError(f"Subtitle {i + 1}: empty TTS audio")
                    pending.replace(raw)
                audio = AudioSegment.from_file(raw)
                # Trim only outer silence, leaving a small natural margin.
                lead = max(0, detect_leading_silence(audio) - 30)
                tail = max(0, detect_leading_silence(audio.reverse()) - 30)
                clip = audio[lead:len(audio) - tail if tail else len(audio)]
                if not len(clip) or clip.rms == 0:
                    raise ValueError(f"Subtitle {i + 1}: silent TTS audio")
                row["attempts"].append({"text": text, "duration_ms": len(clip), "audio": raw.name})
                if best is None or len(clip) < len(best[0]):
                    best = (clip, text, attempt, raw.name)
                if fits_window(len(clip), target):
                    window = target
                    break
                if shorten and attempt < MAX_REWRITES:
                    candidate = rewrites.get(str(attempt))
                    if candidate is None:
                        candidate = shorten(i, text, len(clip), target)
                    if not isinstance(candidate, str) or not candidate.strip():
                        raise ValueError(f"Subtitle {i + 1}: empty rewrite")
                    rewrites[str(attempt)] = candidate.strip()
                    pending_rewrite = rewrite_file.with_suffix(".pending.json")
                    pending_rewrite.write_text(json.dumps(rewrites, ensure_ascii=False), encoding="utf-8")
                    pending_rewrite.replace(rewrite_file)
                    text = candidate.strip()
                    continue
                break
            # All candidates here are too long unless a normal fit ended the loop.
            # Keep the shortest complete candidate instead of blindly using the last retry.
            clip, text, selected_attempt, selected_audio = best
            raw_duration_ms = len(clip)
            row.update(selected_attempt=selected_attempt, selected_audio=selected_audio,
                       duration_ms=raw_duration_ms, available_ms=available)
            if fits_window(len(clip), target):
                window = target
            elif fits_window(len(clip), available):
                window = available
            elif len(clip) <= available * FALLBACK_MAX_TEMPO:
                window = available
                fallback_used = True
                logger.warning(
                    "Subtitle %s: fallback speedup %.3fx; speech=%sms, target=%sms, available=%sms, limit=%.1fx",
                    i + 1, len(clip) / window, len(clip), target, available, FALLBACK_MAX_TEMPO,
                )
            elif dubbing_strategy == const.DUBBING_STRATEGY_TIMELINE_FIRST:
                window = available
                forced_used = True
                logger.warning(
                    "Subtitle %s (source IDs %s): forced speedup %.3fx; speech=%sms, target=%sms, available=%sms",
                    i + 1, source_subtitle_ids[i], len(clip) / window, len(clip), target, available,
                )
            else:
                message = (f"Subtitle {i + 1} (source IDs {source_subtitle_ids[i]}): speech {len(clip)}ms cannot fit "
                           f"{available}ms; normal limit {MAX_TEMPO}x with {BOUNDARY_TOLERANCE_MS}ms tolerance, "
                           f"fallback limit {FALLBACK_MAX_TEMPO}x; manual editing required")
                row.update(status="too_long", final_text=text,
                           required_tempo=len(clip) / available, error=message)
                logger.warning("%s; continuing remaining subtitles", message)
                continue
            tolerance_ms = max(0, len(clip) / MAX_TEMPO - window)
            tempo = max(1.0, len(clip) / window)
            if tempo > 1:
                trimmed = cache / f"trim_{i}.wav"
                fitted = cache / f"fit_{i}.wav"
                clip.export(trimmed, format="wav")
                TTSUtils.stretch_to_duration(str(trimmed), str(fitted), window)
                clip = AudioSegment.from_file(fitted)
            row.update(status="forced_speedup" if forced_used else
            "fallback_speedup" if fallback_used else
            ("short" if len(clip) < target * 0.5 else "accepted"),
                       final_text=text, tempo=tempo,
                       tolerance_ms=0 if fallback_used or forced_used else tolerance_ms,
                       forced_speedup=forced_used,
                       fallback_used=fallback_used,
                       borrowed_ms=max(0, len(clip) - target))
            if row["status"] == "short":
                logger.warning("Subtitle %s: speech covers less than half its window", i + 1)
            timeline = timeline.overlay(clip, position=start)
            final.append(srt.Subtitle(sub.index, sub.start,
                                      timedelta(milliseconds=max(end, start + len(clip))),
                                      text, sub.proprietary))
        failures = [row for row in report if row["status"] == "too_long"]
        if failures:
            details = "\n".join(row["error"] for row in failures)
            raise ValueError(f"Dubbing alignment: {len(failures)}/{len(subs)} subtitles too long. "
                             f"All subtitles checked; report: {cache / 'alignment.json'}\n{details}")
        if final_subtitle_path:
            destination = Path(final_subtitle_path)
            pending = destination.with_suffix(".pending.srt")
            pending.write_text(srt.compose(final), encoding="utf-8")
            pending.replace(destination)
        return timeline
    finally:
        for row in report:
            if row["status"] == "processing":
                row["status"] = "failed"
        (cache / "alignment.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
