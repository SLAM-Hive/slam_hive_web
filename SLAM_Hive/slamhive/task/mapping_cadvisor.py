# This is part of SLAM Hive
# Copyright (C) 2022 Yuanyuan Yang, Bowen Xu, Yinjie Li, Sören Schwertfeger, ShanghaiTech University. 

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
import numpy as np
import matplotlib.pyplot as plt
from dateutil import parser
from slamhive import app
from slamhive.task.utils import *

def mapping_task(configName, mappingtaskID):
    localConfigPath = os.path.join(app.config['MAPPING_RESULTS_PATH'], mappingtaskID + '/' + configName) 
    print("localConfigPath= " + localConfigPath)
    with open(localConfigPath, 'r', encoding='utf-8') as f:
        config_dict = yaml.load(f, Loader=yaml.FullLoader)
        SLAM_HIVE_PATH = get_pkg_path()
        resultPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_results/mapping_results/' + mappingtaskID)
        configPath = os.path.join(resultPath, configName)
        scriptsPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_algos/' + config_dict['slam-hive-algorithm'] + '/slamhive')
        datasetPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_datasets/' + config_dict['slam-hive-dataset'])
        algoTag = config_dict['slam-hive-algorithm']
        localResultsPath = os.path.join(app.config['MAPPING_RESULTS_PATH'], mappingtaskID) 
        print('scriptsPath: '+ scriptsPath)
        print('algoTag: '+ algoTag)
        print('datasetPath: '+ datasetPath)
        print('resultPath: '+ resultPath)
        print('configPath: '+ configPath)
        container(scriptsPath, algoTag, datasetPath, resultPath, configPath, localResultsPath)


def container(scriptsPath, algoTag, datasetPath, resultPath, configPath, localResultsPath):
    # mount datasetPath, resultPath, configPath to image
    # Create Container
    client = docker.from_env()
    print("===========Start Container: [slam-hive-algorithm:" + algoTag + "]===========")
    volume = {scriptsPath:{'bind':'/slamhive','mode':'rw'},
            datasetPath:{'bind':'/slamhive/dataset','mode':'ro'},
            resultPath:{'bind':'/slamhive/result','mode':'rw'},
            configPath:{'bind':'/slamhive/config.yaml','mode':'ro'}}
    algo = client.containers.run("slam-hive-algorithm:" + algoTag, command='/bin/bash', detach=True, tty=True, volumes=volume)
    print("================Running Task=================")
    # algo_exec = algo.exec_run('bash /slamhive/mappingtask.sh', tty=True, stream=True)
    algo_exec = algo.exec_run('python3 /slamhive/mapping.py', tty=True, stream=True)

    total_status_list = []
    start_time = datetime.datetime.utcnow()

    while True:
        try:
            # print(next(algo_exec).decode())
            next(algo_exec)
        except StopIteration:
            break
        if((datetime.datetime.utcnow() - start_time).total_seconds() > 1):
            fetch_stat(algo.id, total_status_list, start_time)

    usage_info = calulate_usage(total_status_list)
    # print(usage_info)
    generate_profiling_csv_and_fig(usage_info, localResultsPath)

    time.sleep(5)
    algo.stop()
    algo.remove()
    print("==================Mapping Task Finished====================")


# Fetch status of a container
# This function should be called once per second when the mapping task runs
def fetch_stat(container_id, total_status_list, start_time):
    # ENDPOINT_CADVISOR = "http://localhost:8085"
    ENDPOINT_CADVISOR = "http://cadvisor:8080"
    r = requests.get(ENDPOINT_CADVISOR+"/api/v1.3/docker/"+str(container_id))
    j = json.loads(r.content)
    status_list = j['/docker/'+container_id]["stats"]
    for status in status_list:
        if status not in total_status_list:
            if(parser.parse(status["timestamp"]).replace(tzinfo=None)>start_time):
                total_status_list.append(status)
    return total_status_list


# Calculate the status logs into CPU usage and memory usage
# The output is a list. Each element of the list is in form of (Time, CPU usage, Memorry usage)
def calulate_usage(total_status_list):
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


# Generate csv and figure from profiling data
# `profiling.csv`, `profiling_cpu.png` and `profiling_ram.png` will be saved to the path specifed
def generate_profiling_csv_and_fig(usage_info, path_to_save):
    print(path_to_save)
    with open(path_to_save+'/profiling.csv', 'w', newline='') as csvfile:
        fieldnames = ['time', 'cpu_usage', 'memory_usage']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for usage in usage_info:
            writer.writerow({'time': usage[0], 'cpu_usage': usage[1], 'memory_usage': usage[2]})
    profiling_data = np.array(usage_info).T

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
