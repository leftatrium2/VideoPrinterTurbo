from abc import abstractmethod, ABC
from typing import Optional


class BaseLLMProvider(ABC):

    @abstractmethod
    def rewrite(self, original_text: str, instruction: str, language: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def generate_script(self, video_subject: str, language: Optional[str] = None,
                        paragraph_number: int = 1) -> str:
        pass

    @abstractmethod
    def generate_terms(self, video_subject: str, video_script: str, amount: int = 5) -> list[str]:
        pass

    @abstractmethod
    def translate_subtitles(self, segments: list[dict], target_language: str) -> list[dict]:
        pass
