"""Subtitle service — Whisper-based subtitle generation and correction."""

import json
import os
import re
from timeit import default_timer as timer

from loguru import logger

from app.config import config
from app.utils import utils


def create(audio_file: str, subtitle_file: str = "") -> Optional[str]:
    """Generate subtitles from an audio file using faster-whisper.

    Args:
        audio_file: Path to the audio file.
        subtitle_file: Output path for the .srt file (auto-generated if empty).

    Returns:
        Path to the subtitle file, or None on failure.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        logger.warning("faster-whisper not available, skipping whisper subtitle generation")
        return None

    if not subtitle_file:
        subtitle_file = f"{audio_file}.srt"

    model_size = config.whisper.model_size
    device = config.whisper.device
    compute_type = config.whisper.compute_type

    model_path = os.path.join(utils.root_dir(), "models", f"whisper-{model_size}")
    model_bin = os.path.join(model_path, "model.bin")
    if not os.path.isdir(model_path) or not os.path.isfile(model_bin):
        model_path = model_size

    logger.info(f"loading whisper model: {model_path}, device: {device}, compute_type: {compute_type}")
    try:
        model = WhisperModel(model_size_or_path=model_path, device=device, compute_type=compute_type)
    except Exception as e:
        logger.error(f"failed to load model: {e}")
        return None

    logger.info(f"transcribing: {audio_file}")
    segments, info = model.transcribe(
        audio_file,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    logger.info(f"detected language: '{info.language}', probability: {info.language_probability:.2f}")

    subtitles = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            subtitles.append({"msg": text, "start_time": seg.start, "end_time": seg.end})

    # Write SRT
    with open(subtitle_file, "w", encoding="utf-8") as f:
        for i, sub in enumerate(subtitles, 1):
            f.write(utils.text_to_srt(i, sub["msg"], sub["start_time"], sub["end_time"]))

    if os.path.isfile(subtitle_file) and os.path.getsize(subtitle_file) > 0:
        logger.success(f"subtitle generated: {subtitle_file}")
        return subtitle_file
    return None


def correct(subtitle_file: str, video_script: str) -> bool:
    """Correct subtitle text to match the original video script.

    Uses fuzzy matching to align whisper output with the original script
    for better accuracy.

    Args:
        subtitle_file: Path to the .srt file.
        video_script: The original script text.

    Returns:
        True if corrected, False otherwise.
    """
    if not os.path.isfile(subtitle_file):
        return False

    with open(subtitle_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse current subtitles
    pattern = re.compile(
        r"(\d+)\s*\n"
        r"(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*\n"
        r"((?:(?!\n\n|\n\d+\n).)*)",
        re.DOTALL,
    )
    entries = list(pattern.finditer(content))
    if not entries:
        return False

    # Simple correction: clean up common whisper artifacts
    script_lines = [s.strip() for s in video_script.split("\n") if s.strip()]
    corrected_entries = []

    for idx, match in enumerate(entries):
        text = match.group(4).strip().replace("\n", " ")
        # Remove repeated punctuation
        text = re.sub(r"([.,!?，。！？])\1+", r"\1", text)
        # Remove leading/trailing whitespace/punctuation
        text = text.strip(",.!?，。！？ ")
        corrected_entries.append((match, text))

    # Write corrected SRT
    new_lines = []
    for match, text in corrected_entries:
        new_lines.append(match.group(1))
        new_lines.append(f"{match.group(2)} --> {match.group(3)}")
        new_lines.append(text)
        new_lines.append("")

    with open(subtitle_file, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))

    logger.info(f"subtitle corrected: {subtitle_file}")
    return True


def file_to_subtitles(subtitle_file: str) -> list:
    """Parse an SRT file into a list of (start_end, text) tuples.

    Returns:
        List of ((start, end), text) tuples, or empty list if parsing fails.
    """
    if not subtitle_file or not os.path.isfile(subtitle_file):
        return []

    from moviepy.video.tools.subtitles import SubtitlesClip
    try:
        sub = SubtitlesClip(subtitles=subtitle_file, encoding="utf-8")
        return sub.subtitles
    except Exception as e:
        logger.warning(f"failed to parse subtitle: {e}")
        # Manual fallback
        entries = []
        pattern = re.compile(
            r"(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*\n(.+?)(?=\n\n|\Z)",
            re.DOTALL,
        )
        with open(subtitle_file, "r", encoding="utf-8") as f:
            content = f.read()

        for match in pattern.finditer(content):
            start = utils.time_convert_seconds_to_hmsm(match.group(1))
            end = utils.time_convert_seconds_to_hmsm(match.group(2))
            text = match.group(3).strip()
            entries.append(((start, end), text))

        return entries
