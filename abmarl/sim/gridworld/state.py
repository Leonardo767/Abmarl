
from abc import ABC, abstractmethod

import numpy as np

from abmarl.sim.gridworld.base import GridWorldBaseComponent


class StateBaseComponent(GridWorldBaseComponent, ABC):
    """
    Abstract State Component base from which all state components will inherit.
    """
    @abstractmethod
    def reset(self, **kwargs):
        """
        Resets the part of the state for which it is responsible.
        """
        pass


class PositionState(StateBaseComponent):
    """
    Manage the agent's positions in the grid.

    Every agent occupies a unique cell.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def reset(self, **kwargs):
        """
        Give agents their starting positions.

        We use the agent's initial position if it exists. Otherwise, we randomly
        place the agent in the grid.
        """
        # Grid lookup by position
        self.grid.fill(None)
        # Prioritize placing agents with initial positions. We must keep track
        # of which positions have been taken so that the random placement below doesn't
        # try to place an agent in an already-taken position.
        ravelled_positions_taken = set()
        for agent in self.agents.values():
            if agent.initial_position is not None:
                r, c = agent.initial_position
                assert self.grid[r, c] is None, f"{agent.id} has the same initial " + \
                    f"position as {self.grid[r, c].id}. All initial positions must be unique."
                agent.position = agent.initial_position
                self.grid[r, c] = agent
                ravelled_positions_taken.add(
                    np.ravel_multi_index(agent.position, (self.rows, self.cols))
                )

        # Now randomly place any other agent who did not come with an initial position.
        ravelled_positions_available = [
            i for i in range(self.rows * self.cols) if i not in ravelled_positions_taken
        ]
        rs, cs = np.unravel_index(
            np.random.choice(ravelled_positions_available, len(self.agents), False),
            shape=(self.rows, self.cols)
        )
        for ndx, agent in enumerate(self.agents.values()):
            if agent.initial_position is None:
                r = rs[ndx]
                c = cs[ndx]
                agent.position = np.array([r, c])
                self.grid[r, c] = agent

    def set_position(self, agent, new_position, **kwargs):
        """
        Attempt to assign a new position to an agent.

        Args:
            agent: The agent whose position we are changing.
            new_position: the new position must be in bounds and must not be occupied
                by another agent.
        """
        if 0 <= new_position[0] < self.rows and \
                0 <= new_position[1] < self.cols and \
                self.grid[new_position[0], new_position[1]] is None:
            self.grid[agent.position[0], agent.position[1]] = None
            agent.position = new_position
            self.grid[agent.position[0], agent.position[1]] = agent
