from enum import IntEnum

from gym.spaces import Box, Discrete, MultiBinary
import numpy as np

from abmarl.sim import Agent, AgentBasedSimulation


class MultiCorridor(AgentBasedSimulation):
    """
    MultiCorridor simulation used for testing. Multiple agents spawn along
    a corridor and can choose to move left, right, or stay still. The agents
    must learn to move to the right until they reach the end position. The agent
    cannot move to spaces that area already occupied by other agents. An agent
    is done once it moves to the end position.

    The agent can observe its own position. It can also see if the two squares
    near it are occupied.
    """
    class Actions(IntEnum):
        LEFT = 0
        STAY = 1
        RIGHT = 2

    def __init__(self, end=10, num_agents=5):
        self.end = end - 1
        agents = {}
        for i in range(num_agents):
            agents[f'agent{i}'] = Agent(
                id=f'agent{i}',
                action_space=Discrete(3),
                observation_space={
                    'direction': MultiBinary(1),
                    'left': MultiBinary(1),
                    'right': MultiBinary(1)
                }
            )
        self.agents = agents

        self.finalize()

    def reset(self, **kwargs):
        # Added to reset target location
        self.target = np.random.randint(self.end-1, size=1)[0]
        #self.target = self.end

        location_sample = np.random.choice(self.end-2, len(self.agents), False)
        self.corridor = np.empty(self.end, dtype=object)
        for i, agent in enumerate(self.agents.values()):
            if(location_sample[i] >= self.target): location_sample[i] += 1
            agent.position = location_sample[i]
            self.corridor[location_sample[i]] = agent

        # Track the agents' rewards over multiple steps.
        self.reward = {agent_id: 0 for agent_id in self.agents}

    def step(self, action_dict, **kwargs):
        for agent_id, action in action_dict.items():
            agent = self.agents[agent_id]

            # Set a value for left of right
            move = 0
            if action == self.Actions.RIGHT:
                move = 1 # Right
            else:
                move = -1 # Left


            if action == self.Actions.STAY:
                self.reward[agent_id] -= 1 # Entropy penalty

            elif(self.target > agent.position and move == -1) or \
                (self.target < agent.position and move == 1):

                # Prevent over-moving to the left
                if agent.position == 0 and move == -1: 
                    self.reward[agent_id] -= 5 

                # Prevent over-moving to the right
                elif agent.position == self.end-1 and move == 1: 
                    self.reward[agent_id] -= 5 

         
                elif self.corridor[agent.position+move] is None:
                    self.corridor[agent.position] = None
                    agent.position += move
                    self.corridor[agent.position] = agent
                    self.reward[agent_id] -= 1

                # Tried to move into another agent
                else:
                    self.reward[agent_id] -= 5 
                    self.reward[self.corridor[agent.position+move].id] -= 2
        
            # GOOD
            elif(self.target < agent.position and move == -1) or \
                (self.target > agent.position and move == 1):

                # Good move /  Check for doneness
                if self.corridor[agent.position + move] is None:
                    self.corridor[agent.position] = None
                    agent.position += move

                    # Are they done?
                    if agent.position == self.target:
                        self.reward[agent_id] += self.end ** 2

                    # Just a good move
                    else:
                        self.corridor[agent.position] = agent
                        self.reward[agent_id] -= 1 

                # Tried to move into another agent
                else: 
                    self.reward[agent_id] -= 5 
                    self.reward[self.corridor[agent.position+move].id] -= 2

    def render(self, *args, fig=None, **kwargs):
        """
        Visualize the state of the simulation. If a figure is received, then we
        will draw but not actually plot because we assume the caller will do the
        work (e.g. with an Animation object). If there is no figure received, then
        we will draw and plot the simulation.
        """
        draw_now = fig is None
        if draw_now:
            from matplotlib import pyplot as plt
            fig = plt.gcf()

        fig.clear()
        ax = fig.gca()
        ax.set(xlim=(-0.5, self.end + 0.5), ylim=(-0.5, 0.5))
        ax.set_xticks(np.arange(-0.5, self.end + 0.5, 1.))
        ax.scatter(np.array(
            [agent.position for agent in self.agents.values()]),
            np.zeros(len(self.agents)),
            marker='s', s=200, c='g'
        )

        if draw_now:
            plt.plot()
            plt.pause(1e-17)

    def get_obs(self, agent_id, **kwargs):
        """
        Agents observe their own position and if the squares to the left and right
        are occupied by other agents.
        """
        agent_position = self.agents[agent_id].position
        if agent_position < self.target:
            direction = False
        else:
            direction = True
        if agent_position == 0 or self.corridor[agent_position-1] is None:
            left = False
        else:
            left = True
        if agent_position == self.end-1 or self.corridor[agent_position+1] is None:
            right = False
        else:
            right = True
        return {
            'direction': [direction],
            'left': [left],
            'right': [right],
        }

    def get_done(self, agent_id, **kwargs):
        """
        Agents are done when they reach the end of the corridor.
        """
        return self.agents[agent_id].position == self.target

    def get_all_done(self, **kwargs):
        """
        Simulation is done when all agents have reached the end of the corridor.
        """
        for agent in self.agents.values():
            if agent.position != self.target:
                return False
        return True

    def get_reward(self, agent_id, **kwargs):
        """
        The agent's reward is tracked throughout the simulation and returned here.
        """
        agent_reward = self.reward[agent_id]
        self.reward[agent_id] = 0
        return agent_reward

    def get_info(self, agent_id, **kwargs):
        """
        Just return an empty dictionary becuase this simulation does not track
        any info.
        """
        return {}
