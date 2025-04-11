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
