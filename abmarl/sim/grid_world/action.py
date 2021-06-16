
from abc import ABC, abstractmethod

from abmarl.sim.grid_world import GridWorldBaseComponent, MovingAgent
from abmarl.sim.grid_world.state import GridWorldState

class ActionBaseComponent(GridWorldBaseComponent, ABC):
    """
    Abstract ActionComponent class from which all ActionComponents will inherit.
    """
    @abstractmethod
    def process_action(self, agent, action, **kwargs):
        """
        Process the agent's action.

        Args:
            agent: The acting agent.
            action: The relevant action.
        """
        pass

    @property
    @abstractmethod
    def key(self):
        """
        The key in the action dictionary.
        """
        pass

    # @property
    # @abstractmethod
    # def corresponding_agent(self):
    #     """
    #     The agent class that works with this Action component.
    #     """
    #     pass


class MoveAction(ActionBaseComponent):
    """
    Process moving agents.
    """
    def __init__(self, grid_state=None, **kwargs):
        super().__init__(**kwargs)
        self.grid_state = grid_state

    def process_action(self, agent, action_dict, **kwargs):
        action = action_dict[self.key]
        self.grid_state.set_position(agent, agent.position + action)

    @property
    def key(self):
        return "move"

    @property
    def grid_state(self):
        return self._grid_state
    
    @grid_state.setter
    def grid_state(self, value):
        assert isinstance(value, GridWorldState), "Grid state must be a GridState object."
        self._grid_state = value
    
    # @property
    # def corresponding_agent(self):
    #     return MovingAgent
