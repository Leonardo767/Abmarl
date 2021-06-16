
from gym.spaces import Box
from matplotlib import pyplot as plt
import numpy as np

from abmarl.sim import AgentBasedSimulation
from abmarl.sim.grid_world import GridWorldAgent, GridObservingAgent, MovingAgent
from abmarl.sim.grid_world.state import GridWorldState
from abmarl.sim.grid_world.actor import MoveActor
from abmarl.tools.matplotlib_utils import mscatter


class WallAgent(GridWorldAgent):
    """
    Wall agents, immobile and view blocking.

    Args:
        encoding: Default encoding is 1.
    """
    def __init__(self, encoding=1, **kwargs):
        super().__init__(**kwargs)
        self.encoding = encoding

class ExploringAgent(MovingAgent, GridObservingAgent):
    """
    Exploring agents, moving around and observing the grid.

    Args:
        encoding: Default encoding is 2.
    """
    def __init__(self, encoding=2, render_shape='o', **kwargs):
        super().__init__(**kwargs)
        self.encoding = encoding
        self.render_shape = render_shape


class GridSim(AgentBasedSimulation):
    def __init__(self, **kwargs):
        self.agents = kwargs['agents']

        # State Components
        self.grid_state = GridWorldState(**kwargs)

        # Action Components
        self.move_actor = MoveActor(grid_state=self.grid_state, **kwargs)

        self.finalize()

    def reset(self, **kwargs):
        self.grid_state.reset(**kwargs)

    def step(self, action_dict, **kwargs):
        for agent_id, action in action_dict.items():
            agent = self.agents[agent_id]
            self.move_actor.process_action(agent, action, **kwargs)

    def render(self, fig=None, **kwargs):
        fig.clear()

        # Draw the resources
        ax = fig.gca()

        # Draw the agents
        ax.set(xlim=(0, self.grid_state.cols), ylim=(0, self.grid_state.rows))
        ax.set_xticks(np.arange(0, self.grid_state.cols, 1))
        ax.set_yticks(np.arange(0, self.grid_state.rows, 1))
        ax.grid()

        agents_x = [
            agent.position[1] + 0.5 for agent in self.agents.values()
        ]
        agents_y = [
            self.grid_state.rows - 0.5 - agent.position[0] for agent in self.agents.values()
        ]
        shape = [agent.render_shape for agent in self.agents.values()]
        mscatter(agents_x, agents_y, ax=ax, m=shape, s=200, edgecolor='black', facecolor='gray')

        plt.plot()
        plt.pause(1e-6)

    def get_obs(self, agent_id, **kwargs):
        """
        Return the agent's observation.
        """
        agent = self.agents[agent_id]
        # Generate a completely empty grid
        local_grid = np.empty((agent.view_range * 2 + 1, agent.view_range * 2 + 1), dtype=object)
        local_grid.fill(-1)

        # Copy the section of the grid around the agent's location
        (r, c) = agent.position
        r_lower = max([0, r - agent.view_range])
        r_upper = min([self.grid_state.rows - 1, r + agent.view_range]) + 1
        c_lower = max([0, c - agent.view_range])
        c_upper = min([self.grid_state.cols - 1, c + agent.view_range]) + 1
        local_grid[
            (r_lower+agent.view_range-r):(r_upper+agent.view_range-r),
            (c_lower+agent.view_range-c):(c_upper+agent.view_range-c)
        ] = self.grid_state.grid[r_lower:r_upper, c_lower:c_upper]

        # Generate an observation mask. The agent's observation can be blocked
        # by walls, which hide the cells "behind" them. In the mask, 1 means that
        # this square is visibile, 0 means that it is invisible.
        mask = np.ones((2 * agent.view_range + 1, 2 * agent.view_range + 1))
        for other in self.agents.values():
            if isinstance(other, WallAgent):
                r_diff, c_diff = other.position - agent.position
                if -agent.view_range <= r_diff <= agent.view_range and \
                        -agent.view_range <= c_diff <= agent.view_range:
                    if c_diff > 0 and r_diff == 0: # Wall is to the right of agent
                        upper = lambda t: (r_diff + 0.5) / (c_diff - 0.5) * t
                        lower = lambda t: (r_diff - 0.5) / (c_diff - 0.5) * t
                        for c in range(c_diff, agent.view_range+1):
                            for r in range(-agent.view_range, agent.view_range+1):
                                if c == c_diff and r == r_diff: continue # don't mask the wall
                                if lower(c) < r < upper(c):
                                    mask[r + agent.view_range, c + agent.view_range] = 0
                    elif c_diff > 0 and r_diff > 0: # Wall is below-right of agent
                        upper = lambda t: (r_diff + 0.5) / (c_diff - 0.5) * t
                        lower = lambda t: (r_diff - 0.5) / (c_diff + 0.5) * t
                        for c in range(c_diff, agent.view_range+1):
                            for r in range(r_diff, agent.view_range+1):
                                if c == c_diff and r == r_diff: continue # Don't mask the wall
                                if lower(c) < r < upper(c):
                                    mask[r + agent.view_range, c + agent.view_range] = 0
                    elif c_diff == 0 and r_diff > 0: # Wall is below the agent
                        left = lambda t: (c_diff - 0.5) / (r_diff - 0.5) * t
                        right = lambda t: (c_diff + 0.5) / (r_diff - 0.5) * t
                        for c in range(-agent.view_range, agent.view_range+1):
                            for r in range(r_diff, agent.view_range+1):
                                if c == c_diff and r == r_diff: continue # don't mask the wall
                                if left(r) < c < right(r):
                                    mask[r + agent.view_range, c + agent.view_range] = 0
                    elif c_diff < 0 and r_diff > 0: # Wall is below-left of agent
                        upper = lambda t: (r_diff + 0.5) / (c_diff + 0.5) * t
                        lower = lambda t: (r_diff - 0.5) / (c_diff - 0.5) * t
                        for c in range(c_diff, -agent.view_range-1, -1):
                            for r in range(r_diff, agent.view_range+1):
                                if c == c_diff and r == r_diff: continue # don't mask the wall
                                if lower(c) < r < upper(c):
                                    mask[r + agent.view_range, c + agent.view_range] = 0
                    elif c_diff < 0 and r_diff == 0: # Wall is left of agent
                        upper = lambda t: (r_diff + 0.5) / (c_diff + 0.5) * t
                        lower = lambda t: (r_diff - 0.5) / (c_diff + 0.5) * t
                        for c in range(c_diff, -agent.view_range-1, -1):
                            for r in range(-agent.view_range, agent.view_range+1):
                                if c == c_diff and r == r_diff: continue # don't mask the wall
                                if lower(c) < r < upper(c):
                                    mask[r + agent.view_range, c + agent.view_range] = 0
                    elif c_diff < 0 and r_diff < 0: # Wall is above-left of agent
                        upper = lambda t: (r_diff + 0.5) / (c_diff - 0.5) * t
                        lower = lambda t: (r_diff - 0.5) / (c_diff + 0.5) * t
                        for c in range(c_diff, -agent.view_range - 1, -1):
                            for r in range(r_diff, -agent.view_range - 1, -1):
                                if c == c_diff and r == r_diff: continue # don't mask the wall
                                if lower(c) < r < upper(c):
                                    mask[r + agent.view_range, c + agent.view_range] = 0
                    elif c_diff == 0 and r_diff < 0: # Wall is above the agent
                        left = lambda t: (c_diff - 0.5) / (r_diff + 0.5) * t
                        right = lambda t: (c_diff + 0.5) / (r_diff + 0.5) * t
                        for c in range(-agent.view_range, agent.view_range+1):
                            for r in range(r_diff, -agent.view_range - 1, -1):
                                if c == c_diff and r == r_diff: continue # don't mask the wall
                                if left(r) < c < right(r):
                                    mask[r + agent.view_range, c + agent.view_range] = 0
                    elif c_diff > 0 and r_diff < 0: # Wall is above-right of agent
                        upper = lambda t: (r_diff + 0.5) / (c_diff + 0.5) * t
                        lower = lambda t: (r_diff - 0.5) / (c_diff - 0.5) * t
                        for c in range(c_diff, agent.view_range+1):
                            for r in range(r_diff, -agent.view_range - 1, -1):
                                if c == c_diff and r == r_diff: continue # don't mask the wall
                                if lower(c) < r < upper(c):
                                    mask[r + agent.view_range, c + agent.view_range] = 0

        # Convolve the grid observation with the mask.
        obs = np.zeros((2 * agent.view_range + 1, 2 * agent.view_range + 1), dtype=np.int)
        for r in range(2 * agent.view_range + 1):
            for c in range(2 * agent.view_range + 1):
                if mask[r, c]:
                    obj = local_grid[r, c]
                    if obj == -1: # Out of bounds
                        obs[r, c] = -1
                    elif obj is None: # Empty
                        obs[r, c] = 0
                    else: # Something there, so get its encoding
                        obs[r, c] = obj.encoding
                else: # Cell blocked by wall. Indicate invisible with -2
                    obs[r, c] = -2

        return {'grid': obs}

    def get_reward(self, agent_id, **kwargs):
        """
        Return the agent's reward.
        """
        pass

    def get_done(self, agent_id, **kwargs):
        """
        Return the agent's done status.
        """
        pass

    def get_all_done(self, **kwargs):
        """
        Return the simulation's done status.
        """
        pass

    def get_info(self, agent_id, **kwargs):
        """
        Return the agent's info.
        """
        pass


def build_grid_sim(object_registry, file_name):
    assert 0 not in object_registry, "0 is reserved for empty space."
    agents = {}
    n = 0
    with open(file_name, 'r') as fp:
        lines = fp.read().splitlines()
        cols = len(lines[0].split(' '))
        rows = len(lines)
        for row, line in enumerate(lines):
            chars = line.split(' ')
            assert len(chars) == cols, f"Mismatched number of columns per row in {file_name}"
            for col, char in enumerate(chars):
                if char in object_registry:
                    agent = object_registry[char](n)
                    agent.initial_position = np.array([row, col])
                    agents[agent.id] = agent
                    n += 1

    return GridSim(rows=rows, cols=cols, agents=agents)


if __name__ == "__main__":
    
    from abmarl.sim import ActingAgent

    fig = plt.figure()
    explorers = {
        f'explorer{i}': ExploringAgent(id=f'explorer{i}', move_range=1, view_range=3)
        for i in range(5)
    }
    explorers['explorer0'].encoding = 5
    walls = {
        f'wall{i}': WallAgent(id=f'wall{i}') for i in range(12)
    }
    agents = {**explorers, **walls}
    sim = GridSim(rows=8, cols=12, agents=agents)
    sim.reset()
    sim.render(fig=fig)

    # Agents move around
    for _ in range(100):
        action = {
            agent.id: agent.action_space.sample() for agent in agents.values()
            if isinstance(agent, ActingAgent)
        }
        sim.step(action)
        sim.render(fig=fig)

    # Examine the agents' observations
    from pprint import pprint
    for agent in explorers.values():
        print(agent.position)
        pprint(sim.get_obs(agent.id)['grid'])
        print()

    plt.show()
