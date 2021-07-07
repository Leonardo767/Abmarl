from abc import ABC, abstractmethod
from gym.spaces import Box, Discrete, Dict
import numpy as np
from abmarl.sim import PrincipleAgent, AgentBasedSimulation


class PredatorPreyAgent(PrincipleAgent, ABC):

    @abstractmethod
    def __init__(self, move=None, view=None, **kwargs):
        super().__init__(**kwargs)
        self.move = move
        self.view = view

    @property
    def configured(self):
        return super().configured and self.move is not None and self.view is not None


class Prey(PredatorPreyAgent):

    def __init__(self, harvest_amount=None, **kwargs):
        super().__init__(**kwargs)
        self.harvest_amount = harvest_amount

    @property
    def configured(self):
        return super().configured and self.harvest_amount is not None

    @property
    def value(self):
        return 1


class Predator(PredatorPreyAgent):

    def __init__(self, attack=None, **kwargs):
        super().__init__(**kwargs)
        self.attack = attack

    @property
    def configured(self):
        return super().configured and self.attack is not None

    @property
    def value(self):
        return 2


