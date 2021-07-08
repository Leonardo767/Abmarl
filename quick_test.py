
from abmarl.external import MultiAgentWrapper
from abmarl.managers import TurnBasedManager, AllStepManager
from abmarl.sim.corridor.multi_corridor import MultiCorridor
import numpy as np

from matplotlib import pyplot as plt
fig = plt.figure()

sim = TurnBasedManager(MultiCorridor())
agents = sim.agents

for episode in range(5):
    print(f"episode {episode}")
    obs = sim.reset()
    sim.render()
    done_agents = set()
    for step in range(1000):
        print(f"step {step}")
        action = {agent: agents[agent].action_space.sample() for agent in obs if agent not in done_agents}
        obs, reward, done, info = sim.step(action)
        sim.render()
        if done['__all__']:
            break
        else:
            for agent, done_val in done.items():
                if done_val:
                    done_agents.add(agent)
