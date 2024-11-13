import os
import sys
from slamhive import app


MAPPING_RESULTS_PATH = os.path.join(os.path.abspath('../..'), 'slam_hive_results/mapping_results')
EVALUATION_RESULTS_PATH = os.path.join(os.path.abspath('../..'), 'slam_hive_results/evaluation_results')
PARAMETERS_PATH = os.path.join(os.path.abspath('../..'), 'slam_hive_parameters')
CONFIGURATIONS_PATH = os.path.join(os.path.abspath('../..'), 'slam_hive_configurations')
DATASETS_PATH = os.path.join(os.path.abspath('../..'), 'slam_hive_datasets')
ALGORITHMS_PATH = os.path.join(os.path.abspath('../..'), 'slam_hive_algos')

MULTIEVALUATION_RESULTS_PATH = os.path.join(os.path.abspath('../..'), 'slam_hive_results/multi_evaluation_results')
# EVALUATION_COMPARE_RESULTS_PATH = os.path.join(os.path.abspath('../..'), 'slam_hive_results/evaluation_compare_results')


BATCHMAPPINGTASK_PATH = os.path.join(os.path.abspath('../..'), 'slam_hive_results/batch_mappingtask')
################
##   Cluster  ##
################
CLUSTER_WORK_NODE_NUMBER = 1

CLUSTER_CONTROLLER_IMAGE_NAME = "ros_true_opencv"

## kubernetes related config

# MASTER_NODE_HOST_IP = "10.19.125.68"
# MASTER_USERNAME = 'root'
# ###########
# MASTER_PASSWORD = ' '

# app.config["WORK_NODES_HOST_IP"] = ['10.19.126.118', '10.19.126.201']
# WORK_NODES_USERNAME = ['root', 'root']
# WORK_NODES_PASSWORD = [' ', ' ']

# 

###############
##   Aliyun  ##
############### 
MASTER_REGION = "cn-zhangjiakou"
MASTER_IP = "47.92.74.135"
WORK_NODE_IMAGE_ID = "m-8vbc1fwipi8g8gd5arxh" ###
MASTER_INNER_IP = "172.17.248.9"
KUBERNETES_JOIN_COMMAND = "kubeadm join 172.17.248.9:6443 --token f5v0y8.if9aceva1386l4q5 --discovery-token-ca-cert-hash sha256:a34480b13648a7f650fc574ec498ed7c228e2dce6b6bd3322874edaea9f38e7f" ###
MAX_NODE_NUMBER = 64
EXPECT_EACH_NODE_TASK_NUMBER = 2 # 假设m个task，希望每个work node能平均地执行8个task，那么则需要 m/8个node
MAX_RESOURCE_SIZE_EACH_NODE = 8 # GB


#########################
##   Version Control   ##
######################### 
# limitation_url = ['/mappingtask/create','/mappingtask/create/single',  '/mappingtask/create/batch', '/mappingtask/create/batch_aliyun']
# workstation = ['/mappingtask/create']
# cluster = ['/mappingtask/create/single', '/mappingtask/create/batch']
# aliyun = ['/mappingtask/create/batch_aliyun']
# view_only
# need to change the right version name when start the project
CURRENT_VERSION = 'workstation'

# NO_NEW
NO_USE_ANALYSIS = "no"
# yes: not use
# no: use