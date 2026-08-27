from dataclasses import dataclass, field


@dataclass
class VideoBean:
    url: str = ""
    """Standardised output from a downloader."""
    video_path: str = ""
    metadata: dict = field(default_factory=dict)
    title: str = ""
    duration: float = 0.0
    width: int = 0
    height: int = 0
