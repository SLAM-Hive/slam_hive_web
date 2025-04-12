More details see in <https://slam-hive.net/wiki>.

Our Demo Website: <https://slam-hive.net>.

# Repo code API overview and SLAM_Hive folder tree introduction
Here: https://github.com/SLAM-Hive/slam_hive_web/blob/main/repo_overview.md

# Modules

Here we offer some easy access to some important modeules in SLAM-Hive:
 - Web inferface
   - [front end](https://github.com/SLAM-Hive/slam_hive_web/tree/main/SLAM_Hive/slamhive/templates)
   - [back end](https://github.com/SLAM-Hive/slam_hive_web/tree/main/SLAM_Hive/slamhive/blueprints)
   - [Functions that handle different tasks](https://github.com/SLAM-Hive/slam_hive_web/tree/main/SLAM_Hive/slamhive/task)
 - Scrpts
   - [Algorithm execution scripts](https://github.com/SLAM-Hive/orb-slam2-ros-mono/blob/master/slamhive/mapping.py)
   - [Dataset play scripts](https://github.com/SLAM-Hive/slam_hive_datasets/blob/main/MH_01_easy/rosbag_play.py)
   - [Data pre-processing scripts](https://github.com/SLAM-Hive/slam_hive_controller/blob/main/Module_B/project/dataset_preprocess.py)
   - [parse multiple configurations](https://github.com/SLAM-Hive/slam_hive_web/blob/main/SLAM_Hive/slamhive/blueprints/utils.py)
   - [parse custom analysis](https://github.com/SLAM-Hive/slam_hive_web/blob/main/SLAM_Hive/slamhive/task/custom_analysis_resolver.py)

# Contents
 - [How to add a new algorithm and dataset to SLAM-Hive and use them?](#4-add-new-algorithm-and-dataset); [Turorial](https://slam-hive.net/wiki/add_new_algorithm_and_dataset)

 - [How to install SLAM-Hive in workstation?](#1-deploy-in-workstation); [Turorial](https://slam-hive.net/wiki/workstation)
 - [How to install SLAM-Hive in cluster?](#2-deploy-in-cluster); [Turorial](https://slam-hive.net/wiki/cluster)
 - [How to install SLAM-Hive in Cloud?](#3-deploy-in-aliyun); [Turorial](https://slam-hive.net/wiki/cloud)


# 1. Deploy in Workstation
Workstation version. You can do some simple mappping running and evaluation.
## 1. Install Docker
Install Docker and docker-compose: <https://www.docker.com>

## 2. Create directory

The path structure of the entire project should be:
```
  - SLAM-Hive
    - slam_hive_algorithm
    - slam_hive_dataset
    - slam_hive_results
    - slam_hive_web
    - slam_hive_controller 
```

``` shell
$ cd /
$ mkdir SLAM-Hive
$ cd /SLAM-Hive
$ git clone https://github.com/SLAM-Hive/slam_hive_results.git
$ cd slam_hive_results & mkdir custom_analysis_group & mkdir multi_evaluation_results & mkdir batch_mappingtasks
# download the Journal paper results from http://robotics.shanghaitech.edu.cn/static/datasets/SLAM-Hive/SLAM-Hive_archive.zip, and then move sub-folder to related position.
$ git clone https://github.com/SLAM-Hive/slam_hive_controller.git # TO CHANGE
```

## 3. Build SLAM algorithm images
We provide some SLAM algorithms Dockerfile and running scripts, here is an example to build an image:
``` shell
$ cd /SLAM-Hive
$ mkdir slam_hive_algos
$ git clone https://github.com/SLAM-Hive/orb-slam2-ros-mono.git
$ cd orb-slam2-ros-mono
$ sudo chmod +x install.sh
$ ./install.sh
```
You can check whether the image is successfully built as follows:
```
$ docker images
```
you can see:
```
slam-hive-algorithm     orb-slam2-ros-mono      [IMAGE ID]      [CREATED]       [SIZE]
```
Go go to other directory in `/SLAM_Hive/slam_hive_algos/<> `and execute the above command to build remaining images. After that you will see the following images:
```
REPOSITORY             TAG                              IMAGE ID       CREATED         SIZE
slam-hive-evaluation   evo                              0254b6ded2cb   5 weeks ago     1.79GB
slam-hive-algorithm    vins-mono                        de2b13e0fc07   5 weeks ago     2.96GB
slam-hive-algorithm    vins-fusion-mono-imu             9078af9ba64a   7 days ago      3.1GB
slam-hive-algorithm    vins-fusion-stereo               9078af9ba64a   7 days ago      3.1GB
slam-hive-algorithm    vins-fusion-stereo-imu           9078af9ba64a   7 days ago      3.1GB
slam-hive-algorithm    orb-slam2-ros-mono               2f8241d1df9a   6 weeks ago     3.39GB
slam-hive-algorithm    orb-slam2-ros-rgbd               2f8241d1df9a   6 weeks ago     3.39GB
slam-hive-algorithm    orb-slam2-ros-stereo             2f8241d1df9a   6 weeks ago     3.39GB
slam-hive-algorithm    orb-slam3-ros-mono               28c13955a331   9 days ago      4.17GB
slam-hive-algorithm    orb-slam3-ros-mono-inertial      28c13955a331   9 days ago      4.17GB
slam-hive-algorithm    orb-slam3-ros-stereo             28c13955a331   9 days ago      4.17GB
slam-hive-algorithm    orb-slam3-ros-stereo-inertial    28c13955a331   9 days ago      4.17GB
slam-hive-algorithm    orb-slam3-ros-rgbd               28c13955a331   9 days ago      4.17GB
slam-hive-algorithm    lio-sam                          99b1395a3b41   9 days ago      3.15GB
```
If the image construction speed is very slow, it is recommended to find the Dockerfile in the corresponding folder and change the source list: `/etc/apt/sources.list`

**maybe upload the image.tar to a open repository.**

## 4. Download datasets
If there is not enough space on your computer, run the following command to download two datasets: `MH_01_easy.bag` (2.7G), `rgbd_dataset_freiburg2_desk.bag` (2.2 GB).
```
$ cd SLAM_Hive
$ git clone https://github.com/SLAM-Hive/slam_hive_datasets.git
$ python3 download.py
```
We also provide download script for other datasets: `SLAM_Hive/slam_hive_datasets/download_all.py`. Please modify the script to download the dataset according to your needs.

## 5. Build web

``` shell
$ cd /SLAM-Hive
$ git clone https://github.com/SLAM-Hive/slam_hive_web.git
```

Before build, you should change some configurations in some files.

```
$ cd /SLAM-Hive/slam_hive_web/SLAM_Hive/slamhive

# __init__.py
# set: app.config['CURRENT_VERSION'] = 'workstation' # version: workstation; view-only
# settings.py
# set HOST = 'mysql_ip' 
```
```
$ cd SLAM_Hive/slam_hive_web
$ sudo chmod -R 777 db/data
$ docker-compose up
```
Then,open your browser and visit: <http://127.0.0.1:5000>

We default to mounting the path in the image to a local path, which facilitates secondary development of the code. You can also first build an image of slam hive web locally, and then use the local image directly at startup.

And if you want to use dataset pre-process, you should also build the slam_hive_controller Docker Image:
``` shell
cd SLAM_Hive/slam_hive_controller/Module_B
docker build -t module_b:xxx . # xxx should be same as app.config['CLUSTER_CONTROLLER_IMAGE_NAME']

```
## 6. Create tasks
Ensure you have installed correspoding images and downloaded the dataset before creating tasks.
### 6.1 Create mapping tasks
Take orb-slam2-ros-mono and MH_01_easy as an example: (please make sure the above steps are successful)

Step1: Click the "Copy" button of the first config in the MappingTaskConfig list. 

Step2: Give this config a name and fill in the description.

Step3: Change some parameter values according to the actual situation, then click the "Save" button and return to the MappingTaskConfig list, click the "Create MappingTask" button, then a mapping task will be generated in the background, and when the task is completed, the status of this mapping task will change to " Finished” on MappingTask list.

You can also create a mapping task from scratch by clicking "Create Config". 

<!-- Click "Create Config" button on MappingTaskConfig page, select the algorithm and dataset you have installed and downloaded.  -->
### 6.2 Create evaluation tasks
When the mapping task is completed, the "Evaluate" button will appear in the MappingTask list. Click it to start the evaluation. After the evaluation is completed, the status of the Evaluation list will become "Finished". Click "Show" to see the evaluation results.

### 6.3 Extending Algorithms, Datasets, parameters
We provide some algorithms, datasets, and parameters supported by SLAM Hive on the web. For new additions, refer to the following tutorials.
### 6.3.1 Create your own algorithm
Step1: Write execution scripts

Algorithm execution scripts include three file. You can create them refer to scripts in `/SLAM_Hive/slam_hive_algos/<>/slamhive/`. The functions of each script are as described below.
| Script      | Description |
| ----------- | ----------- |
|`Docker image`| Build your algorithm Docker image, the image name must be: `slam-hive-algorithm:[tag]`. The name of your algorithm scripts folder must be the same as the image tag name.|
|`template.yaml`| This is the parameters template. Each mapping will generate a `mappingtask.yaml `parameter file based on template and the parameters input on the web. The template format is like `cx: $cx` . (Don't  ignore the space in between)    |
|`mapping.py`| The script first extracts the value of the configuration file generated by the web, generates `mappingtask.yaml` and remap command strings, then executes the corresponding algorithm running command, and finally saves the estimated trajectory to the specified directory.         |
|(optional) `launch file`| The launch file is optional, used to start the ROS node, set the configuration file path, and be responsible for the remap of the algorithm topic. |

##
Step2: Add algorithm to web

Click the "New" button on the Algorithm page, input the algorithm name, the name must be the same as the tag name of the image. Input your algorithm scripts url and description.
### 6.3.2 Create new dataset
Step1: Provide your dataset and a script

| File      | Description |
| ----------- | ----------- |
|`ROS bag`| Provide dataset in the form of ROS bag. |
|`groundtruth.txt`| The groundtruth format must be: `tx ty tz qx qy qz qw`|
|`rosbag_play.py`| This script generates the command of playing and remapping topics of the ROS bag. For details, please refer to `SLAM_Hive/slam_hive_datasets/<>/rosbag_play.py`|

##
Step2: Add dataset to web

Input dataset folder name, which must be the same as the name of dataset folder. Input dataset download url and description.
### 6.3.3 Create parameters
1.Format type declaration

(Don't omit space in between)
| Type      | Format |
| ----------- | ----------- |
|Dataset|This is the parameter type related to dataset, the format should follow: <br>`name1: value1`<br>`name2: value2`<br>...|
|Dataset matrix|If the dataset parameter is a matrix, choose this type, the format should follow:<br>`name: [value1, value2, ...]`|
|Dataset remap|If there is a need for ROS bag topic remap, please choose this type:<br>`name1: topic1`<br>`name2: topic2`<br>...|
|Algorithm| This is the parameter type related to algorithm, the format should follow:<br>`name1: value1`<br>`name2: value2`<br>...|
|Algorithm remap|If there is a need for algorithm remap,please choose this type:<br>`name1: topic1`<br>`name2: topic2`<br>...|
##
2.Add parameters to web

Fristly, add parameters on Parameter page, click "New", input parameter name, select the type according to the table above and fill in the description. Then, when you create MappingTaskConfig, choose the parameter you added in the previous step and input the value according to the format corresponding to the type.

## 7. Create Custom Analysis Task
When you have created some mapping and evaluation tasks, you can select some of them to make custom analysis task.



# 2. Deploy in Cluster
## 1. Install Docker
Install Docker and docker-compose: <https://www.docker.com>
## 2. Install and deploy the Kubernetes
If you have deployed Kubernetes in your cluster, can skip 2.1
We select kubernetes v1.21.3
### 2.1 configure both in master node and work nodes
``` shell
# 1. close firewall
$ sudo apt install -y ufw
$ sudo ufw disable

# 2. close selinux
$ sudo apt install -y selinux-utils
$ setenforce 0

# 3. disable swap partitions
$ swapoff -a
$ sudo vim /etc/fstab # then comment out the "swap" line.

# 4. login root
$ su root

# 5. configure iptables
$ cat > /etc/sysctl.d/k8s.conf <<EOF
$ net.bridge.bridge-nf-call-ip6tables = 1
$ net.bridge.bridge-nf-call-iptables = 1
$ EOF
$ sysctl --system

# 6. configure Kubernetes resource
$ curl -s https://mirrors.aliyun.com/kubernetes/apt/doc/apt-key.gpg | sudo apt-key add -
$ echo "deb https://mirrors.aliyun.com/kubernetes/apt/ kubernetes-xenial main" > /etc/apt/sources.list.d/kubernetes.list
$ apt-get update

# 7. install nfs
$ apt-get install nfs-common

# 8. install Kubernetes components
$ apt install -y kubelet=1.21.3-00 kubeadm=1.21.3-00 kubectl=1.21.3-00

# 9. start kubelet and set kubelet to boot
$ systemctl enable kubelet
$ systemctl start kubelet
```
### 2.2 configure in master node (build Kubernetes cluster)
create a shell script and write follow content into it, and then execute it.
``` shell
#!/bin/bash
images=(
 kube-apiserver:v1.21.3
 kube-controller-manager:v1.21.3
 kube-scheduler:v1.21.3
 kube-proxy:v1.21.3
 pause:3.2
 etcd:3.4.13-0
)
for imageName in ${images[@]} ; do
  docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/${imageName}
  docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/${imageName} k8s.gcr.io/${imageName}
  docker rmi registry.cn-hangzhou.aliyuncs.com/google_containers/${imageName}
done
docker pull coredns/coredns:1.8.0
docker tag coredns/coredns:1.8.0 registry.aliyuncs.com/google_containers/coredns:v1.8.0
docker rmi coredns/coredns:1.8.0
```
``` shell
# 1. Initialize master
$ kubeadm init --image-repository=registry.aliyuncs.com/google_containers  --pod-network-cidr=10.244.0.0/16	 --service-cidr=10.96.0.0/12 # remember the output
$ kubeadm token create --ttl 0 --print-join-command # If forget last command

# 2. configure kubectl
$ mkdir -p $HOME/.kube
$ sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
$ sudo chown $(id -u):$(id -g) $HOME/.kube/config

# 3. network plug-in flannel
$ sudo kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
# If download slowly, you can create a kube-flannel.yml locally and copy the content to the yml file, and then execute: `sudo kubectl apply -f kube-flannel.yml`

# 4. other steps
# For the file: `/etc/kubernetes/manifests/kube-controller-manager.yaml` and `/etc/kubernetes/manifests/kube-scheduler.yaml`, comment out the line that contains "– port=0"
# Then:
$ syatemctl restart kubelet.service
```
### 2.3 configure in work node (join work nodes into the master's cluster)
input the command getting at 2.2.1.

If you want to use `kubectl` in work nodes: copy the /etc/kubernetes/admin.conf from master node to the same directory of the work nodes.

### 2.4 cAdvisor on work node
You should also create a cAdvisor docker container for each work node for usage monitor.


## 3. Create Root Directory
same as `Workstation` version.

## 4. Build SLAM algorithm images
same as `Workstation` version. Besides, you should also zip the algorithm docker image to raleted folder using command: `docker save slam-hive-algorithm:xxx1 > /SLAM-Hive/slam_hive_algos/xxx1`

## 5. Download datasets
same as `Workstation` version.

## 6. Build Web

### 6.1 slam_hive_controller configure
You need to fill the basic information in the configuration file.
``` shell
$ cd /SLAM-Hive/slam_hive_controller/Module_B/project/init_config.py
# fill information based on your cluster.
```
And then build the cluster controller docker image:
```
cd /SLAM-Hive/slam_hive_controller/Module_B
docker build -t module_b:[xxx]
```

### 6.2 pull the slam_hive_web
``` shell
$ cd /SLAM-Hive
$ git clone https://github.com/SLAM-Hive/slam_hive_web.git
```
And you should input the module_b name in file: /SLAM-Hive/slam_hive_web/SLAM_Hive/slamhive/__init__.py
``` shell
# app.config['CLUSTER_CONTROLLER_IMAGE_NAME'] = "[xxx]"
```

### 6.3 cadvisor configure
You need to run a monitor tool: cadvisor in every work nodes.
``` shell
$ cd /SLAM-Hive/slam_hive_web/
$ vim cadvisor_pod.yaml
# change the spec.nodeName to your work node's name.
$ kubectl apply -f cadvisor_pod.yaml
```

### 6.4 slam_hive_web configure
``` shell
$ cd /SLAM-Hive/slam_hive_web/
$ vim slam_hive_pod.yaml
# change the spec.nodeName to your master node's name.

$ cd /SLAM-Hive/slam_hive_web/SLAM_Hive/slamhive
$ vim setting.py
# set: HOST = 'localhost'

$ vim __init__.py
# set: app.config['CURRENT_VERSION'] = 'cluster'
```

### 6.5 build slam-hive-web:xxx docker image
``` shell
$ cd /SLAM-Hive/slam_hive_web
$ docker build -t slam-hive-web:tag_name .
# You can specify the tag_name
$ vim slam_hive_pod.yaml
# set spec.containers[slam-hive-web-kube].image = slam-hive-web:tag_name
```

### 6.5 start slam_hive_web
``` shell
$ cd SLAM_Hive/slam_hive_web
$ sudo chmod -R 777 db/data
$ sudo kubectl apply -f slam_hive_pod.yaml
```

### 6.6 View Website
``` shell
$ sudo kubectl get all -o wide # get the IP of the web
```
Then,open your browser and visit: <http://IP:5000>



# 3. Deploy in Aliyun

## 1. Configure the Aliyun
Firstly, you should have a Aliyun account and get your ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET.

## 2. Configure master node
You should have a Aliyun instance as the master node.
To configure the master node, you can see `2. Deploy in Cluster`

## 3. Build web
We assume that you have finished configuring the environment and creating the directory.

In Master node:
``` shell
$ cd /SLAM-Hive/slam_hive_web
$ vim slam_hive_pod.yaml
# change the spec.nodeName to your master node's name.

$ cd /SLAM-Hive/slam_hive_web/SLAM_Hive/slamhive
$ vim setting.py
# set: HOST = 'localhost'

$ vim __init__.py
# set: app.config['CURRENT_VERSION'] = 'aliyun'
# set: app.config['MASTER_REGION'] = `Region where your master node are at`
# set: app.config['MASTER_IP'] = `Master node pubic network IP`
# set: app.config['WORK_NODE_IMAGE_ID'] = "work node initialize image"
# TODO 需要设置一下共享镜像
# set: app.config['MASTER_INNER_IP'] = "Master node inner IP"

$ kubeadm token create --ttl 0 --print-join-command
# set: app.config["KUBERNETES_JOIN_COMMAND"] = `join command`
```
``` shell
$ cd SLAM_Hive/slam_hive_web
$ sudo chmod -R 777 db/data
$ sudo kubectl apply -f slam_hive_pod.yaml
```
Then enter the slam_hive_web container to set the ALIBABA environment variable.
``` shell
$ cat ALIBABA_CLOUD_ACCESS_KEY_ID > ~/.bashrc
$ cat ALIBABA_CLOUD_ACCESS_KEY_SECRET > ~/.bashrc
$ source ~/.bashrc
```

Then,open your browser and visit: <http://IP:5000>

## 4. how to create task
Same as workstation version, except you should input the aliyun server configuration.


# 4. Add new algorithm and dataset
In wiki tutorial, we give a example of how to add a algorithm and dataset to SLAM-Hive and how to use them: https://slam-hive.net/wiki/add_new_algorithm_and_dataset

# Licence
The source code is released under [GPLv3](http://www.gnu.org/licenses/) license.

We are still working on improving the code reliability. For any technical issues, you can make an issue.

