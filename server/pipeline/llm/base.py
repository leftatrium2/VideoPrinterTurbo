from abc import abstractmethod, ABC


class BaseLLMProvider(ABC):
    @abstractmethod
    def config(self, api_key: str, base_url: str, model: str):
        pass

    @abstractmethod
    def rewrite(self, text: str, src_path: str, dst_path: str):
        pass
