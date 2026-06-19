"""GeminiProvider — LLM text generation via Google Gemini API."""

import re
from typing import Optional

from loguru import logger


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider.

    Requires: pip install google-generativeai
    Configure: gemini_api_key and gemini_model_name in config.toml
    """

    def __init__(self):
        self._model = None
        self._init_model()

    def _init_model(self):
        api_key = ""
        model_name = ""
        if not api_key:
            logger.warning("Gemini API key not configured")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(model_name)
        except ImportError:
            logger.warning("google-generativeai not installed. Run: uv sync --extra gemini")
        except Exception as e:
            logger.warning(f"failed to initialize Gemini: {e}")

    def validate_config(self) -> bool:
        return self._model is not None

    def _call(self, prompt: str) -> str:
        if not self._model:
            raise RuntimeError("Gemini model not initialized — check API key")

        response = self._model.generate_content(prompt)
        return (response.text or "").strip()

    def rewrite(self, original_text: str, instruction: str, language: Optional[str] = None) -> str:
        lang_hint = f" Respond in {language}." if language else ""
        prompt = f"""You are a professional video script writer. Rewrite the following transcript for a short video voice-over.

Rules:
1. Keep the key information and message.
2. Make it conversational, engaging, and clear for voice-over.
3. Do NOT use markdown formatting.
4. Do NOT include stage directions.
5. Return only the raw script text.{lang_hint}

Original transcript:
{original_text}

Instruction: {instruction}

Rewritten script:"""
        return self._call(prompt)

    def generate_script(self, video_subject: str, language: Optional[str] = None,
                        paragraph_number: int = 1) -> str:
        lang_hint = f" Respond in {language}." if language else ""
        prompt = f"""Generate a {paragraph_number}-paragraph video script about: {video_subject}

Rules:
1. For a short video voice-over.
2. No markdown or formatting.
3. No stage directions.
4. Return only the raw script.{lang_hint}"""
        return self._call(prompt)

    def generate_terms(self, video_subject: str, video_script: str, amount: int = 5) -> list[str]:
        prompt = f"""Extract {amount} search keywords from this video topic and script for stock video search (Pexels/Pixabay).
Return only the keywords as a comma-separated list. No numbering, no explanation.

Topic: {video_subject}
Script: {video_script[:500]}

Keywords:"""
        response = self._call(prompt)
        terms = [t.strip() for t in re.split(r"[,，]", response) if t.strip()]
        return terms[:amount]

    def translate_subtitles(self, segments: list[dict], target_language: str) -> list[dict]:
        texts = [seg["text"] for seg in segments]
        joined = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(texts))

        prompt = f"Translate these subtitles to {target_language}. Keep numbering. Return only the translations:\n\n{joined}"
        response = self._call(prompt)

        translated = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if line and re.match(r"^\d+\.", line):
                translated.append(re.sub(r"^\d+\.\s*", "", line))

        result = []
        for i, seg in enumerate(segments):
            result.append({
                "text": translated[i] if i < len(translated) else seg["text"],
                "start": seg["start"],
                "end": seg["end"],
            })
        return result
