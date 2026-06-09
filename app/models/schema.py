"""Pydantic schemas — request/response models for the VideoPrinterTurbo API."""

import warnings
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

warnings.filterwarnings("ignore", category=UserWarning, message="Field name.*shadows an attribute in parent.*")


class VideoAspect(str, Enum):
    """Video aspect ratio."""
    landscape = "16:9"
    portrait = "9:16"
    square = "1:1"

    def to_resolution(self):
        if self == VideoAspect.landscape.value:
            return 1920, 1080
        elif self == VideoAspect.portrait.value:
            return 1080, 1920
        elif self == VideoAspect.square.value:
            return 1080, 1080
        return 1080, 1920


class VideoConcatMode(str, Enum):
    """How video clips are concatenated."""
    random = "random"
    sequential = "sequential"


class VideoTransitionMode(str, Enum):
    """Transition effects between clips."""
    none = None
    shuffle = "Shuffle"
    fade_in = "FadeIn"
    fade_out = "FadeOut"
    slide_in = "SlideIn"
    slide_out = "SlideOut"


class BaseResponse(BaseModel):
    """Standard API response wrapper."""
    status: int = 200
    message: Optional[str] = "success"
    data: Any = None


class VideoMeta(BaseModel):
    """Metadata extracted from a source video."""
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    has_audio: bool = False
    has_subtitle: bool = False
    audio_codec: str = ""
    video_codec: str = ""
    file_size: int = 0
    file_path: str = ""


class TranscriptSegment(BaseModel):
    """A single segment of transcribed/subtitle text with timing."""
    index: int = 0
    text: str = ""
    start: float = 0.0
    end: float = 0.0


class MaterialInfo(BaseModel):
    """Information about a video/image material."""
    provider: str = "pexels"
    url: str = ""
    duration: int = 0


class VideoRewriteParams(BaseModel):
    """Parameters for a video rewrite task."""
    video_url: str = ""
    rewrite_instruction: str = ""
    video_script: str = ""
    video_aspect: Optional[VideoAspect] = VideoAspect.portrait
    video_concat_mode: Optional[VideoConcatMode] = VideoConcatMode.random
    video_clip_duration: Optional[int] = 5
    video_count: Optional[int] = 1
    video_source: Optional[str] = "pexels"

    voice_name: Optional[str] = "zh-CN-XiaoxiaoNeural-Female"
    voice_volume: Optional[float] = 1.0
    voice_rate: Optional[float] = 1.0
    bgm_type: Optional[str] = "random"
    bgm_file: Optional[str] = ""
    bgm_volume: Optional[float] = 0.2

    subtitle_enabled: Optional[bool] = True
    subtitle_position: Optional[str] = "bottom"
    font_name: Optional[str] = "STHeitiMedium.ttc"
    text_fore_color: Optional[str] = "#FFFFFF"
    text_background_color: Optional[bool | str] = True
    font_size: int = 60
    stroke_color: Optional[str] = "#000000"
    stroke_width: float = 1.5
    n_threads: Optional[int] = 2
    paragraph_number: int = 1

    auto_publish: Optional[bool] = False
    publish_platforms: Optional[list[str]] = None


# ── API Request / Response Models ──────────────────────────────────


class TaskQueryRequest(BaseModel):
    """Query parameters for task status (currently empty placeholder)."""
    pass


class TaskResponse(BaseResponse):
    """Response to task creation request."""

    class TaskResponseData(BaseModel):
        task_id: str

    data: TaskResponseData

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": 200,
            "message": "success",
            "data": {"task_id": "6c85c8cc-a77a-42b9-bc30-947815aa0558"},
        },
    })


class TaskQueryResponse(BaseResponse):
    """Response containing task status and result data."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": 200,
            "message": "success",
            "data": {
                "state": 4,
                "progress": 100,
                "videos": ["http://127.0.0.1:8080/tasks/xxx/final-1.mp4"],
            },
        },
    })


class TaskDeletionResponse(BaseResponse):
    """Response after deleting a task."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": 200,
            "message": "success",
            "data": None,
        },
    })
