from abc import ABC, abstractmethod
from typing import Iterable

class Simulator(ABC):
    @property
    @abstractmethod
    def path(self) -> str:
        ...

    @abstractmethod
    def generate(self, **kwargs) -> Iterable[str]:
        ...

    @abstractmethod
    def visualize(self, fig, ax) -> None:
        ...

def plot_loss(job, fig, ax):
    fig.suptitle('Loss')
    job.loss_table['loss'].plot(ax=ax)
