def run(sim, trainer):
    """
    Analyze the behavior of your trained policies using the simulation and trainer
    from your RL experiment.

    Args:
        sim:
            Simulation Manager object from the experiment.
        trainer:
            Trainer that computes actions using the trained policies.
    """
    # Run the simulation with actions chosen from the trained policies
    policy_agent_mapping = trainer.config['multiagent']['policy_mapping_fn']
    total_dict = {"Towards": 0, "Stay": 0, "Away": 0}
    for episode in range(100):
        print('Episode: {}'.format(episode))
        obs = sim.reset()
        done = {agent: False for agent in obs}
        analysis_dict = {"Towards": 0, "Stay": 0, "Away": 0}
        while True: # Run until the episode ends
            # Get actions from policies
            joint_action = {}
            for agent_id, agent_obs in obs.items():
                if done[agent_id]: continue # Don't get actions for done agents
                policy_id = policy_agent_mapping(agent_id)
                action = trainer.compute_action(agent_obs, policy_id=policy_id)
                joint_action[agent_id] = action


                if(agent_obs['direction'] == [False] and agent_obs['left'] == [True]) or \
                  (agent_obs['direction'] == [True] and agent_obs['right'] == [True]):
                    if(action == 0 and agent_obs['direction'] == [False]) or \
                      (action == 2 and agent_obs['direction'] == [True]):
                        analysis_dict['Towards'] += 1
                    elif(action == 2 and agent_obs['direction'] == [False]) or \
                        (action == 0 and agent_obs['direction'] == [True]):
                        analysis_dict['Away'] += 1
                    else:
                        analysis_dict['Stay'] += 1


            # Step the simulation
            obs, reward, done, info = sim.step(joint_action)
            if done['__all__']:
                break
        

        #print(" Towards: " + str(analysis_dict['Towards']))
        #print(" Stay: " + str(analysis_dict['Stay']))
        #print(" Away: " + str(analysis_dict['Away']))
        total_dict['Towards'] += analysis_dict['Towards']
        total_dict['Stay'] += analysis_dict['Stay']
        total_dict['Away'] += analysis_dict['Away']
    print('\n###')
    print(" Towards: " + str(total_dict['Towards']))
    print(" Stay: " + str(total_dict['Stay']))
    print(" Away: " + str(total_dict['Away']))
