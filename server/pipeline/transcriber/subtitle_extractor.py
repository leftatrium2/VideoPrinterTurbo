"""SubtitleExtractor — extracts embedded subtitles from video files without ASR."""

import os
import re
from typing import Optional
from loguru import logger

from pipeline.transcriber.base import BaseTranscriber


class SubtitleExtractor(BaseTranscriber):

    def validate_config(self) -> bool:
        return True

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> list:
        logger.warning("SubtitleExtractor does not support ASR transcription")
        return []

    def extract_subtitles(self, video_path: str) -> list:
        """Extract subtitles from embedded subtitle tracks in a video file.

        Tries common subtitle file extensions in the same directory as the video,
        then falls back to ffprobe to detect embedded subtitle streams.
        """
        if not video_path or not os.path.isfile(video_path):
            logger.warning(f"video file not found: {video_path}")
            return []

        # 1. Check for external subtitle files next to the video
        base_dir = os.path.dirname(video_path)
        base_name = os.path.splitext(os.path.basename(video_path))[0]

        for ext in (".srt", ".vtt", ".ass"):
            sub_path = os.path.join(base_dir, f"{base_name}{ext}")
            if os.path.isfile(sub_path):
                logger.info(f"found subtitle file: {sub_path}")
                return self._parse_file(sub_path)

        # 2. Try to find any .srt or .vtt file in the same directory
        for ext in (".srt", ".vtt", ".ass"):
            candidates = [f for f in os.listdir(base_dir) if f.lower().endswith(ext)]
            if candidates:
                sub_path = os.path.join(base_dir, sorted(candidates)[0])
                logger.info(f"found subtitle file: {sub_path}")
                return self._parse_file(sub_path)

        logger.info(f"no external subtitle files found for: {video_path}")
        return []

    def _parse_file(self, path: str) -> list[TranscriptSegment]:
        """Parse an SRT or VTT subtitle file into TranscriptSegments."""
        ext = os.path.splitext(path)[1].lower()
        if ext == ".srt":
            return self._parse_srt(path)
        elif ext == ".vtt":
            return self._parse_vtt(path)
        elif ext == ".ass":
            return self._parse_ass(path)
        return []

    @staticmethod
    def _parse_timestamp(ts: str) -> float:
        """Convert a timestamp string to seconds.

        Supports formats:
            HH:MM:SS,mmm   (SRT)
            HH:MM:SS.mmm   (VTT)
            H:MM:SS.cc     (ASS centiseconds)
        """
        ts = ts.strip().replace(",", ".")
        parts = ts.split(":")
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        return 0.0

    def _parse_srt(self, path: str) -> list[TranscriptSegment]:
        segments = []
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        pattern = re.compile(
            r"(\d+)\s*\n"
            r"(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*\n"
            r"((?:(?!\n\n|\n\d+\n).)*)",
            re.DOTALL,
        )
        for idx, match in enumerate(pattern.finditer(content), 1):
            start = self._parse_timestamp(match.group(2))
            end = self._parse_timestamp(match.group(3))
            text = match.group(4).strip().replace("\n", " ")
            segments.append(TranscriptSegment(index=idx, text=text, start=start, end=end))

        return segments

    def _parse_vtt(self, path: str) -> list[TranscriptSegment]:
        segments = []
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Strip header (everything before first timestamp)
        pattern = re.compile(
            r"(\d{2}:\d{2}:\d{2}[.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.]\d{3})\s*\n"
            r"((?:(?!\n\n|\n\d{2}:).)*)",
            re.DOTALL,
        )
        for idx, match in enumerate(pattern.finditer(content), 1):
            start = self._parse_timestamp(match.group(1))
            end = self._parse_timestamp(match.group(2))
            text = match.group(3).strip().replace("\n", " ")
            segments.append(TranscriptSegment(index=idx, text=text, start=start, end=end))

        return segments

    def _parse_ass(self, path: str) -> list[TranscriptSegment]:
        """Parse ASS/SSA subtitles — extract [Events] Dialogue lines."""
        segments = []
        in_events = False
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line.upper().startswith("[EVENTS]"):
                    in_events = True
                    continue
                if line.startswith("["):
                    in_events = False
                    continue
                if not in_events or not line.upper().startswith("DIALOGUE:"):
                    continue

                # Format: Dialogue: Layer, Start, End, Style, Actor, MarginL, MarginR, MarginV, Effect, Text
                parts = line.split(",", 9)
                if len(parts) < 10:
                    continue
                start_ts = parts[1].strip()
                end_ts = parts[2].strip()
                text = parts[9].strip()
                # Remove ASS formatting codes
                text = re.sub(r"\{[^}]*\}", "", text).replace("\\N", " ").strip()
                if text:
                    segments.append(TranscriptSegment(
                        index=len(segments) + 1,
                        text=text,
                        start=self._parse_ass_timestamp(start_ts),
                        end=self._parse_ass_timestamp(end_ts),
                    ))
        return segments

    @staticmethod
    def _parse_ass_timestamp(ts: str) -> float:
        """ASS format: H:MM:SS.cc (centiseconds)"""
        parts = ts.strip().split(":")
        if len(parts) == 3:
            h, m, s = parts
            # s can be "SS.cc"
            return int(h) * 3600 + int(m) * 60 + float(s)
        return 0.0
