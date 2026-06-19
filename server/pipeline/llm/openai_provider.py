"""OpenAIProvider — LLM text generation via OpenAI-compatible APIs.

Supports OpenAI, DeepSeek, Moonshot, and any other OpenAI-compatible provider.
"""

import re
from typing import Optional

from loguru import logger
from openai import OpenAI

from pipeline.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI-compatible LLM provider.

    Reads configuration from config.toml [app] section:
      - llm_provider = "openai"  (or "deepseek" / "moonshot")
      - openai_api_key / deepseek_api_key
      - openai_base_url / deepseek_base_url
      - openai_model_name / deepseek_model_name
    """

    def __init__(self):
        self._client = None
        self._model = ""
        self._init_client()

    def _init_client(self):
        provider = ""
        if provider == "deepseek":
            api_key = ""
            base_url = ""
            self._model = ""
        elif provider == "moonshot":
            api_key = ""
            base_url = ""
            self._model = ""
        else:
            api_key = ""
            base_url = ""
            self._model = ""

        if not api_key:
            logger.warning(f"API key not configured for provider: {provider}")
            return

        self._client = OpenAI(api_key=api_key, base_url=base_url or None)

    def validate_config(self) -> bool:
        return self._client is not None

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        if not self._client:
            raise RuntimeError("OpenAI client not initialized — check API key configuration")

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
        )
        content = response.choices[0].message.content
        return (content or "").strip()

    def rewrite(self, original_text: str, instruction: str, language: Optional[str] = None) -> str:
        system_prompt = """You are a professional video script writer. Your task is to rewrite the given transcript.

Rules:
1. Keep the key information and message of the original text.
2. Make it suitable for voice-over in a short video — conversational, engaging, and clear.
3. Do NOT use markdown formatting.
4. Do NOT include stage directions like "voiceover" or "narrator".
5. Return only the raw script text."""
        if language:
            system_prompt += f"\n6. Respond in {language}."

        user_prompt = f"Original transcript:\n{original_text}\n\nInstruction: {instruction}\n\nRewritten script:"
        return self._call(system_prompt, user_prompt)

    def generate_script(self, video_subject: str, language: Optional[str] = None,
                        paragraph_number: int = 1) -> str:
        system_prompt = f"""You are a video script generator.
Generate a {paragraph_number}-paragraph script about: {video_subject}

Rules:
1. The script is for a short video voice-over.
2. Do not use markdown or formatting.
3. Do not include "voiceover" or similar indicators.
4. Return only the raw script text."""
        if language:
            system_prompt += f"\n5. Respond in {language}."

        return self._call(system_prompt, f"Write a script about: {video_subject}")

    def generate_terms(self, video_subject: str, video_script: str, amount: int = 5) -> list[str]:
        system_prompt = f"""Extract {amount} search keywords from the video topic and script.
These keywords will be used to search for video footage on stock video websites (Pexels, Pixabay).
Return only the keywords as a comma-separated list. No numbering, no explanation."""

        user_prompt = f"Topic: {video_subject}\nScript: {video_script[:500]}\n\nKeywords:"
        response = self._call(system_prompt, user_prompt)
        # Parse comma-separated list
        terms = [t.strip() for t in re.split(r"[,，]", response) if t.strip()]
        return terms[:amount]

    def translate_subtitles(self, segments: list[dict], target_language: str) -> list[dict]:
        texts = [seg["text"] for seg in segments]
        joined = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(texts))

        system_prompt = f"Translate the following subtitle lines to {target_language}. Keep the same numbering. Return only the translations."
        response = self._call(system_prompt, joined)

        # Parse numbered translations
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
