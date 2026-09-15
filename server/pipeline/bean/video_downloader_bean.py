from dataclasses import dataclass, field


@dataclass
class VideoDownloaderBean:
    task_url: str = ""
    task_upload_video_path: str = ""
    task_original_video_path: str = ""
    """Standardised output from a downloader."""
    video_path: str = ""
    metadata: dict = field(default_factory=dict)
    title: str = ""
    duration: float = 0.0
    width: int = 0
    height: int = 0
