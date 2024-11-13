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
# along with SLAM Hive.  If not, see <https://www.gnu.org/licenses/>

from flask import redirect, url_for, render_template, request, jsonify, send_from_directory, abort
from slamhive import app, db, socketio
from slamhive.models import MappingTaskConfig, MappingTask, PerformanceResults, BatchMappingTask
from slamhive.forms import DeleteMappingTaskForm
from concurrent.futures import ThreadPoolExecutor
from slamhive.task import mapping_cadvisor
from slamhive.blueprints.utils import *
from slamhive.blueprints.mappingtaskconf import check_parameters_sql
from pathlib import Path
from datetime import datetime
from flask_apscheduler import APScheduler
import zipfile

import json, yaml, os, uuid, time
import subprocess
import numpy as np

executor = ThreadPoolExecutor(10)
scheduler = APScheduler()
scheduler.start()

# 通过判断是否生成finishd文件夹
    # finished文件夹由algo contianer生成：在mapping.py中
    # 需要修改成：判断是否所有的finished都有创建
# def CheckTask(mappingtaskID):
#     mappingtask = MappingTask.query.get(mappingtaskID)
#     finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID)+"/finished")
#     if Path(finished_path).is_file():
#         mappingtask.state = "Finished"
#         db.session.commit()
#         print('[MappingTask ID: '+str(mappingtaskID)+'] finished!')
#         scheduler.remove_job(str(mappingtaskID))
#         #push state to the frontend
#         socketio.emit('update_state', {'data': 'Mapping task ' + str(mappingtaskID) +' is finished!'})
#     else : 
#         print('[MappingTask ID '+str(mappingtaskID)+'] is running...')

def calculate_traj_len(task_id):
    
    # 首先判断轨迹是否成功
    traj_flag_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(task_id) ,"traj_flag.txt")
    with open(traj_flag_path, 'r') as f:
        text = f.read()
        if text == "True": # （至少有轨迹文件，且轨迹内容不为空）
            pass
        else :
            return 0.0
    # 起码是有traj文件的且不为空
    # 通过task id 获取dataset路径
    mappingtask = MappingTask.query.get(task_id)
    dataset_name = mappingtask.mappingTaskConf.dataset.name
    groundtruth_file_path = os.path.join(app.config['DATASETS_PATH'], dataset_name,"groundtruth.txt")
    task_traj_file_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(task_id) ,"traj.txt")
    print(groundtruth_file_path)
    print(task_traj_file_path)

    
    groundtruth_start_timestamp = 0
    groundtruth_end_timestamp = 0
    task_traj_start_timestamp = 0
    task_traj_end_timestamp = 0

        # 读取文件
    with open(groundtruth_file_path, "r") as file:
        lines = file.readlines()
        # 首先找到第一个不是注释的行
        first_line_id = -1
        for i in range(len(lines)):
            if lines[i][0] != "#":
                first_line_id = i
                break
        if first_line_id == -1:
            return 0.0 # groundtruth格式错误

        last_line_id = -1
        for i in range(len(lines)):
            j = len(lines) - i - 1
            if lines[j][0] != "#":
                last_line_id = j
                break
        # 如果能找到lastid，至少是和firstid 同一行  
        print(first_line_id)
        print(last_line_id)      
        
        try:
            groundtruth_start_timestamp = float(lines[first_line_id].split()[0])
            groundtruth_end_timestamp = float(lines[last_line_id].split()[0])
            print(groundtruth_start_timestamp, groundtruth_end_timestamp)
        except Exception as e:
            print("groundtruth file error")
            return 0.0

    with open(task_traj_file_path, "r") as file:
        try:
            lines = file.readlines()
            first_line_id = -1
            for i in range(len(lines)):
                if lines[i][0] != "#":
                    first_line_id = i
                    break
            if first_line_id == -1:
                return 0.0 # groundtruth格式错误

            last_line_id = -1
            for i in range(len(lines)):
                j = len(lines) - i - 1
                if lines[j][0] != "#":
                    last_line_id = j
                    break
            # 如果能找到lastid，至少是和firstid 同一行  
            print(first_line_id)
            print(last_line_id)  

            # 对结果进行分段
            timestamps = []
            for i in range(last_line_id - first_line_id + 1):
                j = first_line_id + i
                timestamp = float(lines[j].split()[0])
                timestamps.append(timestamp)
            timestamps = np.array(timestamps)

            # 计算时间差
            time_diffs = np.diff(timestamps)

            # 设定动态分段的时间差阈值 (例如，时间差的90%分位数)
            threshold = 30 # np.percentile(time_diffs, 99)
            print("threshold",threshold)

            # 初始化分段
            segments = []
            current_segment_ids = [0]  # 用于存储当前段的ID，从第一个数据点的ID 0 开始
            # 遍历数据，根据时间差动态分段
            for i in range(1, len(timestamps)):
                if time_diffs[i - 1] > threshold:
                    # 时间差超过阈值，将当前段的ID存储并开始新的段
                    segments.append(current_segment_ids)
                    current_segment_ids = [i]
                else:
                    # 否则，将ID添加到当前段
                    current_segment_ids.append(i)
            # 添加最后一个段的ID
            segments.append(current_segment_ids)
            total_time = 0.0
            for idx, segment_ids in enumerate(segments, start=1):
                print(f"Segment {idx} IDs:", segment_ids)
                total_time += timestamps[segment_ids[len(segment_ids) - 1]] - timestamps[segment_ids[0]]
            

            print(total_time)
            len_rate = total_time / (groundtruth_end_timestamp - groundtruth_start_timestamp)
        except Exception as e:
            print("task result traj error")
            return 0.0
    
    return len_rate


def CheckTask(mappingtaskID):
    mappingtask = MappingTask.query.get(mappingtaskID)
    finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID)+"/finished")
    if Path(finished_path).is_file():
        print(finished_path)
        mappingtask.state = "Finished"

        traj_flag_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID) ,"traj_flag.txt")
        with open(traj_flag_path, 'r') as f:
            text = f.read()
            if text == "True":
                mappingtask.trajectory_state = "Success"
            else :
                mappingtask.trajectory_state = "Unsuccess"


            # add performance data to mysql
        usage_info = extract_usage_info_single(mappingtaskID)

        sub_performanceresults = PerformanceResults(
            mappingTask_id = mappingtaskID,
            max_cpu = usage_info['max_cpu'],
            mean_cpu = usage_info['mean_cpu'],
            max_ram = usage_info['max_ram']
        )
        db.session.add(sub_performanceresults)
        # mappingtask.performanceresults.append(sub_performanceresults)
        mappingtask.performanceresults = sub_performanceresults
        
        
        # trajectory length
        # print("type of mappingtask ID----------------------------:", type(mappingtaskID))
        # print(type(mappingtask.id)) # 看看类型是否相同
        len_rate = calculate_traj_len(mappingtaskID)
        mappingtask.traj_length = len_rate

        
        db.session.commit()

        print('[MappingTask ID: '+str(mappingtaskID)+'] finished!')
        scheduler.remove_job(str(mappingtaskID))
        #push state to the frontend
        socketio.emit('update_state', {'data': 'Mapping task ' + str(mappingtaskID) +' is finished!'})
    else : 
        print('[MappingTask ID '+str(mappingtaskID)+'] is running...')

def CheckTask_single(mappingtaskID):
    mappingtask = MappingTask.query.get(mappingtaskID)
    finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID)+"/finished")
    if Path(finished_path).is_file():
        print(finished_path)
        mappingtask.state = "Finished"

        traj_flag_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID) ,"traj_flag.txt")
        with open(traj_flag_path, 'r') as f:
            text = f.read()
            if text == "True":
                mappingtask.trajectory_state = "Success"
            else :
                mappingtask.trajectory_state = "Unsuccess"

            # 同时读取cpu文件
            cpu_info_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID) ,"cpu_info.txt")
            # 
            with open(cpu_info_path, 'r') as f:
                text = f.read()
                CPU_type = text.split("\n")[0].split(":")[1]
                CPU_cores = text.split("\n")[1].split(":")[1]
                # 写入数据库中
                mappingtask.CPU_type = CPU_type
                mappingtask.CPU_cores = CPU_cores

            # add performance data to mysql
        usage_info = extract_usage_info_single(mappingtaskID)

        sub_performanceresults = PerformanceResults(
            mappingTask_id = mappingtaskID,
            max_cpu = usage_info['max_cpu'],
            mean_cpu = usage_info['mean_cpu'],
            max_ram = usage_info['max_ram']
        )

        db.session.add(sub_performanceresults)
        # mappingtask.performanceresults.append(sub_performanceresults)
        mappingtask.performanceresults = sub_performanceresults

        # lenght rate
        mappingtask.traj_length = calculate_traj_len(mappingtaskID)

        db.session.commit()

        print('[MappingTask ID: '+str(mappingtaskID)+'] finished!')
        scheduler.remove_job(str(mappingtaskID))
        #push state to the frontend
        socketio.emit('update_state', {'data': 'Mapping task ' + str(mappingtaskID) +' is finished!'})
    else : 
        print('[MappingTask ID '+str(mappingtaskID)+'] is running...')

def CheckTask_batch(batchmappingtaskId, mappingtaskIdList, container_number):
    mappingtask_list = []
    for i in range(container_number):
        mappingtask_list.append(MappingTask.query.get(mappingtaskIdList[i]))
    # 需要逐一判断每个文件夹内是否有finished
    now_finished_number = 0
    print("check...")
    for now_number in range(container_number):
        finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], mappingtaskIdList[now_number],"finished")
        usage_finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'],mappingtaskIdList[now_number],"usage_finished")
        if Path(finished_path).is_file() and Path(usage_finished_path).is_file():
            now_finished_number+=1
            if mappingtask_list[now_number].state == "Finished":
                continue
            mappingtask_list[now_number].state = "Finished"
            db.session.commit()
            usage_info = extract_usage_info_single(mappingtaskIdList[now_number])

            traj_flag_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_list[now_number].id) ,"traj_flag.txt")
            with open(traj_flag_path, 'r') as f:
                text = f.read()
                if text == "True":
                    mappingtask_list[now_number].trajectory_state = "Success"
                else :
                    mappingtask_list[now_number].trajectory_state = "Unsuccess"


            # 同时读取cpu文件
            cpu_info_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_list[now_number].id) ,"cpu_info.txt")
            # 
            with open(cpu_info_path, 'r') as f:
                text = f.read()
                CPU_type = text.split("\n")[0].split(":")[1]
                CPU_cores = text.split("\n")[1].split(":")[1]
                # 写入数据库中
                mappingtask_list[now_number].CPU_type = CPU_type
                mappingtask_list[now_number].CPU_cores = CPU_cores


            sub_performanceresults = PerformanceResults(
                mappingTask_id = mappingtaskIdList[now_number],
                max_cpu = usage_info['max_cpu'],
                mean_cpu = usage_info['mean_cpu'],
                max_ram = usage_info['max_ram']
            )
            db.session.add(sub_performanceresults)
            # mappingtask_list[now_number].performanceresults.append(sub_performanceresults)
            mappingtask_list[now_number].performanceresults = sub_performanceresults
            # mappingtask.performanceresults = sub_performanceresults

            mappingtask_list[now_number].traj_length = calculate_traj_len(mappingtask_list[now_number].id)

            db.session.commit()


            print(" --- task " + str(mappingtask_list[now_number].id) + " finished!")


    if now_finished_number == container_number:
        scheduler.remove_job("batch"+str(batchmappingtaskId))
        print('The mapping task is done!')
    else :
        print("finished number: " + str(now_finished_number))

## abort
# def CheckTask_combination(mappingtaskID, contianer_number):
#     mappingtask = MappingTask.query.get(mappingtaskID)
#     # 需要逐一判断每个文件夹内是否有finished
#     now_finished_number = 0
#     for now_number in range(contianer_number):
#         finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID),str(now_number),"finished")
#         usage_finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID),str(now_number),"usage_finished")
#         if Path(finished_path).is_file() and Path(usage_finished_path).is_file():
#             now_finished_number+=1
#     if now_finished_number == contianer_number:
#         mappingtask.state = "Finished"
#         db.session.commit()

#     # add performance data to mysql
#         for i in range(contianer_number):
#             usage_info = extract_usage_info_combination(mappingtaskID, i)

#             sub_performanceresults = PerformanceResults(
#                 mappingTask_id = mappingtaskID,
#                 max_cpu = usage_info['max_cpu'],
#                 mean_cpu = usage_info['mean_cpu'],
#                 max_ram = usage_info['max_ram']
#             )
#             db.session.add(sub_performanceresults)
#             mappingtask.performanceresults.append(sub_performanceresults)
#             # mappingtask.performanceresults = sub_performanceresults
#             db.session.commit()


#         print('[Combination MappingTask ID: '+str(mappingtaskID)+'] finished!')
#         scheduler.remove_job(str(mappingtaskID))
#         socketio.emit('update_state', {'data': 'Mapping task ' + str(mappingtaskID) +' is finished!'})
#     else :
#         print('[Combination MappingTask ID '+str(mappingtaskID)+'] is running...')
#         print("total substask number is:",contianer_number," now finished subtask number is:", now_finished_number)
#         print()


def extract_usage_info_single(mappingtask_id):
    import csv
    results_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_id))
    usage_csv_path = os.path.join(results_path, 'profiling.csv')
    with open(usage_csv_path, 'r') as f:
        reader = csv.reader(f)
        header_row = next(reader)
        time = []
        cpu = []
        ram = []
        total_cpu = 0
        N = 0
        for row in reader:
            time.append(float(row[0]))
            cpu.append(float(row[1]))
            ram.append(int(row[2])/(1024*1024))
            total_cpu += float(row[1])
            N += 1
    usage_info = {}
    usage_info["max_cpu"] = max(cpu)
    usage_info["mean_cpu"] = total_cpu/N
    usage_info["max_ram"] = max(ram)
    print(usage_info)
    return usage_info

def extract_usage_info_combination(mappingtask_id, sub_id):
    import csv
    results_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_id) + '/' + str(sub_id))
    usage_csv_path = os.path.join(results_path, 'profiling.csv')
    with open(usage_csv_path, 'r') as f:
        reader = csv.reader(f)
        header_row = next(reader)
        time = []
        cpu = []
        ram = []
        total_cpu = 0
        N = 0
        for row in reader:
            time.append(float(row[0]))
            cpu.append(float(row[1]))
            ram.append(int(row[2])/(1024*1024))
            total_cpu += float(row[1])
            N += 1
    usage_info = {}
    usage_info["max_cpu"] = max(cpu)
    usage_info["mean_cpu"] = total_cpu/N
    usage_info["max_ram"] = max(ram)
    print(usage_info)
    return usage_info

# TODO：修改代码：使得同一时刻只能有一个任务在执行（需要在创建任务的开始进行判断）
# 进一步修改：两次之间休眠一段时间
def RunMapping_batch_workstaion(configNameList, mappingtaskIDList):
    # bug：之前遇到的：同时启动多个jobs，会冲突（不知道为啥，这里直接规避）
    for i in range(len(configNameList)):
        # 更新数据库状态
        mappingtask = MappingTask.query.get(mappingtaskIDList[i])
        mappingtask.state = "Running"
        mappingtask.trajectory_state = "Running"
        db.session.add(mappingtask)
        db.session.commit()
        RunMapping(configNameList[i], mappingtaskIDList[i])

        # change
        # 测试一下
        time.sleep(5)
        print("------- sleep -----------")


        # 这里其实已经没有监控作用了，只是为了修改状态（由于上面提到的bug）
        scheduler.add_job(id=mappingtaskIDList[i], func=CheckTask, args=[mappingtaskIDList[i]], trigger="interval", seconds=3)

# 创建cadvisor（不需要了）
# 创建docker容器（修改成创建statefulset）
# configPath：yaml文件的名称
def RunMapping(configName, mappingtaskID):
    mapping_cadvisor.mapping_task(configName, mappingtaskID)
    print('The mapping task is done!')

# 相比原来：增加了container_number参数
    # container_number：algo个数

## abort
# def RunMapping_combination(configPath, mappingtaskID, container_number):
#     mapping_cadvisor.mapping_task_combination(configPath, mappingtaskID, container_number)
#     print("The combination mapping task is done!")
 
def RunMapping_single(configPath, mappingtaskID):
    mapping_cadvisor.mapping_task_single(configPath, mappingtaskID)
    print('The mapping task is done!')


def RunMapping_batch(config_filename_list, mappingtaskconfigIdList, mappingtaskIdList, mappingtask_number, batchMappingTask_id):
    mapping_cadvisor.mapping_task_batch(config_filename_list, mappingtaskconfigIdList, mappingtaskIdList, mappingtask_number, batchMappingTask_id)

def RunMapping_batch_aliyun(mappingtaskIdList, mappingtask_number, batchMappingTask_id, final_node_template, final_config_node, final_task_node, template_algo_dict, template_dataset_dict, template_number, node_number, aliyun_configuration):
    mapping_cadvisor.mapping_task_batch_aliyun(mappingtaskIdList, mappingtask_number, batchMappingTask_id, final_node_template, final_config_node, final_task_node, template_algo_dict, template_dataset_dict, template_number, node_number, aliyun_configuration)    

## mappingtask one in workstation
@app.route('/mappingtask/create/<int:id>', methods=['GET', 'POST'])
def create_mappingtask(id): 

    version = app.config['CURRENT_VERSION']
    if version != 'workstation':
        return abort(403)

    config = MappingTaskConfig.query.get(id)

    print(config.mappingTasks)

    if len(config.mappingTasks) == 1:
        return jsonify(result='exist')

    description = config.description
    state = 'Running'#To do: Check if the container is running
    time = datetime.now().replace(microsecond=0)

    cmd = "cat /proc/cpuinfo | grep 'model name' | sort | uniq | awk -F '[:]' '{print $2}'"
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    # 去除结果字符串前后的空白字符（包括换行符）
    cleaned_result = result.stdout.strip()
    # 存储结果到变量
    CPU_type = cleaned_result
    cmd = "cat /proc/cpuinfo | grep flags | grep ' lm ' | wc -l"
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    cleaned_result = result.stdout.strip()
    try:
        CPU_cores = int(cleaned_result)
    except Exception as e:
        CPU_cores = -1
    


    
    mappingtask = MappingTask(description=description, state=state, time=time, CPU_cores = CPU_cores, CPU_type = CPU_type)
    db.session.add(mappingtask)
    config.mappingTasks.append(mappingtask)
    db.session.commit()

    config_filename = str(id) + "_" + str(config.name) + ".yaml"
    mappingtask_id = mappingtask.id
    # mapping reusult存放的位置 需要修改
    mapping_result_dir = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_id))
    if not os.path.exists(mapping_result_dir):
        os.mkdir(mapping_result_dir)



    config_save_path = os.path.join(mapping_result_dir, config_filename)
    config_dict = generate_config_dict(id)
    # add algo and dataset attribute
    config_dict.update({"algorithm-attribute": config.algorithm.attribute})
    config_dict.update({"dataset-attribute": config.dataset.attribute})
    save_dict_to_yaml(config_dict, config_save_path)
    

    executor.submit(RunMapping, config_filename, str(mappingtask_id))
    # RunMapping(config_filename, str(mappingtask_id))
    scheduler.add_job(id=str(mappingtask_id), func=CheckTask, args=[mappingtask_id], trigger="interval", seconds=3)
    # return redirect(url_for('index_mappingtask'))
    return jsonify(result='success')

## mappingtask one in workstation fake
@app.route('/mappingtask/create/fake/<int:id>', methods=['GET', 'POST'])
def create_mappingtask_fake(id): 
    
    # # 遍历所有mapping task
    # mappingtasks = MappingTask.query.order_by(MappingTask.id.desc()).all()
    # for mappingtask in mappingtasks:
    #     print("-----")
    #     if mappingtask.trajectory_state == "Unsuccess":
    #         mappingtask.traj_length = 0.0
    #     else:
    #         mappingtask.traj_length = calculate_traj_len(mappingtask.id)
    # db.session.commit()

    # return 


    version = app.config['CURRENT_VERSION']
    if version != 'workstation':
        return abort(403)

    config = MappingTaskConfig.query.get(id)

    print(config.mappingTasks)

    description = config.description
    state = 'Running'#To do: Check if the container is running
    time = datetime.now().replace(microsecond=0)
    
    cmd = "cat /proc/cpuinfo | grep 'model name' | sort | uniq | awk -F '[:]' '{print $2}'"
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    # 去除结果字符串前后的空白字符（包括换行符）
    cleaned_result = result.stdout.strip()
    # 存储结果到变量
    CPU_type = cleaned_result
    cmd = "cat /proc/cpuinfo | grep flags | grep ' lm ' | wc -l"
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    cleaned_result = result.stdout.strip()
    try:
        CPU_cores = int(cleaned_result)
    except Exception as e:
        CPU_cores = -1
    
    
    mappingtask = MappingTask(description=description, state=state, time=time, CPU_cores = CPU_cores, CPU_type = CPU_type)

    
    db.session.add(mappingtask)
    config.mappingTasks.append(mappingtask)
    db.session.commit()

    config_filename = str(id) + "_" + str(config.name) + ".yaml"
    mappingtask_id = mappingtask.id
    # mapping reusult存放的位置 需要修改
    mapping_result_dir = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_id))
    if not os.path.exists(mapping_result_dir):
        os.mkdir(mapping_result_dir)



    config_save_path = os.path.join(mapping_result_dir, config_filename)
    config_dict = generate_config_dict(id)
    config_dict.update({"algorithm-attribute": config.algorithm.attribute})
    config_dict.update({"dataset-attribute": config.dataset.attribute})
    save_dict_to_yaml(config_dict, config_save_path)
    

    executor.submit(RunMapping, config_filename, str(mappingtask_id))
    # RunMapping(config_filename, str(mappingtask_id))
    scheduler.add_job(id=str(mappingtask_id), func=CheckTask, args=[mappingtask_id], trigger="interval", seconds=3)
    return jsonify(result='success')


## mappingtask one in cluster
@app.route('/mappingtask/create/single/<int:id>', methods=['GET', 'POST'])
def create_single_mappingtask(id): 

    version = app.config['CURRENT_VERSION']
    if version != 'cluster':
        return abort(403)

    config = MappingTaskConfig.query.get(id)

    print(config.mappingTasks)

    if len(config.mappingTasks) == 1:
        return jsonify(result='exist')

    description = config.description
    state = 'Running'#To do: Check if the container is running
    time = datetime.now().replace(microsecond=0)
       
    
    mappingtask = MappingTask(description=description, state=state, time=time, CPU_cores = CPU_cores, CPU_type = CPU_type)
    db.session.add(mappingtask)
    config.mappingTasks.append(mappingtask)
    db.session.commit()

    config_filename = str(id) + "_" + str(config.name) + ".yaml"
    mappingtask_id = mappingtask.id
    # mapping reusult存放的位置 需要修改
    mapping_result_dir = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_id))
    if not os.path.exists(mapping_result_dir):
        os.mkdir(mapping_result_dir)



    config_save_path = os.path.join(mapping_result_dir, config_filename)
    config_dict = generate_config_dict(id)
    config_dict.update({"algorithm-attribute": config.algorithm.attribute})
    config_dict.update({"dataset-attribute": config.dataset.attribute})
    save_dict_to_yaml(config_dict, config_save_path)
    

    executor.submit(RunMapping_single, config_filename, str(mappingtask_id))
    # RunMapping_single(config_filename, str(mappingtask_id))
    scheduler.add_job(id=str(mappingtask_id), func=CheckTask_single, args=[mappingtask_id], trigger="interval", seconds=3)
    return redirect(url_for('index_mappingtask'))

## mappingtask one in cluster fake
@app.route('/mappingtask/create/single/fake/<int:id>', methods=['GET', 'POST'])
def create_single_mappingtask_fake(id): 

    version = app.config['CURRENT_VERSION']
    if version != 'cluster':
        return abort(403)
    
    config = MappingTaskConfig.query.get(id)

    print(config.mappingTasks)


    description = config.description
    state = 'Running'#To do: Check if the container is running
    time = datetime.now().replace(microsecond=0)
    
    
    mappingtask = MappingTask(description=description, state=state, time=time, CPU_cores = CPU_cores, CPU_type = CPU_type)
    db.session.add(mappingtask)
    config.mappingTasks.append(mappingtask)
    db.session.commit()

    config_filename = str(id) + "_" + str(config.name) + ".yaml"
    mappingtask_id = mappingtask.id
    # mapping reusult存放的位置 需要修改
    mapping_result_dir = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_id))
    if not os.path.exists(mapping_result_dir):
        os.mkdir(mapping_result_dir)



    config_save_path = os.path.join(mapping_result_dir, config_filename)
    config_dict = generate_config_dict(id)
    config_dict.update({"algorithm-attribute": config.algorithm.attribute})
    config_dict.update({"dataset-attribute": config.dataset.attribute})
    save_dict_to_yaml(config_dict, config_save_path)
    

    executor.submit(RunMapping_single, config_filename, str(mappingtask_id))
    # RunMapping_single(config_filename, str(mappingtask_id))
    scheduler.add_job(id=str(mappingtask_id), func=CheckTask_single, args=[mappingtask_id], trigger="interval", seconds=3)
    return redirect(url_for('index_mappingtask'))

## 今天任务：把这个写完并且测试
## 把一些其他小玩意写完
## 开始egeneral或者u建图的

##### changed； 我觉得是ok的

@app.route('/mappingtask/create/batch/workstation', methods=['GET', 'POST'])
def create_batch_mappingtask_workstation():

    version = app.config['CURRENT_VERSION']
    if version != 'workstation':
        return abort(403)

    data = json.loads(request.get_data())
    print(data)
    mappingtaskconfigIdList = []
    for value in data.values():
        # 需要提前判断config是否有重复

        # 现在可以重复了（重复了认为是fake task）
        # if len(MappingTaskConfig.query.get(value["parameterID"]).mappingTasks) != 0:
        #     continue
        # 好像改了这一个地方 就ok了
        mappingtaskconfigIdList.append(value["parameterID"])
    # mappingtask_number已经剔除了不合法的config
    print(mappingtaskconfigIdList)
    mappingtask_number = len(mappingtaskconfigIdList)
    ## create a batch mappingtask
    ## 对于workstation，不需要batch mappingtask来提供整体信息了

    config_filename_list = []
    mappingtaskIdList = []

    for i in range(mappingtask_number):

        config = MappingTaskConfig.query.get(mappingtaskconfigIdList[i])
        description = config.description
        state = 'Waiting'
        trajectory_state = 'Waiting'
        time = datetime.now().replace(microsecond=0)
# cmd = "cat /proc/cpuinfo | grep name | cut -f2 -d: | uniq -c"
        cmd = "cat /proc/cpuinfo | grep 'model name' | sort | uniq | awk -F '[:]' '{print $2}'"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        # 去除结果字符串前后的空白字符（包括换行符）
        cleaned_result = result.stdout.strip()
        # 存储结果到变量
        CPU_type = cleaned_result
        cmd = "cat /proc/cpuinfo | grep flags | grep ' lm ' | wc -l"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        cleaned_result = result.stdout.strip()
        try:
            CPU_cores = int(cleaned_result)
        except Exception as e:
            CPU_cores = -1
    
    
        mappingtask = MappingTask(description=description, state=state, time=time,trajectory_state = trajectory_state, CPU_cores = CPU_cores, CPU_type = CPU_type)

        db.session.add(mappingtask)
        config.mappingTasks.append(mappingtask)
        db.session.commit()

        config_filename = str(mappingtaskconfigIdList[i]) + "_" + str(config.name) + ".yaml"
        config_filename_list.append(config_filename)
        mappingtask_id = mappingtask.id 
        mappingtaskIdList.append(str(mappingtask_id))
        mapping_result_dir = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_id))

        if not os.path.exists(mapping_result_dir):
            os.mkdir(mapping_result_dir)

        config_save_path = os.path.join(mapping_result_dir, config_filename)
        config_dict = generate_config_dict(mappingtaskconfigIdList[i])
        config_dict.update({"algorithm-attribute": config.algorithm.attribute})
        config_dict.update({"dataset-attribute": config.dataset.attribute})
        save_dict_to_yaml(config_dict, config_save_path)




    ####################################################################
    ## (config_filename_list, batch_mappingtask_id, mappingtask_number)
    ####################################################################

    # 需要多次执行RunMapping

    ## executor.submit(RunMapping_batch, config_filename, mappingtaskconfigIdList, mappingtask_number, batchMappingTask_id)

    # executor
    # executor.submit(RunMapping_batch, config_filename_list, mappingtaskconfigIdList, mappingtaskIdList, mappingtask_number, batchMappingTask_id)
    # # # RunMapping_batch(config_filename_list, mappingtaskconfigIdList, mappingtaskIdList, mappingtask_number, batchMappingTask_id)
    # scheduler.add_job(id = "batch" + str(batchMappingTask_id), func=CheckTask_batch, args=[batchMappingTask_id, mappingtaskIdList, mappingtask_number], trigger="interval", seconds=3)
    # return redirect(url_for('index_mappingtask'))  

    # 开一个线程，用来执行下面两个线程
    executor.submit(RunMapping_batch_workstaion, config_filename_list, mappingtaskIdList)

    # executor.submit(RunMapping, config_filename, str(mappingtask_id))
    # # RunMapping(config_filename, str(mappingtask_id))
    # scheduler.add_job(id=str(mappingtask_id), func=CheckTask, args=[mappingtask_id], trigger="interval", seconds=3)
    # return redirect(url_for('index_mappingtask'))
    return jsonify(result='success') 

# 2 change
# now can different algo or dataset(maybe don't need to change)
# change the transfer way
@app.route('/mappingtask/create/batch/cluster', methods=['GET', 'POST'])
def create_batch_mappingtask_cluster():

    version = app.config['CURRENT_VERSION']
    if version != 'cluster':
        return abort(403)

    data = json.loads(request.get_data())
    print(data)
    mappingtaskconfigIdList = []
    for value in data.values():
        # 需要提前判断config是否有重复
        # if len(MappingTaskConfig.query.get(value["parameterID"]).mappingTasks) != 0:
        #     continue
        mappingtaskconfigIdList.append(value["parameterID"])
    # mappingtask_number已经剔除了不合法的config
    print(mappingtaskconfigIdList)
    mappingtask_number = len(mappingtaskconfigIdList)
    ## create a batch mappingtask

    batchMappingTask = BatchMappingTask()
    db.session.add(batchMappingTask)
    db.session.commit()
    # print("id: ", batchMappingTask.id)
    # return redirect(url_for('index_mappingtask'))
    batchMappingTask_id = batchMappingTask.id
    #    batchMappingTask_id = 666  ##
    batchMappingTask_path = os.path.join(app.config['BATCHMAPPINGTASK_PATH'], str(batchMappingTask_id))
    if not os.path.exists(batchMappingTask_path):
        os.mkdir(batchMappingTask_path)
    batchMappingTask.path = batchMappingTask_path

    config_filename_list = []
    mappingtaskIdList = []

    for i in range(mappingtask_number):

        config = MappingTaskConfig.query.get(mappingtaskconfigIdList[i])
        description = config.description
        state = 'Running'
        time = datetime.now().replace(microsecond=0)
    
        mappingtask = MappingTask(description=description, state=state, time=time)
        db.session.add(mappingtask)
        config.mappingTasks.append(mappingtask)
        db.session.commit()

        config_filename = str(mappingtaskconfigIdList[i]) + "_" + str(config.name) + ".yaml"
        config_filename_list.append(config_filename)
        mappingtask_id = mappingtask.id 
        mappingtaskIdList.append(str(mappingtask_id))
        mapping_result_dir = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_id))

        if not os.path.exists(mapping_result_dir):
            os.mkdir(mapping_result_dir)

        config_save_path = os.path.join(mapping_result_dir, config_filename)
        config_dict = generate_config_dict(mappingtaskconfigIdList[i])
        config_dict.update({"algorithm-attribute": config.algorithm.attribute})
        config_dict.update({"dataset-attribute": config.dataset.attribute})
        save_dict_to_yaml(config_dict, config_save_path)
    batchMappingTask_subTask_path = os.path.join(batchMappingTask_path, "subTask.txt")
    batchMappingTask_subTask_file = open(batchMappingTask_subTask_path,'w')
    text_content = ''
    #e
    #########################################################
    ## make schedule to assign task                        ##
    ## notice: I know this way can not get the best assign ##
    #########################################################
    # TODO optical the assign way
    node_number = app.config['CLUSTER_WORK_NODE_NUMBER']
    task_number = mappingtask_number
    assign_number = 0
    MAX_TASK_NUMBER = task_number / node_number + 1
    #1. check number of assignment
    ## (algorithm_id, dataset_id)
    assign_set = set()
    config_list = []
    for i in range(task_number):
        config = MappingTaskConfig.query.get(mappingtaskconfigIdList[i])
        assign_set.add((config.algorithm.id, config.dataset.id))
        config_list.append(config)
    # print(assign_set)
    assign_algo_list = []
    assign_dataset_list = []
    assign_tasks = []
    for a in assign_set:
        assign_algo_list.append(a[0])
        assign_dataset_list.append(a[1])
        assign_tasks.append([])
    # for i in range(len(assign_algo_list)):
    #     print(assign_algo_list[i], assign_dataset_list[i])
    assign_number = len(assign_algo_list)

    # 2. check task belong to which assign
    for i in range(task_number):
        for j in range(assign_number):
            if assign_algo_list[j] == config_list[i].algorithm.id and assign_dataset_list[j] == config_list[i].dataset.id:
                assign_tasks[j].append(config_list[i])
    print(assign_tasks)
    
    # 3. assign task to each node
    node_tasks = []
    for i in range(node_number):
        node_tasks.append([])

    assign_level = 0
    while True:
        check_number = 0
        for i in range(assign_number):
            if assign_level < len(assign_tasks[i]):
                check_number += 1
                # need to assign to node
                check_1 = False
                for j in range(node_number):
                    if len(node_tasks[j]) == 0:
                        node_tasks[j].append(assign_tasks[i][assign_level])
                        check_1 = True
                        break
                if not check_1:
                    # no node is empty
                    check_2 = False
                    for j in range(node_number):
                        if len(node_tasks[j]) >= MAX_TASK_NUMBER:
                            continue
                        for k in range(len(node_tasks[j])):
                            if assign_tasks[i][assign_level].algorithm.id == node_tasks[j][k].algorithm.id and assign_tasks[i][assign_level].dataset.id == node_tasks[j][k].dataset.id:
                                node_tasks[j].append(assign_tasks[i][assign_level])
                                check_2 = True
                                break
                        if check_2:
                            break
                    if not check_2:
                        # random assign
                        for j in range(node_number):
                            if len(node_tasks[j])  < MAX_TASK_NUMBER:
                                # 这样可能i会出现编号小的工作节点 工作时间多余其他j节点
                                # TODO
                                node_tasks[j].append(assign_tasks[i][assign_level])
                                break
        if check_number == 0:
            break
        assign_level += 1
    print(node_tasks)

            
    #return 0

    for i in range(node_number):
        for j in range(len(node_tasks[i]) - 1):
            text_content += str(node_tasks[i][j].id) + ','
        text_content += str(node_tasks[i][len(node_tasks[i]) - 1].id) + ';'
    text_content = text_content[:len(text_content)-1]
    text_content += "\n"

    for i in range(node_number):
        for j in range(len(node_tasks[i]) - 1):
            text_content += str(node_tasks[i][j].mappingTasks[0].id) + ','
            # text_content += str(node_tasks[i][j].id) + ','
        text_content += str(node_tasks[i][len(node_tasks[i]) - 1].mappingTasks[0].id) + ';'
        # text_content += str((node_tasks[i][len(node_tasks[i]) - 1].id)) + ';'
    text_content = text_content[:len(text_content)-1]

    batchMappingTask_subTask_file.write(text_content)
    batchMappingTask_subTask_file.close()

    ####################################################################
    ## (config_filename_list, batch_mappingtask_id, mappingtask_number)
    ####################################################################


    ## executor.submit(RunMapping_batch, config_filename, mappingtaskconfigIdList, mappingtask_number, batchMappingTask_id)
    executor.submit(RunMapping_batch, config_filename_list, mappingtaskconfigIdList, mappingtaskIdList, mappingtask_number, batchMappingTask_id)
    # # RunMapping_batch(config_filename_list, mappingtaskconfigIdList, mappingtaskIdList, mappingtask_number, batchMappingTask_id)
    scheduler.add_job(id = "batch" + str(batchMappingTask_id), func=CheckTask_batch, args=[batchMappingTask_id, mappingtaskIdList, mappingtask_number], trigger="interval", seconds=3)
    return redirect(url_for('index_mappingtask'))


# aliyun不设置 单独create
@app.route('/mappingtask/create/batch/aliyun', methods=['GET', 'POST'])
def create_batch_mappingtask_aliyun():

    version = app.config['CURRENT_VERSION']
    if version != 'aliyun':
        return abort(403)

    # mapping_cadvisor.mapping_task_batch_aliyun()
    data = json.loads(request.get_data())
    aliyun_configuration = data[str(len(data) - 1)]
    del data[str(len(data) - 1)]
    print(aliyun_configuration)
    print(data)
    # print(data)
    mappingtaskconfigIdList = []
    for value in data.values():
        # 需要提前判断config是否有重复

        ## 为了测试 先不做去重处理：要不凑不够例子 TO DELETE

    #S
        # if len(MappingTaskConfig.query.get(value["parameterID"]).mappingTasks) != 0:
        #     continue

    #E
        mappingtaskconfigIdList.append(value["parameterID"])
    # mappingtask_number已经剔除了不合法的config
    mappingtask_number = len(mappingtaskconfigIdList)
    ## create a batch mappingtask
    #S
    batchMappingTask = BatchMappingTask()
    db.session.add(batchMappingTask)
    db.session.commit()
    
    # print("id: ", batchMappingTask.id)
    # return redirect(url_for('index_mappingtask'))
    batchMappingTask_id = batchMappingTask.id
    batchMappingTask_path = os.path.join(app.config['BATCHMAPPINGTASK_PATH'], str(batchMappingTask_id))
    if not os.path.exists(batchMappingTask_path):
        os.mkdir(batchMappingTask_path)
    batchMappingTask.path = batchMappingTask_path

    # create config
    config_filename_list = []
    mappingtaskIdList = []

    for i in range(mappingtask_number):

        config = MappingTaskConfig.query.get(mappingtaskconfigIdList[i])
        description = config.description
        state = 'Running'
        time = datetime.now().replace(microsecond=0)
    
        mappingtask = MappingTask(description=description, state=state, time=time)
        db.session.add(mappingtask)
        config.mappingTasks.append(mappingtask)
        db.session.commit()

        config_filename = str(mappingtaskconfigIdList[i]) + "_" + str(config.name) + ".yaml"
        config_filename_list.append(config_filename)
        mappingtask_id = mappingtask.id 
        mappingtaskIdList.append(str(mappingtask_id))
        mapping_result_dir = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_id))

        if not os.path.exists(mapping_result_dir):
            os.mkdir(mapping_result_dir)

        config_save_path = os.path.join(mapping_result_dir, config_filename)
        config_dict = generate_config_dict(mappingtaskconfigIdList[i])
        config_dict.update({"algorithm-attribute": config.algorithm.attribute})
        config_dict.update({"dataset-attribute": config.dataset.attribute})
        save_dict_to_yaml(config_dict, config_save_path)
    #E

    task_number = mappingtask_number
    node_number = min(app.config['MAX_NODE_NUMBER'], int((task_number+1) / app.config['EXPECT_EACH_NODE_TASK_NUMBER']))
    print("node number:", node_number)
    # 例子：18个task, 9个node
    # 统计n共有多少个族k，以及每个族的task和个数
    assign_number = 0
    #1. check number of assignment
    ## (algorithm_id, dataset_id)
    assign_set = set()
    config_list = []
    for i in range(task_number):
        config = MappingTaskConfig.query.get(mappingtaskconfigIdList[i])
        assign_set.add((config.algorithm.id, config.dataset.id))
        config_list.append(config)
    # print(assign_set)
    assign_algo_list = []
    assign_dataset_list = []
    assign_tasks = []
    for a in assign_set:
        assign_algo_list.append(a[0])
        assign_dataset_list.append(a[1])
        assign_tasks.append([])
    # for i in range(len(assign_algo_list)):
    #     print(assign_algo_list[i], assign_dataset_list[i])
    assign_number = len(assign_algo_list)
    print("assign_number: ", assign_number) # 分为4个类

    # 2. check task belong to which assign
    for i in range(task_number):
        for j in range(assign_number):
            if assign_algo_list[j] == config_list[i].algorithm.id and assign_dataset_list[j] == config_list[i].dataset.id:
                assign_tasks[j].append(config_list[i])
    # print(assign_tasks) # 每个类分别有哪些task
    class Assign:
        def __init__(self, assign_algo_id, assign_dataset_id, assign_task, algo_size, dataset_size):
            self.assign_algo_id = assign_algo_id
            self.assign_dataset_id = assign_dataset_id
            self.assign_task = assign_task
            self.assign_task_number = len(assign_task)
            self.algo_size = algo_size
            self.dataset_size = dataset_size
    Assigns = []

    ###############################
    ## get algo and dataset size ## TODO
    ###############################

    ## 先假设已经求得了size，n后面再补上
    for i in range(assign_number):
        # TODO 这里默认所有都一样
        Assigns.append(Assign(assign_algo_list[i], assign_dataset_list[i], assign_tasks[i], 1, 1))

        # Assigns.append(Assign(assign_algo_list[i], assign_dataset_list[i], assign_tasks[i], assign_number - i, assign_number - i))
    # 按照 resource size排序
    Assigns = sorted(Assigns, reverse=True, key=lambda x: x.algo_size + x.dataset_size)

    template_number = min(assign_number, node_number) + 1 # initialize
    last_template_number = 0
    template_assign_list = []
    last_template_assign_list = []
    template_size = []
    last_template_size = []
    while True:
        # a个template，将k个族依次分配，分配o完成后，check是否合法
        # 每一次迭代：template_number，清空template_assign_list，记录上一次的template_assign_list
        last_template_assign_list = template_assign_list
        last_template_number = template_number
        last_template_size = template_size

        template_assign_list = []
        template_size = []
        template_number -= 1 # 依次-1
        for i in range(template_number):
            template_assign_list.append([])
            template_size.append(0)
        for i in range(assign_number):
            # print((Assigns[i].algo_size + Assigns[i].dataset_size))
            temp_template_sign = 0
            for j in range(template_number):
                if template_size[j] < template_size[temp_template_sign]:
                    temp_template_sign = j
            # 族i选择了template j
            template_size[temp_template_sign] += (Assigns[i].algo_size + Assigns[i].dataset_size)
            template_assign_list[temp_template_sign].append(Assigns[i])
        max_size = 0
        # print(template_size)
        for i in range(template_number):
            max_size = max(max_size, template_size[i])
        
        if(max_size > app.config['MAX_RESOURCE_SIZE_EACH_NODE']):
            # 本次迭代结果不能满足情况，返回上次的迭代结果
            template_number = last_template_number
            template_assign_list = last_template_assign_list
            template_size = last_template_size
            break
        if template_number == 1:
            # 意味着创建一个模版，模版包含所有task需要的静态资源，并且没有超过可以被传输的资源大小上限
            break
        
        # 本次迭代结果可行，则继续迭代
    # 迭代完成后：得到了template的数量：template_number，每个template所包含的族：template_assign_list，以及他们的size：template_size\
    print("template number: ", template_number)
    print(template_assign_list)
    print(template_size)
    
    final_task_node = {} # {task: node, task: node...}
    final_node_template = {} # {node: template,...}
    final_config_node = {} # {config: node, config: node...}
    # tremplate_assign_list [[Assign],[],...]: 
    temp_node_number = 0 # 这里可能会出现某个模版对应1个任务，因此四舍五入后分配了0个node（所以当有剩余node时，需要从小到大分配剩余node，从而填充0的tempalte）
    node_number_for_each_template = [] # 每个template有多少个node
    task_number_for_each_template = []
    for i in range(template_number):
        # 对第i个template，计算给他分配多少个node
        now_total_task_number = 0
        for j in range(len(template_assign_list[i])): # 第i个template，有j个族
            # 每个族有多少个task
            now_total_task_number += template_assign_list[i][j].assign_task_number
        now_node_number = int((now_total_task_number / task_number) * node_number)
        node_number_for_each_template.append(now_node_number)
        task_number_for_each_template.append(now_total_task_number)
        temp_node_number += now_node_number
    while temp_node_number < node_number:
        need_add_template_index = 0
        for i in range(template_number):
            if node_number_for_each_template[i] < node_number_for_each_template[need_add_template_index]:
                need_add_template_index = i

        node_number_for_each_template[need_add_template_index] += 1
        temp_node_number += 1
    # 现在知道了每个template对应多少个node，现在分配具体的node编号
    temp_index = 0
    for i in range(template_number):
        for j in range(node_number_for_each_template[i]):
            final_node_template.update({temp_index: i}) #########################################
            temp_index += 1

    print("node_number_for_each_template: ", node_number_for_each_template)
    print("task_number_for_each_template: ", task_number_for_each_template)

    node_start_index = 0
    for i in range(template_number):
        temp_node_number = node_number_for_each_template[i] # 每个template有多少个node
        temp_task_number = task_number_for_each_template[i]
        # 怎么拿到每一个task
        # template_assign_list[i][j].assign_task[0...].mappingTasks[0].id task的id
        # 计算每个node应该分配多少个task
        have_assign_number = 0
        task_number_for_each_node = []
        for j in range(temp_node_number):
            task_number_for_each_node.append(int(temp_task_number/temp_node_number))
            have_assign_number += int(temp_task_number/temp_node_number)
        # 可能没有分配完
        temp_index = 0
        while have_assign_number < temp_task_number:
            task_number_for_each_node[temp_index % temp_node_number] += 1
            have_assign_number += 1
            temp_index += 1
        # 现在知道了应该给每个节点分配多少个任务了
        task_number_for_each_node_add = []
        task_number_for_each_node_add.append(task_number_for_each_node[0])
        for j in range(temp_node_number):
            if j == 0:
                continue
            task_number_for_each_node_add.append(task_number_for_each_node[j] + task_number_for_each_node_add[j-1])
        # print(task_number_for_each_node_add[0])

        temp_index = 0
        for j in range(len(template_assign_list[i])):
            for k in range(len(template_assign_list[i][j].assign_task)):
    # s
                now_task_id = template_assign_list[i][j].assign_task[k].mappingTasks[0].id
    # e
                # now_task_id = 0 # TO DELETE
                now_config_id = template_assign_list[i][j].assign_task[k].id
                #判断一下temp_index属于哪个node
                temp_node_index = 0
                # print(temp_index)
                while temp_index >= task_number_for_each_node_add[temp_node_index]:
                    temp_node_index += 1
                final_task_node.update({now_task_id: temp_node_index + node_start_index}) ###########################################
                final_config_node.update({now_config_id: temp_node_index + node_start_index})
                temp_index += 1
        node_start_index += temp_node_index + 1
    print(final_config_node)
    print(final_task_node)
    print(final_node_template)
    print(template_assign_list)
    
    ## 应该是正确的




    # batchMappingTask_path = os.path.join(app.config['BATCHMAPPINGTASK_PATH'], str(9999))

    batchMappingTask_subTask_path = os.path.join(batchMappingTask_path, "subTask_Aliyun.yaml")
    batchMappingTask_subTask_file = open(batchMappingTask_subTask_path,'w')
    text_content = ''
    # for i in range(mappingtask_number - 1):
    #     text_content += mappingtaskconfigIdList[i] + ','
    # text_content += mappingtaskconfigIdList[mappingtask_number - 1] + '\n'
    # for i in range(mappingtask_number - 1):
    #     text_content += mappingtaskIdList[i] + ','
    # text_content += mappingtaskIdList[mappingtask_number - 1]
    text_json_dict = {}
    text_json_dict.update({"node_template": final_node_template})
    text_json_dict.update({"config_node": final_config_node})
    text_json_dict.update({"task_node": final_task_node})

    batchMappingTask_subTask_file.write(yaml.dump(text_json_dict, indent = 2))
    batchMappingTask_subTask_file.close()

    # 还应该直到每个template需要哪些algo + dataset
    template_algo_dict = {}
    for i in range(template_number):
        value = []
        key = i
        value_set = set()
        for j in range(len(template_assign_list[i])):
            value_set.add(template_assign_list[i][j].assign_algo_id)
        for v in value_set:
            value.append(v)
        template_algo_dict.update({key: value})
    template_dataset_dict = {}
    for i in range(template_number):
        value = []
        key = i
        value_set = set()
        for j in range(len(template_assign_list[i])):
            value_set.add(template_assign_list[i][j].assign_dataset_id)
        for v in value_set:
            value.append(v)
        template_dataset_dict.update({key: value})
    
    print("template_algo_dict:", template_algo_dict)
    print("tempalte_dataset_dict:", template_dataset_dict)
    # return ???????????????????/

    ####################################################################
    ## (config_filename_list, batch_mappingtask_id, mappingtask_number)
    ####################################################################

    ## executor.submit(RunMapping_batch, config_filename, mappingtaskconfigIdList, mappingtask_number, batchMappingTask_id)
    # executor.submit(RunMapping_batch, config_filename_list, mappingtaskconfigIdList, mappingtaskIdList, mappingtask_number, batchMappingTask_id)
    # TO DELETE
    # 测试：创建一个id全为999的task list
    # mappingtaskIdList = []
    # for i in range(task_number):
    #     mappingtaskIdList.append(999)
    # RunMapping_batch_aliyun(mappingtaskIdList, mappingtask_number, batchMappingTask_id, final_node_template, final_config_node, final_task_node, template_algo_dict, template_dataset_dict, template_number, node_number, aliyun_configuration)
    
    executor.submit(RunMapping_batch_aliyun, mappingtaskIdList, mappingtask_number, batchMappingTask_id, final_node_template, final_config_node, final_task_node, template_algo_dict, template_dataset_dict, template_number, node_number, aliyun_configuration)
    #s    
    scheduler.add_job(id = "batch" + str(batchMappingTask_id), func=CheckTask_batch, args=[batchMappingTask_id, mappingtaskIdList, mappingtask_number], trigger="interval", seconds=3)
    return redirect(url_for('index_mappingtask'))
    #e  
    return 


## abort
# 创建combination mapping task
# @app.route('/mappingtask/create_combination/<int:id>', methods=['GET', 'POST'])
# def create_combination_mappingtask(id):
#     config = MappingTaskConfig.query.get(id)
#     # print("config: " , config.id," ", config.name)
#     description = config.description
#     # print("config description: ", description)
#     state = 'Running'#To do: Check if the container is running
#     time = datetime.now().replace(microsecond=0)
    
#     # 先不提交任务
# #######################################################################################################
#     mappingtask = MappingTask(description=description, state=state, time=time)
#     db.session.add(mappingtask)
#     config.mappingTasks.append(mappingtask)
#     db.session.commit()
# #######################################################################################################
#     config_filename = str(id) + "_" + str(config.name) + ".yaml"
#     # mappingtask_id = mappingtask.id
#     mappingtask_id = mappingtask.id #### 先人为规定一个，后续就按照之前的正常流程就可以
#     ############### mapping reusult存放的位置 需要修改

#     ##好像不需要在这里改动了
#     ##因为外面已经挂载好了
#     mapping_result_dir = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_id))
#      # 修改为clusternfs的路径
#      ## 注意这个id，后面创建statefulset的时候，要用到这个id
#     if not os.path.exists(mapping_result_dir):
#         os.mkdir(mapping_result_dir)

#      ######## 要生成若干个config文件，所以要先生成config文件数量的文件夹（从0开始命名），分别把config存储到对应的文件夹中
#     ##config_save_path = os.path.join(mapping_result_dir, config_filename)


#     ####### 解析对应的文件
#     ####### 修改该函数
#     # config_dict = generate_config_dict(id)
#     config_dict_combination = generate_config_dict_combination(id)
#     ########## 考虑save_path的问题
#     ### 实际情况：让该contianer挂载到clusternfs下的一个文件夹下；在那个文件夹下创建：34/0/.yaml  34/1/.yaml  ......
#     ### 目前测试：该项目已经挂载的目录：/slam_hive_results 挂载到了；所以可以先把这个文件夹

#     # 需要在mapping_result_dir 和 cofig_filename中间加一层
#     contianer_number =  save_dict_to_yaml_combination(config_dict_combination, mapping_result_dir, config_filename)
    
#     executor.submit(RunMapping_combination, config_filename, str(mappingtask_id), contianer_number)
#     # RunMapping_combination(config_filename, str(mappingtask_id), contianer_number)
#     ## scheduler.add_job(id=str(mappingtask_id), func=CheckTask_combination, args=[mappingtask_id, contianer_number], trigger="interval", seconds=3)
#     return redirect(url_for('index_mappingtask'))



@app.route('/mappingtask/index')
def index_mappingtask():
    form = DeleteMappingTaskForm()
    mappingtasks = MappingTask.query.order_by(MappingTask.id.desc()).all()
    algos = Algorithm.query.order_by(Algorithm.id.desc()).all()
    datasets = Dataset.query.order_by(Dataset.id.desc()).all()
    return render_template('/mappingtask/index.html', mappingtasks=mappingtasks, form=form, algos=algos, datasets=datasets, version=app.config['CURRENT_VERSION'])


@app.route('/mappingtask/<int:id>/delete', methods=['POST'])
def delete_mappingtask(id):

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    form = DeleteMappingTaskForm()
    if form.validate_on_submit():
        mappingtask = MappingTask.query.get(id)
        db.session.delete(mappingtask)
        db.session.commit()
    return redirect(url_for('index_mappingtask'))


## abort
## 不能显示实时
@app.route('/mappingtask/check_combination_task/<int:id>')
def check_combination_task_running(id):
    mappingtask = MappingTask.query.get(id)
    pod_flags, pod_infos, container_number, ready_number =  mapping_cadvisor.check_combination_task_running_k8s(id)


    # for i in range(container_number):
    #     print(pod_infos[i].metadata.name)

    return render_template('/mappingtask/show_running_detail.html', pod_flags = pod_flags,
                                                                    pod_infos = pod_infos,
                                                                    container_number = container_number,
                                                                    ready_number = ready_number,
                                                                    task_id = id,
                                                                    mappingtask = mappingtask)










@app.route('/mappingtask/<int:id>/show', methods=['GET', 'POST'])
def show_mappingtask(id):
    imgfolder = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(id))
    mappingtask = MappingTask.query.get(id)
    config = mappingtask.mappingTaskConf
    
    # 返回mappingtask对象和config对象
    # 设置下载按钮
    # 设置跳转按钮（config）
    # 性能图片
    # 显示mapping

    map_flag = False
    map_path = app.config['MAPPING_RESULTS_PATH'] + "/" + str(id) + "/Map.pcd"

    if os.path.exists(map_path):
        map_flag = True


    mapping_result_folder = str(id)
    config_filename = str(mappingtask.mappingTaskConf.id) + '_' + mappingtask.mappingTaskConf.name + '.yaml'
    config_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/' + config_filename)
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.load(f, Loader=yaml.FullLoader)
    usage_ram_img = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/profiling_ram.png')
    usage_cpu_img = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/profiling_cpu.png')
    mapping_usage_img_list = [usage_ram_img, usage_cpu_img]
    # print(usage_ram_img)
    usage_info = extract_usage_info_single(mappingtask.id)



    # 遍历路径，查看是否有叫 grid.png的
    grid_flag = False
    grid_path = app.config['MAPPING_RESULTS_PATH'] + "/" + str(id) + "/grid.png"

    if os.path.exists(grid_path):
        grid_flag = True

    # 需要判断是否进行了evaluation
    check_evaluation = True
    if mappingtask.evaluation is None:
        check_evaluation = False



    return render_template('/mappingtask/show.html', config_dict = config_dict, 
                                                    mapping_usage_img_list=mapping_usage_img_list, 
                                                    usage_info=usage_info,
                                                    mappingtask = mappingtask,
                                                    config = config,
                                                    map_flag = map_flag,
                                                    grid_flag = grid_flag,
                                                    check_evaluation = check_evaluation
                                                    )


def zipDir(dirpath, outFullName):
    """
    压缩指定文件夹
    :param dirpath: 目标文件夹路径
    :param outFullName: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath, '')
 
        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()

@app.route('/mappingtask/download_single/<int:id>')
def download_mappingtask_single(id):
    download_folder_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(id))
    download_zip_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], "mappingtask_" + str(id) + ".zip")
    if os.path.exists(download_zip_path):
        return send_from_directory(app.config['MAPPING_RESULTS_PATH'], "mappingtask_" + str(id) + ".zip", as_attachment=True)
    else:
        zipDir(download_folder_path, download_zip_path)
        return send_from_directory(app.config['MAPPING_RESULTS_PATH'], "mappingtask_" + str(id) + ".zip", as_attachment=True)


@app.route('/mappingtask/<int:id>/show_map', methods=['GET', 'POST'])
def show_mappingtask_map(id):
    mappingtask = MappingTask.query.get(id)
    map_path = "/static/mapping_results/" + str(id) + "/Map.pcd"
    map_path1 = app.config['MAPPING_RESULTS_PATH'] + "/" + str(id) + "/Map.pcd"
    if os.path.exists(map_path1):
        return render_template('/mappingtask/show_map.html', map_path = map_path, mappingtask = mappingtask)
    else :
        return show_mappingtask(id) 

    # config = mappingtask.mappingTaskConf
    
    # # 返回mappingtask对象和config对象
    # # 设置下载按钮
    # # 设置跳转按钮（config）
    # # 性能图片
    # # 显示mapping


    # mapping_result_folder = str(id)
    # config_filename = str(mappingtask.mappingTaskConf.id) + '_' + mappingtask.mappingTaskConf.name + '.yaml'
    # config_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/' + config_filename)
    # with open(config_path, 'r', encoding='utf-8') as f:
    #     config_dict = yaml.load(f, Loader=yaml.FullLoader)
    # usage_ram_img = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/profiling_ram.png')
    # usage_cpu_img = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/profiling_cpu.png')
    # mapping_usage_img_list = [usage_ram_img, usage_cpu_img]
    # # print(usage_ram_img)
    # usage_info = extract_usage_info_single(mappingtask.id)
    # return render_template('/mappingtask/show.html', config_dict = config_dict, 
    #                                                 mapping_usage_img_list=mapping_usage_img_list, 
    #                                                 usage_info=usage_info,
    #                                                 mappingtask = mappingtask,
    #                                                 config = config
    #                                                 )


# @app.route('/mappingtask/<int:id>/get_map', methods=['GET', 'POST'])
# def show_mappingtask_map(id):
#     mappingtask = MappingTask.query.get(id)
#     map_path = app.config['MAPPING_RESULTS_PATH'] + "/" + str(id) + "/Map.pcd"
#     if os.path.exists(map_path):
#         return render_template('/mappingtask/show_map.html', map_path = map_path, mappingtask = mappingtask)
#     else :
#         return show_mappingtask(id) 


@app.route('/mappingtask/search/submit', methods=['POST'])
def submit_search_configs_mappingtask():
    data = json.loads(request.get_data())
    # print(data)
    algo_flag = False
    algo_list = data['algo_list']
    if "All" in algo_list:
        algo_flag = True
    dataset_flag = False
    dataset_list = data['dataset_list']
    if "All" in dataset_list:
        dataset_flag = True
    
    raw_parameters = data['parameters']
    param_flag = False
    if raw_parameters.strip(" ") == "":
        param_flag = True
    
    parameters_list = raw_parameters.split("\n")

    
    suit_configs = []

    configs = MappingTaskConfig.query.order_by(MappingTaskConfig.id.desc()).all()
    for i in range(len(configs)):
        # algorithm
        if algo_flag == False:
            if str(configs[i].algorithm.id) not in algo_list:
                continue
        if dataset_flag == False:
            if str(configs[i].dataset.id) not in dataset_list:
                continue
        if param_flag == False:
            if not check_parameters_sql(parameters_list, configs[i]):
                continue
        suit_configs.append(configs[i])
    print(suit_configs)
    mappingTasks_number = {}
    for i in range(len(suit_configs)):
        mappingTasks_number.update({suit_configs[i].id: len(suit_configs[i].mappingTasks)})
    
    ret = []
    for i in range(len(suit_configs)):
        if len(suit_configs[i].mappingTasks) != 0:
            for task in suit_configs[i].mappingTasks:
                ret.append(task.id)
    
    # return jsonify(data=ret)
    print(ret)
    ret.sort() # reverse()

    return render_template('/mappingtask/search_result.html', tasks_id = ret)