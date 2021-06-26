
from abc import ABC, abstractmethod

import numpy as np

class Grid(ABC):
    """
    A Grid has a numpy array that stores the positions of the agents.

    Manages the agent positions through the add and remove functions while abstracting
    the underlying datatype used to store the agent there.

    Args:
        rows: The number of rows in the grid.
        cols: The number of columns in the grid.
    """
    def __init__(self, rows, cols):
        self._internal = np.empty((rows, cols), dtype=object)

    @abstractmethod
    def reset(self, **kwargs):
        """
        Reset the grid to an empty state.
        """
        pass

    @abstractmethod
    def query(self, agent, ndx):
        """
        Query a cell in the grid to see if is available to this agent.

        Args:
            agent: The agent for which we are checking availabilty.
            ndx: The cell to query.

        Returns:
            True if the cell is available for this agent, otherwise False.
        """
        pass

    @abstractmethod
    def place(self, agent, ndx):
        """
        Place an agent at an index.

        If the placement is successful, the agent will be placed at that index
        in the grid and the agent's position will be updated.

        Args:
            agent: The agent to place.
            ndx: The new index for this agent.

        Returns:
            The successfulness of the placement.
        """
        pass

    @abstractmethod
    def move(self, agent, to_ndx):
        """
        Move an agent from one index to another.

        If the move is successful, the agent will be placed at that index in the
        grid and the agent's position will be updated.

        Note: the agent will be removed from its old position in the grid.

        Args:
            agent: The agent to move.
            to_ndx: The new index for this agent.

        Returns:
            The successfulness of the move.
        """
        pass

    @abstractmethod
    def remove(self, agent, ndx):
        """
        Remove an agent from an index.

        Args:
            agent: The agent to remove
            ndx: The old index for this agent.
        """
        pass

    @abstractmethod
    def search(self, ndx, search_func, **kwargs):
        """
        Search the grid at an index.

        If an agent is positioned at that cell and meets the requirements in search_func,
        then return that agent.

        Args:
            ndx: The cell at which to search.
            search_func: a function that defines the search criteria. That function
                should take an agent as input and any other kwargs as necessary.

        Returns:
            If there is an agent that meets the critera, then return it. Otherwise,
            return None.
        """

    @abstractmethod
    def _place(self, agent, ndx):
        """
        Unprotected placement. Internal use only.
        """
        pass


class NonOverlappingGrid(Grid):
    """
    A grid where agents cannot overlap.
    """
    def reset(self, **kwargs):
        self.fill(None)

    def query(self, agent, ndx):
        """
        The cell is available for the agent if it is empty.
        """
        ndx = tuple(ndx)
        return self[ndx] is None

    def place(self, agent, ndx):
        """
        The placement is succesful if the new position is unoccupied.
        """
        ndx = tuple(ndx)
        if self.query(agent, ndx):
            self._place(agent, ndx)
            agent.position = np.array(ndx)
            return True
        else:
            return False

    def move(self, agent, to_ndx):
        """
        The move is succesful if the new position is unoccupied.
        """
        from_ndx = tuple(agent.position)
        to_ndx = tuple(to_ndx)
        if to_ndx == from_ndx:
            return True
        if self.query(agent, to_ndx):
            self.remove(agent, from_ndx)
            self._place(agent, to_ndx)
            agent.position = np.array(to_ndx)
            return True
        else:
            return False

    def remove(self, agent, ndx):
        ndx = tuple(ndx)
        self[ndx] = None

    def search(self, ndx, search_func, **kwargs):
        if search_func(self[ndx], **kwargs):
            return self[ndx]

    def _place(self, agent, ndx):
        # Unprotected placement
        self[ndx] = agent


class OverlappableGrid(Grid):
    """
    A grid where agents can overlap.
    """
    def reset(self, **kwargs):
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                self[i,j] = {}

    def query(self, agent, ndx):
        """
        The cell is available for the agent if it is empty or if both the occupying
        agent and the querying agent are overlappable.
        """
        ndx = tuple(ndx)
        return not self[ndx] or (
            next(iter(self[ndx].values())).overlappable and agent.overlappable
        )

    def place(self, agent, ndx):
        """
        The placement is successful if the new position is unoccupied or if the
        agent already occupying that position is overlappable AND this agent is
        overlappable.
        """
        ndx = tuple(ndx)
        if self.query(agent, ndx):
            self._place(agent, ndx)
            agent.position = np.array(ndx)
            return True
        else:
            return False

    def move(self, agent, to_ndx):
        """
        The move is successful if the new position is unoccupied or if the agent
        already occupying that position is overlappable AND this agent is overlappable.
        """
        from_ndx = tuple(agent.position)
        to_ndx = tuple(to_ndx)
        if to_ndx == from_ndx:
            return True
        elif self.query(agent, to_ndx):
            self.remove(agent, from_ndx)
            self._place(agent, to_ndx)
            agent.position = np.array(to_ndx)
            return True
        else:
            return False

    def remove(self, agent, ndx):
        ndx = tuple(ndx)
        del self[ndx][agent.id]

    def search(self, ndx, search_func, **kwargs):
        for agent in self[ndx].values():
            if search_func(agent, **kwargs):
                return agent

    def _place(self, agent, ndx):
        # Unprotected placement
        self[ndx][agent.id] = agent
