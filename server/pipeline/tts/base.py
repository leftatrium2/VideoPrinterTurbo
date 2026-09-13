from abc import abstractmethod, ABC
from typing import Optional


class TTSBase(ABC):

    @abstractmethod
    def rewrite(self, subtitle_path: str, lang: str, voice: str) -> Optional[str]:
        pass
