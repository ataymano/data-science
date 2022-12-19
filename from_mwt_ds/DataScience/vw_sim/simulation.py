import random
import numpy as np
from itertools import chain


class Simulation(list):
    def __init__(self, examples):
        super().__init__(examples)

    @staticmethod
    def run(example_gen, count, seed=0):
        random.seed(seed)
        np.random.seed(seed)
        return Simulation([example_gen.get(i) for i in range(count)])

    def __add__(self, other):
        return Simulation(self + other)

    @property
    def txt(self):
        return chain.from_iterable(map(lambda ex: ex.txt, self))

    @property
    def dsjson(self):
        return map(lambda ex: ex.dsjson, self)
