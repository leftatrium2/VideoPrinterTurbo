from abc import abstractmethod, ABC


# ASR 功能，本身不带翻译功能
class BaseTranscriber(ABC):

    # Transcribe audio file into text segments with timestamps
    @abstractmethod
    def transcribe(self, audio_path: str) -> str or None:
        pass
