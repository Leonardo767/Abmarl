from matplotlib import pyplot as plt
import numpy as np

from abmarl.sim.components.state import ContinuousPositionState, SpeedAngleState
from abmarl.sim.components.actor import SpeedAngleMovementActor
from abmarl.sim.components.observer import SpeedObserver, AngleObserver
from abmarl.sim.components.done import TooCloseDone
from abmarl.sim.components.agent import SpeedAngleAgent, SpeedAngleActingAgent, \
    SpeedAngleObservingAgent
from abmarl.sim import AgentBasedSimulation
from abmarl.tools.matplotlib_utils import mscatter


class BirdAgent(SpeedAngleAgent, SpeedAngleActingAgent, SpeedAngleObservingAgent): pass


class Flight(AgentBasedSimulation):
    def __init__(self, **kwargs):
        self.agents = kwargs['agents']

        # State
        self.position_state = ContinuousPositionState(**kwargs)
        self.speed_angle_state = SpeedAngleState(**kwargs)

        # Actor
        self.move_actor = SpeedAngleMovementActor(
            position_state=self.position_state, speed_angle_state=self.speed_angle_state, **kwargs
        )

        # Observer
        self.speed_observer = SpeedObserver(**kwargs)
        self.angle_observer = AngleObserver(**kwargs)

        # Done
        self.done = TooCloseDone(position=self.position_state, **kwargs)

        self.finalize()

    def reset(self, **kwargs):
        self.position_state.reset(**kwargs)
        self.speed_angle_state.reset(**kwargs)

    def step(self, action_dict, **kwargs):
        for agent, action in action_dict.items():
            self.move_actor.process_move(
                self.agents[agent], action.get('accelerate', np.zeros(1)),
                action.get('bank', np.zeros(1)), **kwargs
            )

    def render(self, fig=None, **kwargs):
        fig.clear()

        # Draw the resources
        ax = fig.gca()

        # Draw the agents
        ax.set(xlim=(0, self.position_state.region), ylim=(0, self.position_state.region))
        ax.set_xticks(np.arange(0, self.position_state.region, 1))
        ax.set_yticks(np.arange(0, self.position_state.region, 1))

        agents_x = [agent.position[0] for agent in self.agents.values()]
        agents_y = [agent.position[1] for agent in self.agents.values()]
        mscatter(agents_x, agents_y, ax=ax, m='o', s=100, edgecolor='black', facecolor='gray')

        plt.plot()
        plt.pause(1e-6)

    def get_obs(self, agent_id, **kwargs):
        agent = self.agents[agent_id]
        return {
            **self.speed_observer.get_obs(agent, **kwargs),
            **self.angle_observer.get_obs(agent, **kwargs),
        }

    def get_reward(self, agent_id, **kwargs):
        pass

    def get_done(self, agent_id, **kwargs):
        return self.done.get_done(self.agents[agent_id], **kwargs)

    def get_all_done(self, **kwargs):
        return self.done.get_all_done(**kwargs)

    def get_info(self, agent_id, **kwargs):
        pass


if __name__ == "__main__":
    agents = {
        f'bird{i}': BirdAgent(
            id=f'bird{i}', min_speed=0.5, max_speed=1.0, max_acceleration=0.1,
            max_banking_angle=90, max_banking_angle_change=90,
            initial_banking_angle=30
        ) for i in range(24)
    }

    sim = Flight(
        region=20,
        agents=agents,
        collision_distance=1.0,
    )
    fig = plt.figure()
    sim.reset()
    sim.render(fig=fig)

    print(sim.get_obs('bird0'))

    for i in range(50):
        sim.step({agent.id: agent.action_space.sample() for agent in agents.values()})
        sim.render(fig=fig)
        for agent in agents:
            print(agent, ': ', sim.get_done(agent))
        print('\n')

    print(sim.get_all_done())
