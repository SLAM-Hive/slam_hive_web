# This is part of SLAM Hive
# Copyright (C) 2024 Xinzhe Liu, Yuanyuan Yang, Bowen Xu, Sören Schwertfeger, ShanghaiTech University. 

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

import docker, time, os, yaml, requests, json, datetime, csv
from docker.errors import ContainerError, ImageNotFound, APIError
import numpy as np
import matplotlib.pyplot as plt
from dateutil import parser
from slamhive import app
from slamhive.task.utils import *
from slamhive.task.rosbag_conversion import prepare_dataset_for_mapping
from pathlib import Path

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from slamhive.task.aliyun_project.create_esc.alibabacloud_sample.controller import Aliyun_controller



# STATEFULSET_NAME = "test1"
# POD_NUMBER = 10
# SERVEIVE_NAME = "test1service"

# kubernetes related
def create_service(core_v1_api, service_name):
    body = client.V1Service(
        api_version = "v1",
        kind = "Service",
        metadata = client.V1ObjectMeta(
            name = service_name,
        ),
        spec = client.V1ServiceSpec(
            ports = [client.V1ServicePort(
                port = 80,
                target_port = 80
            )],
            cluster_ip = "None",
            selector = {"app": "slamhive"}
        )
    )

    core_v1_api.create_namespaced_service(namespace = "default", body = body)


def create_stateful_set_object(pod_number, service_name, statefulset_name, task_id, command):
    # container

    ### in real environment, this should be the k8s IP (need to check)
    # app.config['MASTER_NODE_HOST_IP'] = "10.19.125.68"
    # app.config['MASTER_USERNAME'] = 'root'
    # app.config['MASTER_PASSWORD'] = ' '

    container = client.V1Container(
        #demo nginx
        # module b
        name = "moduleb",
        # image = "module_b:vnodex",
        # image = "module_b:handware_test1",
        image = "module_b:" + app.config['CLUSTER_CONTROLLER_IMAGE_NAME'],
        image_pull_policy = "IfNotPresent",
        # 将docker的开机自启动命令添加在这里（不需要重新构建镜像）
        command = command,
        # command = ['sh','-c','echo "hello" && sleep 36000'],
        # ports=[client.V1ContainerPort(container_port = 0, host_port= 0)]
        ## volume_mounts = [client.V1VolumeMount(mount_path="/test", name="bpy")],
        ports = [client.V1ContainerPort(container_port=80)],
        # env 通过环境变量的方式传入自己pod的信息
        env = [
            client.V1EnvVar(
                name = "MY_POD_NAME",
                value_from = client.V1EnvVarSource(
                    field_ref = client.V1ObjectFieldSelector(
                        field_path = "metadata.name"
                    )
                )
            ),
            client.V1EnvVar(
                name = "MY_POD_NAMESPACE",
                value_from = client.V1EnvVarSource(
                    field_ref = client.V1ObjectFieldSelector(
                        field_path = "metadata.namespace"
                    )
                )
            ), 
            client.V1EnvVar(
                name = "MY_POD_HOST_IP",
                value_from = client.V1EnvVarSource(
                    field_ref = client.V1ObjectFieldSelector(
                        field_path = "status.hostIP"
                    )
                )
            ), 
        ],
        
        volume_mounts = [
            # use docker api
            client.V1VolumeMount(
                name = "dockerpath",
                mount_path = "/var/run/docker.sock"
            ),
            # use k8s api
            client.V1VolumeMount(
                name = "k8spath",
                mount_path = "/root/.kube/config"
            ),
            # slam-hive related
            client.V1VolumeMount(
                name = "detailedresultpath",
                mount_path = "/slamhive/detailedResult"
            ),
            client.V1VolumeMount(
                name = "datasetpath",
                mount_path = "/slamhive/dataset"
            ),
            client.V1VolumeMount(
                name = "algopath",
                mount_path = "/slamhive/algo"
            ),
            # node1 or nodex
            client.V1VolumeMount(
                name = "codepath",
                mount_path = "/home/code/project"
            ),
        ]
    )
    # template
    template = client.V1PodTemplateSpec(
        spec = client.V1PodSpec(
                # test in node1
                node_name = "xinzhe",
                containers = [container],
                # in nodex
                volumes = [
                    client.V1Volume(
                        name = "dockerpath",
                        host_path = client.V1HostPathVolumeSource(path = "/var/run/docker.sock")
                    ),
                    # nodex
                    client.V1Volume(
                        name = "k8spath",
                        host_path = client.V1HostPathVolumeSource(path = "/etc/kubernetes/admin.conf")
                    ),     
                    # node1               
                    # client.V1Volume(
                    #     name = "k8spath",
                    #     host_path = client.V1HostPathVolumeSource(path = "/root/.kube/config")
                    # ),
                                # slam-hive related
                    client.V1Volume(
                        name = "detailedresultpath",
                        ## host_path = client.V1HostPathVolumeSource(path = "/home/Combination_result/slam_hive_results/mapping_results/" + task_id)
                        host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive/slam_hive_results/mapping_results/" + task_id)
                    ),     
                    client.V1Volume(
                        name = "datasetpath",
                        # host_path = client.V1HostPathVolumeSource(path = "/home/SLAM_Hive_root/SLAM_Hive/slam_hive_datasets")
                        host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive/slam_hive_datasets")
                    ),
                    client.V1Volume(
                        name = "algopath",
                        ## host_path = client.V1HostPathVolumeSource(path = "/home/SLAM_Hive_root/SLAM_Hive/slam_hive_algos")
                        host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive/slam_hive_algos")
                    ),
                    # test in nodex
                    client.V1Volume(
                        name = "codepath",
                        ## host_path = client.V1HostPathVolumeSource(path = "/home/lxz/slam_hive_controller/Module_B/project")
                        host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive/slam_hive_controller/Module_B/project")
                    ),
                    
                ],
                # in node1
                # volumes = [
                #     client.V1Volume(
                #         name = "dockerpath",
                #         host_path = client.V1HostPathVolumeSource(path = "/var/run/docker.sock")
                #     ),
                #     client.V1Volume(
                #         name = "k8spath",
                #         host_path = client.V1HostPathVolumeSource(path = "/root/.kube/config")
                #     ),
                #                 # slam-hive related
                #     client.V1Volume(
                #         name = "detailedresultpath",
                #         host_path = client.V1HostPathVolumeSource(path = "/clusternfs/home/Combination_result/slam_hive_results/mapping_results/999")
                #     ),
                #     client.V1Volume(
                #         name = "datasetpath",
                #         host_path = client.V1HostPathVolumeSource(path = "/clusternfs/home/SLAM_Hive_root/SLAM_Hive/slam_hive_datasets")
                #     ),
                #     client.V1Volume(
                #         name = "algopath",
                #         host_path = client.V1HostPathVolumeSource(path = "/clusternfs/home/SLAM_Hive_root/SLAM_Hive/slam_hive_algos")
                #     ),

                #     ## test in node1
                #     client.V1Volume(
                #         name = "codepath",
                #         host_path = client.V1HostPathVolumeSource(path = "/home/robot1/lxz/slam_hive_controller/Module_B/project")
                #     ),
                    
                # ],
            ),
            metadata = client.V1ObjectMeta(
                labels = {"app": "slamhive"}
            ),
    )
    # spec
    spec = client.V1StatefulSetSpec(
        replicas = pod_number,
        service_name = service_name,
        template = template,
        selector = client.V1LabelSelector(
            match_labels={"app":"slamhive"}
        ),
        # volume_claim_templates = [client.V1PersistentVolumeClaimTemplate(
        #     metadata = client.V1PersistentVolumeclaims

        #     # name = "bpy",
        #     # host_path = "/disk/statefultest"
        # )],

    )
    # statefulSet
    statefulset = client.V1StatefulSet(
        api_version="apps/v1",
        kind = "StatefulSet",
        metadata = client.V1ObjectMeta(name = statefulset_name),
        spec = spec,
    )
    return statefulset

def create_stateful_set_object_batch(pod_number, service_name, statefulset_name, command, master_inner_ip):
    # container

    ### in real environment, this should be the k8s IP (need to check)
    # app.config['MASTER_NODE_HOST_IP'] = "10.19.125.68"
    # app.config['MASTER_USERNAME'] = 'root'
    # app.config['MASTER_PASSWORD'] = ' '

    container = client.V1Container(
        name = "moduleb",
        # image = "module_b:handware_test1",
        image = "module_b:" + app.config['CLUSTER_CONTROLLER_IMAGE_NAME'],
        image_pull_policy = "IfNotPresent",
        # 将docker的开机自启动命令添加在这里（不需要重新构建镜像）
        command = command,
        ports = [client.V1ContainerPort(container_port=80)],
        # env 通过环境变量的方式传入自己pod的信息
        env = [
            client.V1EnvVar(
                name = "MY_POD_NAME",
                value_from = client.V1EnvVarSource(
                    field_ref = client.V1ObjectFieldSelector(
                        field_path = "metadata.name"
                    )
                )
            ),
            client.V1EnvVar(
                name = "MY_POD_NAMESPACE",
                value_from = client.V1EnvVarSource(
                    field_ref = client.V1ObjectFieldSelector(
                        field_path = "metadata.namespace"
                    )
                )
            ), 
            client.V1EnvVar(
                name = "MY_POD_HOST_IP",
                value_from = client.V1EnvVarSource(
                    field_ref = client.V1ObjectFieldSelector(
                        field_path = "status.hostIP"
                    )
                )
            ), 
            client.V1EnvVar(
                name = "MY_NODE_NAME",
                value_from = client.V1EnvVarSource(
                    field_ref = client.V1ObjectFieldSelector(
                        field_path = "spec.nodeName"
                    )
                )
            ), 
            client.V1EnvVar(
                name = "MASTER_INNER_IP",
                value = master_inner_ip
            )
        ],
        
        volume_mounts = [
            # use docker api
            client.V1VolumeMount(
                name = "dockerpath",
                mount_path = "/var/run/docker.sock"
            ),
            client.V1VolumeMount(
                name = "dockerpath2",
                mount_path = "/usr/bin/docker"
            ),
            # use k8s api
            client.V1VolumeMount(
                name = "k8spath",
                mount_path = "/root/.kube/config"
            ),
            # slam-hive related
            client.V1VolumeMount(
                name = "mappingresultpath",
                mount_path = "/slamhive/result"
            ),
            client.V1VolumeMount(
                name = "batchresultpath",
                mount_path = "/slamhive/batch_mappingtask"
            ),
            client.V1VolumeMount(
                name = "datasetpath",
                mount_path = "/slamhive/dataset"
            ),
            client.V1VolumeMount(
                name = "algopath",
                mount_path = "/slamhive/algo"
            ),
            # node1 or nodex
            client.V1VolumeMount(
                name = "codepath",
                mount_path = "/home/code/project"
            ),
        ]
    )
    # template
    template = client.V1PodTemplateSpec(
        spec = client.V1PodSpec(
                # test in node1
                # node_name = "yyy",
                containers = [container],
                # in nodex
                volumes = [
                    client.V1Volume(
                        name = "dockerpath",
                        host_path = client.V1HostPathVolumeSource(path = "/var/run/docker.sock")
                    ),
                    client.V1Volume(
                        name = "dockerpath2",
                        host_path = client.V1HostPathVolumeSource(path = "/usr/bin/docker")
                    ),
                    # nodex
                    client.V1Volume(
                        name = "k8spath",
                        host_path = client.V1HostPathVolumeSource(path = "/etc/kubernetes/admin.conf")
                    ),     
                    # node1               
                    # client.V1Volume(
                    #     name = "k8spath",
                    #     host_path = client.V1HostPathVolumeSource(path = "/root/.kube/config")
                    # ),
                                # slam-hive related
                    client.V1Volume(
                        name = "mappingresultpath",
                        ## host_path = client.V1HostPathVolumeSource(path = "/home/Combination_result/slam_hive_results/mapping_results/" + task_id)
                        host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive/slam_hive_results/mapping_results/")
                        # host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive-Test/SLAM-Hive/slam_hive_results/mapping_results/")
                    ),
                    client.V1Volume(
                        name = "batchresultpath",
                        ## host_path = client.V1HostPathVolumeSource(path = "/home/Combination_result/slam_hive_results/mapping_results/" + task_id)
                        host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive/slam_hive_results/batch_mappingtask/")
                        # host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive-Test/SLAM-Hive/slam_hive_results/batch_mappingtask/")
                    ),       
                    client.V1Volume(
                        name = "datasetpath",
                        # host_path = client.V1HostPathVolumeSource(path = "/home/SLAM_Hive_root/SLAM_Hive/slam_hive_datasets")
                        host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive/slam_hive_datasets")
                        # host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive-Test/SLAM-Hive/slam_hive_datasets")
                    ),
                    client.V1Volume(
                        name = "algopath",
                        ## host_path = client.V1HostPathVolumeSource(path = "/home/SLAM_Hive_root/SLAM_Hive/slam_hive_algos")
                        host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive/slam_hive_algos")
                        # host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive-Test/SLAM-Hive/slam_hive_algos")
                    ),
                    # test in nodex
                    client.V1Volume(
                        name = "codepath",
                        ## host_path = client.V1HostPathVolumeSource(path = "/home/lxz/slam_hive_controller/Module_B/project")
                        host_path = client.V1HostPathVolumeSource(path = "/SLAM-Hive/slam_hive_controller/Module_B/project")
                    ),
                    
                ],
            ),
            metadata = client.V1ObjectMeta(
                labels = {"app": "slamhive"}
            ),
    )
    # spec
    spec = client.V1StatefulSetSpec(
        replicas = pod_number,
        service_name = service_name,
        template = template,
        selector = client.V1LabelSelector(
            match_labels={"app":"slamhive"}
        ),
        # volume_claim_templates = [client.V1PersistentVolumeClaimTemplate(
        #     metadata = client.V1PersistentVolumeclaims

        #     # name = "bpy",
        #     # host_path = "/disk/statefultest"
        # )],

    )
    # statefulSet
    statefulset = client.V1StatefulSet(
        api_version="apps/v1",
        kind = "StatefulSet",
        metadata = client.V1ObjectMeta(name = statefulset_name),
        spec = spec,
    )
    return statefulset

def create_stateful_set(app_v1_api, stateful_set_object):
    app_v1_api.create_namespaced_stateful_set(
        namespace = "default",
        body = stateful_set_object
    )

# 创建docker
# 启动cadvisor监控
def mapping_task(configName, mappingtaskID):
    app.logger.info(f"########### [Now In mapping_cadvisor.py] ###########")
    app.logger.info(f"[START!] Now run mapping task {configName} with mappingtaskID {mappingtaskID}")

    localConfigPath = os.path.join(app.config['MAPPING_RESULTS_PATH'], mappingtaskID + '/' + configName)    # yaml配置文件的路径
    print("localConfigPath= " + localConfigPath)
    with open(localConfigPath, 'r', encoding='utf-8') as f: # 读取配置文件
        config_dict = yaml.load(f, Loader=yaml.FullLoader)
        # SLAM_HIVE_PATH = get_pkg_path() # 得到主机的全局路径（用于挂载）；；我的话 要写死了 指定一个路径

        SLAM_HIVE_PATH = "/SLAM-Hive"

        resultPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_results/mapping_results/' + mappingtaskID) # 结果存储路径（主机下）
        configPath = os.path.join(resultPath, configName)   # yaml文件的路径（主机下）
        scriptsPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_algos/' + config_dict['slam-hive-algorithm'] + '/slamhive')   # mapping.py的路径（主机下）
        
                # 将slamhive文件夹拷贝到一个单独的目录
        slamhive_from_path = "/slam_hive_algos/" + config_dict['slam-hive-algorithm'] + '/slamhive'
        slamhive_to_path = "/slam_hive_results/mapping_results/" + mappingtaskID + "/slamhive"
        # if not os.path.exists(slamhive_to_path) :
        #     os.mkdir(slamhive_to_path)
        import shutil
        if not os.path.exists(slamhive_to_path):
            shutil.copytree(slamhive_from_path, slamhive_to_path)

        scriptsPath = resultPath + "/slamhive"
        # 兼容某些历史算法目录：slamhive 下存在 config.yaml 目录（而非配置文件），
        # 例如 orb-slam3-ros-mono-inertial。
        # 在此阶段统一重命名为 config.yaml.dir，避免后续以文件形式挂载 /slamhive/config.yaml 失败。
        legacy_cfg_dir = os.path.join(scriptsPath, 'config.yaml')
        if os.path.isdir(legacy_cfg_dir):
            renamed_cfg_dir = legacy_cfg_dir + '.dir'
            if os.path.exists(renamed_cfg_dir):
                try:
                    shutil.rmtree(renamed_cfg_dir)
                except Exception as err:
                    app.logger.warning(f"清理旧的 legacy config 目录失败: {renamed_cfg_dir}, err={err}")
            try:
                os.rename(legacy_cfg_dir, renamed_cfg_dir)
                app.logger.info(f"已重命名 legacy config 目录: {legacy_cfg_dir} -> {renamed_cfg_dir}")
            except Exception as err:
                app.logger.error(f"重命名 legacy config 目录失败: {legacy_cfg_dir}, err={err}")
        datasetPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_datasets/' + config_dict['slam-hive-dataset']) # 数据集的路径（主机下）
        algoTag = config_dict['slam-hive-algorithm']    # algo 镜像名称
        localResultsPath = os.path.join(app.config['MAPPING_RESULTS_PATH'], mappingtaskID)  # contianer视角下的result路径

        # 判断是否需要预处理数据集
            # datasetPath = os.path.join('/SLAM-Hive-Test/SLAM-Hive/slam_hive_datasets', config_dict['slam-hive-dataset']) # 数据集的路径（主机下）
        dataset_frequency = config_dict.get('dataset-frequency')
        dataset_resolution = config_dict.get('dataset-resolution')
        dataset_check = False

        datasetPath = os.path.join('/SLAM-Hive/slam_hive_datasets', config_dict['slam-hive-dataset'])
        datasetPath_new = os.path.join('/SLAM-Hive/slam_hive_datasets', config_dict['slam-hive-dataset'] + "_" + configName)

        

        skip_list = [config_dict['slam-hive-dataset'] + ".bag"]

        if dataset_frequency != None or dataset_resolution != None:
            datasetPath_change = "/slamhive/dataset/" + config_dict['slam-hive-dataset']
            datasetPath_change_new = "/slamhive/dataset/" + config_dict['slam-hive-dataset'] + "_" + configName
            local_datasetPath_change_new = "/slam_hive_datasets/"  + config_dict['slam-hive-dataset'] + "_" + configName
            # 将两个路径写入到配置文件中
            dataset_change_configPath = os.path.join(app.config['MAPPING_RESULTS_PATH'], mappingtaskID + '/' + "dataset_change_config.txt") 
            t_f = open(dataset_change_configPath, 'w')
            t_f.write(datasetPath_change + "\n" + datasetPath_change_new)
            t_f.close()
            print(datasetPath_change, datasetPath_change_new)
            local_dataset_change_configPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_results/mapping_results/' + mappingtaskID) + "/dataset_change_config.txt"
            #cnm 这里直接写个配置文件吧 然后写入 然后怪哉 然后读取
            container_dataset_preprocess(scriptsPath, algoTag, datasetPath, datasetPath_new, resultPath, configPath, localResultsPath, local_dataset_change_configPath, configName, "/slam_hive_datasets/" + config_dict['slam-hive-dataset'] + "_" + configName)
            datasetPath = datasetPath_new

        prepared_dataset = prepare_dataset_for_mapping(
            config_dict,
            datasetPath,
            resultPath,
            logger=app.logger,
        )
        datasetPath = prepared_dataset.dataset_path
        app.logger.info(
            "ROS dataset preparation: status=%s algorithm_ros=%s dataset_ros=%s cache_key=%s manifest=%s",
            prepared_dataset.status,
            prepared_dataset.algorithm_ros,
            prepared_dataset.dataset_ros,
            prepared_dataset.cache_key,
            prepared_dataset.manifest_path,
        )

        app.logger.info("--------------Now in [mapping_cadvisor.py] mapping_task function: --------------")
        app.logger.info(f"[CHECKING PATHS:]")
        app.logger.info(f"scriptsPath: {scriptsPath}")
        app.logger.info(f"algoTag: {algoTag}")
        app.logger.info(f"datasetPath: {datasetPath}")
        app.logger.info(f"resultPath: {resultPath}")
        app.logger.info(f"configPath: {configPath}")
        container(scriptsPath, algoTag, datasetPath, resultPath, configPath, localResultsPath, mappingtaskID)

        # 删除刚才创建的数据集，要不然内存占的太大了 ## 
        if dataset_frequency != None or dataset_resolution != None: 
            print("--------------  rm ---------------", datasetPath_change_new)
            shutil.rmtree(local_datasetPath_change_new)
        print("leave mapping_cadvisor")

#  cluster version
def mapping_task_single(configName, mappingtaskID):

    container_number = 1

    localConfigPaths = []
    # for now_number in range(container_number):
    #     print(now_number)
    #     localConfigPaths[now_number] = os.path.join(app.config['MAPPING_RESULTS_PATH']+str(mappingtaskID)+str(now_number), configName) 

    ## kubernetes
    config.load_kube_config()
    #create statefulSet2323
    v1_App = client.AppsV1Api()
    v1_Core = client.CoreV1Api()
    service_name = "slamhive-"+ str(mappingtaskID)
        ## important
    statefulset_name ="task-" + str(mappingtaskID)
    # print("statefulset name : ", statefulset_name)
    
    command = ['python3', '/home/code/project/controller_single_run.py']
    # command = ['sh', '-c', 'source /opt/ros/noetic/setup.bash && python3 /home/code/project/controller_single.py ']
    #command = ['','python3','/home/code/project/controller_single.py',master_ip , master_user, master_password]
    # command = ['sh','-c','echo "hello" && sleep 3600000']
    stateful_set_obj = create_stateful_set_object(pod_number=container_number, service_name=service_name, statefulset_name=statefulset_name, task_id = str(mappingtaskID), 
                                                  command = command)


    create_service(v1_Core, service_name)
    create_stateful_set(v1_App, stateful_set_obj)
    # read the status of the statefulSet
    import time

    # while True:
    #     time.sleep(2)
    #     api_response = v1_App.read_namespaced_stateful_set_status(
    #         name = statefulset_name,
    #         namespace = "default"
    #     )
    #     readyPodNumber = api_response.status.ready_replicas
    #     print("ready pod number: ", readyPodNumber)
    #     if readyPodNumber == container_number:
    #         print("All pods have been ready !")
    #         break




    # ret = v1_Core.list_pod_for_all_namespaces(watch=False)
    # pods_list = list() # store pod name and IP (tuple)

    # for item in ret.items:
    #     # get name
    #     pod_name = item.metadata.name
    #     if len(pod_name.split('-')) <= 1:
    #         continue
    #     if pod_name.split('-')[0] + pod_name.split('-')[1] == statefulset_name:
    #         # this pod belongs to this statefulSet
    #         pods_list.append((item.metadata.name, item.status.pod_ip))



    # 等待所有pod均写入cadvisor_config.txt文件
    # 没测试不写行不行，但是以防万一
    # time.sleep(1)
    # print("==============  pod information 0 ========================")
    # ------------------------------------------
    ## 需要插入循环判断条件 判断何时所有mapping task都完成

    ## 同时进行cadvisor监控的操作
     # 做法：
     # task-999-x中：将自己所在k8s集群中的IP地址、contianer_id写入到/999/x中的一个文件内 x

    # ------------------------------------------

    total_status_list_list = []
    for i in range(container_number):
        total_status_list_list.append([])
    pod_host_ip = []
    pod_container_id = []
    

    #读取每个sub文件夹的cadvisor_config.txt

    flag = []
    for i in range(container_number):
        # 设置初始标志为0，读取到对应的cadvisor文件，就将标志置为1
        flag.append(0)
    # ready_cadvisor_number = 0
    # while True:
    #     # 反复
    #     if ready_cadvisor_number == container_number:
    #         break
    #     for now_number in range(container_number):
    #         if flag[now_number] == 1:
    #             continue
    #         cadvisor_file_path = "/slam_hive_results/mapping_results/" + str(mappingtaskID) + "/" + str(now_number) + "/cadvisor_config.txt"
    #         if os.path.exists(cadvisor_file_path):
    #             flag[now_number] = 1
    #             ready_cadvisor_number += 1

    # 直到所有的cadvisor_config.txt文件都创建完成，开始统一读取（为了顺序统一）

    for now_number in range(container_number):
        # cadvisor_file_path = "/slam_hive_results/mapping_results/" + str(mappingtaskID) + "/" + str(now_number) + "/cadvisor_config.txt"
        # cadvisor_file = open(cadvisor_file_path, 'r')
        # cadvisor_content = cadvisor_file.read()
        # cadvisor_file.close()


        pod_host_ip.append('')
        pod_container_id.append('')

        # pod_host_ip.append(cadvisor_content.split(' ')[0].split(':')[1])
        # pod_container_id.append(cadvisor_content.split(' ')[1].split(':')[1])
    
    # print("==============  pod information 1 ========================")
    # for now_number in range(container_number):
    #     print(str(now_number), pod_host_ip[now_number], pod_container_id[now_number])

    start_time = datetime.datetime.utcnow()

    while True:
        # 判断是否所有task都finished
        now_finished_number = 0
        for now_number in range(container_number):
            finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID),"finished")
            if Path(finished_path).is_file():
                now_finished_number+=1
        if now_finished_number == container_number:
            # print("leave ========================================")
            break
        # else:
        #     # print(str(now_finished_number))
        #     now_finished_number = 0
        
        
        # cadvisor related
        if((datetime.datetime.utcnow() - start_time).total_seconds() > 1):


            # print(str(now_finished_number))
            # start_time = datetime.datetime.utcnow()

            # print(start_time)


            # 循环读写每一个cadvisor
            for now_number in range(container_number):
                cadvisor_file_path = "/slam_hive_results/mapping_results/" + str(mappingtaskID) + "/cadvisor_config.txt"

                if flag[now_number] == 0:
                    if not Path(cadvisor_file_path).is_file():
                        # print("??????")
                        continue
                    else :
                        flag[now_number] = 1
                        time.sleep(0.001) #################################################################################################
                        cadvisor_file = open(cadvisor_file_path, 'r')
                        cadvisor_content = cadvisor_file.read()
                        print("content",cadvisor_content) ###########################################
                        cadvisor_file.close()
                        pod_host_ip[now_number] = cadvisor_content.split(' ')[0].split(':')[1]
                        pod_container_id[now_number] = cadvisor_content.split(' ')[1].split(':')[1]
                fetch_stat_combination(pod_container_id[now_number], total_status_list_list[now_number], start_time, pod_host_ip[now_number])
                # print("after fetch")
                # print("after fetch",str(now_number))
    print("after while")        
    # 所有子任务都完成
    # 判断是否有正确的轨迹生成
    # 写入文件中
     # 有文件 | 文件中有轨迹 True
     # else False

    for now_number in range(container_number):
        traj_flag = True
        traj_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID),"traj.txt")
        traj_flag_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID),"traj_flag.txt")
        if not Path(traj_path).is_file():
            traj_flag = False
        else :
            # 判断轨迹文件中是否有内容
            if not os.path.getsize(traj_path):
                traj_flag = False
        if traj_flag == False:
            # 轨迹生成失败
            f = open(traj_flag_path, 'w')
            f.write("False")
            f.close()
        else :
            f = open(traj_flag_path, 'w')
            f.write("True")
            f.close()
            


    for now_number in range(container_number):
        usage_info = calulate_usage_combination(total_status_list_list[now_number])
        localResultsPath = app.config['MAPPING_RESULTS_PATH'] + "/" + str(mappingtaskID)
        generate_profiling_csv_and_fig(usage_info, localResultsPath)

        # write "usage_finished" file
        usage_finished_path = localResultsPath + "/usage_finished"
        usage_file = open(usage_finished_path,'w')
        usage_file.close()


    # print(usage_info)

    # 等待所有pod删除algo container 并且进入sleep状态后，删除statefulset
    time.sleep(1)

    # delete service and statefulset
    v1_Core.delete_namespaced_service(name = service_name, namespace = "default")
    v1_App.delete_namespaced_stateful_set(name = statefulset_name, namespace = "default")

    # check if all pods in statefulset are deleted
    # while True:
    #     ret = v1_Core.list_pod_for_all_namespaces(watch=False)
    #     pods_list = list() # store pod name and IP (tuple)
    #     remain_number = 0
    #     for item in ret.items:
    #         # get name
    #         pod_name = item.metadata.name
    #         if pod_name.split('-')[0] + pod_name.split('-')[1] == statefulset_name:
    #             # this pod belongs to this statefulSet
    #             remain_number+=1
    #     if remain_number != 0:
    #         print("remained pods number: " + str(remain_number))
    #     else:
    #         break
    #     time.sleep(1)

    time.sleep(10)
    print("all pods have been deleted!")


def mapping_task_batch(configNameList, mappingtaskconfigIdList, mappingtaskIdList, container_number, batchMappingTask_id):
    ## kubernetes
    config.load_kube_config()
    #create statefulSet2323
    v1_App = client.AppsV1Api()
    v1_Core = client.CoreV1Api()
    service_name = "slamhive-"+ str(batchMappingTask_id)
    statefulset_name ="task-" + str(batchMappingTask_id)
    command = ['python3','/home/code/project/controller_run.py']
    # command = ['sh','-c','echo "hello" && sleep 360000']
    ## 修改了每个pod做负责的任务，所以pod的数量不再是任务的数量
    pod_number = app.config['CLUSTER_WORK_NODE_NUMBER']
    stateful_set_obj = create_stateful_set_object_batch(pod_number, service_name, statefulset_name, command, '0.0.0.0')
    create_service(v1_Core, service_name)
    create_stateful_set(v1_App, stateful_set_obj)
    # read the status of the statefulSet
    
    import time
    total_status_list_list = []
    for i in range(container_number):
        total_status_list_list.append([])
    pod_host_ip = []
    pod_container_id = []
    flag = []
    usage_finished_flag = []
    for i in range(container_number):
        # 设置初始标志为0，读取到对应的cadvisor文件，就将标志置为1
        flag.append(0)
        usage_finished_flag.append(0)
    for now_number in range(container_number):
        pod_host_ip.append('')
        pod_container_id.append('')


    start_time = datetime.datetime.utcnow()
    now_finished_number = 0
    print("total number: " + str(container_number))
    while True:
        # 判断是否所有task都finished
        
        for now_number in range(container_number):
            finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], mappingtaskIdList[now_number] ,"finished")
            # print(finished_path)
            usage_finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], mappingtaskIdList[now_number] ,"usage_finished")
            if Path(finished_path).is_file():
                # print("1111")
                if Path(usage_finished_path).is_file():
                    # have generated usage info
                    continue
                else:
                    # just finished the task, can generate the usage info
                    now_finished_number+=1
                    print("finish " + str(now_number))
                    # usage
                    usage_info = calulate_usage_combination(total_status_list_list[now_number])
                    localResultsPath = app.config['MAPPING_RESULTS_PATH'] + "/" + mappingtaskIdList[now_number]
                    generate_profiling_csv_and_fig(usage_info, localResultsPath)

                    # write "usage_finished" file
                    usage_finished_path = localResultsPath + "/usage_finished"
                    usage_file = open(usage_finished_path,'w')
                    usage_file.close()
                    usage_finished_flag[now_number] = 1
                

        if now_finished_number == container_number:
            break
        # cadvisor related
        if((datetime.datetime.utcnow() - start_time).total_seconds() > 1):

            for now_number in range(container_number):
                if usage_finished_flag[now_number] == 1:
                    continue 

                cadvisor_file_path = "/slam_hive_results/mapping_results/" + mappingtaskIdList[now_number] + "/cadvisor_config.txt"

                if flag[now_number] == 0:
                    if not Path(cadvisor_file_path).is_file():
                        continue
                    else :
                        time.sleep(0.01)
                        flag[now_number] = 1
                        cadvisor_file = open(cadvisor_file_path, 'r')
                        cadvisor_content = cadvisor_file.read()
                        print("content",cadvisor_content)
                        cadvisor_file.close()
                        pod_host_ip[now_number] = cadvisor_content.split(' ')[0].split(':')[1]
                        pod_container_id[now_number] = cadvisor_content.split(' ')[1].split(':')[1]
                fetch_stat_combination(pod_container_id[now_number], total_status_list_list[now_number], start_time, pod_host_ip[now_number])
        time.sleep(0.01)
    print("after while")        

            
    # for now_number in range(container_number):
    #     usage_info = calulate_usage_combination(total_status_list_list[now_number])
    #     localResultsPath = app.config['MAPPING_RESULTS_PATH'] + "/" + mappingtaskIdList[now_number]
    #     generate_profiling_csv_and_fig(usage_info, localResultsPath)

    #     # write "usage_finished" file
    #     usage_finished_path = localResultsPath + "/usage_finished"
    #     usage_file = open(usage_finished_path,'w')
    #     usage_file.close()


    # print(usage_info)

    # 等待所有pod删除algo container 并且进入sleep状态后，删除statefulset
    time.sleep(1)

    # delete service and statefulset
    v1_Core.delete_namespaced_service(name = service_name, namespace = "default")
    v1_App.delete_namespaced_stateful_set(name = statefulset_name, namespace = "default")

    time.sleep(10)
    print("all pods have been deleted!")


def mapping_task_batch_aliyun_test():
    inner_IP_list, real_esc_number = Aliyun_controller.prepare_process(
        MASTER_REGION = "cn-zhangjiakou",
        MASTER_IP = "47.92.74.135",
        required_esc_number = 2,
        task_signal = "batch999",
        batch_task_id = 999,
        WORK_NODE_IMAGE_ID = "m-8vbgm940ya8e778gic5g",    
    )

    #     # create a new config to assign the task
    # inner_IP_list = ['172.17.248.11', '172.17.248.12']
    batchMappingTask_id = 999
    task_node = {}
    task_node.update({998: 0}) # task id: node id
    task_node.update({999: 1})

    batchMappingTask_path = os.path.join(app.config['BATCHMAPPINGTASK_PATH'], str(batchMappingTask_id))
    taskAssign_path = os.path.join(batchMappingTask_path, "taskAssign.txt")
    taskAssign_file = open(taskAssign_path,'w')
    text_content = ''
    temp_number = 0
    for key, value in task_node.items():
        if temp_number != len(task_node) - 1:
            text_content += str(key) + "," + str(value) + "\n"
        else :
            text_content += str(key) + "," + str(value)
        temp_number += 1
    taskAssign_file.write(text_content)
    taskAssign_file.close()

    dest_taskAssign_path = "/SLAM-Hive/slam_hive_results/batch_mappingtask/" + str(batchMappingTask_id) + "/taskAssign.txt"
    Aliyun_controller.transfer_assgin_file(
        inner_IP_list,
        taskAssign_path,
        dest_taskAssign_path
    )

def mapping_task_batch_aliyun(mappingtaskIdList, container_number, batchMappingTask_id, final_node_template, final_config_node, final_task_node, template_algo_dict, template_dataset_dict, template_number, node_number, aliyun_configuration):
#def mapping_task_batch_aliyun():    
# ####1
    # task_signal = "batch999"
    task_signal = "batch" + str(batchMappingTask_id)
    print("------------aliyun---------------")
    return
    # 这个函数只是用来购买服务器的
    ## 注意： 购买n完成服务器之后的操作一模一样，变化是：需要同时创建多个image，并且不同的work node 参照的image不同
    inner_IP_list, real_esc_number, image_id, instance_id_list_total = Aliyun_controller.prepare_process(
        MASTER_REGION = app.config['MASTER_REGION'],
        MASTER_IP = app.config['MASTER_IP'],
        required_esc_number = container_number,
        task_signal = task_signal,
        batch_task_id = batchMappingTask_id,
        WORK_NODE_IMAGE_ID = app.config['WORK_NODE_IMAGE_ID'],
        final_node_template = final_node_template, 
        final_config_node = final_config_node, 
        final_task_node = final_task_node, 
        template_algo_dict = template_algo_dict, 
        template_dataset_dict = template_dataset_dict,
        template_number = template_number, 
        node_number = node_number,
        aliyun_configuration = aliyun_configuration
    )

    # 那里还是要改成列表（不能随便选）
    if inner_IP_list == "error":
        return 

    if real_esc_number != node_number:
        print("not enough node")
####
    # inner_IP_list = ['172.17.248.32', '172.17.248.31'] ## TO DELETE
    # real_esc_number = 2 ## TO DELETE

    #     # create a new config to assign the task
    # inner_IP_list = ['172.17.248.11', '172.17.248.12']
    # batchMappingTask_id = 999
    # task_node = {}
    # for i in range(container_number):
    #     task_node.update({mappingtaskIdList[i]: i})
    # task_node.update({998: 0}) # task id: node id
    # task_node.update({999: 1})
####1
    # batchMappingTask_path = os.path.join(app.config['BATCHMAPPINGTASK_PATH'], str(batchMappingTask_id))
    # taskAssign_path = os.path.join(batchMappingTask_path, "taskAssign.txt")
    # taskAssign_file = open(taskAssign_path,'w')
    # text_content = ''
    # temp_number = 0
    # for key, value in task_node.items():
    #     if temp_number != len(task_node) - 1:
    #         text_content += str(key) + "," + str(value) + "\n"
    #     else :
    #         text_content += str(key) + "," + str(value)
    #     temp_number += 1
    # taskAssign_file.write(text_content)
    # taskAssign_file.close()

    # dest_taskAssign_path = "/SLAM-Hive/slam_hive_results/batch_mappingtask/" + str(batchMappingTask_id) + "/taskAssign.txt"
    # Aliyun_controller.transfer_assgin_file(
    #     inner_IP_list,
    #     taskAssign_path,
    #     dest_taskAssign_path
    # )
####
    #####################################
    ## aliyun project                   # 
    ## waiting for all the server ready #
    #####################################
    # mappingtaskIdList = ["998", "999"]
    # container_number = 2
    # batchMappingTask_id = 999

    # real_esc_number = 2
    
    ## kubernetes
    config.load_kube_config()
    #create statefulSet2323
    v1_App = client.AppsV1Api()
    v1_Core = client.CoreV1Api()
    service_name = "bslamhive-"+ str(batchMappingTask_id)
    statefulset_name ="btask-" + str(batchMappingTask_id)
    # master_ip = app.config['MASTER_NODE_HOST_IP']
    # master_user = app.config['MASTER_USERNAME']
    # master_password = app.config['MASTER_PASSWORD']
    master_ip = app.config['MASTER_IP']
    master_inner_ip = app.config['MASTER_INNER_IP']
    master_user = "root"
    master_password = "slam-hive1"
    command = ['python3','/home/code/project/controller_aliyun_run.py']
    # command = ['sh','-c','echo "hello" && sleep 360000']
    stateful_set_obj = create_stateful_set_object_batch(real_esc_number, service_name, statefulset_name, command, master_inner_ip)
    create_service(v1_Core, service_name)
    create_stateful_set(v1_App, stateful_set_obj)
    # read the status of the statefulSet
    
    import time
    total_status_list_list = []
    for i in range(container_number):
        total_status_list_list.append([])
    pod_host_ip = []
    pod_container_id = []
    flag = []
    usage_finished_flag = []
    for i in range(container_number):
        # 设置初始标志为0，读取到对应的cadvisor文件，就将标志置为1
        flag.append(0)
        usage_finished_flag.append(0)
    for now_number in range(container_number):
        pod_host_ip.append('')
        pod_container_id.append('')


    start_time = datetime.datetime.utcnow()
    now_finished_number = 0
    print("total number: " + str(container_number))
    while True:
        # 判断是否所有task都finished
        
        for now_number in range(container_number):
            finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], mappingtaskIdList[now_number] ,"finished")
            # print(finished_path)
            usage_finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], mappingtaskIdList[now_number] ,"usage_finished")
            if Path(finished_path).is_file():
                # print("1111")
                if Path(usage_finished_path).is_file():
                    # have generated usage info
                    continue
                else:
                    # just finished the task, can generate the usage info
                    now_finished_number+=1
                    print("finish " + str(now_number))
                    # usage
                    usage_info = calulate_usage_combination(total_status_list_list[now_number])
                    localResultsPath = app.config['MAPPING_RESULTS_PATH'] + "/" + mappingtaskIdList[now_number]
                    generate_profiling_csv_and_fig(usage_info, localResultsPath)

                    # write "usage_finished" file
                    usage_finished_path = localResultsPath + "/usage_finished"
                    usage_file = open(usage_finished_path,'w')
                    usage_file.close()
                    usage_finished_flag[now_number] = 1
                

        if now_finished_number == container_number:
            break
        # cadvisor related
        if((datetime.datetime.utcnow() - start_time).total_seconds() > 1):

            for now_number in range(container_number):
                if usage_finished_flag[now_number] == 1:
                    continue 

                cadvisor_file_path = "/slam_hive_results/mapping_results/" + mappingtaskIdList[now_number] + "/cadvisor_config.txt"

                if flag[now_number] == 0:
                    if not Path(cadvisor_file_path).is_file():
                        continue
                    else :
                        time.sleep(0.01)
                        flag[now_number] = 1
                        cadvisor_file = open(cadvisor_file_path, 'r')
                        cadvisor_content = cadvisor_file.read()
                        print("content",cadvisor_content)
                        cadvisor_file.close()
                        pod_host_ip[now_number] = cadvisor_content.split(' ')[0].split(':')[1]
                        pod_container_id[now_number] = cadvisor_content.split(' ')[1].split(':')[1]
                fetch_stat_combination(pod_container_id[now_number], total_status_list_list[now_number], start_time, pod_host_ip[now_number])
        time.sleep(0.01)
    print("after while")        

            
    # for now_number in range(container_number):
    #     usage_info = calulate_usage_combination(total_status_list_list[now_number])
    #     localResultsPath = app.config['MAPPING_RESULTS_PATH'] + "/" + mappingtaskIdList[now_number]
    #     generate_profiling_csv_and_fig(usage_info, localResultsPath)

    #     # write "usage_finished" file
    #     usage_finished_path = localResultsPath + "/usage_finished"
    #     usage_file = open(usage_finished_path,'w')
    #     usage_file.close()


    # print(usage_info)

    # 等待所有pod删除algo container 并且进入sleep状态后，删除statefulset
    time.sleep(1)

    # delete service and statefulset
    v1_Core.delete_namespaced_service(name = service_name, namespace = "default")
    v1_App.delete_namespaced_stateful_set(name = statefulset_name, namespace = "default")

    time.sleep(10)
    print("all pods have been deleted!")

    # 删除work node
    # 删除image
    # 将节点从k8s集群中删除
    Aliyun_controller.after_process(
        MASTER_REGION = app.config['MASTER_REGION'],
        instance_id_list = instance_id_list_total,
        image_id = image_id,
        task_signal = task_signal
    )
    time.sleep(5)

# abort
def mapping_task_combination(configName, mappingtaskID, container_number):
    localConfigPaths = []
    # for now_number in range(container_number):

    #     print(now_number)
    #     localConfigPaths[now_number] = os.path.join(app.config['MAPPING_RESULTS_PATH']+str(mappingtaskID)+str(now_number), configName) 

    ## kubernetes
    config.load_kube_config()
    #create statefulSet2323
    v1_App = client.AppsV1Api()
    v1_Core = client.CoreV1Api()
    service_name = "slamhive-"+ str(mappingtaskID)
        ## important
    statefulset_name ="task-" + str(mappingtaskID)
    # print("statefulset name : ", statefulset_name)
    command = ['python3','/home/code/project/controller.py']
    stateful_set_obj = create_stateful_set_object(pod_number=container_number, service_name=service_name, statefulset_name=statefulset_name, task_id = str(mappingtaskID), 
                                                  command = command)


    create_service(v1_Core, service_name)
    create_stateful_set(v1_App, stateful_set_obj)
    # read the status of the statefulSet
    import time

    # while True:
    #     time.sleep(2)
    #     api_response = v1_App.read_namespaced_stateful_set_status(
    #         name = statefulset_name,
    #         namespace = "default"
    #     )
    #     readyPodNumber = api_response.status.ready_replicas
    #     print("ready pod number: ", readyPodNumber)
    #     if readyPodNumber == container_number:
    #         print("All pods have been ready !")
    #         break




    # ret = v1_Core.list_pod_for_all_namespaces(watch=False)
    # pods_list = list() # store pod name and IP (tuple)

    # for item in ret.items:
    #     # get name
    #     pod_name = item.metadata.name
    #     if len(pod_name.split('-')) <= 1:
    #         continue
    #     if pod_name.split('-')[0] + pod_name.split('-')[1] == statefulset_name:
    #         # this pod belongs to this statefulSet
    #         pods_list.append((item.metadata.name, item.status.pod_ip))



    # 等待所有pod均写入cadvisor_config.txt文件
    # 没测试不写行不行，但是以防万一
    # time.sleep(1)
    # print("==============  pod information 0 ========================")
    # ------------------------------------------
    ## 需要插入循环判断条件 判断何时所有mapping task都完成

    ## 同时进行cadvisor监控的操作
     # 做法：
     # task-999-x中：将自己所在k8s集群中的IP地址、contianer_id写入到/999/x中的一个文件内 x

    # ------------------------------------------

    total_status_list_list = []
    for i in range(container_number):
        total_status_list_list.append([])
    pod_host_ip = []
    pod_container_id = []
    

    #读取每个sub文件夹的cadvisor_config.txt

    flag = []
    for i in range(container_number):
        # 设置初始标志为0，读取到对应的cadvisor文件，就将标志置为1
        flag.append(0)
    # ready_cadvisor_number = 0
    # while True:
    #     # 反复
    #     if ready_cadvisor_number == container_number:
    #         break
    #     for now_number in range(container_number):
    #         if flag[now_number] == 1:
    #             continue
    #         cadvisor_file_path = "/slam_hive_results/mapping_results/" + str(mappingtaskID) + "/" + str(now_number) + "/cadvisor_config.txt"
    #         if os.path.exists(cadvisor_file_path):
    #             flag[now_number] = 1
    #             ready_cadvisor_number += 1

    # 直到所有的cadvisor_config.txt文件都创建完成，开始统一读取（为了顺序统一）

    for now_number in range(container_number):
        # cadvisor_file_path = "/slam_hive_results/mapping_results/" + str(mappingtaskID) + "/" + str(now_number) + "/cadvisor_config.txt"
        # cadvisor_file = open(cadvisor_file_path, 'r')
        # cadvisor_content = cadvisor_file.read()
        # cadvisor_file.close()


        pod_host_ip.append('')
        pod_container_id.append('')

        # pod_host_ip.append(cadvisor_content.split(' ')[0].split(':')[1])
        # pod_container_id.append(cadvisor_content.split(' ')[1].split(':')[1])
    
    # print("==============  pod information 1 ========================")
    # for now_number in range(container_number):
    #     print(str(now_number), pod_host_ip[now_number], pod_container_id[now_number])

    start_time = datetime.datetime.utcnow()

    while True:
        # 判断是否所有task都finished
        now_finished_number = 0
        for now_number in range(container_number):
            finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID),str(now_number),"finished")
            if Path(finished_path).is_file():
                now_finished_number+=1
        if now_finished_number == container_number:
            # print("leave ========================================")
            break
        # else:
        #     # print(str(now_finished_number))
        #     now_finished_number = 0
        
        
        # cadvisor related
        if((datetime.datetime.utcnow() - start_time).total_seconds() > 1):


            # print(str(now_finished_number))
            # start_time = datetime.datetime.utcnow()

            # print(start_time)


            # 循环读写每一个cadvisor
            for now_number in range(container_number):
                cadvisor_file_path = "/slam_hive_results/mapping_results/" + str(mappingtaskID) + "/" + str(now_number) + "/cadvisor_config.txt"
                # 另一个逻辑

                
                # if flag[now_number] == 0:
                #     if Path(cadvisor_file_path).is_file():
                #         flag[now_number] = 1
                #         time.sleep(0.01)
                #         cadvisor_file = open(cadvisor_file_path, 'r')
                #         cadvisor_content = cadvisor_file.read()
                #         print(cadvisor_content) ###########################################################################################
                #         cadvisor_file.close()
                #         pod_host_ip[now_number] = cadvisor_content.split(' ')[0].split(':')[1]
                #         pod_container_id[now_number] = cadvisor_content.split(' ')[1].split(':')[1]
                #         fetch_stat_combination(pod_container_id[now_number], total_status_list_list[now_number], start_time, pod_host_ip[now_number])
                # else:
                #     fetch_stat_combination(pod_container_id[now_number], total_status_list_list[now_number], start_time, pod_host_ip[now_number])
                #     # print("nmd")


                if flag[now_number] == 0:
                    if not Path(cadvisor_file_path).is_file():
                        # print("??????")
                        continue
                    else :
                        flag[now_number] = 1
                        time.sleep(0.001) #################################################################################################
                        cadvisor_file = open(cadvisor_file_path, 'r')
                        cadvisor_content = cadvisor_file.read()
                        print("content",cadvisor_content) ###########################################
                        cadvisor_file.close()
                        pod_host_ip[now_number] = cadvisor_content.split(' ')[0].split(':')[1]
                        pod_container_id[now_number] = cadvisor_content.split(' ')[1].split(':')[1]
                fetch_stat_combination(pod_container_id[now_number], total_status_list_list[now_number], start_time, pod_host_ip[now_number])
                # print("after fetch")
                # print("after fetch",str(now_number))
    print("after while")        
    # 所有子任务都完成
    # 判断是否有正确的轨迹生成
    # 写入文件中
     # 有文件 | 文件中有轨迹 True
     # else False

    for now_number in range(container_number):
        traj_flag = True
        traj_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID),str(now_number),"traj.txt")
        traj_flag_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID),str(now_number),"traj_flag.txt")
        if not Path(traj_path).is_file():
            traj_flag = False
        else :
            # 判断轨迹文件中是否有内容
            if not os.path.getsize(traj_path):
                traj_flag = False
        if traj_flag == False:
            # 轨迹生成失败
            f = open(traj_flag_path, 'w')
            f.write("False")
            f.close()
        else :
            f = open(traj_flag_path, 'w')
            f.write("True")
            f.close()
            


    for now_number in range(container_number):
        usage_info = calulate_usage_combination(total_status_list_list[now_number])
        localResultsPath = app.config['MAPPING_RESULTS_PATH'] + "/" + str(mappingtaskID) + "/" + str(now_number)
        generate_profiling_csv_and_fig(usage_info, localResultsPath)

        # write "usage_finished" file
        usage_finished_path = localResultsPath + "/usage_finished"
        usage_file = open(usage_finished_path,'w')
        usage_file.close()


    # print(usage_info)

    # 等待所有pod删除algo container 并且进入sleep状态后，删除statefulset
    time.sleep(1)

    # delete service and statefulset
    v1_Core.delete_namespaced_service(name = service_name, namespace = "default")
    v1_App.delete_namespaced_stateful_set(name = statefulset_name, namespace = "default")


    time.sleep(10)
    print("all pods have been deleted!")



# abort
## new function 3.21
## show the k8s running info of different sub task
def check_combination_task_running_k8s(id):
    # task-204
    statefulset_name = "task-" + str(id)
    st_namespace = "default"

    # 读取该statefulset

        ## kubernetes
    config.load_kube_config()
    #create statefulSet2323
    v1_App = client.AppsV1Api()
    v1_Core = client.CoreV1Api()

    # task_st = v1_App.read_namespaced_stateful_set(statefulset_name, st_namespace)

    # print(task_st) # 好像没有有用的信息

    # 直接找每个pod吧

    pod_names_all = [] #理论上应该有的pod

    sub_dirs = os.listdir("/slam_hive_results/mapping_results/" + str(id))
    container_number = len(sub_dirs)

    pods_flag = []
    for now_number in range(container_number):
        pod_names_all.append("task-" + str(id) + "-" + str(now_number))
        pods_flag.append(True)
    

    pod_infos = []
    ready_number = 0

    for now_number in range(container_number):
        try:
            pod_info = v1_Core.read_namespaced_pod(name = pod_names_all[now_number], namespace = st_namespace)
            pod_infos.append(pod_info)
            ready_number += 1
            # 
        except ApiException as e:
            name = pod_names_all[now_number]
            pod_infos.append(name)
            pods_flag[now_number] = False

    # 返回元组 （）可以省略
    return pods_flag, pod_infos, container_number, ready_number

    # print(pod_infos[0])

    # nodes info
    
    # nodes_info = v1_Core.list_node()
    # print(nodes_info.items[0].metadata.name)
    # print(nodes_info.items[0].status.addresses[0].address)


    # nodes_info: list
    # nodes_info[i].metadata.name
    #              .status.addresses[] (type = InternalIP)
    #              .

# pod name: task-214-0 ready: True age: 2023-03-22 07:40:52+00:00 pod_ip: 10.244.1.119 host_ip: 172.30.2.1 node: node2
# pod name: task-214-1 ready: True age: 2023-03-22 07:40:53+00:00 pod_ip: 10.244.2.114 host_ip: 172.30.3.1 node: node3
# pod name: task-214-2 ready: True age: 2023-03-22 07:40:54+00:00 pod_ip: 10.244.1.120 host_ip: 172.30.2.1 node: node2
# pod name: task-214-3 ready: True age: 2023-03-22 07:40:56+00:00 pod_ip: 10.244.2.115 host_ip: 172.30.3.1 node: node3
# pod name: task-214-4 ready: True age: 2023-03-22 07:40:57+00:00 pod_ip: 10.244.1.121 host_ip: 172.30.2.1 node: node2
# pod name: task-214-5 ready: True age: 2023-03-22 07:40:59+00:00 pod_ip: 10.244.2.116 host_ip: 172.30.3.1 node: node3
# node1
# 172.30.1.1



def container_dataset_preprocess(scriptsPath, algoTag, datasetPath, datasetPath_new, resultPath, configPath, localResultsPath, local_dataset_change_configPath, configName, check_dataset_path):
    # mount datasetPath, resultPath, configPath to image
    # Create Container
    # 这里要传入那个sb config的文件名称
    print("sdfsfdsfdsf")
    print(configPath)
    print(local_dataset_change_configPath)
    client = docker.from_env()
    print("===========Start Container: [module_b:"+app.config['CLUSTER_CONTROLLER_IMAGE_NAME']+"]===========")
    volume = {scriptsPath:{'bind':'/slamhive','mode':'rw'},
            "/SLAM-Hive/slam_hive_datasets":{'bind':'/slamhive/dataset','mode':'rw'},
            configPath:{'bind':'/slamhive/config.yaml','mode':'ro'},
            "/SLAM-Hive/slam_hive_controller/Module_B/project": {'bind':'/home/code/project', 'mode':'rw'},
            local_dataset_change_configPath:{'bind':'/slamhive/dataset_change_config.yaml','mode':'ro'}}
    algo = client.containers.run("module_b:"+app.config['CLUSTER_CONTROLLER_IMAGE_NAME'],detach=True, tty=True, volumes=volume)
    print("================Running Changing dataset=================")
    # algo_exec = algo.exec_run('bash /slamhive/mappingtask.sh', tty=True, stream=True)
    algo_exec = algo.exec_run('python3 /home/code/project/controller_workstation_run.py', tty=True, stream=True)
    # 读完输出即脚本结束，再检查 finished（原来的空转等待在脚本失败时会永远卡住）
    for chunk in algo_exec.output:
        print(chunk.decode("utf-8", "replace"), end="")

    check_path = check_dataset_path + "/finished"
    print(check_path)
    finished = os.path.exists(check_path)
    time.sleep(2)
    algo.stop()
    algo.remove()
    if not finished:
        raise RuntimeError("dataset preprocessing did not create {}".format(check_path))
    print("==================Changing dataset Finished====================")

def container(scriptsPath, algoTag, datasetPath, resultPath, configPath, localResultsPath, mappingtaskID):
    # mount datasetPath, resultPath, configPath to image
    # Create Container
    import sys
    import traceback
    import os
    from pathlib import Path
    
    app.logger.info("--------------Now in [mapping_cadvisor.py] container function!!!--------------")
    
    app.logger.info(f"现在开始检测docker环境...")
    try:
        # === 第1步：检查Docker客户端连接 ===
        app.logger.info("检查Docker客户端连接...")
        app.logger.info("[STEP1]:检查Docker客户端连接...")
        # 修复Docker-in-Docker环境的连接问题
        import os
        if 'DOCKER_HOST' in os.environ and 'http+docker' in os.environ['DOCKER_HOST']:
            app.logger.info("检测到有问题的DOCKER_HOST环境变量，正在清理...")
            del os.environ['DOCKER_HOST']
        
        # 在容器内部使用unix socket连接Docker守护进程
        try:
            client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
            app.logger.info("使用unix socket连接Docker守护进程")
        except Exception as e:
            app.logger.info(f"unix socket连接失败，尝试使用from_env: {e}")
            client = docker.from_env()
        
        # 测试Docker连接
        try:
            docker_info = client.info()
            app.logger.info(f"Docker连接成功，版本: {docker_info.get('ServerVersion', 'unknown')}")
        except Exception as e:
            app.logger.info(f"❌ Docker连接失败: {e}")
            raise Exception(f"Docker守护进程连接失败: {e}")
        
        # === 第2步：检查镜像是否存在 ===
        image_name = f"slam-hive-algorithm:{algoTag}"
        app.logger.info("[STEP2]:检查镜像是否存在...")
        app.logger.info(f"检查镜像是否存在: {image_name}")
        
        try:
            image = client.images.get(image_name)
            app.logger.info(f"✅ 镜像存在: {image.id}")
            app.logger.info(f"镜像标签: {image.tags}")
            
            # 列出所有可用镜像（调试信息）
            images = client.images.list()
            app.logger.info("可用的镜像:")
            for img in images:
                if img.tags:
                    app.logger.info(f"  - {img.tags[0]}")
            
            # 镜像存在，继续执行
            app.logger.info(f"✅ 镜像检查通过: {image_name}")
            
        except ImageNotFound:
            app.logger.error(f"❌ 镜像不存在: {image_name}")
            # 列出所有可用镜像
            images = client.images.list()
            app.logger.info("可用的镜像:")
            for img in images:
                if img.tags:
                    app.logger.info(f"  - {img.tags[0]}")
            raise Exception(f"镜像 {image_name} 不存在")
        except Exception as e:
            app.logger.error(f"❌ 检查镜像时出错: {e}")
            raise Exception(f"镜像检查失败: {e}")
        
        # === 第3步：检查挂载路径是否存在 ===
        app.logger.info("[STEP3]:检查挂载路径...")
        app.logger.info("检查挂载路径...")
        
        # 路径转换函数：将主机路径转换为容器内路径
        def convert_to_container_path(host_path):
            # 检查是否在容器内运行
            if os.path.exists("/.dockerenv"):
                # 在容器内，需要转换路径
                if host_path.startswith("/SLAM-Hive/slam_hive_results"):
                    return host_path.replace("/SLAM-Hive/slam_hive_results", "/slam_hive_results")
                elif host_path.startswith("/SLAM-Hive/slam_hive_datasets"):
                    return host_path.replace("/SLAM-Hive/slam_hive_datasets", "/slam_hive_datasets")
                elif host_path.startswith("/SLAM-Hive/slam_hive_algos"):
                    return host_path.replace("/SLAM-Hive/slam_hive_algos", "/slam_hive_algos")
                elif host_path.startswith("/SLAM-Hive/slam_hive_configurations"):
                    return host_path.replace("/SLAM-Hive/slam_hive_configurations", "/slam_hive_configurations")
            # 如果不在容器内或不需要转换，返回原路径
            return host_path
        
        # 转换路径用于检查
        container_scriptsPath = convert_to_container_path(scriptsPath)
        container_datasetPath = convert_to_container_path(datasetPath)
        container_resultPath = convert_to_container_path(resultPath)
        container_configPath = convert_to_container_path(configPath)
        
        paths_to_check = {
            'scriptsPath': (scriptsPath, container_scriptsPath),
            'datasetPath': (datasetPath, container_datasetPath),
            'resultPath': (resultPath, container_resultPath),
            'configPath': (configPath, container_configPath)
        }
        
        app.logger.info(f"容器运行检测: {os.path.exists('/.dockerenv')}")
        
        for name, (host_path, container_path) in paths_to_check.items():
            app.logger.info(f"检查路径 {name}:")
            app.logger.info(f"  主机路径: {host_path}")
            app.logger.info(f"  容器路径: {container_path}")
            
            if os.path.exists(container_path):
                app.logger.info(f"✅ {name}: {container_path} (存在)")
                if os.path.isfile(container_path):
                    size = os.path.getsize(container_path)
                    app.logger.info(f"   文件大小: {size} bytes")
                elif os.path.isdir(container_path):
                    try:
                        files = os.listdir(container_path)
                        app.logger.info(f"   目录包含 {len(files)} 个文件/文件夹")
                        if files:
                            app.logger.info(f"   前几个项目: {files[:3]}")
                    except PermissionError:
                        app.logger.info(f"   ⚠️ 无权限访问目录")
            else:
                app.logger.info(f"❌ {name}: {container_path} (不存在)")
                # 尝试创建目录（如果是结果路径）
                if name == 'resultPath':
                    try:
                        os.makedirs(container_path, exist_ok=True)
                        app.logger.info(f"✅ 已创建结果目录: {container_path}")
                    except Exception as e:
                        app.logger.info(f"❌ 创建结果目录失败: {e}")
        
        # === 第4步：准备卷挂载配置 ===
        app.logger.info("[STEP4]:准备卷挂载配置...")
        app.logger.info("准备卷挂载配置...")
        
        # 为Docker容器创建使用正确的路径
        # 注意：当Flask应用在Docker容器内运行时，新创建的容器需要映射主机路径，而不是Flask容器内的路径
        volume = {
            scriptsPath: {'bind': '/slamhive', 'mode': 'rw'},
            datasetPath: {'bind': '/slamhive/dataset', 'mode': 'ro'},
            resultPath: {'bind': '/slamhive/result', 'mode': 'rw'},
            configPath: {'bind': '/slamhive/config.yaml', 'mode': 'ro'}
        }
        
        app.logger.info("卷挂载配置:")
        for host_path, mount_info in volume.items():
            app.logger.info(f"  {host_path} -> {mount_info['bind']} ({mount_info['mode']})")
        
        # === 第5步：准备日志文件 ===
        app.logger.info("[STEP5]:准备日志文件...")
        log_path = "/slam_hive_results/mapping_results/" + str(mappingtaskID) + "/log.txt"
        log_file = open(log_path, 'a+')
        log_file.write(configPath + "\n")
        log_file.flush()
        
        # === 第6步：创建容器 ===
        app.logger.info("[STEP6]:开始创建容器...")
        app.logger.info(f"开始创建容器: {image_name}")
        print("===========Start Container: [slam-hive-algorithm:" + algoTag + "]===========")

        config_dict = {}
        config_candidates = [configPath]
        if 'container_configPath' in locals():
            config_candidates.append(container_configPath)
        config_error = None
        for candidate in config_candidates:
            try:
                with open(candidate, "r", encoding="utf-8") as file:
                    config_dict = yaml.load(file, Loader=yaml.FullLoader) or {}
                app.logger.info(f"GPU判定使用配置文件: {candidate}")
                config_error = None
                break
            except Exception as config_err:
                config_error = config_err
        if config_error is not None:
            app.logger.info(f"读取配置文件失败，默认关闭GPU透传: {config_error}")
            config_dict = {}

        algorithm_attribute = str(config_dict.get("algorithm-attribute") or "")
        lower_attribute = algorithm_attribute.lower()
        use_gpu = ("gpu" in lower_attribute) or ("cuda" in lower_attribute)
        app.logger.info(
            f"算法属性: '{algorithm_attribute}', GPU透传: {'启用' if use_gpu else '关闭'}"
        )
        
        try:
            run_kwargs = {
                "command": "/bin/bash",
                "detach": True,
                "tty": True,
                "volumes": volume,
                "network": "host",
                "name": f"slam-task-{mappingtaskID}",
                "remove": False,
                "mem_limit": "16g",
                "memswap_limit": "16g",
                "shm_size": "4g",
            }
            if use_gpu:
                gpu_request = docker.types.DeviceRequest(
                    count=-1, capabilities=[["gpu"]]
                )
                run_kwargs["device_requests"] = [gpu_request]
                app.logger.info(
                    f"容器GPU请求参数: {run_kwargs['device_requests']}"
                )

            algo = client.containers.run(image_name, **run_kwargs)
            
            app.logger.info(f"✅ 容器创建成功!")
            app.logger.info(f"容器ID: {algo.id}")
            app.logger.info(f"容器名称: {algo.name}")
            app.logger.info(f"容器状态: {algo.status}")
            
            # 检查容器是否真正运行
            algo.reload()
            app.logger.info(f"容器刷新后状态: {algo.status}")
            
            if algo.status != 'running':
                app.logger.info(f"⚠️ 容器未正常运行，状态: {algo.status}")
                # 获取容器日志
                logs = algo.logs(tail=50).decode('utf-8')
                app.logger.info(f"容器日志:\n{logs}")
        
        except ContainerError as e:
            app.logger.info(f"❌ 容器运行错误: {e}")
            app.logger.info(f"容器退出码: {e.exit_status}")
            app.logger.info(f"容器日志: {e.stderr}")
            raise
        except ImageNotFound as e:
            app.logger.info(f"❌ 镜像未找到: {e}")
            raise
        except APIError as e:
            app.logger.info(f"❌ Docker API错误: {e}")
            app.logger.info(f"错误详情: {e.explanation}")
            if use_gpu:
                app.logger.info(
                    "GPU模式创建失败，请检查宿主机NVIDIA驱动、Docker GPU运行时和设备可见性。"
                )
            raise
        except Exception as e:
            app.logger.info(f"❌ 容器创建时发生未知错误: {e}")
            app.logger.info(f"错误类型: {type(e).__name__}")
            app.logger.info(f"错误堆栈: {traceback.format_exc()}")
            raise
        
        # === 第6步：执行容器内命令 ===
        app.logger.info("[STEP6]:开始执行容器内任务...")
        app.logger.info("开始执行容器内任务...")
        print("================Running Task=================")
        
        try:
            # 先检查容器内环境
            check_result = algo.exec_run('ls -la /slamhive/')
            app.logger.info(f"容器内/slamhive/目录内容:\n{check_result.output.decode()}")
            
            # 检查系统资源
            mem_result = algo.exec_run('cat /proc/meminfo | grep MemTotal')
            app.logger.info(f"容器内存信息: {mem_result.output.decode()}")
            
            # 执行主要任务，并实时捕获输出
            app.logger.info("开始执行 mapping.py...")
            # algo_exec = algo.exec_run('sleep 9999999s', stream=True, tty=True)

            ###########################################################################
            app.logger.info("开始进入sleep调试")
            # sleep = algo.exec_run('sleep 9999999s')
            ###########################################################################

            algo_exec = algo.exec_run('python3 /slamhive/mapping.py', stream=True, tty=True)
            app.logger.info("✅ 成功启动容器内执行")
            
            # 实时读取和记录输出
        except Exception as e:
            app.logger.error(f"❌ 执行容器内命令失败: {e}")
            # 尝试检查容器内文件是否存在
            try:
                check_result = algo.exec_run('ls -la /slamhive/')
                app.logger.info(f"容器内/slamhive/目录内容:\n{check_result.output.decode()}")
                
                check_result = algo.exec_run('python3 --version')
                app.logger.info(f"Python版本: {check_result.output.decode()}")
            except:
                pass
            log_file.close()
            raise

    except Exception as e:
        app.logger.info(f"🚨 容器创建流程失败: {e}")
        app.logger.info(f"完整错误信息: {traceback.format_exc()}")
        
        # 尝试清理
        try:
            if 'algo' in locals():
                algo.stop()
                algo.remove()
                app.logger.info("已清理失败的容器")
        except:
            pass
        
        # 关闭日志文件
        try:
            log_file.close()
        except:
            pass
        
        raise Exception(f"Docker容器创建失败: {e}")

    #######################
    ## 需要加入一些新的功能 ##
    #######################


    total_status_list = []
    start_time = datetime.datetime.utcnow()

    while True:
        time.sleep(0.1)
        try:
            # print(next(algo_exec.output).decode())
            now_str = next(algo_exec.output).decode()
            if "[RUNNING]  Bag Time" in now_str :
                continue
            # ==print(now_str)
            # print(now_str)
            log_file.write(now_str)
        except StopIteration:
            # 实在不行考虑一下判断finished吧
            break
        except Exception as e:
            app.logger.info(f"读取容器输出时出错: {e}")
            break
            
        if((datetime.datetime.utcnow() - start_time).total_seconds() > 1):
            fetch_stat(algo.id, total_status_list, start_time)


    log_file.close()

    usage_info = calulate_usage(total_status_list)
    # print(usage_info)
    generate_profiling_csv_and_fig(usage_info, localResultsPath)


    traj_flag = True
    traj_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID),"traj.txt")
    traj_flag_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID),"traj_flag.txt")
    if not Path(traj_path).is_file():
        traj_flag = False
    else :
        # 判断轨迹文件中是否有内容
        if not os.path.getsize(traj_path):
            traj_flag = False
    if traj_flag == False:
        # 轨迹生成失败
        f = open(traj_flag_path, 'w')
        f.write("False")
        f.close()
    else :
        f = open(traj_flag_path, 'w')
        f.write("True")
        f.close()


    time.sleep(5)
    algo.stop()
    algo.remove()
    print("==================Mapping Task Finished====================")

# Fetch status of a container
# This function should be called once per second when the mapping task runs
def fetch_stat_combination(container_id, total_status_list, start_time, host_ip):
    # 自动检测运行环境并选择正确的 cAdvisor 端点
    import os
    
    # 在Docker Compose环境中，使用服务名连接
    if os.path.exists('/.dockerenv'):  # 检查是否在Docker容器内
        ENDPOINT_CADVISOR = "http://cadvisor:8080"  # Docker Compose 环境
    else:
        ENDPOINT_CADVISOR = "http://" + host_ip + ":8085"  # 集群环境
    
    app.logger.info(f"连接 cAdvisor: {ENDPOINT_CADVISOR}")
    r = requests.get(ENDPOINT_CADVISOR+"/api/v1.3/docker/"+container_id)
    if r.content.decode().split(' ')[0] == 'failed':
        # 该容器已经执行完毕
        # print("error")
        return total_status_list
    
    try:
        j = json.loads(r.content)
        status_list = j['/system.slice/docker-'+container_id+'.scope']["stats"]
        for status in status_list:
            if status not in total_status_list:
                if(parser.parse(status["timestamp"]).replace(tzinfo=None)>start_time):
                    total_status_list.append(status)
        return total_status_list
    except Exception as e:
        print(e)
    return total_status_list


# Calculate the status logs into CPU usage and memory usage
# The output is a list. Each element of the list is in form of (Time, CPU usage, Memorry usage)
def calulate_usage_combination(total_status_list):
    #print("cal1")
    cpu_usage_list=[0]
    time_start = parser.parse(total_status_list[0]["timestamp"])
    #print("cal2")
    for i in range(1,len(total_status_list)):
        s0 = total_status_list[i-1]
        s1 = total_status_list[i]
        time_diff = (parser.parse(s1["timestamp"]) - parser.parse(s0["timestamp"])).total_seconds() * 1000000000
        cpu_time_diff = s1["cpu"]["usage"]["total"] - s0["cpu"]["usage"]["total"]
        cpu_usage = cpu_time_diff/time_diff
        cpu_usage_list.append(cpu_usage)
    #print("cal3")
    mem_usage_list = [s["memory"]["usage"] for s in total_status_list]
    #print("cal4")
    time_list = [(parser.parse(s["timestamp"])-time_start).total_seconds() for s in total_status_list]
    #print("cal5")

    return list(zip(time_list,cpu_usage_list,mem_usage_list))










# Fetch status of a container
# This function should be called once per second when the mapping task runs
def fetch_stat(container_id, total_status_list, start_time):
    # 自动检测运行环境并选择正确的 cAdvisor 端点
    import os
    
    # 在Docker Compose环境中，使用服务名连接
    if os.path.exists('/.dockerenv'):  # 检查是否在Docker容器内
        ENDPOINT_CADVISOR = "http://cadvisor:8080"  # Docker Compose 环境
    else:
        ENDPOINT_CADVISOR = "http://localhost:8080"  # 本地开发环境
    
    app.logger.info(f"连接 cAdvisor: {ENDPOINT_CADVISOR}")
    # print(ENDPOINT_CADVISOR+"/api/v1.3/docker/"+str(container_id))
    r = requests.get(ENDPOINT_CADVISOR+"/api/v1.3/docker/"+str(container_id))
    j = json.loads(r.content)
    status_list = j['/system.slice/docker-'+str(container_id)+'.scope']["stats"]
    for status in status_list:
        if status not in total_status_list:
            if(parser.parse(status["timestamp"]).replace(tzinfo=None)>start_time):
                total_status_list.append(status)
    return total_status_list


# Calculate the status logs into CPU usage and memory usage
# The output is a list. Each element of the list is in form of (Time, CPU usage, Memorry usage)
def calulate_usage(total_status_list):
    # 检查列表是否为空
    if not total_status_list:
        app.logger.warning("监控数据为空，无法计算使用率统计")
        return []
    
    # 检查列表是否只有一个元素
    if len(total_status_list) < 2:
        app.logger.warning("监控数据不足，无法计算使用率统计")
        return []
    
    try:
        cpu_usage_list=[0]
        time_start = parser.parse(total_status_list[0]["timestamp"])
        for i in range(1,len(total_status_list)):
            s0 = total_status_list[i-1]
            s1 = total_status_list[i]
            time_diff = (parser.parse(s1["timestamp"]) - parser.parse(s0["timestamp"])).total_seconds() * 1000000000
            cpu_time_diff = s1["cpu"]["usage"]["total"] - s0["cpu"]["usage"]["total"]
            cpu_usage = cpu_time_diff/time_diff
            cpu_usage_list.append(cpu_usage)
        
        mem_usage_list = [s["memory"]["usage"] for s in total_status_list]
        time_list = [(parser.parse(s["timestamp"])-time_start).total_seconds() for s in total_status_list]

        return list(zip(time_list,cpu_usage_list,mem_usage_list))
    except Exception as e:
        app.logger.error(f"计算使用率统计时出错: {e}")
        return []


# Generate csv and figure from profiling data
# `profiling.csv`, `profiling_cpu.png` and `profiling_ram.png` will be saved to the path specifed
def generate_profiling_csv_and_fig(usage_info, path_to_save):
    print(path_to_save)
    
    # 检查 usage_info 是否为空
    if not usage_info:
        app.logger.warning("监控数据为空，无法生成性能分析图表")
        # 创建空的CSV文件
        with open(path_to_save+'/profiling.csv', 'w', newline='') as csvfile:
            fieldnames = ['time', 'cpu_usage', 'memory_usage']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        return
    
    # 生成CSV文件
    with open(path_to_save+'/profiling.csv', 'w', newline='') as csvfile:
        fieldnames = ['time', 'cpu_usage', 'memory_usage']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for usage in usage_info:
            writer.writerow({'time': usage[0], 'cpu_usage': usage[1], 'memory_usage': usage[2]})
    
    try:
        profiling_data = np.array(usage_info).T

        # 生成CPU使用率图表
        plt.plot(profiling_data[0],profiling_data[1])
        plt.xlabel("Time (sec)")
        plt.ylabel("CPU usage (cores)")    
        plt.title("CPU usage over Time")
        max_cpu = max(profiling_data[1])
        time_cpu = profiling_data[0][np.argmax(profiling_data[1])]
        print(max_cpu)
        plt.annotate('Max CPU usage = ' + str(round(max_cpu,2)), xy=(time_cpu, max_cpu), xytext=(time_cpu-25, max_cpu-0.5),
                    color="r", arrowprops=dict(arrowstyle="->", color="r"))
        plt.savefig(path_to_save+"/profiling_cpu.png")
        plt.close()

        # 生成内存使用率图表
        plt.plot(profiling_data[0],profiling_data[2]/(1024*1024))
        plt.xlabel("Time (sec)")
        plt.ylabel("RAM usage (MiB)")    
        plt.title("RAM usage over Time")
        max_ram = max(profiling_data[2]/(1024*1024))
        time_ram = profiling_data[0][np.argmax(profiling_data[2])]
        print(max_ram)
        plt.annotate('Max RAM usage = ' + str(round(max_ram,2)), xy=(time_ram, max_ram), xytext=(time_ram-50, max_ram-300),
                    color="r", arrowprops=dict(arrowstyle="->", color="r"))
        plt.savefig(path_to_save+"/profiling_ram.png")
        plt.close()
    except Exception as e:
        app.logger.error(f"生成性能分析图表时出错: {e}")
        # 清理可能创建的图表文件
        try:
            plt.close('all')
        except:
            pass
