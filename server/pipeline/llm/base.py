from abc import abstractmethod, ABC


class BaseLLMProvider(ABC):

    @abstractmethod
    def rewrite(self, prompt: str, src: str, dst: str) -> bool:
        pass
