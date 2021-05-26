
from .communication_wrapper import CommunicationWrapper

import py_interface
import ctypes

class NS3Environment(ctypes.Structure):
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


class NS3AgentActions(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('run_simulation', ctypes.c_bool),
        ('agent_send_msg', ctypes.c_bool * 10),
        ('agent_position_x', ctypes.c_uint32 * 10),
        ('agent_position_y', ctypes.c_uint32 * 10),
        ('agent_position_z', ctypes.c_uint32 * 10)
    ]


class NS3CommunicationWrapper(CommunicationWrapper):

    def __init__(self, env):
        super().__init__(env)
        py_interface.Init(1234, 4096) # key poolSize
        self.ns3_environment = py_interface.Ns3AIRL(1234, NS3Environment, NS3AgentActions)

    def step(self, action_dict, **kwargs):
        """
        First, we process the receive actions, which will be used to determine
        any message that are successfully communicated among agents. Then, we call
        the step function from the wrapped environment. Finally, we process the
        send actions to update the message buffer observations.
        """
        # transfer data from/to the environment
        if not self.ns3_environment.isFinish():
            with self.ns3_environment as data:
                if data != None:
                    # receive environment data from ns3
                    print("Getting ns3 environment data...")
                    print("Environment version: " + str(self.ns3_environment.GetVersion()))
                    # dummy data received
                    nodeId = data.env.nodeId
                    socketUid = data.env.socketUid
                    envType = data.env.envType
                    simTime_us = data.env.simTime_us
                    ssThresh = data.env.ssThresh
                    cWnd = data.env.cWnd
                    segmentSize = data.env.segmentSize
                    segmentsAcked = data.env.segmentsAcked
                    bytesInFlight = data.env.bytesInFlight
                    # send action data to ns3
                    print("Environment data: nodeId: " + str(nodeId))
                    print("Sending actions to ns3...")
                    # set this to true for ns3 to start the simulation
                    data.act.run_simulation = True
                    #set each agent to send a message for now. admiral to determine which agents to send msg
                    for index in range(0, len(data.act.agent_send_msg)):
                        data.act.agent_send_msg[index]= True
#                    data.act.agent_send_msg[2] = False # set specific agent to not send msg, for testing
                    print("Actions: run_simulation: " + str(data.act.run_simulation))

        super().step(action_dict, **kwargs)

        #check to see if done condition is true, if so, shut down simulation.
        if self.env.get_all_done():
            with self.ns3_environment as data:
                if data != None:
                    #set this to false for ns3 to end the simulation
                    data.act.run_simulation = False
                    print("Actions: shutdown, " + " run_simulation: " + str(data.act.run_simulation))
                    self.release_shared_memory()

    def release_shared_memory(self):
        py_interface.FreeMemory()
