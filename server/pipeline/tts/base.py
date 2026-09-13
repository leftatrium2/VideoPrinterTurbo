from abc import abstractmethod, ABC


class TTSBase(ABC):

    @abstractmethod
    def rewrite(self, subtitle_path: str, lang: str, voice: str) -> str or None:
        pass
