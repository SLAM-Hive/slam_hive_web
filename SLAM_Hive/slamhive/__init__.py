# This is part of SLAM Hive
# Copyright (C) 2024 Zinzhe Liu, Yuanyuan Yang, Bowen Xu, Sören Schwertfeger, ShanghaiTech University. 

# SLAM Hive is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# SLAM Hive is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with SLAM Hive.  If not, see <https://www.gnu.org/licenses/>.

from flask import Flask
from flask_bootstrap import Bootstrap4
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
import os

app = Flask('slamhive')
# app = Flask(__name__)
app.config.from_pyfile('settings.py')
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

db = SQLAlchemy(app)
bootstrap = Bootstrap4(app)
moment = Moment(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)

app.config['MAPPING_RESULTS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_results/mapping_results')
app.config['EVALUATION_RESULTS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_results/evaluation_results')
app.config['PARAMETERS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_parameters')
app.config['CONFIGURATIONS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_configurations')
app.config['DATASETS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_datasets')
app.config['ALGORITHMS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_algos')

app.config['MULTIEVALUATION_RESULTS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_results/multi_evaluation_results')
# app.config['EVALUATION_COMPARE_RESULTS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_results/evaluation_compare_results')


app.config['BATCHMAPPINGTASK_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_results/batch_mappingtask')
################
##   Cluster  ##
################
app.config['CLUSTER_WORK_NODE_NUMBER'] = 1

app.config['CLUSTER_CONTROLLER_IMAGE_NAME'] = "ros_true_opencv"

## kubernetes related config

# app.config['MASTER_NODE_HOST_IP'] = "10.19.125.68"
# app.config['MASTER_USERNAME'] = 'root'
# ###########
# app.config['MASTER_PASSWORD'] = ' '

# app.config["WORK_NODES_HOST_IP"] = ['10.19.126.118', '10.19.126.201']
# app.config['WORK_NODES_USERNAME'] = ['root', 'root']
# app.config['WORK_NODES_PASSWORD'] = [' ', ' ']

# 

###############
##   Aliyun  ##
############### 
app.config['MASTER_REGION'] = "cn-zhangjiakou"
app.config['MASTER_IP'] = "47.92.74.135"
app.config['work_node_image_id'] = "m-8vbc1fwipi8g8gd5arxh"
app.config['MASTER_INNER_IP'] = "172.17.248.9"
app.config["kubernetes_join_command"] = "kubeadm join 172.17.248.9:6443 --token f5v0y8.if9aceva1386l4q5 --discovery-token-ca-cert-hash sha256:a34480b13648a7f650fc574ec498ed7c228e2dce6b6bd3322874edaea9f38e7f"
app.config['MAX_NODE_NUMBER'] = 64
app.config['EXPECT_EACH_NODE_TASK_NUMBER'] = 2 # 假设m个task，希望每个work node能平均地执行8个task，那么则需要 m/8个node
app.config['MAX_RESOURCE_SIZE_EACH_NODE'] = 8 # GB


#########################
##   Version Control   ##
######################### 
app.config['limitation_url'] = ['/mappingtask/create','/mappingtask/create/single',  '/mappingtask/create/batch', '/mappingtask/create/batch_aliyun']
app.config['workstation'] = ['/mappingtask/create']
app.config['cluster'] = ['/mappingtask/create/single', '/mappingtask/create/batch']
app.config['aliyun'] = ['/mappingtask/create/batch_aliyun']
# view_only
# need to change the right version name when start the project
app.config['CURRENT_VERSION'] = 'view_only'



from slamhive.blueprints import views, params, algo, mappingtaskconf, mappingtask, dataset, evaluate, customanalysis
from slamhive import commands
