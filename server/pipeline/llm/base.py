"""BaseLLMProvider — abstract interface for LLM text generation plugins."""

from abc import abstractmethod
from typing import Optional

from app.pipeline.base import BasePlugin, PluginType


class BaseLLMProvider(BasePlugin):
    """Language model provider for script generation, rewriting, and keyword extraction."""

    type = PluginType.LLM

    @abstractmethod
    def rewrite(self, original_text: str, instruction: str, language: Optional[str] = None) -> str:
        """Rewrite the given text according to the instruction.

        Args:
            original_text: The source text (e.g. original video transcript).
            instruction: User's rewrite instruction (e.g. "make it more engaging").
            language: Optional target language code.

        Returns:
            The rewritten text.
        """
        ...

    @abstractmethod
    def generate_script(self, video_subject: str, language: Optional[str] = None,
                        paragraph_number: int = 1) -> str:
        """Generate a video script from a subject/topic.

        Args:
            video_subject: The subject of the video.
            language: Optional language code.
            paragraph_number: How many paragraphs to generate.

        Returns:
            The generated script text.
        """
        ...

    @abstractmethod
    def generate_terms(self, video_subject: str, video_script: str, amount: int = 5) -> list[str]:
        """Extract search keywords/terms from a video subject and script.

        Args:
            video_subject: The video subject.
            video_script: The full script text.
            amount: How many terms to generate.

        Returns:
            List of search terms.
        """
        ...

    @abstractmethod
    def translate_subtitles(self, segments: list[dict], target_language: str) -> list[dict]:
        """Translate subtitle segments to a target language.

        Args:
            segments: List of dicts with "text", "start", "end" keys.
            target_language: Target language code.

        Returns:
            Translated segments with same structure.
        """
        ...
