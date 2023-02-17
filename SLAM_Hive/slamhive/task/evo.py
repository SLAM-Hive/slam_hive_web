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

import docker, time, os
from slamhive.task.utils import *
from slamhive import app


def evo_task(trajFolder, datasetName, evoId):
    # trajPath = os.path.join(app.config['MAPPING_RESULTS_PATH'], trajFolder + '/traj.txt')
    # groundtruth = os.path.join(app.config['DATASETS_PATH'], datasetName + "/groundtruth.txt")
    # resultPath = os.path.join(app.config['EVALUATION_RESULTS_PATH'], evoId)
    print("evo_task(trajFolder, datasetName, evoId):")
    SLAM_HIVE_PATH = get_pkg_path()
    print("SLAM_HIVE_PATH= " + SLAM_HIVE_PATH)
    trajPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_results/mapping_results/' + trajFolder + '/traj.txt')
    groundtruth = os.path.join(SLAM_HIVE_PATH, 'slam_hive_datasets/' + datasetName + "/groundtruth.txt")
    resultPath = os.path.join(SLAM_HIVE_PATH, 'slam_hive_results/evaluation_results/' + evoId)
    print(trajPath)
    print(groundtruth)
    print(resultPath)
    evo_container(trajPath, groundtruth, resultPath)

def evo_container(trajPath, groundtruth, resultPath):
    client = docker.from_env()
    print("===========Start Container: [slam-hive-evaluation:evo]===========")
    volume = {trajPath:{'bind':'/slamhive/traj.txt','mode':'ro'},
            groundtruth:{'bind':'/slamhive/groundtruth.tum','mode':'ro'},
            resultPath:{'bind':'/slamhive/result','mode':'rw'}}
    evo = client.containers.run("slam-hive-evaluation:evo", command='/bin/bash', detach=True, tty=True, volumes=volume)

    print("========================Running EVO Task=========================")
    evo_traj = evo.exec_run('bash -c "evo_traj tum \
            /slamhive/traj.txt \
            --ref /slamhive/groundtruth.tum \
            -as -v --full_check --plot_mode xyz \
            --save_plot /slamhive/result/traj"',
            tty=True, stream=True)
    # command format reference-trajectory estimated-trajectory [options] 
    evo_ape = evo.exec_run('bash -c "evo_ape tum \
            /slamhive/groundtruth.tum \
            /slamhive/traj.txt \
            -as -v -r trans_part --plot_mode xyz \
            --save_plot /slamhive/result/ape \
            --save_result /slamhive/result/ape.zip"',
            tty=True, stream=True)
    # evo_rpe tum reference.txt estimate.txt --pose_relation angle_deg --delta 1 --delta_unit m
    evo_rpe = evo.exec_run('bash -c "evo_rpe tum \
            /slamhive/groundtruth.tum \
            /slamhive/traj.txt \
            -as -v -r trans_part --plot_mode xyz --all_pairs -d 1 -u m \
            --save_plot /slamhive/result/rpe \
            --save_result /slamhive/result/rpe.zip"',
            tty=True, stream=True)

    while True:
        try:
            print(next(evo_traj).decode())
            # next(play_exec)
        except StopIteration:
            break

#     time.sleep(10)
#     stop_evo = evo.exec_run('bash -c "source /opt/ros/noetic/setup.bash && rosnode kill -a"', tty=True, stream=True)
    evo.exec_run('bash -c "touch /slamhive/result/finished"')
    time.sleep(5)
    evo.stop()
    evo.remove()
    print("=========================EVO Task Finished!=====================")



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
    print("===========Start Container: [slam-hive-evaluation:evo]===========")
    volume = {eval_results_path:{'bind':'/slamhive','mode':'ro'},
            compare_result_path:{'bind':'/slamhive/result','mode':'rw'}}
    evo = client.containers.run("slam-hive-evaluation:evo", command='/bin/bash', detach=True, tty=True, volumes=volume)
    print("========================Running EVO Comparing Task=========================")
    ape_res_command = "bash -c 'evo_res --use_filenames " \
                    + ape_path_command + " " + \
                    "--save_plot /slamhive/result/ape_res'"
    rpe_res_command = "bash -c 'evo_res --use_filenames " \
                    + rpe_path_command + " " + \
                    "--save_plot /slamhive/result/rpe_res'"
    evo_ape_res = evo.exec_run(ape_res_command, tty=True, stream=True)
    evo_rpe_res = evo.exec_run(rpe_res_command, tty=True, stream=True)

    while True:
        try:
            print(next(evo_ape_res).decode())
        except StopIteration:
            break

    evo.exec_run('bash -c "touch /slamhive/result/finished"')
    time.sleep(5)
    evo.stop()
    evo.remove()
    print("=========================EVO Comparing Task Finished!=====================")
    