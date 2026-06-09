"""Voice/TTS service — text-to-speech generation using edge-tts and other providers."""

import asyncio
import math
import os
import re
import shutil
from typing import Optional, Union

import edge_tts
from edge_tts import SubMaker
from loguru import logger
from moviepy.audio.io.AudioFileClip import AudioFileClip

from app.config import config
from app.utils import utils


def parse_voice_name(voice_name: str) -> str:
    """Parse and validate a voice name, returning the full edge-tts voice ID."""
    if not voice_name:
        return "zh-CN-XiaoxiaoNeural-Female"

    # Handle short names like "zh-CN-XiaoxiaoNeural" without gender suffix
    voice_name = voice_name.strip()
    if voice_name.endswith(("-Male", "-Female")):
        return voice_name

    # Try to match with a known suffix
    for suffix in ("-Male", "-Female"):
        candidate = f"{voice_name}{suffix}"
        if candidate in _get_voice_list():
            return candidate

    return voice_name


def _get_voice_list() -> list[str]:
    """Return a set of known edge-tts voice IDs for validation."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        voices = loop.run_until_complete(edge_tts.list_voices())
        loop.close()
        return [v["Name"] for v in voices]
    except Exception:
        return []


def tts(text: str, voice_name: str, voice_rate: float, voice_file: str) -> Optional[SubMaker]:
    """Generate TTS audio from text using edge-tts.

    Args:
        text: The text to synthesize.
        voice_name: Edge TTS voice name (e.g. "zh-CN-XiaoxiaoNeural-Female").
        voice_rate: Speaking rate multiplier (1.0 = normal).
        voice_file: Output path for the audio file.

    Returns:
        SubMaker instance (for word-level timing), or None on failure.
    """
    if not text or not text.strip():
        logger.error("empty text for TTS")
        return None

    timeout = config.app.edge_tts_timeout

    async def _do_tts():
        rate_str = f"+{int((voice_rate - 1) * 100)}%" if voice_rate >= 1 else f"{int(voice_rate * 100)}%"
        communicate = edge_tts.Communicate(text=text, voice=voice_name, rate=rate_str)
        sub_maker = SubMaker()

        # Determine the output file extension
        file_ext = os.path.splitext(voice_file)[1].lower() or ".mp3"
        media_type = "audio/mp3" if file_ext == ".mp3" else "audio/wav"

        with open(voice_file, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    sub_maker.create_sub(
                        (chunk["offset"], chunk["duration"]),
                        chunk["text"],
                        media_type,
                    )
        return sub_maker

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sub_maker = loop.run_until_complete(_do_tts())
        loop.close()

        if os.path.isfile(voice_file) and os.path.getsize(voice_file) > 0:
            logger.success(f"TTS generated: {voice_file}")
            return sub_maker
        else:
            logger.error("TTS produced empty file")
            return None
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        return None


def get_audio_duration(sub_maker_or_path: Union[SubMaker, str]) -> int:
    """Get audio duration in seconds from a SubMaker or file path."""
    if isinstance(sub_maker_or_path, str):
        try:
            clip = AudioFileClip(sub_maker_or_path)
            duration = math.ceil(clip.duration)
            clip.close()
            return duration
        except Exception as e:
            logger.error(f"failed to get audio duration: {e}")
            return 0

    # From SubMaker
    sub_maker = sub_maker_or_path
    if hasattr(sub_maker, 'offset') and sub_maker.offset:
        # edge-tts SubMaker stores offsets in 100-nanosecond units
        max_offset = max(sub_maker.offset) if sub_maker.offset else 0
        return math.ceil(max_offset / 10_000_000)
    return 0


def create_subtitle(text: str, sub_maker, subtitle_file: str) -> bool:
    """Create an SRT subtitle file from a SubMaker with word-level timing.

    Args:
        text: The full text that was synthesized.
        sub_maker: SubMaker instance from the TTS call.
        subtitle_file: Output path for the .srt file.

    Returns:
        True if subtitle was created, False otherwise.
    """
    try:
        if hasattr(sub_maker, 'offset') and sub_maker.offset:
            sub_maker.merge_sub(title="", lang="")
            # merge_sub creates subtitle data in sub_maker.subs
            if hasattr(sub_maker, 'subs') and sub_maker.subs:
                with open(subtitle_file, "w", encoding="utf-8") as f:
                    f.write(sub_maker.subs)
                if os.path.isfile(subtitle_file) and os.path.getsize(subtitle_file) > 0:
                    logger.success(f"subtitle created: {subtitle_file}")
                    return True
        return False
    except Exception as e:
        logger.error(f"subtitle creation failed: {e}")
        return False
