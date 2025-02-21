from abc import ABC, abstractmethod
class BaseAI(ABC):
    @abstractmethod
    def make_move(self, history: list) -> str:
        """return AI choices, history is gaming history sequences"""
        pass
 