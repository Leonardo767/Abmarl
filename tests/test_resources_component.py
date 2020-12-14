
from gym.spaces import Box

import numpy as np

from admiral.envs.components.resources import ObservingAgent, HarvestingAgent, PositionAgent
from admiral.envs.components.resources import GridResourceState, GridResourceObserver, GridResourcesActor

class ResourcesTestAgent(ObservingAgent, PositionAgent, HarvestingAgent): pass

def test_grid_resources_components():
    agents = {
        'agent0': ResourcesTestAgent(id='agent0', max_harvest=0.5, view=1, starting_position=np.array([0, 0])),
        'agent1': ResourcesTestAgent(id='agent1', max_harvest=0.5, view=2, starting_position=np.array([2, 2])),
        'agent2': ResourcesTestAgent(id='agent2', max_harvest=0.5, view=3, starting_position=np.array([3, 1])),
        'agent3': ResourcesTestAgent(id='agent3', max_harvest=0.5, view=4, starting_position=np.array([1, 4])),
    }
    initial_resources = np.array([
        [0.84727271, 0.47440489, 0.29693299, 0.5311798,  0.25446477],
        [0.58155565, 0.79666705, 0.53135774, 0.51300926, 0.90118474],
        [0.7125912,  0.86805178, 0.,         0.,         0.38538807],
        [0.48882905, 0.36891643, 0.76354359, 0.,         0.71936923],
        [0.55379678, 0.32311497, 0.46094834, 0.12981774, 0.        ],
    ])

    state = GridResourceState(agents=agents, original_resources=initial_resources, regrow_rate=0.4)
    actor = GridResourcesActor(resources=state, agents=agents)
    observer = GridResourceObserver(resources=state, agents=agents)

    state.reset()
    for agent in agents.values():
        agent.position = agent.starting_position
    np.testing.assert_array_equal(state.resources, initial_resources)

    assert np.allclose(observer.get_obs(agents['agent0']), np.array([
        [-1.,         -1.,         -1.        ],
        [-1.,          0.84727271,  0.47440489],
        [-1.,          0.58155565,  0.79666705],
    ]))
    assert np.allclose(observer.get_obs(agents['agent1']), np.array([
        [0.84727271, 0.47440489, 0.29693299, 0.5311798,  0.25446477],
        [0.58155565, 0.79666705, 0.53135774, 0.51300926, 0.90118474],
        [0.7125912,  0.86805178, 0.,         0.,         0.38538807],
        [0.48882905, 0.36891643, 0.76354359, 0.,         0.71936923],
        [0.55379678, 0.32311497, 0.46094834, 0.12981774, 0.        ],
    ]))
    assert np.allclose(observer.get_obs(agents['agent2']), np.array([
        [-1.,         -1.,          0.84727271,  0.47440489,  0.29693299,  0.5311798,   0.25446477],
        [-1.,         -1.,          0.58155565,  0.79666705,  0.53135774,  0.51300926,  0.90118474],
        [-1.,         -1.,          0.7125912,   0.86805178,  0.,          0.,          0.38538807],
        [-1.,         -1.,          0.48882905,  0.36891643,  0.76354359,  0.,          0.71936923],
        [-1.,         -1.,          0.55379678,  0.32311497,  0.46094834,  0.12981774,  0.        ],
        [-1.,         -1.,         -1.,         -1.,         -1.,         -1.,         -1.        ],
        [-1.,         -1.,         -1.,         -1.,         -1.,         -1.,         -1.        ],
    ]))
    assert np.allclose(observer.get_obs(agents['agent3']), np.array([
        [-1.,         -1.,         -1.,         -1.,         -1.,         -1., -1.,         -1.,         -1.,        ],
        [-1.,         -1.,         -1.,         -1.,         -1.,         -1., -1.,         -1.,         -1.,        ],
        [-1.,         -1.,         -1.,         -1.,         -1.,         -1., -1.,         -1.,         -1.,        ],
        [ 0.84727271,  0.47440489,  0.29693299,  0.5311798,   0.25446477, -1., -1.,         -1.,         -1.,        ],
        [ 0.58155565,  0.79666705,  0.53135774,  0.51300926,  0.90118474, -1., -1.,         -1.,         -1.,        ],
        [ 0.7125912,   0.86805178,  0.,          0.,          0.38538807, -1., -1.,         -1.,         -1.,        ],
        [ 0.48882905,  0.36891643,  0.76354359,  0.,          0.71936923, -1., -1.,         -1.,         -1.,        ],
        [ 0.55379678,  0.32311497,  0.46094834,  0.12981774,  0.,         -1., -1.,         -1.,         -1.,        ],
        [-1.,         -1.,         -1.,         -1.,         -1.,         -1., -1.,         -1.,         -1.,        ],
    ]))

    state.regrow()
    assert np.allclose(state.resources, np.array([
        [1., 0.87440489, 0.69693299, 0.9311798,  0.65446477],
        [0.98155565, 1., 0.93135774, 0.91300926, 1.],
        [1.,  1., 0.,         0.,         0.78538807],
        [0.88882905, 0.76891643, 1., 0.,         1.],
        [0.95379678, 0.72311497, 0.86094834, 0.52981774, 0.        ],
    ]))
    
    assert actor.process_harvest(agents['agent0'], 0.5) == 0.5
    assert actor.process_harvest(agents['agent1'], 0.5) == 0.
    assert actor.process_harvest(agents['agent2'], 0.5) == 0.5
    assert actor.process_harvest(agents['agent3'], 0.5) == 0.5
    assert np.allclose(state.resources, np.array([
        [0.5, 0.87440489, 0.69693299, 0.9311798,  0.65446477],
        [0.98155565, 1., 0.93135774, 0.91300926, 0.5],
        [1.,  1., 0.,         0.,         0.78538807],
        [0.88882905, 0.26891643, 1., 0.,         1.],
        [0.95379678, 0.72311497, 0.86094834, 0.52981774, 0.        ],
    ]))
    
    assert actor.process_harvest(agents['agent0'], 0.5) == 0.5
    assert actor.process_harvest(agents['agent2'], 0.5) == 0.26891643
    assert actor.process_harvest(agents['agent3'], 0.5) == 0.5
    assert np.allclose(state.resources, np.array([
        [0., 0.87440489, 0.69693299, 0.9311798,  0.65446477],
        [0.98155565, 1., 0.93135774, 0.91300926, 0.],
        [1.,  1., 0.,         0.,         0.78538807],
        [0.88882905, 0., 1., 0.,         1.],
        [0.95379678, 0.72311497, 0.86094834, 0.52981774, 0.        ],
    ]))

    state.regrow()
    assert np.allclose(state.resources, np.array([
        [0., 1., 1., 1.,  1.],
        [1., 1., 1., 1., 0.],
        [1., 1., 0., 0., 1.],
        [1., 0., 1., 0.,         1.],
        [1., 1., 1., 0.92981774, 0.        ],
    ]))
