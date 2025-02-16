---
title: 'Abmarl: Connecting Agent-Based Simulations with Multi-Agent Reinforcement Learning'
tags:
  - Python
  - agent-based simulation
  - multi-agent reinforcement learning
  - machine learning
  - agent-based modeling
authors:
  - name: Edward Rusu
    orcid: 0000-0003-1033-439X
    affiliation: 1
  - name: Ruben Glatt
    affiliation: 1
affiliations:
 - name: Lawrence Livermore National Laboratory
   index: 1
date: 10 June 2021
bibliography: paper.bib
---

# Summary

Abmarl is a package for developing Agent-Based Simulations and training them
with Multi-Agent Reinforcement Learning (MARL). We provide an intuitive command line
interface for engaging with the full workflow of MARL experimentation: training,
visualizing, and analyzing agent behavior. We define an Agent-Based Simulation
Interface and Simulation Manager, which control which agents interact with the
simulation at each step. We support integration with popular reinforcement learning
simulation interfaces, including gym.Env [@gym] and MultiAgentEnv [@rllib].
We leverage RLlib's framework for reinforcement learning and extend it to more easily
support custom simulations, algorithms, and policies. We enable researchers to
rapidly prototype MARL experiments and simulation design and lower the barrier
for pre-existing projects to prototype Reinforcement Learning (RL) as a potential solution.

# Statement of need

In 2016, @gym published OpenAi Gym, an interface for single-agent simulations. This interface
quickly became one of the most popular connections between simulation and training
in RL experimentation. It has been used by many simulation benchmarks
for single-agent reinforcement learning, including the Arcade Learning Environment [@arcade].
Since then the field of Deep Reinforcement Learning (DRL) has exploded in both
algorithm development and simulation design, and over the past few years researchers
have been extending their interest to Multi-Agent Reinforcement Learning (MARL).
Surprisingly complex and hierarchical behavior emerges in the
interaction among multiple agents, especially when those agents differ in their
objectives [@hide-n-seek]. 

To train agents with Multi-Agent Reinforcement Learning, one needs two components: simulation
and algorithm (also commonly referred to as environment and agent). Much effort
has been given to the development of MARL algorithms, which has brought us exciting
breakthroughs and enhancements in the field of artificial intelligence. Our aim,
however, focuses on the simulation component of MARL.

Several projects have attempted to define a standard set
of benchmark scenarios for Multi-Agent problems. In their groundbreaking work,
@maddpg introduced MADDPG, a "centralized training, decentralized execution" multi-agent
algorithm. Along with their algorithmic development, they created Multi-Particle
Environment (MPE) (now managed as a part of PettingZoo) as a benchmark suite that
includes continuous movement and communication features. @magent produced scalable
grid-based simulations and demonstrated emergent behavior in multi-team games
on the order of millions of agents. @smac and @marlo brought RL research closer to home,
giving researchers access to dozens of multi-agent scenarios in the popular games
StarCraft and Minecraft, respectively. @neuralmmo also targeted video games by
supporting MARL in MMORPG-styled simulations with
persistent, open-ended tasks among multiple agents. @smarts brought us realistic
traffic simulation scenarios to lead society towards autonomous driving.

Each of these efforts and more are great milestones in RL simulation. Naturally,
each of them couples the simulation interface with the 
underlying simulation. @pettingzoo have attempted to unify some of
the more popular simulations under a single interface, giving researchers easier
access to these simulations. While this is a step towards
a standard multi-agent interface, most simulation efforts are tied to a specific
set of already-built simulations with limited flexibility.

Abmarl defines an interface for multi-agent simulations that is versatile,
extendible, and intuitive. Rather than adapting gym's interface for a targeted
multi-agent simulation, we have built an interface from scratch that allows for
the greatest flexibility while connecting to one of the most advanced, general-purpose, and
open-source libraries: RLlib [@rllib]. Our interface manages the loop between agents
and the trainer, enabling the researcher to focus on simulation design and algorithmic
development without worrying about the data exchange.

We developed and tuned Abmarl's intuitive command-line interface through practical experience
while working on [@hybrid]. Our interface gives researchers a running-start
in MARL experimentation. We handle all the workflow elements needed to setup, run,
and reproduce MARL experiments, providing direct access to train, visualize,
and analyze experiments. We streamline the savvy-practitioner's experience and lower
the barrier for new researchers to join the field. The analysis module sets Abmarl
apart from others as it provides a simple command line interface to add
analytics to trained policies, allowing researchers to generate additional statistics
and visualizations of agent and simulation metrics after the policy has been trained.


# Acknowledgements

This work was performed under the auspices of the U.S. Department of Energy by
Lawrence Livermore National Laboratory under contract DE-AC52-07NA27344. Lawrence 
Livermore National Security, LLC through the support of LDRD 20-SI-005, 20-COMP-015,
and 21-COMP-017. LLNL-CODE-815883.

# References
