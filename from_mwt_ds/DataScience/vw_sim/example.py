from typing import List
from vw_sim import core


class Regression(core.Example):
    @property
    def txt(self) -> List[str]:
        return [f'{self.label} |{self.features.txt}']

    @property
    def dsjson(self) -> str:
        raise NotImplementedError()
