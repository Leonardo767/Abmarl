/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2009 The Boeing Company
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 */

// This script configures two nodes on an 802.11b physical layer, with
// 802.11b NICs in adhoc mode, and by default, sends one packet of 1000
// (application) bytes to the other node.  The physical layer is configured
// to receive at a fixed RSS (regardless of the distance and transmit
// power); therefore, changing position of the nodes has no effect.
//
// There are a number of command-line options available to control
// the default behavior.  The list of available command-line options
// can be listed with the following command:
// ./waf --run "wifi-simple-adhoc --help"
//
// For instance, for this configuration, the physical layer will
// stop successfully receiving packets when rss drops below -97 dBm.
// To see this effect, try running:
//
// ./waf --run "wifi-simple-adhoc --rss=-97 --numPackets=20"
// ./waf --run "wifi-simple-adhoc --rss=-98 --numPackets=20"
// ./waf --run "wifi-simple-adhoc --rss=-99 --numPackets=20"
//
// Note that all ns-3 attributes (not just the ones exposed in the below
// script) can be changed at command line; see the documentation.
//
// This script can also be helpful to put the Wifi layer into verbose
// logging mode; this command will turn on all wifi logging:
//
// ./waf --run "wifi-simple-adhoc --verbose=1"
//
// When you are done, you will notice two pcap trace files in your directory.
// If you have tcpdump installed, you can try this:
//
// tcpdump -r wifi-simple-adhoc-0-0.pcap -nn -tt
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

NS_LOG_COMPONENT_DEFINE ("WifiSimpleAdhoc");

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

struct NS3AgentActions
{
  uint32_t new_ssThresh;
  uint32_t new_cWnd;
};

class Ns3RlEnv : public Ns3AIRL<NS3Environment, NS3AgentActions>
{
public:
  Ns3RlEnv () = delete;
  Ns3RlEnv (uint16_t id);

protected:
};

Ns3RlEnv::Ns3RlEnv(uint16_t id) : Ns3AIRL<NS3Environment, NS3AgentActions>(id)
{
  SetCond(2, 0);
}

Ns3RlEnv * my_env = new Ns3RlEnv(1234);

static int packetsReceived = 0;

void ReceivePacket (Ptr<Socket> socket)
{

  while (socket->Recv ())
  {
    ++packetsReceived;
//    NS_LOG_UNCOND ("Received one packet! " << packetsReceived);
  }
//  NS_LOG_UNCOND("ReceivePacket: function exited. " << "Time: " << (uint64_t)(Simulator::Now().GetNanoSeconds()) << " ID: " << socket->GetNode()->GetId());
}

static void SendReceivedPacketData(Ptr<Socket> socket, uint32_t pktSize,
                                   uint32_t pktCount, Time pktInterval) {
  auto env = my_env->EnvSetterCond();
  env->socketUid = 2;
  env->envType = 1;
  env->simTime_us = Simulator::Now().GetMicroSeconds();
  env->nodeId = 5;
  env->segmentSize = packetsReceived;
  NS_LOG_UNCOND ("Time: " << (uint64_t)(Simulator::Now().GetNanoSeconds()) << " env->ssThresh: " << env->ssThresh << " env->cWnd: "
                 << env->cWnd << " Packets Received: (env->segmentSize): " << env->segmentSize);
  my_env->SetCompleted();
}

static void GenerateTraffic (std::vector<Ptr<Socket>> & sockets, uint32_t pktSize,
                             uint32_t pktCount, Time pktInterval )
{
  auto act = my_env->ActionGetterCond();
  static bool firstTime = true;
  static bool endSimulation = false;
  static int numPackets = 0;

  if(act->new_ssThresh == 1){
    NS_LOG_UNCOND ("Time: " << Simulator::Now().GetNanoSeconds() << " new_cWnd: " << act->new_cWnd << " ID: " << sockets[0]->GetNode()->GetId());
    act->new_ssThresh = 0;
    for (int index = 0; index < pktCount; ++index) {
      ++numPackets;
      NS_LOG_UNCOND("GenerateTraffic: Sending new packet. PktCount: " << numPackets << " Time: " << (uint64_t)(Simulator::Now().GetNanoSeconds()));
      sockets[0]->Send(Create<Packet> (pktSize));
    }
  } else if (act->new_ssThresh == 1234) {
    NS_LOG_UNCOND("GenerateTraffic: Closing socket.");
    sockets[0]->Close ();
    my_env->SetFinish();
    endSimulation = true;
    NS_LOG_UNCOND("GenerateTraffic: Socket closed, environment finished.");
  } else {
    if(firstTime == true){
      firstTime = false;
      sockets[0]->Send (Create<Packet> (pktSize));
      ++numPackets;
    } else {
      NS_LOG_UNCOND("ERROR, incorrect state.");
    }
  }
  if(endSimulation == false){
    const double smallestTimeUnit = 0.001; //millisecond
    Time smallTimeInterval = Seconds (smallestTimeUnit);
    Time receiveInterval = pktInterval - smallTimeInterval;
    //schedule the received packet callback to send pkt data to agents
    Simulator::Schedule (receiveInterval, &SendReceivedPacketData,
                         sockets[0], pktSize,pktCount, pktInterval);
    Simulator::Schedule (pktInterval, &GenerateTraffic,
                         sockets, pktSize,pktCount, pktInterval);
  } else {
    Simulator::Stop();
  }
}

uint32_t numNodes = 4;

static void GenerateTraffic2 (std::vector<Ptr<Socket>> & sockets, uint32_t pktSize,
                             uint32_t pktCount, Time pktInterval)
{
  static int numPackets = 0;
  static int nodeNum = 0;

  for (int index = 0; index < pktCount; ++index) {
      ++numPackets;
//      NS_LOG_UNCOND("GenerateTraffic2: Sending new packet. PktCount: " << numPackets
//                    << " Time: " << (uint64_t)(Simulator::Now().GetNanoSeconds())
//                    << " ID: " << sockets[nodeNum]->GetNode()->GetId());
      sockets[nodeNum]->Send (Create<Packet> (pktSize));
  }
  if(nodeNum < numNodes-1){
    ++nodeNum;
  } else {
    nodeNum = 0;
  }
  Simulator::Schedule (pktInterval, &GenerateTraffic2,
                       sockets, pktSize,pktCount, pktInterval);
}


int main (int argc, char *argv[])
{
  std::string phyMode ("DsssRate1Mbps");
  double rss = -80;  // -dBm
  uint32_t packetSize = 1000; // bytes
  uint32_t numPackets = 1;
  double interval = 1.0; // seconds
  bool verbose = false;
  double distMultiplier = 10.0;

  CommandLine cmd;
  cmd.AddValue ("phyMode", "Wifi Phy mode", phyMode);
  cmd.AddValue ("rss", "received signal strength", rss);
  cmd.AddValue ("packetSize", "size of application packet sent", packetSize);
  cmd.AddValue ("numPackets", "number of packets generated per interval", numPackets);
  cmd.AddValue ("interval", "interval (seconds) between RL steps", interval);
  cmd.AddValue ("numNodes", "the number of nodes in this scenario", numNodes);
  cmd.AddValue ("distMultiplier", "the multiplier for distance between nodes, actual distance will be random", distMultiplier);
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
  // The below FixedRssLossModel will cause the rss to be fixed regardless
  // of the distance between the two stations, and the transmit power
  wifiChannel.AddPropagationLoss ("ns3::FixedRssLossModel","Rss",DoubleValue (rss));
  wifiPhy.SetChannel (wifiChannel.Create ());

  // Add a mac and disable rate control
  WifiMacHelper wifiMac;
  wifi.SetRemoteStationManager ("ns3::ConstantRateWifiManager",
                                "DataMode",StringValue (phyMode),
                                "ControlMode",StringValue (phyMode));
  // Set it to adhoc mode
  wifiMac.SetType ("ns3::AdhocWifiMac");
  NetDeviceContainer devices = wifi.Install (wifiPhy, wifiMac, c);

  // Note that with FixedRssLossModel, the positions below are not
  // used for received signal strength.
  MobilityHelper mobility;
  Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator> ();
  for(int index = 0; index < numNodes; ++index){
    std::random_device rd1;
    std::mt19937 gen1(rd1());
    std::uniform_real_distribution<> distribution1(0, 1);
    double random1 = distribution1(gen1) * distMultiplier;
    std::random_device rd2;
    std::mt19937 gen2(rd2());
    std::uniform_real_distribution<> distribution2(0, 1);
    double random2 = distribution2(gen2) * distMultiplier;
    std::random_device rd3;
    std::mt19937 gen3(rd3());
    std::uniform_real_distribution<> distribution3(0, 1);
    double random3 = distribution3(gen3) * distMultiplier;
    positionAlloc->Add (Vector (random1, random2, random3));

    std::cout.precision(std::numeric_limits<double>::max_digits10);
    std::cout << "Random number1: " << random1
              << " Random number2: " << random2
              << " Random number3: " << random3 << std::endl;
  }
  mobility.SetPositionAllocator (positionAlloc);
  mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
  mobility.Install (c);

  InternetStackHelper internet;
  internet.Install (c);

  Ipv4AddressHelper ipv4;
  NS_LOG_UNCOND ("Assign IP Addresses.");
  ipv4.SetBase ("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer i = ipv4.Assign (devices);

  TypeId tid = TypeId::LookupByName ("ns3::UdpSocketFactory");
  for(int index = 0; index < numNodes; ++index){
    Ptr<Socket> recvSink = Socket::CreateSocket (c.Get (index), tid);
    InetSocketAddress local = InetSocketAddress (Ipv4Address::GetAny (), 80);
    recvSink->Bind (local);
    recvSink->SetRecvCallback (MakeCallback (&ReceivePacket));
  }

  std::vector<Ptr<Socket>> sources;
  for(int index = 0; index < numNodes; ++index){
    Ptr<Socket> source = Socket::CreateSocket (c.Get (index), tid);
    InetSocketAddress remote = InetSocketAddress (Ipv4Address ("255.255.255.255"), 80);
    source->SetAllowBroadcast (true);
    source->Connect (remote);
    sources.push_back(source);
  }

  // Tracing
  wifiPhy.EnablePcap ("wifi-simple-adhoc", devices);

  // Output what we are doing
  NS_LOG_UNCOND ("Testing " << numPackets  << " packets sent with receiver rss " << rss );
  auto env = Create<Ns3RlEnv> (1234);
  NS_LOG_UNCOND ("CreateEnv: " << (env == 0));

  Simulator::ScheduleWithContext (sources[0]->GetNode ()->GetId (),
                                  Seconds (1.0), &GenerateTraffic,
                                  sources, packetSize, numPackets, interPacketInterval);

  for(int index = 0; index < numNodes; ++index){
    std::random_device rd1;
    std::mt19937 gen1(rd1());
    std::uniform_real_distribution<> distribution1(0, 1);
    double random1 = distribution1(gen1);
    Simulator::ScheduleWithContext (sources[index]->GetNode ()->GetId (),
                                    Seconds(1.0) + Seconds(random1), &GenerateTraffic2,
                                    sources, packetSize, numPackets, interPacketInterval);
  }

  Simulator::Run ();
  Simulator::Destroy ();

  NS_LOG_UNCOND("Simulation finished.");

  return 0;
}
