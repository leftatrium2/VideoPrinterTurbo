"""Video rewrite engine — composes the final video from materials, audio, and subtitles.

Key functions:
    - compose_from_materials: Build video from stock footage + new audio + subtitle
    - replace_audio_track: Replace source video audio + add subtitle overlay
"""

import gc
import io
import os
import random
import shutil
import subprocess
from contextlib import redirect_stdout
from typing import Optional

from loguru import logger
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
    afx,
)
from moviepy.video.tools.subtitles import SubtitlesClip
from PIL import Image, ImageFont

from app.models import const
from app.models.schema import VideoAspect, VideoConcatMode, VideoParams
from app.utils import file_security, utils

# ── Constants ──────────────────────────────────────────────────────

audio_codec = "aac"
audio_bitrate = "192k"
video_codec = "libx264"
fps = 30


# ── FFmpeg helpers ─────────────────────────────────────────────────

def _get_ffmpeg_binary():
    configured = os.environ.get("IMAGEIO_FFMPEG_EXE")
    if configured:
        return configured
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


# ── Clip lifecycle ─────────────────────────────────────────────────

def close_clip(clip):
    if clip is None:
        return
    try:
        if hasattr(clip, 'reader') and clip.reader is not None:
            clip.reader.close()
        if hasattr(clip, 'audio') and clip.audio is not None:
            if hasattr(clip.audio, 'reader') and clip.audio.reader is not None:
                clip.audio.reader.close()
            del clip.audio
        if hasattr(clip, 'mask') and clip.mask is not None:
            if hasattr(clip.mask, 'reader') and clip.mask.reader is not None:
                clip.mask.reader.close()
            del clip.mask
        if hasattr(clip, 'clips') and clip.clips:
            for child in clip.clips:
                if child is not clip:
                    close_clip(child)
            clip.clips = []
    except Exception as e:
        logger.error(f"close clip error: {e}")
    del clip
    gc.collect()


def delete_files(files):
    if isinstance(files, str):
        files = [files]
    for f in files:
        try:
            os.remove(f)
        except Exception as e:
            logger.debug(f"delete failed: {f}, {e}")


# ── Video composition ──────────────────────────────────────────────

class _SubClippedVideo:
    def __init__(self, file_path, start_time=0, end_time=0, width=0, height=0, duration=0):
        self.file_path = file_path
        self.start_time = start_time
        self.end_time = end_time
        self.width = width
        self.height = height
        self.duration = duration if duration else end_time - start_time


def _open_video_quietly(video_path: str, audio: bool = False) -> VideoFileClip:
    captured = io.StringIO()
    with redirect_stdout(captured):
        clip = VideoFileClip(video_path, audio=audio)
    output = captured.getvalue().strip()
    if output:
        logger.debug(f"suppressed MoviePy stdout for {video_path}")
    return clip


def concat_video_clips(clip_files: list, output_file: str, threads: int = 2):
    """Concatenate video clips using ffmpeg concat demuxer."""
    output_dir = os.path.dirname(output_file)
    concat_file = os.path.join(output_dir, "ffmpeg-concat-list.txt")
    with open(concat_file, "w", encoding="utf-8") as fp:
        for clip_file in clip_files:
            abs_path = os.path.abspath(clip_file)
            escaped = abs_path.replace("'", "'\\''")
            fp.write(f"file '{escaped}'\n")

    cmd = [
        _get_ffmpeg_binary(), "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c:v", video_codec, "-threads", str(threads or 2),
        "-pix_fmt", "yuv420p", output_file,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            error = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(error or "ffmpeg concat failed")
    finally:
        delete_files(concat_file)


def combine_videos(
    combined_video_path: str,
    video_paths: list,
    audio_file: str,
    video_aspect="9:16",
    video_concat_mode="random",
    max_clip_duration: int = 5,
    threads: int = 2,
) -> str:
    """Combine multiple video clips into one video matching the audio duration."""
    audio_clip = AudioFileClip(audio_file)
    try:
        audio_duration = audio_clip.duration
    finally:
        close_clip(audio_clip)

    logger.info(f"combine: audio={audio_duration}s, {len(video_paths)} clips")

    aspect = VideoAspect(video_aspect) if isinstance(video_aspect, str) else video_aspect
    if isinstance(aspect, VideoAspect):
        video_width, video_height = aspect.to_resolution()
    else:
        video_width, video_height = 1080, 1920

    # Build clip segments
    subclips = []
    for vp in video_paths:
        try:
            clip = _open_video_quietly(vp)
            cd = clip.duration
            cw, ch = clip.size
            close_clip(clip)

            start = 0
            while start < cd:
                end = min(start + max_clip_duration, cd)
                if end > start:
                    subclips.append(_SubClippedVideo(
                        file_path=vp, start_time=start, end_time=end,
                        width=cw, height=ch, duration=end - start,
                    ))
                start = end
                if video_concat_mode == "sequential":
                    break
        except Exception as e:
            logger.warning(f"failed to process clip {vp}: {e}")

    concat_mode_val = VideoConcatMode(video_concat_mode) if isinstance(video_concat_mode, str) else video_concat_mode
    if hasattr(concat_mode_val, 'value'):
        concat_mode_val = concat_mode_val.value

    if concat_mode_val == "random":
        random.shuffle(subclips)

    # Build processed clips
    processed = []
    video_duration = 0.0

    # First pass
    for sc in subclips:
        if video_duration >= audio_duration:
            break
        try:
            clip = _open_video_quietly(sc.file_path).subclipped(sc.start_time, sc.end_time)
            cw, ch = clip.size
            if cw != video_width or ch != video_height:
                ratio = clip.w / clip.h
                target_ratio = video_width / video_height
                if ratio == target_ratio:
                    clip = clip.resized(new_size=(video_width, video_height))
                else:
                    if ratio > target_ratio:
                        clip = clip.resized(width=video_width)
                    else:
                        clip = clip.resized(height=video_height)
                    clip = clip.cropped(x_center=clip.w / 2, y_center=clip.h / 2,
                                        width=video_width, height=video_height)

            # Write to temp for memory management
            temp_file = os.path.join(os.path.dirname(combined_video_path),
                                     f"_temp_{len(processed):04d}.mp4")
            clip.write_videofile(temp_file, fps=fps, logger=None)
            close_clip(clip)
            processed.append(temp_file)
            video_duration += sc.duration
        except Exception as e:
            logger.warning(f"clip processing error: {e}")

    # Loop if needed
    base_count = len(processed)
    while video_duration < audio_duration and processed:
        for i in range(base_count):
            if video_duration >= audio_duration:
                break
            src = processed[i]
            dest = os.path.join(os.path.dirname(combined_video_path),
                                f"_temp_{len(processed):04d}.mp4")
            shutil.copy(src, dest)
            processed.append(dest)
            video_duration += AudioFileClip(audio_file).duration if False else max_clip_duration

    if not processed:
        logger.warning("no clips available for merging")
        return combined_video_path

    if len(processed) == 1:
        shutil.copy(processed[0], combined_video_path)
        delete_files(processed)
        return combined_video_path

    concat_video_clips(processed, combined_video_path, threads)
    delete_files(processed)
    return combined_video_path


def generate_video(
    video_path: str,
    audio_path: str,
    subtitle_path: str,
    output_file: str,
    params,
):
    """Generate final video with audio, subtitles, and optional BGM."""
    aspect = VideoAspect(params.video_aspect) if isinstance(params.video_aspect, str) else params.video_aspect
    if isinstance(aspect, VideoAspect):
        video_width, video_height = aspect.to_resolution()
    else:
        video_width, video_height = 1080, 1920

    output_dir = os.path.dirname(output_file)
    font_path = ""

    if getattr(params, 'subtitle_enabled', True) and subtitle_path and os.path.isfile(subtitle_path):
        font_name = getattr(params, 'font_name', 'STHeitiMedium.ttc')
        font_path = os.path.join(utils.font_dir(), font_name)
        if os.name == "nt":
            font_path = font_path.replace("\\", "/")

    # Open clips
    video_clip = _open_video_quietly(video_path)
    audio_clip = AudioFileClip(audio_path).with_effects([
        afx.MultiplyVolume(getattr(params, 'voice_volume', 1.0))
    ])

    # Add subtitles
    if subtitle_path and os.path.isfile(subtitle_path) and font_path:
        text_clips = []
        sub = SubtitlesClip(subtitles=subtitle_path, encoding="utf-8",
                            make_textclip=lambda txt: TextClip(text=txt, font=font_path,
                                                               font_size=getattr(params, 'font_size', 60)))

        for item in sub.subtitles:
            wrapped, txt_h = _wrap_text(
                item[1], max_width=video_width * 0.9,
                font=font_path, fontsize=getattr(params, 'font_size', 60)
            )
            interline = int(getattr(params, 'font_size', 60) * 0.25)
            line_count = wrapped.count("\n") + 1
            vertical_padding = int(getattr(params, 'font_size', 60) * 0.35)
            size = (int(video_width * 0.9), int(txt_h + vertical_padding + (interline * line_count)))

            clip = TextClip(
                text=wrapped, font=font_path,
                font_size=getattr(params, 'font_size', 60),
                color=getattr(params, 'text_fore_color', '#FFFFFF'),
                bg_color=getattr(params, 'text_background_color', True) or None,
                stroke_color=getattr(params, 'stroke_color', '#000000'),
                stroke_width=int(getattr(params, 'stroke_width', 1.5)),
                interline=interline, size=size, text_align="center",
            )
            duration = item[0][1] - item[0][0]
            clip = clip.with_start(item[0][0]).with_duration(duration)

            pos = getattr(params, 'subtitle_position', 'bottom')
            if pos == "bottom":
                clip = clip.with_position(("center", video_height * 0.95 - clip.h))
            elif pos == "top":
                clip = clip.with_position(("center", video_height * 0.05))
            else:
                clip = clip.with_position(("center", "center"))

            text_clips.append(clip)

        if text_clips:
            video_clip = CompositeVideoClip([video_clip, *text_clips])

    # Add BGM
    bgm_file = _get_bgm_file(
        bgm_type=getattr(params, 'bgm_type', 'random'),
        bgm_file=getattr(params, 'bgm_file', ''),
    )
    if bgm_file:
        try:
            bgm_clip = AudioFileClip(bgm_file).with_effects([
                afx.MultiplyVolume(getattr(params, 'bgm_volume', 0.2)),
                afx.AudioFadeOut(3),
                afx.AudioLoop(duration=video_clip.duration),
            ])
            audio_clip = CompositeAudioClip([audio_clip, bgm_clip])
        except Exception as e:
            logger.error(f"bgm error: {e}")

    video_clip = video_clip.with_audio(audio_clip)
    output_audio_fps = int(getattr(audio_clip, "fps", 0) or 44100)

    video_clip.write_videofile(
        output_file,
        audio_codec=audio_codec,
        audio_fps=output_audio_fps,
        audio_bitrate=audio_bitrate,
        temp_audiofile_path=output_dir,
        threads=getattr(params, 'n_threads', 2) or 2,
        logger=None,
        fps=fps,
    )
    video_clip.close()
    del video_clip


# ── Public API ─────────────────────────────────────────────────────

def compose_from_materials(
    video_materials: list[str],
    audio_path: str,
    subtitle_path: str,
    output_path: str,
    params,
) -> bool:
    """Compose a video from stock footage materials + new audio + subtitle."""
    try:
        combined_path = output_path.replace(".mp4", ".combined.mp4")
        combine_videos(
            combined_video_path=combined_path,
            video_paths=video_materials,
            audio_file=audio_path,
            video_aspect=getattr(params, 'video_aspect', '9:16'),
            video_concat_mode=getattr(params, 'video_concat_mode', 'random'),
            max_clip_duration=getattr(params, 'video_clip_duration', 5),
            threads=getattr(params, 'n_threads', 2),
        )
        generate_video(
            video_path=combined_path,
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            output_file=output_path,
            params=params,
        )
        delete_files(combined_path)
        return os.path.isfile(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        logger.error(f"compose from materials failed: {e}")
        return False


def replace_audio_track(
    video_path: str,
    audio_path: str,
    subtitle_path: str,
    output_path: str,
    params,
) -> bool:
    """Replace the audio track of a source video and overlay new subtitles."""
    try:
        generate_video(
            video_path=video_path,
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            output_file=output_path,
            params=params,
        )
        return os.path.isfile(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        logger.error(f"replace audio track failed: {e}")
        return False


# ── Internal helpers ───────────────────────────────────────────────

def _get_bgm_file(bgm_type: str = "random", bgm_file: str = ""):
    if not bgm_type:
        return ""
    if bgm_file:
        song_dir = utils.song_dir()
        candidate = os.path.join(song_dir, bgm_file)
        if os.path.isfile(candidate) and candidate.lower().endswith(".mp3"):
            return candidate
    if bgm_type == "random":
        import glob
        files = glob.glob(os.path.join(utils.song_dir(), "*.mp3"))
        if files:
            return random.choice(files)
    return ""


def _wrap_text(text, max_width, font="Arial", fontsize=60):
    font_obj = ImageFont.truetype(font, fontsize) if os.path.isfile(font) else ImageFont.load_default()

    def get_size(t):
        t = t.strip()
        if not t:
            return 0, fontsize
        left, top, right, bottom = font_obj.getbbox(t)
        return right - left, bottom - top

    width, height = get_size(text)
    if width <= max_width:
        return text, height

    lines = []
    current = ""
    for word in text.split(" "):
        candidate = f"{current} {word}".strip() if current else word
        cw, _ = get_size(candidate)
        if cw <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    result = "\n".join(lines)
    return result, len(lines) * height
