from pipeline.tts.base import TTSBase


class GoogleGeminiTTS(TTSBase):
    def config(self, api_key: str = None, region: str = None, proxy: str = None):
        pass

    def rewrite(self, subtitle_path: str, lang: str, voice: str) -> str or None:
        pass
