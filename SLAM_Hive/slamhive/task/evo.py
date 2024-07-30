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

import docker, time, os
from slamhive.task.utils import *
from slamhive import app
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor

#用来多线程评测同一个combination task中的不同sub task
executor = ThreadPoolExecutor(10)


def evo_task(trajFolder, datasetName, evoId):
    # trajPath = os.path.join(app.config['MAPPING_RESULTS_PATH'], trajFolder + '/traj.txt')
    # groundtruth = os.path.join(app.config['DATASETS_PATH'], datasetName + "/groundtruth.txt")
    # resultPath = os.path.join(app.config['EVALUATION_RESULTS_PATH'], evoId)
    print("evo_task(trajFolder, datasetName, evoId):")
    # SLAM_HIVE_PATH = get_pkg_path()
    SLAM_HIVE_PATH = "/SLAM-Hive"
    print("SLAM_HIVE_PATH= " + SLAM_HIVE_PATH)
    trajPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_results/mapping_results/' + trajFolder + '/traj.txt')
    groundtruth = os.path.join(SLAM_HIVE_PATH, 'slam_hive_datasets/' + datasetName + "/groundtruth.txt")
    resultPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_results/evaluation_results/' + evoId)
    print(trajPath)
    print(groundtruth)
    print(resultPath)
    evo_container(trajPath, groundtruth, resultPath)

def evo_task_batch(trajFolder, datasetName, evoId, mappingtaskIdList):
    evo_number = len(trajFolder)

    print("evo_task(trajFolder, datasetName, evoId):")
    # SLAM_HIVE_PATH = get_pkg_path()
    SLAM_HIVE_PATH = "/SLAM-Hive"
    print("SLAM_HIVE_PATH= " + SLAM_HIVE_PATH)
    # 同时创建一个comparison task

    trajPaths = []

    # 获取trajFolder下的所有子目录的名称
    ## temp_trajPath = "/clusternfs/home/Combination_result/slam_hive_results/mapping_results/" + trajFolder
    root_trajPath = "/SLAM-Hive/slam_hive_results/mapping_results"
    for now_number in range(evo_number):
        trajPaths.append(os.path.join(root_trajPath, mappingtaskIdList[now_number], "traj.txt"))
    
    groundtruths = []
    root_groundtruth = "/SLAM-Hive/slam_hive_datasets"
    for now_number in range(evo_number):
        groundtruths.append(os.path.join("/SLAM-Hive/slam_hive_datasets", datasetName[now_number], 'groundtruth.txt'))

    resultPaths = []
    root_resultPath = "/SLAM-Hive/slam_hive_results/evaluation_results"

    
    sub_evo_flags = []
    for now_number in range(evo_number):
        resultPaths.append(os.path.join(root_resultPath, evoId[now_number]))

        traj_flagPath = app.config["MAPPING_RESULTS_PATH"] + "/" + trajFolder[now_number] + "/traj_flag.txt"
        f = open(traj_flagPath, 'r')
        content = f.read()
        f.close()
        if content == 'False':
            sub_evo_flags.append(False)
            # result_flagPath = app.config["EVALUATION_RESULTS_PATH"] + "/" + evoId + "/" + str(now_number) + "/flag.txt"
            # f = open(result_flagPath, 'w')
            # f.write("False")
            # f.close()
        else :
            sub_evo_flags.append(True)
            # result_flagPath = app.config["EVALUATION_RESULTS_PATH"] + "/" + evoId + "/" + str(now_number) + "/flag.txt"
            # f = open(result_flagPath, 'w')
            # f.write("True")
            # f.close() 

        
    
    print(trajPaths)
    print(groundtruths)
    print(resultPaths)


    for now_number in range(evo_number):
        if sub_evo_flags[now_number]:
            # evo_container(trajPath, groundtruth, resultPath)
            executor.submit(evo_container, trajPaths[now_number], groundtruths[now_number], resultPaths[now_number])

# assume the task trajectorys are all right
def evo_task_multi(multiEvaluation_id, mappingtaskIdList, evaluationIdList, datasetName):
    evo_number = len(mappingtaskIdList)

    print("evo_task(trajFolder, datasetName, evoId):")
    groundtruth = '/SLAM-Hive/slam_hive_datasets/' + datasetName + "/groundtruth.txt"

    resultPath = "/SLAM-Hive/slam_hive_results/multi_evaluation_results/" + str(multiEvaluation_id)
    
    successful_number = 0
    compared_total_flag = True
    sub_evo_flags = []
    for now_number in range(evo_number):
        # 同时判断mapping_results中的traj是否合法
        traj_flagPath = app.config["MAPPING_RESULTS_PATH"] + "/" + mappingtaskIdList[now_number] + "/traj_flag.txt"
        f = open(traj_flagPath, 'r')
        content = f.read()
        f.close()
        if content == 'False':
            sub_evo_flags.append(False)
            successful_number = successful_number
        else :
            sub_evo_flags.append(True)
            successful_number += 1
    if successful_number <  evo_number:
        # 并不是全部的子任务都有轨迹，所以compared/total会失败
        compared_total_flag = False
            
    print(resultPath)

    executor.submit(evo_compare_task_multi, resultPath, evo_number, mappingtaskIdList, evaluationIdList, sub_evo_flags, groundtruth)
    # evo_compare_task_combination(evoId, compare_list, compare_result_path, len(sub_dirs))

# def evo_certain_compare_combination(eval_id, sub_number):
#         # comparison task

#     ## compare_list: id列表
#     compare_list = []
#     for i in range(sub_number):
#         compare_list.append(i)

#     compare_result_path = "/clusternfs/home/Combination_result/slam_hive_results/evaluation_results/" + evoId + '/compared/total'
#     executor.submit(evo_compare_task_combination,evoId, compare_list, compare_result_path, len(sub_dirs))

def evo_task_combination(trajFolder, datasetName, evoId):


    # 同时创建一个comparison task

    # trajPath = os.path.join(app.config['MAPPING_RESULTS_PATH'], trajFolder + '/traj.txt')
    # groundtruth = os.path.join(app.config['DATASETS_PATH'], datasetName + "/groundtruth.txt")
    # resultPath = os.path.join(app.config['EVALUATION_RESULTS_PATH'], evoId)
    print("evo_task(trajFolder, datasetName, evoId):")

    # SLAM_HIVE_PATH = get_pkg_path()
    # print("SLAM_HIVE_PATH= " + SLAM_HIVE_PATH)
    # trajPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_results/mapping_results/' + trajFolder + '/traj.txt')
    # groundtruth = os.path.join(SLAM_HIVE_PATH, 'slam_hive_datasets/' + datasetName + "/groundtruth.txt")
    # resultPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_results/evaluation_results/' + evoId)
    trajPaths = []

    # 获取trajFolder下的所有子目录的名称
    ## temp_trajPath = "/clusternfs/home/Combination_result/slam_hive_results/mapping_results/" + trajFolder
    temp_trajPath = "/SLAM-Hive/slam_hive_results/mapping_results/" + trajFolder
    sub_dirs = os.listdir("/slam_hive_results/mapping_results/" + trajFolder)
    for now_number in range(len(sub_dirs)):
        trajPaths.append(temp_trajPath + "/" + str(now_number) + "/traj.txt")
    
    groundtruth = "/SLAM-Hive/slam_hive_datasets/" + datasetName + '/groundtruth.txt'

    resultPaths = []
    temp_resultPath = "/SLAM-Hive/slam_hive_results/evaluation_results/" + evoId

    
    successful_number = 0
    compared_total_flag = True
    sub_evo_flags = []
    for now_number in range(len(sub_dirs)):
        resultPaths.append(temp_resultPath + "/" + str(now_number))
        # 同时判断mapping_results中的traj是否合法
        traj_flagPath = app.config["MAPPING_RESULTS_PATH"] + "/" + trajFolder + "/" + str(now_number) + "/traj_flag.txt"
        f = open(traj_flagPath, 'r')
        content = f.read()
        f.close()
        if content == 'False':
            sub_evo_flags.append(False)
            successful_number = successful_number
            # result_flagPath = app.config["EVALUATION_RESULTS_PATH"] + "/" + evoId + "/" + str(now_number) + "/flag.txt"
            # f = open(result_flagPath, 'w')
            # f.write("False")
            # f.close()
        else :
            sub_evo_flags.append(True)
            successful_number += 1
            # result_flagPath = app.config["EVALUATION_RESULTS_PATH"] + "/" + evoId + "/" + str(now_number) + "/flag.txt"
            # f = open(result_flagPath, 'w')
            # f.write("True")
            # f.close() 
    if successful_number <  len(sub_dirs):
        # 并不是全部的子任务都有轨迹，所以compared/total会失败
        compared_total_flag = False
            

    
    print(temp_trajPath)
    print(groundtruth)
    print(temp_resultPath)






    for now_number in range(len(sub_dirs)):
        executor.submit(evo_container_combination, trajPaths[now_number], groundtruth, resultPaths[now_number], evoId, now_number, sub_evo_flags[now_number])

        # evo_container_combination(trajPaths[now_number], groundtruth, resultPaths[now_number], evoId, now_number, sub_evo_flags[now_number])

        # evo_container_combination(trajPaths[now_number], groundtruth, resultPaths[now_number])
        
        # print(trajPaths[now_number], groundtruth, resultPaths[now_number])

    # comparison task

    ## compare_list: id列表
    compare_list = []
    for i in range(len(sub_dirs)):
        if sub_evo_flags[i] == True:
            compare_list.append(i)

    compare_result_path = "/SLAM-Hive/slam_hive_results/evaluation_results/" + evoId + '/compared/total'
    executor.submit(evo_compare_task_combination,evoId, compare_list, compare_result_path, len(sub_dirs), compared_total_flag, "total")
    # evo_compare_task_combination(evoId, compare_list, compare_result_path, len(sub_dirs))

# def evo_certain_compare_combination(eval_id, sub_number):
#         # comparison task

#     ## compare_list: id列表
#     compare_list = []
#     for i in range(sub_number):
#         compare_list.append(i)

#     compare_result_path = "/clusternfs/home/Combination_result/slam_hive_results/evaluation_results/" + evoId + '/compared/total'
#     executor.submit(evo_compare_task_combination,evoId, compare_list, compare_result_path, len(sub_dirs))



def evo_certain_compare_combination(compare_list_str, evoId, sub_number):

    
    compare_list_temp = compare_list_str.split('-')
    compare_list = []
    for i in range(len(compare_list_temp)):
        
        compare_list.append(int(compare_list_temp[i]))

    compare_result_path = "/SLAM-Hive/slam_hive_results/evaluation_results/" + str(evoId) + '/compared/' + compare_list_str
    print(compare_result_path)
    # executor.submit(evo_compare_task_combination,evoId, compare_list, compare_result_path, sub_number)
    evo_compare_task_combination(str(evoId), compare_list, compare_result_path, sub_number, True, local_folder = compare_list_str)



def evo_container_combination(trajPath, groundtruth, resultPath, evoId, now_number, flag):


    if flag == False:
        client = docker.from_env()
        print("===========Start Container: [slam-hive-evaluation:evo_latex]===========")
        volume = {trajPath:{'bind':'/slamhive/traj.txt','mode':'ro'},
                groundtruth:{'bind':'/slamhive/groundtruth.tum','mode':'ro'},
                resultPath:{'bind':'/slamhive/result','mode':'rw'}}
        evo = client.containers.run("slam-hive-evaluation:evo_latex", command='/bin/bash', detach=True, tty=True, volumes=volume)

        print("========================Running EVO Task=========================")


    #     time.sleep(10)
    #     stop_evo = evo.exec_run('bash -c "source /opt/ros/noetic/setup.bash && rosnode kill -a"', tty=True, stream=True)
        evo.exec_run('bash -c "touch /slamhive/result/finished"')


            # 写入flag文件
        flagPath = app.config["EVALUATION_RESULTS_PATH"] + '/'  + evoId + "/" + str(now_number) + "/flag.txt"
        f = open(flagPath, 'w')
        f.write("False")
        f.close()
        print("=============== writing flag to", evoId,str(now_number), " False ================")



        time.sleep(0.1)
        evo.stop()
        evo.remove()
        print("=========================EVO Task Finished!=====================")
        
    else:
        client = docker.from_env()
        print("===========Start Container: [slam-hive-evaluation:evo_latex]===========")
        volume = {trajPath:{'bind':'/slamhive/traj.txt','mode':'ro'},
                groundtruth:{'bind':'/slamhive/groundtruth.tum','mode':'ro'},
                resultPath:{'bind':'/slamhive/result','mode':'rw'}}
        evo = client.containers.run("slam-hive-evaluation:evo_latex", command='/bin/bash', detach=True, tty=True, volumes=volume)

        print("========================Running EVO Task=========================")
        # evo_config = evo.exec_run('bash -c "evo_config set plot_usetex') ## need to install other package
        evo.exec_run('bash -c " evo_config set plot_seaborn_style darkgrid" ')
        evo_traj = evo.exec_run('bash -c "evo_traj tum \
                /slamhive/traj.txt \
                --ref /slamhive/groundtruth.tum \
                -as -v --full_check --plot_mode xyz \
                --save_plot /slamhive/result/traj"',
                tty=True, stream=True)
        evo_traj_pgf = evo.exec_run('bash -c "evo_traj tum \
                    /slamhive/traj.txt \
                    --ref /slamhive/groundtruth.tum \
                    -as -v --full_check --plot_mode xyz \
                    --save_plot /slamhive/result/traj.pgf"',
                    tty=True, stream=True)
        # command format reference-trajectory estimated-trajectory [options] 
        evo_ape = evo.exec_run('bash -c "evo_ape tum \
                /slamhive/groundtruth.tum \
                /slamhive/traj.txt \
                -as -v -r trans_part --plot_mode xyz \
                --save_plot /slamhive/result/ape \
                --save_result /slamhive/result/ape.zip"',
                tty=True, stream=True)
        evo_ape_pgf = evo.exec_run('bash -c "evo_ape tum \
                    /slamhive/groundtruth.tum \
                    /slamhive/traj.txt \
                    -as -v -r trans_part --plot_mode xyz \
                    --save_plot /slamhive/result/ape.pgf"',
                    tty=True, stream=True)
        # evo_rpe tum reference.txt estimate.txt --pose_relation angle_deg --delta 1 --delta_unit m
        evo_rpe = evo.exec_run('bash -c "evo_rpe tum \
                /slamhive/groundtruth.tum \
                /slamhive/traj.txt \
                -as -v -r trans_part --plot_mode xyz --all_pairs -d 1 -u m \
                --save_plot /slamhive/result/rpe \
                --save_result /slamhive/result/rpe.zip"',
                tty=True, stream=True)
        evo_rpe_pgf = evo.exec_run('bash -c "evo_rpe tum \
                    /slamhive/groundtruth.tum \
                    /slamhive/traj.txt \
                    -as -v -r trans_part --plot_mode xyz --all_pairs -d 1 -u m \
                    --save_plot /slamhive/result/rpe.pgf"',
                    tty=True, stream=True)
        total_completed_number = 0
        while True:
            try:
                # print(next(evo_traj).decode())
                print(next(evo_traj).decode())
                # next(play_exec)
            except StopIteration:
                break
        time.sleep(10)
    #     stop_evo = evo.exec_run('bash -c "source /opt/ros/noetic/setup.bash && rosnode kill -a"', tty=True, stream=True)
        evo.exec_run('bash -c "touch /slamhive/result/finished"')


            # 写入flag文件
        flagPath = app.config["EVALUATION_RESULTS_PATH"] + '/'  + evoId + "/" + str(now_number) + "/flag.txt"
        f = open(flagPath, 'w')
        f.write("True")
        f.close()
        print("=============== writing flag to", evoId,str(now_number), " True ================")



        time.sleep(0.1)
        evo.stop()
        evo.remove()
        print("=========================EVO Task Finished!=====================")

def evo_container(trajPath, groundtruth, resultPath):
    client = docker.from_env()
    print("===========Start Container: [slam-hive-evaluation:evo_latex]===========")
    volume = {trajPath:{'bind':'/slamhive/traj.txt','mode':'ro'},
            groundtruth:{'bind':'/slamhive/groundtruth.tum','mode':'ro'},
            resultPath:{'bind':'/slamhive/result','mode':'rw'}}
    evo = client.containers.run("slam-hive-evaluation:evo_latex", command='/bin/bash', detach=True, tty=True, volumes=volume)

    print("========================Running EVO Task=========================")
        # evo_config = evo.exec_run('bash -c "evo_config set plot_usetex') ## need to install other package
    # evo.exec_run("cd /slamhive/result")
    evo.exec_run('bash -c " evo_config set plot_seaborn_style darkgrid" ')
    evo_traj = evo.exec_run('bash -c "evo_traj tum \
            /slamhive/traj.txt \
            --ref /slamhive/groundtruth.tum \
            -as -v --full_check --plot_mode xyz \
            --save_as_tum --save_plot /slamhive/result/traj"',
            tty=True, stream=True)
    evo_traj_pgf = evo.exec_run('bash -c "evo_traj tum \
                /slamhive/traj.txt \
                --ref /slamhive/groundtruth.tum \
                -as -v --full_check --plot_mode xyz \
                --save_plot /slamhive/result/traj.pgf"',
                tty=True, stream=True)
    # command format reference-trajectory estimated-trajectory [options] 
    evo_ape = evo.exec_run('bash -c "evo_ape tum \
            /slamhive/groundtruth.tum \
            /slamhive/traj.txt \
            -as -v -r trans_part --plot_mode xyz \
            --save_plot /slamhive/result/ape \
            --save_result /slamhive/result/ape.zip"',
            tty=True, stream=True)
    evo_ape_pgf = evo.exec_run('bash -c "evo_ape tum \
                /slamhive/groundtruth.tum \
                /slamhive/traj.txt \
                -as -v -r trans_part --plot_mode xyz \
                --save_plot /slamhive/result/ape.pgf"',
                tty=True, stream=True)
    # evo_rpe tum reference.txt estimate.txt --pose_relation angle_deg --delta 1 --delta_unit m
    evo_rpe = evo.exec_run('bash -c "evo_rpe tum \
            /slamhive/groundtruth.tum \
            /slamhive/traj.txt \
            -as -v -r trans_part --plot_mode xyz --all_pairs -d 1 -u m \
            --save_plot /slamhive/result/rpe \
            --save_result /slamhive/result/rpe.zip"',
            tty=True, stream=True)
    evo_rpe_pgf = evo.exec_run('bash -c "evo_rpe tum \
                /slamhive/groundtruth.tum \
                /slamhive/traj.txt \
                -as -v -r trans_part --plot_mode xyz --all_pairs -d 1 -u m \
                --save_plot /slamhive/result/rpe.pgf"',
                tty=True, stream=True)
    while True:
        try:
            # print(next(evo_traj).decode())
            print(next(evo_traj).decode())
            # next(play_exec)
        except StopIteration:
            break
    time.sleep(10)
## ???????????????????????????????? 这个是为啥来着？？？？？？？？？？？？？？？？？？？？？？？？？？
    evo.exec_run('cp /traj.tum /slamhive/result/traj.tum')
    evo.exec_run('cp /groundtruth.tum /slamhive/result/groundtruth.tum')
#     stop_evo = evo.exec_run('bash -c "source /opt/ros/noetic/setup.bash && rosnode kill -a"', tty=True, stream=True)
    evo.exec_run('bash -c "touch /slamhive/result/finished"')
    time.sleep(0.1)
    evo.stop()
    evo.remove()
    print("=========================EVO Task Finished!=====================")


def evo_compare_task_combination(evoId, compare_list, compare_result_path, sub_number, compared_total_flag, local_folder):

    # 阻塞判断sub task是否完成
    while True:
        time.sleep(1)
        father_path = os.path.join(app.config['EVALUATION_RESULTS_PATH'], evoId)
        print("evo "+father_path, sub_number)
        finished_number = 0
        for now_number in range(sub_number):
            sub_path = father_path + "/" + str(now_number) +"/finished"
            if Path(sub_path).is_file():
                finished_number += 1
        if finished_number == sub_number:
            # 开始compared task
            break

    ape_path_list = []
    rpe_path_list = []
    for id in compare_list:
        # ape_path_list.append(os.path.join("/slamhive", str(evoId) + '/' + str(id) + "/ape.zip"))
        # rpe_path_list.append(os.path.join("/slamhive", str(evoId) + '/' + str(id) + "/rpe.zip"))
        ape_path_list.append(os.path.join("/" + str(id) + "/ape.zip"))
        rpe_path_list.append(os.path.join("/" + str(id) + "/rpe.zip"))
    ape_path_command = " ".join(ape_path_list)
    rpe_path_command = " ".join(rpe_path_list)
    # eval_results_path = app.config['EVALUATION_RESULTS_PATH']
    eval_results_path = "/SLAM-Hive/slam_hive_results/evaluation_results"
    evo_compare_container_combination(ape_path_command, rpe_path_command, eval_results_path, compare_result_path, evoId, sub_number, compared_total_flag, local_folder)

def evo_compare_task_multi(resultPath, evo_number, mappingtaskIdList, evaluationIdList, sub_evo_flags, groundtruth):
    ape_path_list = []
    rpe_path_list = []
    traj_path_list = []
    k = -1
    for id in mappingtaskIdList:
        k = k + 1
        # ape_path_list.append(os.path.join("/slamhive", str(evoId) + '/' + str(id) + "/ape.zip"))
        # rpe_path_list.append(os.path.join("/slamhive", str(evoId) + '/' + str(id) + "/rpe.zip"))
        ape_path_list.append(os.path.join(str(id) + "/ape.zip"))
        rpe_path_list.append(os.path.join(str(id) + "/rpe.zip"))
        import shutil
        shutil.copyfile(os.path.join("/slam_hive_results/mapping_results" ,str(id) + "/traj.txt"),os.path.join("/slam_hive_results/mapping_results" ,str(id) + "/traj_"+str(id)+".txt"))
        traj_path_list.append(os.path.join(str(id) + "/traj_"+str(id)+".txt"))
    ape_path_command = " ".join(ape_path_list)
    rpe_path_command = " ".join(rpe_path_list)
    # 需要给轨迹重命名
    traj_path_command = " ".join(traj_path_list)
    eval_results_path = "/SLAM-Hive/slam_hive_results/evaluation_results"
    mapping_results_path = "/SLAM-Hive/slam_hive_results/mapping_results"
    evo_compare_container_multi(ape_path_command, rpe_path_command, eval_results_path, resultPath, mappingtaskIdList, evaluationIdList, evo_number, traj_path_command, mapping_results_path,groundtruth)

def evo_compare_container_multi(ape_path_command, rpe_path_command, eval_results_path, resultPath, mappingtaskIdList,  evaluationIdList, evo_number, traj_path_command, mapping_results_path,groundtruth):
    client = docker.from_env()
    print("===========Start Container: [slam-hive-evaluation:evo_latex]===========")
    volume = {eval_results_path:{'bind':'/slamhive','mode':'rw'},
            mapping_results_path:{'bind':'/mapping','mode':'ro'},
            resultPath:{'bind':'/slamhive/result','mode':'rw'},
            groundtruth:{'bind':'/slamhive/groundtruth.tum','mode':'ro'}
            }


    # volume = {trajPath:{'bind':'/slamhive/traj.txt','mode':'ro'},
    #         groundtruth:{'bind':'/slamhive/groundtruth.tum','mode':'ro'},
    #         resultPath:{'bind':'/slamhive/result','mode':'rw'}}

    evo = client.containers.run("slam-hive-evaluation:evo_latex", command='/bin/bash', detach=True, tty=True, volumes=volume)

    # time.sleep(3600)
    print("========================Running EVO Comparing Task=========================")
    ape_res_command = "bash -c 'evo_res --use_filenames " \
                    + ape_path_command + " " + \
                    "--save_plot /slamhive/result/ape_res'"
    rpe_res_command = "bash -c 'evo_res --use_filenames " \
                    + rpe_path_command + " " + \
                    "--save_plot /slamhive/result/rpe_res'"
    ape_pgf_command = "bash -c 'evo_res --use_filenames " \
                    + ape_path_command + " " + \
                    "--save_plot /slamhive/result/ape_res.pgf'"
    rpe_pgf_command = "bash -c 'evo_res --use_filenames " \
                    + rpe_path_command + " " + \
                    "--save_plot /slamhive/result/rpe_res.pgf'"

    ## TODO 
    #  traj in the same plot
    evo_traj_command = 'bash -c "evo_traj tum ' \
        + traj_path_command + \
        ' --ref /slamhive/groundtruth.tum \
        -as -v --full_check --plot_mode xyz \
        --save_plot /slamhive/result/traj"'
        ################################################ show_full_names

    # print(evo_traj_command)

    evo_traj_pgf_command = 'bash -c "evo_traj tum ' \
                + traj_path_command + \
                ' --ref /slamhive/groundtruth.tum \
                -as -v --full_check --plot_mode xyz \
                --save_plot /slamhive/result/traj.pgf"'

    ## 路径太长，导致名字重叠；
    ## 所以将需要的文件复制到根目录下


    #### set evo config
    ##########
    ##########
    evo.exec_run("evo_config set plot_seaborn_style darkgrid")

    for i in range(evo_number):
        mkdir_command = "mkdir /" + str(mappingtaskIdList[i])
        evo.exec_run(mkdir_command)
        time.sleep(0.0001)
        cp_command = "cp -r /slamhive/" + str(evaluationIdList[i]) + "/." + " /" + str(mappingtaskIdList[i])
        print(cp_command)
        evo.exec_run(cp_command)
        time.sleep(0.0001)
        cp_command = "cp /mapping/" + str(mappingtaskIdList[i]) + "/traj_"+ str(mappingtaskIdList[i]) +".txt" + " /" + str(mappingtaskIdList[i])
        print(cp_command)
        evo.exec_run(cp_command)

    evo_traj = evo.exec_run(evo_traj_command,tty=True, stream=True)
    evo_traj_pgf = evo.exec_run(evo_traj_pgf_command,tty=True, stream=True)
                    
    evo_ape_res = evo.exec_run(ape_res_command, tty=True, stream=True)
    evo_rpe_res = evo.exec_run(rpe_res_command, tty=True, stream=True)
    evo_ape_pgf = evo.exec_run(ape_pgf_command, tty=True, stream=True)
    evo_rpe_pgf = evo.exec_run(rpe_pgf_command, tty=True, stream=True)

    while True:
        try:
            # print(next(evo_ape_res).decode())
            print(next(evo_traj).decode())
        except StopIteration:
            break

    evo.exec_run('bash -c "touch /slamhive/result/finished"')


    time.sleep(10)
    evo.stop()
    evo.remove()
    print("=========================EVO Comparing Task Finished!=====================")

def evo_compare_container_combination(ape_path_command, rpe_path_command, eval_results_path, compare_result_path, evoId, sub_number, compared_total_flag, local_folder): 
    client = docker.from_env()
    print("===========Start Container: [slam-hive-evaluation:evo_latex]===========")
    volume = {eval_results_path:{'bind':'/slamhive','mode':'rw'},
            compare_result_path:{'bind':'/slamhive/result','mode':'rw'}
            }
    evo = client.containers.run("slam-hive-evaluation:evo_latex", command='/bin/bash', detach=True, tty=True, volumes=volume)

    evo.exec_run('bash -c " evo_config set plot_seaborn_style darkgrid" ')

    # time.sleep(3600)
    print("========================Running EVO Comparing Task=========================")
    ape_res_command = "bash -c 'evo_res --use_filenames " \
                    + ape_path_command + " " + \
                    "--save_plot /slamhive/result/ape_res'"
    ape_pgf_command = "bash -c 'evo_res --use_filenames " \
                    + ape_path_command + " " + \
                    "--save_plot /slamhive/result/ape_res.pgf'"
    rpe_res_command = "bash -c 'evo_res --use_filenames " \
                    + rpe_path_command + " " + \
                    "--save_plot /slamhive/result/rpe_res'"
    rpe_pgf_command = "bash -c 'evo_res --use_filenames " \
                    + rpe_path_command + " " + \
                    "--save_plot /slamhive/result/rpe_res.pgf'"

    # ape_res_command = "bash -c 'evo_res --use_filenames " \
    #                 + ape_path_command + " " + \
    #                 "--save_plot /slamhive/" + str(evoId) + '/compared' + "/ape_res'"
    # rpe_res_command = "bash -c 'evo_res --use_filenames " \
    #                 + rpe_path_command + " " + \
    #                 "--save_plot /slamhive/" + str(evoId) + '/compared' + "/rpe_res'"


    ## 路径太长，导致名字重叠；
    ## 所以将需要的文件复制到根目录下

    for i in range(sub_number):
        cp_command = "cp -r /slamhive/" + str(evoId) + "/" + str(i) + " /"
        evo.exec_run(cp_command)

                    
    evo_ape_res = evo.exec_run(ape_res_command, tty=True, stream=True)
    evo_rpe_res = evo.exec_run(rpe_res_command, tty=True, stream=True)
    evo_ape_pgf = evo.exec_run(ape_pgf_command, tty=True, stream=True)
    evo_rpe_pgf = evo.exec_run(rpe_pgf_command, tty=True, stream=True)

    while True:
        try:
            print(next(evo_ape_res).decode())
        except StopIteration:
            break
    time.sleep(10)

    evo.exec_run('bash -c "touch /slamhive/result/finished"')




    # 写入flag文件
    flagPath = app.config["EVALUATION_RESULTS_PATH"] + "/" + evoId + "/compared/" + local_folder + "/flag.txt"
    f = open(flagPath, 'w')
    if compared_total_flag == True:
        f.write("True")
    else :
        f.write('False')
    f.close()
    print("=============== writing flag to", evoId,"compared",local_folder, " successful ================")



    time.sleep(0.1)
    evo.stop()
    evo.remove()
    print("=========================EVO Comparing Task Finished!=====================")


def evo_compare_task(compare_list, compare_result_path):
    ape_path_list = []
    rpe_path_list = []
    for id in compare_list:
        ape_path_list.append(os.path.join("/slamhive", str(id) + "/ape.zip"))
        rpe_path_list.append(os.path.join("/slamhive", str(id) + "/rpe.zip"))
    ape_path_command = " ".join(ape_path_list)
    rpe_path_command = " ".join(ape_path_list)
    eval_results_path = app.config['EVALUATION_RESULTS_PATH']
    evo_compare_container(ape_path_command, rpe_path_command, eval_results_path, compare_result_path)

def evo_compare_container(ape_path_command, rpe_path_command, eval_results_path, compare_result_path): 
    client = docker.from_env()
    print("===========Start Container: [slam-hive-evaluation:evo_latex]===========")
    volume = {eval_results_path:{'bind':'/slamhive','mode':'ro'},
            compare_result_path:{'bind':'/slamhive/result','mode':'rw'}}
    evo = client.containers.run("slam-hive-evaluation:evo_latex", command='/bin/bash', detach=True, tty=True, volumes=volume)
    print("========================Running EVO Comparing Task=========================")
    evo.exec_run('bash -c " evo_config set plot_seaborn_style darkgrid" ')
    ape_res_command = "bash -c 'evo_res --use_filenames " \
                    + ape_path_command + " " + \
                    "--save_plot /slamhive/result/ape_res'"
    rpe_res_command = "bash -c 'evo_res --use_filenames " \
                    + rpe_path_command + " " + \
                    "--save_plot /slamhive/result/rpe_res'"
    ape_pgf_command = "bash -c 'evo_res --use_filenames " \
                    + ape_path_command + " " + \
                    "--save_plot /slamhive/result/ape_res.pgf'"
    rpe_pgf_command = "bash -c 'evo_res --use_filenames " \
                    + rpe_path_command + " " + \
                    "--save_plot /slamhive/result/rpe_res.pgf'"
    evo_ape_res = evo.exec_run(ape_res_command, tty=True, stream=True)
    evo_rpe_res = evo.exec_run(rpe_res_command, tty=True, stream=True)
    evo_ape_pgf = evo.exec_run(ape_pgf_command, tty=True, stream=True)
    evo_rpe_pgf = evo.exec_run(rpe_pgf_command, tty=True, stream=True)

    while True:
        try:
            print(next(evo_ape_res).decode())
        except StopIteration:
            break

    time.sleep(10)
    evo.exec_run('bash -c "touch /slamhive/result/finished"')
    time.sleep(0.1)
    evo.stop()
    evo.remove()
    print("=========================EVO Comparing Task Finished!=====================")
    
    




def check_parameters_sql(parameters_list, config):

    # print(parameters_list)
    # case1: key1: value1
    parameters_dict_equal = {}
    parameters_dict_greater = {}
    parameters_dict_smaller = {}
    parameters_dict_greater_equal = {}
    parameters_dict_smaller_equal = {}
    for i in range(len(parameters_list)):
        if ":" in parameters_list[i]:
            parameters_dict_equal.update({parameters_list[i].split(":")[0].strip(" "): parameters_list[i].split(":")[1].strip(" ")})
        elif "=" in parameters_list[i] and ">" not in parameters_list[i] and "<" not in parameters_list[i]:
            parameters_dict_equal.update({parameters_list[i].split("=")[0].strip(" "): parameters_list[i].split("=")[1].strip(" ")})
        elif "<" in parameters_list[i] and "=" not in parameters_list[i]:
            parameters_dict_smaller.update({parameters_list[i].split("<")[0].strip(" "): parameters_list[i].split("<")[1].strip(" ")})
        elif ">" in parameters_list[i] and "=" not in parameters_list[i]:
            parameters_dict_greater.update({parameters_list[i].split(">")[0].strip(" "): parameters_list[i].split(">")[1].strip(" ")})
        elif ">=" in parameters_list[i]:
            parameters_dict_greater_equal.update({parameters_list[i].split(">=")[0].strip(" "): parameters_list[i].split(">=")[1].strip(" ")})
        elif "<=" in parameters_list[i]:
            parameters_dict_smaller_equal.update({parameters_list[i].split("<=")[0].strip(" "): parameters_list[i].split("<=")[1].strip(" ")})
    suit_number = 0
    for i in range(len(config.paramValues)):
        current_key = config.paramValues[i].keyName
        current_value = config.paramValues[i].value

        if current_key in parameters_dict_equal.keys():
            try:
                if config.paramValues[i].valueType == 'int':
                    if int(current_value) == int(parameters_dict_equal[current_key]):
                        suit_number += 1
                elif config.paramValues[i].valueType == 'float':
                    if float(current_value) == float(parameters_dict_equal[current_key]):
                        suit_number += 1                
                elif current_value == parameters_dict_equal[current_key]:
                    suit_number += 1
            except Exception as e:
                pass
                print(e)

        if current_key in parameters_dict_greater.keys():
            try:
                if config.paramValues[i].valueType == 'int':
                    if int(current_value) > int(parameters_dict_greater[current_key]):
                        suit_number += 1
                elif config.paramValues[i].valueType == 'float':
                    if float(current_value) > float(parameters_dict_greater[current_key]):
                        suit_number += 1
            except Exception as e:
                pass
                print(e)

        if current_key in parameters_dict_smaller.keys():
            try:
                
                if config.paramValues[i].valueType == 'int':
                    if int(current_value) < int(parameters_dict_smaller[current_key]):
                        suit_number += 1
                elif config.paramValues[i].valueType == 'float':
                    if float(current_value) < float(parameters_dict_smaller[current_key]):
                        suit_number += 1
            except Exception as e:
                pass
                print(e)

        if current_key in parameters_dict_greater_equal.keys():
            try:
                
                if config.paramValues[i].valueType == 'int':
                    if int(current_value) >= int(parameters_dict_greater_equal[current_key]):
                        suit_number += 1
                elif config.paramValues[i].valueType == 'float':
                    if float(current_value) >= float(parameters_dict_greater_equal[current_key]):
                        suit_number += 1
            except Exception as e:
                pass
                print(e)

        if current_key in parameters_dict_smaller_equal.keys():
            try:
                # print(current_value,parameters_dict_smaller_equal[current_key])
                if config.paramValues[i].valueType == 'int':
                    if int(current_value) <= int(parameters_dict_smaller_equal[current_key]):
                        suit_number += 1
                elif config.paramValues[i].valueType == 'float':
                    if float(current_value) <= float(parameters_dict_smaller_equal[current_key]):
                        suit_number += 1
            except Exception as e:
                pass
                print(e)
    if suit_number == len(parameters_dict_equal) + len(parameters_dict_greater) + len(parameters_dict_smaller) + len(parameters_dict_smaller_equal) + len(parameters_dict_greater_equal): return True
    return False

def check_results_sql(data, config):
    print(data)
    
    if len(config.mappingTasks) == 0:
        return False
    if config.mappingTasks[0].evaluation is None:
        return False
    if config.mappingTasks[0].evaluation.evoResults is None:
        return False
    if config.mappingTasks[0].performanceresults is None:
        return False
    
    evoResults = config.mappingTasks[0].evaluation.evoResults
    performanceResults = config.mappingTasks[0].performanceresults

    # evo results
    ate_rmse = evoResults.ate_rmse
    if not data['ate_rmse_nolimitation']:
        minimum_str = data['ate_rmse_minimum']
        maximum_str = data['ate_rmse_maximum']
        if minimum_str == "":
            # just maximum
            if ate_rmse > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if ate_rmse < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if ate_rmse < float(minimum_str) or ate_rmse > float(maximum_str):
                    return False   
    ate_mean = evoResults.ate_mean
    if not data['ate_mean_nolimitation']:
        minimum_str = data['ate_mean_minimum']
        maximum_str = data['ate_mean_maximum']
        if minimum_str == "":
            # just maximum
            if ate_mean > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if ate_mean < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if ate_mean < float(minimum_str) or ate_mean > float(maximum_str):
                    return False               
    ate_median = evoResults.ate_median
    if not data['ate_median_nolimitation']:
        minimum_str = data['ate_median_minimum']
        maximum_str = data['ate_median_maximum']
        if minimum_str == "":
            # just maximum
            if ate_median > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if ate_median < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if ate_median < float(minimum_str) or ate_median > float(maximum_str):
                    return False
    ate_std = evoResults.ate_std
    if not data['ate_std_nolimitation']:
        minimum_str = data['ate_std_minimum']
        maximum_str = data['ate_std_maximum']
        if minimum_str == "":
            # just maximum
            if ate_std > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if ate_std < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if ate_std < float(minimum_str) or ate_std > float(maximum_str):
                    return False
    ate_min = evoResults.ate_min
    if not data['ate_min_nolimitation']:
        minimum_str = data['ate_min_minimum']
        maximum_str = data['ate_min_maximum']
        if minimum_str == "":
            # just maximum
            if ate_min > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if ate_min < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if ate_min < float(minimum_str) or ate_min > float(maximum_str):
                    return False
    ate_max = evoResults.ate_max
    if not data['ate_max_nolimitation']:
        minimum_str = data['ate_max_minimum']
        maximum_str = data['ate_max_maximum']
        if minimum_str == "":
            # just maximum
            if ate_max > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if ate_max < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if ate_max < float(minimum_str) or ate_max > float(maximum_str):
                    return False
    rpe_sse = evoResults.rpe_sse
    if not data['rpe_sse_nolimitation']:
        minimum_str = data['rpe_sse_minimum']
        maximum_str = data['rpe_sse_maximum']
        if minimum_str == "":
            # just maximum
            if rpe_sse > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if rpe_sse < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if rpe_sse < float(minimum_str) or rpe_sse > float(maximum_str):
                    return False    
    rpe_rmse = evoResults.rpe_rmse
    if not data['rpe_rmse_nolimitation']:
        minimum_str = data['rpe_rmse_minimum']
        maximum_str = data['rpe_rmse_maximum']
        if minimum_str == "":
            # just maximum
            if rpe_rmse > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if rpe_rmse < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if rpe_rmse < float(minimum_str) or rpe_rmse > float(maximum_str):
                    return False   
    rpe_rmse = evoResults.rpe_rmse
    if not data['rpe_rmse_nolimitation']:
        minimum_str = data['rpe_rmse_minimum']
        maximum_str = data['rpe_rmse_maximum']
        if minimum_str == "":
            # just maximum
            if rpe_rmse > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if rpe_rmse < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if rpe_rmse < float(minimum_str) or rpe_rmse > float(maximum_str):
                    return False               
    rpe_median = evoResults.rpe_median
    if not data['rpe_median_nolimitation']:
        minimum_str = data['rpe_median_minimum']
        maximum_str = data['rpe_median_maximum']
        if minimum_str == "":
            # just maximum
            if rpe_median > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if rpe_median < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if rpe_median < float(minimum_str) or rpe_median > float(maximum_str):
                    return False
    rpe_std = evoResults.rpe_std
    if not data['rpe_std_nolimitation']:
        minimum_str = data['rpe_std_minimum']
        maximum_str = data['rpe_std_maximum']
        if minimum_str == "":
            # just maximum
            if rpe_std > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if rpe_std < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if rpe_std < float(minimum_str) or rpe_std > float(maximum_str):
                    return False
    rpe_min = evoResults.rpe_min
    if not data['rpe_min_nolimitation']:
        minimum_str = data['rpe_min_minimum']
        maximum_str = data['rpe_min_maximum']
        if minimum_str == "":
            # just maximum
            if rpe_min > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if rpe_min < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if rpe_min < float(minimum_str) or rpe_min > float(maximum_str):
                    return False
    rpe_max = evoResults.rpe_max
    if not data['rpe_max_nolimitation']:
        minimum_str = data['rpe_max_minimum']
        maximum_str = data['rpe_max_maximum']
        if minimum_str == "":
            # just maximum
            if rpe_max > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if rpe_max < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if rpe_max < float(minimum_str) or rpe_max > float(maximum_str):
                    return False
    rpe_sse = evoResults.rpe_sse
    if not data['rpe_sse_nolimitation']:
        minimum_str = data['rpe_sse_minimum']
        maximum_str = data['rpe_sse_maximum']
        if minimum_str == "":
            # just maximum
            if rpe_sse > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if rpe_sse < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if rpe_sse < float(minimum_str) or rpe_sse > float(maximum_str):
                    return False  
  
    # performance results
    cpu_max = performanceResults.max_cpu
    if not data['cpu_max_nolimitation']:
        minimum_str = data['cpu_max_minimum']
        maximum_str = data['cpu_max_maximum']
        if minimum_str == "":
            # just maximum
            if cpu_max > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if cpu_max < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if cpu_max < float(minimum_str) or cpu_max > float(maximum_str):
                    return False   
    cpu_mean = performanceResults.mean_cpu
    if not data['cpu_mean_nolimitation']:
        minimum_str = data['cpu_mean_minimum']
        maximum_str = data['cpu_mean_maximum']
        if minimum_str == "":
            # just maximum
            if cpu_mean > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if cpu_mean < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if cpu_mean < float(minimum_str) or cpu_mean > float(maximum_str):
                    return False     
    ram_max = performanceResults.max_ram
    if not data['ram_max_nolimitation']:
        minimum_str = data['ram_max_minimum']
        maximum_str = data['ram_max_maximum']
        if minimum_str == "":
            # just maximum
            if ram_max > float(maximum_str):
                return False
        else:
            if maximum_str == "":
                # just minimum
                if ram_max < float(minimum_str):
                    return False
            else :
                # maximum and minimum
                if ram_max < float(minimum_str) or ram_max > float(maximum_str):
                    return False 
    
    return True