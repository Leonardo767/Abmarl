"""Example of running a policy server. Copy this file for your use case.
To try this out, in two separate shells run:
    $ python cartpole_server.py
    $ python cartpole_client.py --inference-mode=local|remote
"""

import argparse
import os

import ray
from ray.rllib.agents.dqn import DQNTrainer
from ray.rllib.agents.ppo import PPOTrainer
from ray.rllib.env.policy_server_input import PolicyServerInput
from ray.rllib.examples.custom_metrics_and_callbacks import MyCallbacks
from ray.tune.logger import pretty_print

parser = argparse.ArgumentParser()
parser.add_argument(
    "--run",
    type=str,
    default="DQN"
)
parser.add_argument(
    "--framework",
    choices=["tf", "torch"],
    default="tf",
    help="The DL framework specifier."
)
parser.add_argument(
    '--ip-head',
    type=str,
    default='localhost:9900',
    help='The ip address and port of the remote server.'
)

if __name__ == "__main__":
    print("From the server")
    args = parser.parse_args()

    # TODO: error: Address already in use
    server_address = args.ip_head.split(':')[0]
    # Since this python file is already being run on the head node, maybe we can
    # use localhost instead of the actual ip address.
    # server_address = 'localhost'

    # server_port = int(args.ip_head.split(':')[1])
    server_port = 9900
    # ray.init(address=args.ip_head)
    # ray.util.connect(args.ip_head)
    ray.init()

    print(f'server: {server_address}:{server_port}')

    env = "CartPole-v0"
    connector_config = {
        # Use the connector server to generate experiences.
        "input": (
            lambda ioctx: PolicyServerInput(ioctx, server_address, server_port)
        ),
        # Use a single worker process to run the server.
        # TODO: How to configure this to use multiple workers? Why?
        "num_workers": 0,
        # Disable OPE, since the rollouts are coming from online clients.
        "input_evaluation": [],
        "callbacks": MyCallbacks,
    }

    if args.run == "DQN":
        # Example of using DQN (supports off-policy actions).
        trainer = DQNTrainer(
            env=env,
            config=dict(
                connector_config, **{
                    "learning_starts": 100,
                    "timesteps_per_iteration": 200,
                    "framework": args.framework,
                }))
    elif args.run == "PPO":
        # Example of using PPO (does NOT support off-policy actions).
        trainer = PPOTrainer(
            env=env,
            config=dict(
                connector_config, **{
                    "rollout_fragment_length": 1000,
                    "train_batch_size": 4000,
                    "framework": args.framework,
                }))
    else:
        raise ValueError("--run must be DQN or PPO")
    
    print('All done')

    # Serving and training loop.
    while True:
        print(pretty_print(trainer.train()))