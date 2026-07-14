from abc import abstractmethod, ABC


class TTSBase(ABC):
    @abstractmethod
    def config(self, api_key: str = None, region: str = None, proxy: str = None):
        pass

    @abstractmethod
    def rewrite(self, subtitle_path: str, lang: str, voice: str) -> str or None:
        pass
