
from amber.envs.predator_prey import PredatorPreyEnv, Predator, Prey

"""
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

py_interface.Init(1234, 4096) # key poolSize
var = py_interface.Ns3AIRL(1234, TcpRlEnv, TcpRlAct)
#with v as o:
#    for i in range(10):
#        o[i] = ctypes.c_int(i)
#    print(*o)
#with var as data:

while not var.isFinish():
    # while var.GetVersion() % 2 != 1:
    #     pass
    # with var as data:
    #     # print(data.env.ssThresh, data.env.cWnd)
    with var as data:
        if data == None:
            break
#data = var
    print("second loop")
    #if data == None:
     #   print("none") 
    print(var.GetVersion())
    ssThresh = data.env.ssThresh
    cWnd = data.env.cWnd
    segmentsAcked = data.env.segmentsAcked
    segmentSize = data.env.segmentSize
    bytesInFlight = data.env.bytesInFlight
    print(ssThresh, cWnd, segmentsAcked, segmentSize, bytesInFlight)
    new_cWnd = 1
    new_ssThresh = 1

    data.act.new_cWnd = new_cWnd
    data.act.new_ssThresh = new_ssThresh

py_interface.FreeMemory()
"""
region = 6
predators = [Predator(id=f'predator{i}', attack=1) for i in range(2)]
prey = [Prey(id=f'prey{i}') for i in range(7)]
agents = predators + prey

env_config = {
    'region': region,
    'max_steps': 200,
    'observation_mode': PredatorPreyEnv.ObservationMode.DISTANCE,
    'agents': agents,
}
env = PredatorPreyEnv.build(env_config)
obs = env.reset()
done = {agent_id: False for agent_id in env.agents}
print(obs['predator0'])
env.render()
while True:
    action = {agent_id: env.agents[agent_id].action_space.sample() for agent_id in obs if not done[agent_id]}
    obs, reward, done, info = env.step(action)
    print(obs['predator0'])
    env.render()
    if done['__all__']:
        break
env.release_shared_memory()
