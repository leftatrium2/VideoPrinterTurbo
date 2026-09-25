from dataclasses import field


class VideoDownloaderBean:
    task_url: str = ""
    task_upload_video_path: str = ""
    task_original_video_path: str = ""
    """Standardised output from a downloader."""
    video_full_path: str = ""
    metadata: dict = field(default_factory=dict)
    title: str = ""
    duration: float = 0.0
    width: int = 0
    height: int = 0

    def __str__(self) -> str:
        return f"""
        VideoDownloaderBean(
            task_url: {self.task_url}, 
            task_upload_video_path: {self.task_upload_video_path}, 
            task_original_video_path: {self.task_original_video_path}, 
            video_full_path: {self.video_full_path}, 
            metadata: {self.metadata}, 
            title: {self.title}, 
            duration: {self.duration}, 
            width: {self.width}, 
            height: {self.height}
        )
        """
