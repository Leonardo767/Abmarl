
import numpy as np

from abmarl.sim import PrincipleAgent, ActingAgent, ObservingAgent


class GridWorldAgent(PrincipleAgent):
    """
    The base agent in the GridWorld.
    """
    def __init__(self, initial_position=None, view_blocking=False, **kwargs):
        super().__init__(**kwargs)
        self.initial_position = initial_position
        self.view_blocking = view_blocking

    @property
    def initial_position(self):
        """
        The agent's initial position at reset.
        """
        return self._initial_position

    @initial_position.setter
    def initial_position(self, value):
        if value is not None:
            assert type(value) is np.ndarray, "Initial position must be a numpy array."
            assert value.shape == (2,), "Initial position must be a 2-element array."
            assert value.dtype in [np.int, np.float], "Initial position must be numerical."
        self._initial_position = value

    @property
    def position(self):
        """
        The agent's position in the grid.
        """
        return self._position

    @position.setter
    def position(self, value):
        self._position = value

    @property
    def encoding(self):
        """
        The numerical value given to other agents who observe this agent.
        """
        return self._encoding

    @encoding.setter
    def encoding(self, value):
        assert type(value) is int, f"{self.id}'s encoding must be an integer."
        assert value != -2, "-2 encoding reserved for masked observation."
        assert value != -1, "-1 encoding reserved for out of bounds."
        assert value != 0, "0 encoding reserved for empty cell."
        self._encoding = value

    @property
    def render_shape(self):
        """
        The agent's shape in the rendered grid.
        """
        return getattr(self, '_render_shape', 's')

    @render_shape.setter
    def render_shape(self, value):
        self._render_shape = value

    @property
    def view_blocking(self):
        """
        Specify if this agent blocks other agent's observations.
        """
        return self._view_blocking

    @view_blocking.setter
    def view_blocking(self, value):
        assert type(value) is bool, "View blocking must be either True or False."
        self._view_blocking = value

    @property
    def confiured(self):
        return super().configured and self.encoding is not None

class GridObservingAgent(GridWorldAgent, ObservingAgent):
    """
    Observe the grid up to view_range cells.

    Attributes:
        view_range: 
    """
    def __init__(self, view_range=None, **kwargs):
        super().__init__(**kwargs)
        self.view_range = view_range
    
    @property
    def view_range(self):
        """
        The number of cells "away" this agent can observe in each step.
        """
        return self._view_range

    @view_range.setter
    def view_range(self, value):
        assert type(value) is int, "View range must be an integer."
        assert 0 <= value, "View range must be a nonnegative integer."
        self._view_range = value

    @property
    def confiured(self):
        return super().configured and self.view_range is not None


class MovingAgent(GridWorldAgent, ActingAgent):
    """
    Move up to move_range cells.
    """
    def __init__(self, move_range=None, **kwargs):
        super().__init__(**kwargs)
        self.move_range = move_range
    
    @property
    def move_range(self):
        """
        The maximum number of cells away that the agent can move.
        """
        return self._move_range

    @move_range.setter
    def move_range(self, value):
        assert type(value) is int, "Move range must be an integer."
        assert 0 <= value, "Move range must be a nonnegative integer."
        self._move_range = value

    @property
    def confiured(self):
        return super().configured and self.move_range is not None


class HealthAgent(GridWorldAgent):
    """
    Agents have health points and can die.

    Health is bounded between 0 and 1.
    """
    def __init__(self, initial_health=None, **kwargs):
        super().__init__(**kwargs)
        self.initial_health = initial_health

    @property
    def health(self):
        """
        The agent's health throughout the simulation trajectory.

        The health will always be between 0 and 1.
        """
        return self._health

    @health.setter
    def health(self, value):
        assert type(value) in [int, float], "Health must be a numeric value."
        self._health = min(max(value, 0), 1)
        assert 0 <= value <= 1, "Health must be between 0 and 1."
        self._health = value
    
    @property
    def initial_health(self):
        """
        The agent's initial health between 0 and 1.
        """
        return self._initial_health
    
    @initial_health.setter
    def initial_health(self, value):
        assert type(value) in [int, float], "Initial health must be a numeric value."
        assert 0 < value <= 1, "Initial value must be between 0 and 1."
        self._initial_health = value

    @property
    def is_alive(self):
        """
        The agent "is alive" if its health is greater than 0.
        """
        return self.health > 0


class TeamAgent(GridWorldAgent):
    """
    Agents with team assignment.

    The team value can be used to set rules for inter-agent interaction.
    """
    def __init__(self, team=None, **kwargs):
        super().__init__(**kwargs)
        self.team = team

    @property
    def team(self):
        """
        The agent's team must be an integer.
        """
        return self._team

    @team.setter
    def team(self, value):
        assert type(value) is int, "Team must be an integer."
        self._team = value

    @property
    def configured(self):
        return super().configured and self.team is not None

class AttackingAgent(ActingAgent, GridWorldAgent):
    """
    Agents that can attack other agents.
    """
    def __init__(self, attack_range=None, attack_strength=None, attack_accuracy=None, 
            **kwargs):
        super().__init__(**kwargs)
        self.attack_range = attack_range
        self.attack_strength = attack_strength
        self.attack_accuracy = attack_accuracy

    @property
    def attack_range(self):
        """
        The maximum range of the attack.
        """
        return self._attack_range

    @attack_range.setter
    def attack_range(self, value):
        assert type(value) is int, "Attack range must be an integer."
        assert 0 <= value, "Attack range must be a nonnegative integer."
        self._attack_range = value

    @property
    def attack_strength(self):
        """
        How much of the attacked agent's health is depleted.
        """
        return self._attack_strength

    @attack_strength.setter
    def attack_strength(self, value):
        assert type(value) in [int, float], "Attack strength must be a numeric value."
        assert 0 <= value <= 1, "Attack strength must be between 0 and 1."
        self._attack_strength = value

    @property
    def attack_accuracy(self):
        """
        The effective accuracy of the agent's attack. Should be between 0 and 1.
        To make deterministic attacks, use 1.
        """
        return self._attack_accuracy

    @attack_accuracy.setter
    def attack_accuracy(self, value):
        assert type(value) in [int, float], "Attack accuracy must be a numeric value."
        assert 0 <= value <= 1, "Attack accuracy must be between 0 and 1."
        self._attack_accuracy = value
    
    @property
    def confiured(self):
        return super().configured and self.attack_range is not None and \
            self.attack_strength is not None and self.attack_accuracy is not None


class BroadcastingAgent(ActingAgent, GridWorldAgent):
    """
    Agents can broadcast their observations to other agents.
    """
    def __init__(self, broadcast_range, **kwargs):
        super().__init__(**kwargs)
        self.broadcast_range = broadcast_range

    @property
    def broadcast_range(self):
        """
        The range of the broadcast, centered around the agent's position.

        Broadcast range must be a nonnegative integer.
        """
        return self._broadcast_range

    @broadcast_range.setter
    def broadcast_range(self, value):
        assert type(value) is int, "Broadcast range must be an integer."
        assert 0 <= value, "Broadcast range must be a nonnegative integer."
        self._broadcast_range = value

    @property
    def configured(self):
        return super().configured and self.broadcast_range is not None
