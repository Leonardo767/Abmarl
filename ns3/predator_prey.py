
from abc import ABC, abstractmethod

from gym.spaces import Box, Discrete, Dict
import numpy as np

from amber.envs import Agent
from amber.envs import CommunicationEnvironment

import py_interface
import ctypes

class TcpRlEnv(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('nodeId', ctypes.c_uint32),
        ('socketUid', ctypes.c_uint32),
        ('envType', ctypes.c_uint8),
        ('simTime_us', ctypes.c_int64),
        ('ssThresh', ctypes.c_uint32),
        ('cWnd', ctypes.c_uint32),
        ('segmentSize', ctypes.c_uint32),
        ('segmentsAcked', ctypes.c_uint32),
        ('bytesInFlight', ctypes.c_uint32),
    ]


class TcpRlAct(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('new_ssThresh', ctypes.c_uint32),
        ('new_cWnd', ctypes.c_uint32)
    ]

"""
class NS3Environment(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('message_received', ctypes.bool),
    ]


class PredatorAction(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('simulation_end', ctypes.c_bool),
        ('send_message', ctypes.c_bool)
    ]
"""

py_interface.Init(1234, 4096) # key poolSize
# ns3_environment = py_interface.Ns3AIRL(1234, NS3Environment, PredatorAction)
ns3_environment = py_interface.Ns3AIRL(1234, TcpRlEnv, TcpRlAct)

class PredatorPreyAgent(Agent, ABC):
    """
    In addition to their own agent-type-specific parameters, every Agent in the Predator Prey
    environment will have the following parameters:

    move: int
        The maximum movement range. 0 means the agent can only stay, 1 means the agent
        can move one square away (including diagonals), 2 means two, and so on.
        Default 1.
    view: int
        How much of the region the agent can observe.
        Default 10.
    """
    @abstractmethod
    def __init__(self, move=None, view=None, **kwargs):
        super().__init__(**kwargs)
        self.move = move
        self.view = view

    @property
    def configured(self):
        """
        Determine if the agent has been successfully configured.
        """
        if super().configured and self.move is not None and self.view is not None:
            return True
        else:
            return False

class Prey(PredatorPreyAgent):
    """
    Currently, Prey don't have any additional required parameters beyond the shared parameters. We
    include this class for the sake of the design.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @property
    def value(self):
        """
        The enumerated value of this agent is 1.
        """
        return 1

class Predator(PredatorPreyAgent):
    """
    In addition to the shared parameters, Predators must have the following property:

    attack: int
        The effective range of the attack. 0 means only effective on the same square, 1
        means effective at range 1, 2 at range 2, and so on.
        Default 0.
    """
    def __init__(self, attack=None, **kwargs):
        super().__init__(**kwargs)
        self.attack = attack

    @property
    def configured(self):
        """
        Determine if the agent has been successfully configured.
        """
        if super().configured and self.attack is not None:
            return True
        else:
            return False
    
    @property
    def value(self):
        """
        The enumerated value of this agent is 1.
        """
        return 2

class PredatorPreyEnv(CommunicationEnvironment):
    """
    Each agent observes other agents around its own location. Both predators and
    prey agents can move around. Predators' goal is to approach prey and attack
    it. Preys' goal is to stay alive for as long as possible.

    Note: we recommend that you use the class build function to instantiate the environment because
    it has smart config checking for the environment and will create agents that are configured to
    work with the environment.
    """

    from enum import IntEnum
    class ObservationMode(IntEnum):
        GRID = 0
        DISTANCE = 1

    class ActionStatus(IntEnum):
        BAD_MOVE = 0
        GOOD_MOVE = 1
        NO_MOVE = 2
        BAD_ATTACK = 3
        GOOD_ATTACK = 4
        EATEN = 5

    @classmethod
    def build(cls, env_config={}):
        """
        Parameters
        ----------

        region: int
            The size of the discrete space.
            Region must be >= 2.
            Default 10.

        max_steps: int
            The maximum number of steps per episode.
            Must be >= 1.
            Default 200.
        
        observation_mode: ObservationMode enum
            Either GRID or DISTANCE. In GRID, the agents see a grid of values around them as
            large as their view. In DISTANCE, the agents see the distance between themselves and
            other agents that they can see. Note: communication only works with
            DISTANCE observation mode.
            Default GRID.
        
        rewards: dict
            A dictionary that maps the various action status to a reward per each
            agent type. Any agent type that you create must have mappings for all
            possible action statuses for that agent type. The default is {
                'predator': {
                    BAD_MOVE: -region,
                    GOOD_MOVE: -1,
                    NO_MOVE: 0,
                    BAD_ATTACK: -region,
                    GOOD_ATTACK: region**2
                },
                'prey': {
                    BAD_MOVE: -2,
                    GOOD_MOVE: region,
                    NO_MOVE: region,
                    EATEN: -region**2
                },
            }

        agents: list of PredatorPreyAgent objects.
            You can set the parameters for each of the agent that will override
            the default parameters. For example,
                agents = [
                    Prey(id='prey0', view=7, move=2),
                    Predator(id='predator1', view=3, attack=2),
                    Prey(id='prey2', view=5, move=3),
                    Predator(id='predator3', view=2, move=2, attack=1),
                    Predator(id='predator4', view=0, attack=3)
                ]
        
        Returns:
        --------
        Configured instance of PredatorPreyEnv with configured PredatorPreyAgents.
        """
        import warnings
        config = {  # default config
            'region': 10,
            'max_steps': 200,
            'observation_mode': cls.ObservationMode.GRID,
            # 'rewards': # Determined based on the size of the region. See below.
            # 'agents': # Determine based on the size of the region. See below.
        }

        # --- region --- #
        if 'region' in env_config:
            region = env_config['region']
            if type(region) is not int or region < 2:
                raise TypeError("region must be an integer greater than 2.")
            else:
                config['region'] = region

        # Assign this here because we must use the right size of the region.
        config['agents'] = [
            Prey(id='prey0', view=config['region']-1, move=1),
            Predator(id='predator0', view=config['region']-1, move=1, attack=0)
        ]
        # Assign this here so that we can coordinate rewards with region size.
        config['rewards'] = {
            'predator': {
                cls.ActionStatus.BAD_MOVE: -config['region'],
                cls.ActionStatus.GOOD_MOVE: -1,
                cls.ActionStatus.NO_MOVE: 0,
                cls.ActionStatus.BAD_ATTACK: -config['region'],
                cls.ActionStatus.GOOD_ATTACK: config['region']**2,
            },
            'prey': {
                cls.ActionStatus.BAD_MOVE: -config['region'],
                cls.ActionStatus.GOOD_MOVE: config['region'],
                cls.ActionStatus.NO_MOVE: config['region'],
                cls.ActionStatus.EATEN: -config['region']**2,
            },
        }

        # --- max_steps --- #
        if 'max_steps' in env_config:
            max_steps = env_config['max_steps']
            if type(max_steps) is not int or max_steps < 1:
                raise TypeError("max_steps must be an integer at least 1.")
            else:
                config['max_steps'] = max_steps

        # --- observation_mode --- #
        if 'observation_mode' in env_config:
            observation_mode = env_config['observation_mode']
            if observation_mode not in cls.ObservationMode:
                raise TypeError("observation_mode must be either GRID or DISTANCE.")
            else:
                config['observation_mode'] = observation_mode
        
        # --- rewards --- #
        if 'rewards' in env_config:
            rewards = env_config['rewards']
            if type(rewards) is not dict:
                raise TypeError("rewards must be a dict (see docstring).")
            else:
                config['rewards'] = rewards

        # --- agents --- #
        if 'agents' in env_config:
            agents = env_config['agents']
            if type(agents) is not list:
                raise TypeError("agents must be a list of PredatorPreyAgent objects. " + \
                    "Each element in the list is an agent's configuration. See " + \
                    "PredatorPreyAgent docstring for more information.")
            else:
                for agent in agents:
                    if not isinstance(agent, PredatorPreyAgent):
                        raise TypeError("Every agent must be an instance of PredatorPreyAgent.")

                    if agent.view is None:
                        agent.view = config['region'] - 1
                    elif type(agent.view) is not int or \
                        agent.view < 0 or \
                        agent.view > config['region'] -1:
                        raise TypeError(agent['id'] + " must have a view that is an integer " + \
                            "between 0 and " + str(config['region'] - 1))
                    
                    if agent.move is None:
                        agent.move = 1
                    elif type(agent.move) is not int or \
                        agent.move < 0 or \
                        agent.move > config['region'] - 1:
                        raise TypeError(agent['id'] + " must have a move that is an integer " + \
                            "between 0 and " + str(config['region'] - 1))
                    
                    if type(agent) is Predator:
                        if agent.attack is None:
                            agent.attack = 0
                        elif type(agent.attack) is not int or \
                            agent.attack < 0 or \
                            agent.attack > config['region']:
                            raise TypeError(agent['id'] + " must have an attack that is an integer " + \
                                "between 0 and " + str(config['region']))
                config['agents'] = agents
        
        # Create list of agent objects
        if config['observation_mode'] == cls.ObservationMode.GRID:
            observation_space_builder = lambda agent: Box(-1, 2, (2*agent.view+1, 2*agent.view+1), np.int)
        else: # 'distance
            observation_space_builder = lambda agent: Dict({
                    other_agent.id: Box(-config['region']+1, config['region']-1, (3,), np.int)
                    for other_agent in config['agents'] if other_agent.id != agent.id
                })

        for agent in config['agents']:
            if type(agent) is Prey:
                agent.observation_space = observation_space_builder(agent)
                agent.action_space = Box(-agent.move, agent.move, (2,), np.int)
            else:
                agent.observation_space = observation_space_builder(agent)
                agent.action_space = Dict({
                    'attack': Discrete(2),
                    'move': Box(-agent.move, agent.move, (2,), np.int),
                })
        config['agents'] = {agent.id: agent for agent in config['agents']}

        return cls(config)

    def __init__(self, config):
        """
        region: int
        max_steps: int
        agents: List of agent ids
        """
        self.region = config['region']
        self.max_steps = config['max_steps']
        self.agents = config['agents']
        self.rewards = config['rewards']
        self._collect_state = self._observe_grid \
            if config['observation_mode'] == self.ObservationMode.GRID \
            else self._observe_distance

    def reset(self):
        """
        Randomly pick positions for each of the agents.
        """
        import copy
        self.step_count = 0

        # Randomly assign agent positions
        for agent in self.agents.values():
            agent.position = np.random.randint(0, self.region, 2)

        # The morgue is the staging area for agents who have died in this time
        # step. We need it because we must output the obsersvations, rewards, and
        # done status (True) for dead agents. However, we don't want those agents
        # to appear in other agents' observations since they have died. We can
        # accomplish this with the morgue.
        self.morgue = set()

        # Holding for all agents that have died in previous time-steps. Agents
        # in the cememtery are effectively removed from the environment. They don't
        # appear in other agents' observations and they don't have observations
        # of their own.
        self.cemetery = set()

        return self._collect_state()

    def step(self, joint_actions):
        """
        The environment will update its state with the joint actions from all
        the agents. All agents can choose to move up to the amount of squares
        enabled in their move configuration. In addition, predators can choose to ATTACK.

        The actions are received as a dictionary that maps the agent's id to its
        action. We then return dictionaries mapping the agents' ids to observations,
        rewards, done conditions, and additional info.
        """
        self.step_count += 1

        # transfer data from/to the environment
        if not ns3_environment.isFinish():
            with ns3_environment as data:
                if data != None:
                    print("Getting ns3 environment data...")
                    print("Environment version: " + str(ns3_environment.GetVersion()))
                    nodeId = data.env.nodeId
                    socketUid = data.env.socketUid
                    envType = data.env.envType
                    simTime_us = data.env.simTime_us
                    ssThresh = data.env.ssThresh
                    cWnd = data.env.cWnd
                    segmentSize = data.env.segmentSize
                    segmentsAcked = data.env.segmentsAcked
                    bytesInFlight = data.env.bytesInFlight
                    #message_received = data.env.message_received
                    #print("Environment data: message_received: " + str(message_received))
                    print("Environment data: nodeId: " + str(nodeId))
                    print("Sending actions to ns3...")
                    data.act.new_ssThresh = 1
                    data.act.new_cWnd = 1
                    print("Actions: new_ssThresh: " + str(data.act.new_ssThresh))
                    #data.act.send_message = true
                    #data.act.simulation_end = false
                    #print("Actions: send_message: " + str(data.act.send_message)) 

        # We want to make sure that only agents that are still alive have sent us actions
        for agent_id in joint_actions:
            assert agent_id not in self.cemetery

        # Initial setup
        rewards = {}
        done = {agent_id: False for agent_id in joint_actions}
        done['__all__'] = False

        # Process the predators first
        for predator_id, action in joint_actions.items():
            predator = self.agents[predator_id]
            if type(predator) == Prey: continue # Process the predators first
            # Attack takes precedent over move
            if action['attack'] == 1:
                action_status = self._process_attack_action(predator)
            else:
                action_status = self._process_move_action(predator, action['move'])
            rewards[predator_id] = self.rewards['predator'][action_status]
        
        # Now process the prey actions
        for prey_id, action in joint_actions.items():
            prey = self.agents[prey_id]
            if type(prey) == Predator: continue # Process the prey now
            if prey_id in self.morgue: # This prey was eaten by a predator in this time step.
                done[prey_id] = True
                rewards[prey_id] = self.rewards['prey'][self.ActionStatus.EATEN]
                continue
            action_status = self._process_move_action(prey, action)
            rewards[prey_id] = self.rewards['prey'][action_status]

        # Are there any more prey left?
        done['__all__'] = True
        for agent in self.agents.values():
            if type(agent) == Prey and agent.id not in self.morgue and agent.id not in self.cemetery:
                done['__all__'] = False
                break

        if self.step_count >= self.max_steps:
            done['__all__'] = True

        #check to see if done condition is true, if so, shut down simulation.
        if done['__all__']:
            with ns3_environment as data:
                if data != None:
                    #data.act.simulation_end = true
                    #print("Actions: Shutdown, " + " simulation_end: " + str(data.act.simulation_end))
                    data.act.new_ssThresh = 1234
                    print("Actions: shutdown, " + " new_ssThresh: " + str(data.act.new_ssThresh))
 
        return self._collect_state(), rewards, done, {}

    def render(self, *args, fig=None, **kwargs):
        """
        Visualize the state of the environment. If a figure is received, then we
        will draw but not actually plot because we assume the caller will do the
        work (e.g. with an Animation object). If there is no figure received, then
        we will draw and plot the environment.
        """
        draw_now = fig is None
        if draw_now:
            from matplotlib import pyplot as plt
            fig = plt.gcf()

        fig.clear()
        ax = fig.gca()
        ax.set(xlim=(-0.5, self.region - 0.5), ylim=(-0.5, self.region - 0.5))
        ax.set_xticks(np.arange(-0.5, self.region - 0.5, 1.))
        ax.set_yticks(np.arange(-0.5, self.region - 0.5, 1.))
        ax.grid(linewidth=5)

        prey_x = [agent.position[0] for agent in self.agents.values() if type(agent) == Prey and agent.id not in self.cemetery]
        prey_y = [agent.position[1] for agent in self.agents.values() if type(agent) == Prey and agent.id not in self.cemetery]
        ax.scatter(prey_x, prey_y, marker='s', s=200, c='g')

        predator_x = [agent.position[0] for agent in self.agents.values() if type(agent) == Predator and agent.id not in self.cemetery]
        predator_y = [agent.position[1] for agent in self.agents.values() if type(agent) == Predator and agent.id not in self.cemetery]
        ax.scatter(predator_x, predator_y, s=200)
    
        if draw_now:
            plt.plot()
            plt.pause(1e-17)

        return ax
    
    def fuse_observations(self, obs, fusion_matrix):
        if self._collect_state == self._observe_grid:
            raise NotImplementedError("We do not yet support communications with GRID observation_mode.")

        for receiving_agent_id in obs:
            if receiving_agent_id in self.cemetery: continue # Ignore dead agents
            received_messages = fusion_matrix[receiving_agent_id]
            receiving_agent = self.agents[receiving_agent_id]
            for sending_agent_id, message in received_messages.items():
                if sending_agent_id not in self.cemetery and message: # Only receive messages from alive agents
                    for spied_agent_id, distance_type in obs[sending_agent_id].items():
                        # Don't receive a message about yourself or other agents
                        # that you already see
                        if spied_agent_id != receiving_agent_id and \
                                obs[receiving_agent_id][spied_agent_id][2] == 0 and \
                                distance_type[2] != 0: # We actually see an agent here
                            spied_agent = self.agents[spied_agent_id]
                            y_diff = spied_agent.position[1] - receiving_agent.position[1]
                            x_diff = spied_agent.position[0] - receiving_agent.position[0]
                            obs[receiving_agent_id][spied_agent_id] = np.array([x_diff, y_diff, spied_agent.value])
                    # Also see the relative location of the sending agent itself
                    sending_agent = self.agents[sending_agent_id]
                    y_diff = sending_agent.position[1] - receiving_agent.position[1]
                    x_diff = sending_agent.position[0] - receiving_agent.position[0]
                    obs[receiving_agent_id][sending_agent_id] = np.array([x_diff, y_diff, sending_agent.value])
        return obs
    
    def _process_move_action(self, agent, action):
        """
        The environment will attempt to move the agent according to its action.
        If that move is successful, the agent will move and we will return GOOD_MOVE.
        If that move is unsuccessful, the agent will not move and we will return
        BAD_MOVE. Moves can be unsuccessful if the agent moves against a wall.
        If the agent chooses to stay, then we do not move the agent and return NO_MOVE.

        This should only be called if the agent has chosen to move or stay still.
        """
        if all(action == [0, 0]):
            return self.ActionStatus.NO_MOVE
        elif 0 <= agent.position[0] + action[0] < self.region and \
           0 <= agent.position[1] + action[1] < self.region: # Still inside the boundary, good move
            agent.position += action
            return self.ActionStatus.GOOD_MOVE
        else:
            return self.ActionStatus.BAD_MOVE
    
    def _process_attack_action(self, predator):
        """
        The environment will process the predator's attack action. If that attack
        is successful, the prey will be added to the morgue and we will return
        GOOD_ATTACK. If the attack is unsuccessful, then we will return BAD_ATTACK.

        This should only be called if the agent chooses to attack. Only predators
        can choose to attack.
        """
        for prey in self.agents.values():
            if type(prey) == Predator: continue # Not a prey
            if prey.id in self.cemetery: continue # Ignore dead agents
            if abs(predator.position[0] - prey.position[0]) <= predator.attack and abs(predator.position[1] - prey.position[1]) <= predator.attack: # Good attack, prey is eaten:
                self.morgue.add(prey.id)
                return self.ActionStatus.GOOD_ATTACK
        return self.ActionStatus.BAD_ATTACK
    
    def _observe_grid(self):
        """
        Each agent observes a grid of values surrounding its location, whose size
        is determiend by the agent's view. These cells are filled with the value
        of the agent's type, including -1 for out of bounds and 0 for empty square.
        If there are multiple agents on the same cell, then we prioritize the agent
        that is of a different type. For example, a prey will only see a predator
        on a cell that a predator and another prey both occupy.
        """
        observations = {agent_id: np.zeros((agent.view*2+1, agent.view*2+1)) for agent_id, agent in self.agents.items() if agent_id not in self.cemetery}
        
        for my_id, my_agent in self.agents.items():
            if my_id in self.cemetery: continue # Ignore dead agents
            signal = observations[my_id]

            # --- Determine the boundaries of the agents' grids --- #
            # For left and top, we just do: view - x,y >= 0
            # For the right and bottom, we just do region - x,y - 1 - view > 0
            if my_agent.view - my_agent.position[0] >= 0: # Left end
                signal[0:my_agent.view - my_agent.position[0], :] = -1
            if my_agent.view - my_agent.position[1] >= 0: # Top end
                signal[:, 0:my_agent.view - my_agent.position[1]] = -1
            if self.region - my_agent.position[0] - my_agent.view - 1 < 0: # Right end
                signal[self.region- my_agent.position[0] - my_agent.view - 1:,:] = -1
            if self.region - my_agent.position[1] - my_agent.view - 1 < 0: # Bottom end
                signal[:, self.region - my_agent.position[1] - my_agent.view - 1:] = -1

            # --- Determine the positions of all the other alive agents --- #
            for other_id, other_agent in self.agents.items():
                if other_id == my_id or other_id in self.morgue or other_id in self.cemetery: continue
                y_diff = other_agent.position[1] - my_agent.position[1]
                x_diff = other_agent.position[0] - my_agent.position[0]
                if -my_agent.view <= y_diff <= my_agent.view and -my_agent.view <= x_diff <= my_agent.view:
                    x_diff += my_agent.view
                    y_diff += my_agent.view
                    if signal[x_diff, y_diff] != 0: # Already another agent here
                        if type(my_agent) != type(other_agent):
                            signal[x_diff, y_diff] = other_agent.value
                    else:
                        signal[x_diff, y_diff] = other_agent.value
            
            # --- Save the observations for this agent --- #
            observations[my_id] = np.flipud(np.transpose(signal))
        
        self._clean_agent_lists()
        return observations
    
    def _observe_distance(self):
        """
        Agents observe a distance from itself to other agents only if the other
        agents are visible (i.e. within the agent's view). If agents are not visible,
        then the observation "slot" is empty.
        """
        observations = {}
        for my_id, my_agent in self.agents.items():
            if my_id in self.cemetery: continue # Ignore dead agents
            observations[my_id] = {}
            for other_id in self.agents:
                if my_id == other_id: continue
                observations[my_id][other_id] = np.zeros(3, dtype=np.int)
            for other_id, other_agent in self.agents.items(): # Fill values for agents that are still alive
                if other_id == my_id or other_id in self.morgue or other_id in self.cemetery: continue
                y_diff = other_agent.position[1] - my_agent.position[1]
                x_diff = other_agent.position[0] - my_agent.position[0]
                if -my_agent.view <= y_diff <= my_agent.view and -my_agent.view <= x_diff <= my_agent.view:
                    observations[my_id][other_id] = np.array((x_diff, y_diff, other_agent.value))
        
        self._clean_agent_lists()
        return observations

    def _clean_agent_lists(self):
        """
        Any agent that has died is removed from the list of agents.
        """ 
        for agent_id in self.morgue:
            self.cemetery.add(agent_id)
        self.morgue.clear()

    def release_shared_memory(self):
        py_interface.FreeMemory()

