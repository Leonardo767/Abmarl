// This script configures N number of nodes on an 802.11b physical layer, with
// 802.11b NICs in adhoc mode, and by default, sends 1 packet to all the nodes
// within range. The packet size and number of packets to send are configurable.
// The max communication distance between nodes, before packets are not received,
// is determined by the 3 log distance loss model.
// The distance between nodes is determined randomly by setting the maxDistance
// variable.
//
// There are a number of command-line options available to control
// the default behavior.  The list of available command-line options
// can be listed with the following command:
// ./waf --run "rl-wifi --help"
//
// Example of changing the number of packets to send for each node:
// ./waf --run "rl-wifi --numPackets=20"
//
// Note that all ns-3 attributes (not just the ones exposed in the below
// script) can be changed at command line;
//
// This script can also be helpful to put the Wifi layer into verbose
// logging mode; this command will turn on all wifi logging:
//
// ./waf --run "rl-wifi --verbose=1"
//
#include <limits>
#include <random>
#include "ns3/command-line.h"
#include "ns3/config.h"
#include "ns3/double.h"
#include "ns3/string.h"
#include "ns3/log.h"
#include "ns3/yans-wifi-helper.h"
#include "ns3/mobility-helper.h"
#include "ns3/ipv4-address-helper.h"
#include "ns3/yans-wifi-channel.h"
#include "ns3/mobility-model.h"
#include "ns3/internet-stack-helper.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/ns3-ai-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("RLWifiNS3AI");

/*
This struct defines the data being sent from the NS3 environment
to the RL environment. The data below is example data. More useful
data products could include which packets were received by various
nodes.
Changes to this struct must be mirrored in the RL environment
communication wrapper.
*/
struct NS3Environment
{ 
  uint32_t nodeId;
  uint32_t socketUid;
  uint8_t envType;
  int64_t simTime_us;
  uint32_t ssThresh;
  uint32_t cWnd;
  uint32_t segmentSize;
  uint32_t segmentsAcked;
  uint32_t bytesInFlight;
} Packed;

/*
This struct defines the data being received from the RL environment.
Changes to this struct must be mirrored in the RL environment.
*/
struct NS3AgentActions
{
    bool runSimulation; //control simulation startup
    //array of bools, each representing one agent(node) indexed by agent id,
    //if true, that agent sends a message during this time increment
    bool agentSendMsg[10];
    //agents x, y, z positions during this time increment, currently unused
    uint32_t agentPositionX[10];
    uint32_t agentPositionY[10];
    uint32_t agentPositionZ[10];
} Packed;

//NS3AI required class definition
class Ns3RlEnv : public Ns3AIRL<NS3Environment, NS3AgentActions>
{
public:
  Ns3RlEnv () = delete;
  Ns3RlEnv (uint16_t id);

protected:
};

//NS3AI required definition
Ns3RlEnv::Ns3RlEnv(uint16_t id) : Ns3AIRL<NS3Environment, NS3AgentActions>(id)
{
  SetCond(2, 0);
}

//Instantiate the NS3AI environment. Number sequence given here must match
//Number sequence given in RL environment.
Ns3RlEnv * my_env = new Ns3RlEnv(1234);

static int packetsReceived = 0;

//Packet receive callback function.
void ReceivePacket (Ptr<Socket> socket)
{

  while (socket->Recv ())
  {
    ++packetsReceived;
//    NS_LOG_UNCOND ("Received one packet! " << packetsReceived);
  }
  NS_LOG_UNCOND("ReceivePacket: function exited. " << "Time: " << (uint64_t)(Simulator::Now().GetNanoSeconds()) << " ID: " << socket->GetNode()->GetId());
}

// command line arguments made global to be easily passed to callback functions
uint32_t numNodes = 4; // number of agents, ie. nodes
double interval = 1.0; // length of time increment, in seconds

static void RandomizedSocketSend (std::vector<Ptr<Socket>> & sockets, uint32_t pktSize,
                                  uint32_t pktCount, Time pktInterval)
{ 
  static int numPackets = 0;
  static int nodeNum = 0;
  auto act = my_env->ActionGetterCond();
  
  if(act->agentSendMsg[nodeNum] == true){ 
    for (int index = 0; index < pktCount; ++index) {
        ++numPackets;
        NS_LOG_UNCOND("RandomizedSocketSend: Sending new packet. PktCount: " << numPackets
                      << " Time: " << (uint64_t)(Simulator::Now().GetNanoSeconds())
                      << " ID: " << sockets[nodeNum]->GetNode()->GetId());
        sockets[nodeNum]->Send (Create<Packet> (pktSize));
    }
  } else {
     NS_LOG_UNCOND("RandomizedSocketSend: node skipped: " << nodeNum);
  }
  if(nodeNum < numNodes-1){
    ++nodeNum;
  } else {
    nodeNum = 0;
  }
}

//This function blocks on receiving data from RL environment. After data is received,
//packet sends are generated for each node in the network. Packet sends are given a
//random time increment within the packet interval so that packets are unlikely to be
//sent at exactly the same time. This is because the NS3 simulator will not send a
//packet if two packets are sent at exactly the same time. This is a reasonable 
//modification to make since it is extremely unlikely for this to occur in the real
//world. In the real world, clocks on different nodes will not be aligned. However,
//in the simulator's world, these packet collisions can occur.
static void GenerateTraffic (std::vector<Ptr<Socket>> & sockets, uint32_t pktSize,
                             uint32_t pktCount, Time pktInterval )
{
    // *** Send NS3 environment data to RL, Blocking***
    auto env = my_env->EnvSetterCond();
    env->socketUid = 2; //dummy data, just to test if it works...
    env->envType = 1; //dummy data
    env->simTime_us = Simulator::Now().GetMicroSeconds(); //dummy data
    env->nodeId = 5; //dummy data
    env->segmentSize = packetsReceived; //dummy data. commandeered for packets received
    NS_LOG_UNCOND ("SendReceivedPacketData Func: Time: " << (uint64_t)(Simulator::Now().GetNanoSeconds())
                   << " env->ssThresh: " << env->ssThresh << " env->cWnd: "
                   << env->cWnd << " Packets Received: (env->segmentSize): " << env->segmentSize);
    my_env->SetCompleted(); //blocking
    // *** End send ***

    // *** Receive action data from RL, non-blocking ***
    auto act = my_env->ActionGetterCond();
    bool runSimulation = act->runSimulation;
    // *** End receive ***

    // on true, send randomized packets.
    if(runSimulation == true) {
        NS_LOG_UNCOND ("GenerateTraffic: Time: " << Simulator::Now().GetNanoSeconds());
        for(int nodeNum = 0; nodeNum < sockets.size(); ++nodeNum) {
            std::random_device rd1;
            std::mt19937 gen1(rd1());
            std::uniform_real_distribution<> distribution1(0, (double)interval/10);
            double random1 = distribution1(gen1);
            Simulator::ScheduleWithContext (nodeNum,
                                            Seconds(random1), &RandomizedSocketSend,
                                            sockets, pktSize, pktCount, pktInterval);
        }
        Simulator::Schedule (pktInterval, &GenerateTraffic,
                             sockets, pktSize,pktCount, pktInterval);
    } else {
        NS_LOG_UNCOND("GenerateTraffic: Closing socket.");
        for(int index = 0; index < sockets.size(); ++index){
            sockets[index]->Close ();
        }
        my_env->SetFinish();
        NS_LOG_UNCOND("GenerateTraffic: Socket closed, environment finished.");
        Simulator::Stop();
    }
}

// RL-wifi NS3 main script
int main (int argc, char *argv[])
{
  std::string phyMode ("DsssRate1Mbps");
  uint32_t packetSize = 1000; // bytes per packet
  uint32_t numPackets = 1; // packets produced per agent during a time increment
  bool verbose = false; // increase verbosity of output to screen / log
  double maxDistance = 10.0; //The x,y,z position of nodes/agents, generated randomly, from 0 to maxDistance

  CommandLine cmd;
  cmd.AddValue ("phyMode", "Wifi Phy mode", phyMode);
  cmd.AddValue ("packetSize", "size of application packet sent", packetSize);
  cmd.AddValue ("numPackets", "number of packets generated per interval", numPackets);
  cmd.AddValue ("interval", "interval (seconds) between RL steps", interval);
  cmd.AddValue ("numNodes", "the number of nodes in this scenario", numNodes);
  cmd.AddValue ("maxDistance", "the max distance between nodes, actual distance random between one and max", maxDistance);
  cmd.AddValue ("verbose", "turn on all WifiNetDevice log components", verbose);
  cmd.Parse (argc, argv);
  // Convert to time object
  Time interPacketInterval = Seconds (interval);

  // Fix non-unicast data rate to be the same as that of unicast
  Config::SetDefault ("ns3::WifiRemoteStationManager::NonUnicastMode",
                      StringValue (phyMode));

  NodeContainer c;
  c.Create (numNodes);

  // The below set of helpers will help us to put together the wifi NICs we want
  WifiHelper wifi;
  if (verbose)
    {
      wifi.EnableLogComponents ();  // Turn on all Wifi logging
    }
  wifi.SetStandard (WIFI_STANDARD_80211b);

  YansWifiPhyHelper wifiPhy =  YansWifiPhyHelper::Default ();
  // This is one parameter that matters when using FixedRssLossModel
  // set it to zero; otherwise, gain will be added
  wifiPhy.Set ("RxGain", DoubleValue (0) );

  // ns-3 supports RadioTap and Prism tracing extensions for 802.11b
  wifiPhy.SetPcapDataLinkType (WifiPhyHelper::DLT_IEEE802_11_RADIO);

  YansWifiChannelHelper wifiChannel;
  wifiChannel.SetPropagationDelay ("ns3::ConstantSpeedPropagationDelayModel");
  //Using Three Log Distance propagation loss model so that packets will be dropped
  //when a receiver is too far from sender
  wifiChannel.AddPropagationLoss ("ns3::ThreeLogDistancePropagationLossModel");
  wifiPhy.SetChannel (wifiChannel.Create ());

  // Add a mac and disable rate control
  WifiMacHelper wifiMac;
  wifi.SetRemoteStationManager ("ns3::ConstantRateWifiManager",
                                "DataMode",StringValue (phyMode),
                                "ControlMode",StringValue (phyMode));
  // Set it to adhoc mode
  wifiMac.SetType ("ns3::AdhocWifiMac");
  NetDeviceContainer devices = wifi.Install (wifiPhy, wifiMac, c);

  // *** Allocate Positions of Nodes ***
  // Note that with FixedRssLossModel, the positions below are not
  // used for received signal strength.
  // However, with the three log distance propagation loss model,
  // these node/agent positions are used for determining pack loss
  MobilityHelper mobility;
  Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator> ();
  // Generate random numbers for x, y, z, coordinates for each node
  for(int index = 0; index < numNodes; ++index){
    std::random_device rd1;
    std::mt19937 gen1(rd1());
    std::uniform_real_distribution<> distribution1(0, maxDistance);
    double random1 = distribution1(gen1);
    std::random_device rd2;
    std::mt19937 gen2(rd2());
    std::uniform_real_distribution<> distribution2(0, maxDistance);
    double random2 = distribution2(gen2);
    std::random_device rd3;
    std::mt19937 gen3(rd3());
    std::uniform_real_distribution<> distribution3(0, maxDistance);
    double random3 = distribution3(gen3);
    //add node coordinates to Position Allocator
    positionAlloc->Add (Vector (random1, random2, random3));

    NS_LOG_UNCOND("Postion for agent " << index << ": x("
                  << random1 << ") y(" << random2 << ") z(" << random2 << ")"); 
  }
  mobility.SetPositionAllocator (positionAlloc);
  mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
  mobility.Install (c);

  InternetStackHelper internet;
  internet.Install (c);

  Ipv4AddressHelper ipv4;
  NS_LOG_UNCOND ("Assign IP Addresses.");
  ipv4.SetBase ("10.1.0.0", "255.255.0.0");
  Ipv4InterfaceContainer i = ipv4.Assign (devices);

  TypeId tid = TypeId::LookupByName ("ns3::UdpSocketFactory");
  //Create receiver sink sockets for each node
  for(int index = 0; index < numNodes; ++index){
    Ptr<Socket> recvSink = Socket::CreateSocket (c.Get (index), tid);
    InetSocketAddress local = InetSocketAddress (Ipv4Address::GetAny (), 80);
    recvSink->Bind (local);
    recvSink->SetRecvCallback (MakeCallback (&ReceivePacket));
  }

  std::vector<Ptr<Socket>> sources;
  //Create sender broadcast sockets for each node
  for(int index = 0; index < numNodes; ++index){
    Ptr<Socket> source = Socket::CreateSocket (c.Get (index), tid);
    InetSocketAddress remote = InetSocketAddress (Ipv4Address ("255.255.255.255"), 80);
    source->SetAllowBroadcast (true);
    source->Connect (remote);
    sources.push_back(source);
  }

  //run simulator
  Simulator::ScheduleWithContext (sources[0]->GetNode ()->GetId (),
                                  Seconds (0.0), &GenerateTraffic,
                                  sources, packetSize, numPackets, interPacketInterval);
  Simulator::Run ();
  Simulator::Destroy ();

  NS_LOG_UNCOND("Simulation finished.");

  return 0;
}
