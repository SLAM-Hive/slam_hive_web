Here is the the whole SLAM_Hive folder introduction by its tree structure:

SLAM_Hive mainly has follow folders:

slam_hive_algos
 - store the build context to build algorithm images.

slam_hive_datasets
 - store the datasets

slam_hive_results
 - store the results of mapping run, evaluation and custom analysis task results.

slam_hive_controller
 - This is a middle controller module of SLAM Hive, using mainly in cluster and aliyun modes. This module is also used for dataset pre-processing.

slam_hive_web
 - The website code.

# slam_hive_web

SLAM_Hive
 - The code folder.

db/data
 - Store the database data.

Dockerfile
 - Used for docker image building

cadvisor_pod.yaml
 - Used for creating a Kubernetes Pod (similar to a docker container); When you using cluster mode, you should deploy Cadvisor at each work node by hand.

docker-compose.yml
  - Used for creating 3 docker containers (Web; MySQL; CAdvisor)

slam_hive_pod.yaml
 - Used for creating a Kubernetes Pod (similar to a docker container); This is used to deploy the web pod in master node.

## SLAM_Hive/slamhive
blueprints
 - The back end of slam hive website, handling the request from web page, and is main module to access the DB.
 - For each task module (algorithm, dataset, config...), there have a .py script to handle related requests form related front end module.

static
 - store the front end static resources

task
 - handle some detailed tasks; called by blueprints; creating and manage the task containers

templates
 - front end; each task module (algorithm, dataset, config...), there have a sub-folder to store html pages.

### blueprints

algo.py
 - show algorithms list
 - create new algorithms
 - delete algorithms

dataset.py
 - show dataset list
 - create a new dataset
 - delete dataset

params.py
 - show all the parameter templates
 - create new parameter template
 - delete parameter template

mappingtaskconf.py
 - show all configs
 - show all combination-configs
 - search configs by rules
 - show certain configs
 - create a new config
 - create many configs by combination creating
 - delete config

mappingtasks.py
 - show all created tasks
 - search tasks
 - create a task by select one/many(list) configs
 - delete task

evaluation.py
 - show all eval tasks
 - search tasks
 - create eval task
 - delete tasks

customanalysis.py
 - create custom analysis tasks
 - show custom analysis tasks
### task

mapping_cadvisor.py
 - mainly used for creating, monitor and kill the mapping run task in every modes

 evo.py
  - used to creating, monitor and kill the evaluation task

custom_analysis_resolver.py
 - parse and check the yaml file from front end, and create related custom analysis tasks based on yaml file.

aliyun_project
 - called by mapping_cadvisor; used to buy nodes in aliyun.


# slam_hive_controller

This is a middle controller module of SLAM Hive, using mainly in cluster and aliyun modes. This module is also used for dataset pre-processing.


Dockerfile
 - Used for docker image building
module_b_pod.yaml
 - - Used for creating a Kubernetes Pod (similar to a docker container); This container is a middle module between slam hive web and Kubernetes
project
 - core codes of controller

## project
controller_xxx_run.py
 - used to call controller_xxx.py

controller_xxx.py
 - controller_workstation
	 - used for downsample dataset
 - controller.py
	 - used in cluster mode
		 - transfer algorithm image, dataset, configs from master to work node
		 - pre-process dataset
		 - create task container in this node
		 - transfer results to master node
 - controller_aliyun.py
	 - used in aliyun mode
		 - similar to cluster mode

dataset_preprocess.py
 - used for dataset process -- data down-sample
	 - two main parts: dataset framerate and image resolution
		 - read the original rosbag
		 - handle each message accord

# slam_hive_algorithm

For example:

orb-slam2-ros-mono
 - build context of orb-slam2-ros-mono algorithm.

And for other algorithms, there also have related folders.

## orb-slam2-ros-mono (as example)

slamhive
 - store the running script to start a mapping task

Dockerfile
 - used to build algorithm image.

.install.sh
 - used to call for Dockerfile to build algorithm image. This is the file for user to build Docker image -- run ./install.sh

ORB-SLAM2
 - from project repo. We change some output parts to generate needed results.

### slamhive

mapping.py
 - parse the configs from the web
 - start the algorithm
 - start the dataset playback
 - write "finished" flag.

template.yaml
 - used for pars configuration parameters.


# slam_hive_datasets

For example:

MH_01_easy (a sequence of EuRoC dataset)
 - store the rosbag file, groundtruth and rosbag play scripts.

## MH_01_easy as a example 

MH_01_easy.bag (need to be same name as folder name)

groundtruth.txt
 - the groundtruth of this sequence (in TUM format)

rosbag_play.py
 - used to play the rosbag file and remap some topic (this script is called by algorithm mapping.py script)


# slam_hive_results

mapping_results
 - store the mapping run tasks. For certain mapping task with ID xxx, there will be a ./xxx sub-folder to store all the results of this tasks(including estimated traj, CPU & Memory monitor data)

evaluation_results
 - store the evaluation task results. For certain evaluation task with ID xxx, there will be a ./xxx sub-folder to store all the results of this tasks (include statistic results, figures and raw data of ATE and RPE)

custom_analysis_group
 - store the custom analysis task results. We use the timestamp as the ID of each tasks, and in each ./ID, there is the analysis results.


