from abc import ABC, abstractmethod


class SeparateVocalsBase(ABC):

    @abstractmethod
    def convert(self):
        pass
