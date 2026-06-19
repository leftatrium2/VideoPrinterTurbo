from typing import Optional

from pipeline.publisher.base import BasePublisher


class UploadPostPublisher(BasePublisher):
    def publish(self, video_path: str, title: str, description: str = "",
                tags: Optional[list[str]] = None) -> bool:
        return True
