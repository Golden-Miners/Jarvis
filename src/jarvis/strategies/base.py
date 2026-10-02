from abc import ABC, abstractmethod

from jarvis.schemas.models import SetupCandidate
from jarvis.strategies.context import StrategyContext


class BaseStrategy(ABC):
    def __init__(self, params: dict[str, object]) -> None:
        self.params = params.copy()

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def analyse(self, ctx: StrategyContext) -> list[SetupCandidate]:
        raise NotImplementedError
