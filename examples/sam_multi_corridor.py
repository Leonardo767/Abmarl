from enum import IntEnum
from gym.spaces import Box, Discrete, MultiBinary
import numpy as np
from abmarl.sim import Agent, AgentBasedSimulation

class MultiCorridor(AgentBasedSimulation):

    class Actions(IntEnum):
        LEFT = 0
        STAY = 1
        RIGHT = 2

    def __init__(self, end=10, num_agents=5):
        self.end = end
        agents = {}
        for i in range(num_agents):
            agents[f'agent{i}'] = Agent(
                id=f'agent{i}',
                action_space=Discrete(3),
                observation_space={
                    'position': Box(0, self.end-1, (1,), np.int),
                    'left': MultiBinary(1),
                    'right': MultiBinary(1)
                }
            )
        self.agents = agents
        self.finalize()

def reset(self, **kwargs):
    location_sample = np.random.choice(self.end-1, len(self.agents), False)
    self.corridor = np.empty(self.end, dtype=object)
    for i, agent in enumerate(self.agents.values()):
        agent.position = location_sample[i]
        self.corridor[location_sample[i]] = agent

    self.reward = {agent_id: 0 for agent_id in self.agents}

def step(self, action_dict, **kwargs):
    for agent_id, action in action_dict.items():
        agent = self.agents[agent_id]

        if action == self.Actions.LEFT:
            if agent.position != 0 and self.corridor[agent.position-1] is None:
                self.corridor[agent.position] = None
                agent.position -= 1
                self.corridor[agent.position] = agent
                self.reward[agent_id] -= 1

            elif agent.position == 0: 
                self.reward[agent_id] -= 5 

            else:
                self.reward[agent_id] -= 5 
                self.reward[self.corridor[agent.position-1].id] -= 2
	
        elif action == self.Actions.RIGHT:
            if self.corridor[agent.position + 1] is None:
                self.corridor[agent.position] = None
                agent.position += 1
                if agent.position == self.end-1:
                    self.reward[agent_id] += self.end ** 2
                else:

                    self.corridor[agent.position] = agent
                    self.reward[agent_id] -= 1 

            else: 
                self.reward[agent_id] -= 5 
                self.reward[self.corridor[agent.position+1].id] -= 2

        elif action == self.Actions.STAY:
            self.reward[agent_id] -= 1

###########################################################################
# Getters
def get_obs(self, agent_id, **kwargs):
    agent_position = self.agents[agent_id].position

    if agent_position == 0 or self.corridor[agent_position-1] is None:
        left = False
    else:
        left = True

    if agent_position == self.end-1 or self.corridor[agent_position+1] is None:
        right = False
    else:
        right = True

    return {
        'position': [agent_position],
        'left': [left],
        'right': [right],
    }

def get_done(self, agent_id, **kwargs):
    return self.agents[agent_id].position == self.end - 1

def get_all_done(self, **kwargs):
    for agent in self.agents.values():
        if agent.position != self.end - 1:
            return False
    return True

def get_reward(self, agent_id, **kwargs):
    agent_reward = self.reward[agent_id]
    self.reward[agent_id] = 0
    return agent_reward

def get_info(self, agent_id, **kwargs):
    return {}
##########################################################################

def render(self, *args, fig=None, **kwargs):
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










