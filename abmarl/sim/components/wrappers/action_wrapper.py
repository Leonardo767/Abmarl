
from abmarl.sim.components.agent import GridMovementAgent
from gym.spaces import Box, Discrete
import numpy as np

from abmarl.sim.components.agent import GridMovementAgent
from abmarl.sim.components.actor import Actor, GridMovementActor

class DiscretizeMovement(Actor):

    action_mapping = {
        0: np.array([-1, -1]),
        1: np.array([-1,  0]),
        2: np.array([-1,  1]),
        3: np.array([ 0, -1]),
        4: np.array([ 0,  0]),
        5: np.array([ 0,  1]),
        6: np.array([ 1, -1]),
        7: np.array([ 1,  0]),
        8: np.array([ 1,  1]),
    }

    def __init__(self, actor=None, agents=None, **kwargs):
        self.actor = actor
        self.agents = agents
        for agent in self.agents.values():
            if isinstance(agent, GridMovementAgent):
                assert agent.move_range == 1, "DiscretizeMovemenet only works with move_range of 1."
                agent.action_space[self.channel] = Discrete(9)
    
    @property
    def actor(self):
        return self._actor

    @actor.setter
    def actor(self, value):
        assert isinstance(value, GridMovementActor), "Actor must be a GridMovementActor."
        self._actor = value

    @property
    def channel(self):
        return self.actor.channel

    @property
    def null_value(self):
        return 4

    def process_action(self, agent, action_dict, **kwargs):
        action = super()._get_action_from_dict(action_dict, **kwargs)
        action_as_box = self.action_mapping[action]
        action_dict[self.channel] = action_as_box
        return self.actor.process_action(agent, action_dict, **kwargs)
