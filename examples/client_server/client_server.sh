#!/bin/bash
#SBATCH --job-name=test-ray
#SBATCH --nodes=2
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --partition=pvis
#SBATCH --exclusive
#SBATCH --no-kill
#SBATCH --output="slurm-%j.out"
#SBATCH --ip-isolate yes

source /usr/WS1/rusu1/abmarl_scale_test/v_ray_test_tf/bin/activate

# Getting the node names
nodes=$(scontrol show hostnames "$SLURM_JOB_NODELIST")
nodes_array=($nodes)

head_node=${nodes_array[0]}
head_node_ip=$(srun --nodes=1 --ntasks=1 -w "$head_node" hostname --ip-address)

# if we detect a space character in the head node IP, we'll
# convert it to an ipv4 address. This step is optional.
if [[ "$head_node_ip" == *" "* ]]; then
IFS=' ' read -ra ADDR <<<"$head_node_ip"
if [[ ${#ADDR[0]} -gt 16 ]]; then
  head_node_ip=${ADDR[1]}
else
  head_node_ip=${ADDR[0]}
fi
echo "IPV6 address detected. We split the IPV4 address as $head_node_ip"
fi

port=6379
ip_head=$head_node_ip:$port
export ip_head
echo "IP Head: $ip_head"

echo "Starting HEAD at $head_node"
srun --nodes=1 --ntasks=1 -w "$head_node" --output="slurm-%j-HEAD.out" \
  python3 -u ./cartpole_server.py --framework=tf --ip-head $ip_head &

# optional, though may be useful in certain versions of Ray < 1.0.
sleep 30

# number of nodes other than the head node
echo "SLURM JOB NUM NODES " $SLURM_JOB_NUM_NODES
worker_num=$((SLURM_JOB_NUM_NODES - 1))

for ((i = 1; i <= worker_num; i++)); do
    node_i=${nodes_array[$i]}
    echo "Starting WORKER $i at $node_i"
    srun --nodes=1 --ntasks=1 -w "$node_i" --output="slurm-%j-$node_i.out" \
      python3 -u ./cartpole_client.py --ip-head $ip_head &
    sleep 5
done

wait

# __doc_script_start__
# ray/doc/source/cluster/examples/simple-trainer.py
# python -u simple-trainer.py "$SLURM_CPUS_PER_TASK"
# srun python3 -u /usr/workspace/rusu1/abmarl_scale_test/ray_scale_test/simple-trainer.py "$SLURM_CPUS_PER_TASK"