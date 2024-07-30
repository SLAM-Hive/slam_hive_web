# This is part of SLAM Hive
# Copyright (C) 2024 Zinzhe Liu, Yuanyuan Yang, Bowen Xu, Sören Schwertfeger, ShanghaiTech University. 

# SLAM Hive is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# SLAM Hive is distributed in the hope that it will be useful
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with SLAM Hive.  If not, see <https://www.gnu.org/licenses/>.

from flask import flash, redirect, url_for, render_template, send_from_directory, request, jsonify, abort
from slamhive import app, db, socketio
from slamhive.models import MappingTask, Evaluation, EvoResults, MultiEvaluation, PerformanceResults, Algorithm, Dataset, MappingTaskConfig, GroupMappingTaskConfig
from slamhive.forms import DeleteEvaluationForm
from slamhive.task import evo
from concurrent.futures import ThreadPoolExecutor
from flask_apscheduler import APScheduler
from pathlib import Path
import os, json, time, yaml

from slamhive.forms import DeleteMappingTaskConfigForm

import zipfile





import numpy as np
import pandas as pd # pandas == 2.0.3
import seaborn as sns # seaborn == 0.13.0
import matplotlib.pyplot as plt
from scipy import stats, integrate # scipy == 1.10.1

####
from pyecharts.charts import Bar, Scatter # pyecharts == 2.0.4
from pyecharts import options as opts
from pyecharts.globals import ThemeType
from jinja2 import Markup, Environment, FileSystemLoader
from pyecharts.commons.utils import JsCode
from pyecharts.faker import Faker



executor = ThreadPoolExecutor(10)
scheduler = APScheduler()
scheduler.start()

def RunEVO(args1, args2, args3):
    evo.evo_task(args1, args2, args3)
    print('The EVO task is done!')

def RunEVO_batch(args1, args2, args3, args4):
    evo.evo_task_batch(args1, args2, args3, args4)
    # print('The batch EVO task is done!')

def RunEVO_multi(args1, args2, args3, args4):
    evo.evo_task_multi(args1, args2, args3, args4)
    # print('The batch EVO task is done!')

def RunEVO_combination(args1, args2, args3):
    evo.evo_task_combination(args1, args2, args3)
    print('The combination EVO task is done!')



def CheckEVO(id):
    eval = Evaluation.query.get(id)
    finished_path = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id)+"/finished")
    if Path(finished_path).is_file():
        # when evaluation Finished, call 2 functions to get 14 ate & rpe parameters and get 3 performance parameters
        eval.state = "Finished"
        ate_stats_dict = {}
        rpe_stats_dict = {}
        ################################################## if evo no matching, will cause error ( TODO)
        try:
            ate_stats_dict, rpe_stats_dict = extract_error_info(id)
            eval.resultPath = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id))
            sub_evoresults = EvoResults(evaluation_id = id,
                                        ate_rmse = ate_stats_dict['rmse'], 
                                        ate_mean = ate_stats_dict['mean'],
                                        ate_median = ate_stats_dict['median'],
                                        ate_std = ate_stats_dict['std'],
                                        ate_min = ate_stats_dict['min'],
                                        ate_max = ate_stats_dict['max'],
                                        ate_sse = ate_stats_dict['sse'],
                                        rpe_rmse = rpe_stats_dict['rmse'], 
                                        rpe_mean = rpe_stats_dict['mean'],
                                        rpe_median = rpe_stats_dict['median'],
                                        rpe_std = rpe_stats_dict['std'],
                                        rpe_min = rpe_stats_dict['min'],
                                        rpe_max = rpe_stats_dict['max'],
                                        rpe_sse = rpe_stats_dict['sse'])
            db.session.add(sub_evoresults)
            db.session.commit()
            print('[EVO ID: '+str(id)+'] finished!')
            scheduler.remove_job(str(id))
            #push state to the frontend
            socketio.emit('update_eval_state', {'data': 'Evaluation task ' + str(id)+' is done'})
        except Exception as e:
            delete_evaluate_when_running(id)
            

            scheduler.remove_job(str(id))
            #push state to the frontend
            socketio.emit('update_eval_state', {'data': 'Evaluation task ' + str(id)+' is failed'})
            # 并且修改轨迹的状态


def CheckEVO_multi(id):
    print("multi id:", id)
    eval = MultiEvaluation.query.get(id)
    finished_path = os.path.join(app.config['MULTIEVALUATION_RESULTS_PATH'], str(id)+"/finished")
    if Path(finished_path).is_file():
        # when evaluation Finished, call 2 functions to get 14 ate & rpe parameters and get 3 performance parameters
        path = os.path.join(app.config['MULTIEVALUATION_RESULTS_PATH'], str(id))
        eval.state = "Finished"
        eval.path = path
        eval.resultPath = os.path.join(app.config['MULTIEVALUATION_RESULTS_PATH'], str(id))
        db.session.commit()
        print('[EVO ID: '+str(id)+'] finished!')
        scheduler.remove_job("multiEvaluation"+str(id))
        #push state to the frontend
        socketio.emit('update_eval_state', {'data': 'Evaluation task ' + str(id)+' is done'})

def CheckEVO_batch(eval_id):
    eval_number = len(eval_id)
    eval = []
    for i in range(eval_number):

        eval.append(Evaluation.query.get(eval_id[i]))

    father_path = app.config['EVALUATION_RESULTS_PATH']
    print(father_path)
    finished_number = 0
    for now_number in range(eval_number):
        sub_path = father_path + "/" + eval_id[now_number] + "/finished"
        if Path(sub_path).is_file():
            finished_number += 1
            
            print(eval_id[now_number])
            if eval[now_number].state == "Finished" or eval[now_number].state == "Failed":
                continue
            else :
                try:
                    eval[now_number].state = "Finished"
                    eval[now_number].resultPath = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(eval_id[now_number]))
                    ate_stats_dict, rpe_stats_dict = extract_error_info(eval_id[now_number])
                    print(ate_stats_dict)
                    print(rpe_stats_dict)
                    sub_evoresults = EvoResults( # evaluation_id = id,
                                        ate_rmse = ate_stats_dict['rmse'], 
                                        ate_mean = ate_stats_dict['mean'],
                                        ate_median = ate_stats_dict['median'],
                                        ate_std = ate_stats_dict['std'],
                                        ate_min = ate_stats_dict['min'],
                                        ate_max = ate_stats_dict['max'],
                                        ate_sse = ate_stats_dict['sse'],
                                        rpe_rmse = rpe_stats_dict['rmse'], 
                                        rpe_mean = rpe_stats_dict['mean'],
                                        rpe_median = rpe_stats_dict['median'],
                                        rpe_std = rpe_stats_dict['std'],
                                        rpe_min = rpe_stats_dict['min'],
                                        rpe_max = rpe_stats_dict['max'],
                                        rpe_sse = rpe_stats_dict['sse'])
                    db.session.add(sub_evoresults)
                    # eval[now_number].evoResults.append(sub_evoresults)
                    eval[now_number].evoResults = sub_evoresults
                    db.session.commit()

                    print('[EVO ID: '+str(eval_id[now_number])+'] finished!')
                except Exception as e:
                    eval[now_number].state = "Failed"
                

    if finished_number == eval_number:

        for i in range(len(eval)):
            # 秋后算账 删除failed掉的eva 并且修改mappingtask的状态

            if eval[i].state == "Failed":
                delete_evaluate_when_running(eval[i].id)
                #push state to the frontend
                # 并且修改轨迹的状态
            
        scheduler.remove_job(eval_id[0])
            #push state to the frontend
        socketio.emit('update_eval_state', {'data': 'Evaluation task  is done'})     
    else:
        print("finished evo task number:", str(finished_number)) 

## abort
# def CheckEVO_combination(id, sub_number):
#     eval = Evaluation.query.get(id)

#     father_path = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id))
#     print(father_path)
#     finished_number = 0
#     for now_number in range(sub_number):
#         sub_path = father_path + "/" + str(now_number) +"/finished"
#         if Path(sub_path).is_file():
#             finished_number += 1
#     if finished_number == sub_number:
#         # 开始compared task

#         sub_path = father_path + "/compared/total/finished"
#         if Path(sub_path).is_file():
#             eval.state = "Finished"
#             eval.resultPath = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id))
#             db.session.commit()


#             # parse zip files
#             for i in range(sub_number):
#                 ate_stats_dict, rpe_stats_dict = extract_error_info_combination(id, i)
#                 print(i)
#                 print(ate_stats_dict)
#                 print(rpe_stats_dict)

#                 # mappingtask = MappingTask(description=description, state=state, time=time)
                
#                 # db.session.add(mappingtask)
#                 # config.mappingTasks.append(mappingtask)


#                 sub_evoresults = EvoResults(evaluation_id = id,
#                                             ate_rmse = ate_stats_dict['rmse'], 
#                                             ate_mean = ate_stats_dict['mean'],
#                                             ate_median = ate_stats_dict['median'],
#                                             ate_std = ate_stats_dict['std'],
#                                             ate_min = ate_stats_dict['min'],
#                                             ate_max = ate_stats_dict['max'],
#                                             ate_sse = ate_stats_dict['sse'],
#                                             rpe_rmse = rpe_stats_dict['rmse'], 
#                                             rpe_mean = rpe_stats_dict['mean'],
#                                             rpe_median = rpe_stats_dict['median'],
#                                             rpe_std = rpe_stats_dict['std'],
#                                             rpe_min = rpe_stats_dict['min'],
#                                             rpe_max = rpe_stats_dict['max'],
#                                             rpe_sse = rpe_stats_dict['sse'])
#                 db.session.add(sub_evoresults)
#                 eval.evoResults.append(sub_evoresults)
#                 db.session.commit()


#             print('[EVO ID: '+str(id)+'] finished!')
#             scheduler.remove_job(str(id))
#             #push state to the frontend
#             socketio.emit('update_eval_state', {'data': 'Evaluation task ' + str(id)+' is done'})     
#     else:
#         print("finished sub-evo task number:", str(finished_number))  


@app.route('/eval/create/<int:id>')
def create_evaluate(id):

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)
    mappingtask = MappingTask.query.get(id)
    trajFolder = str(id)
    datasetName = mappingtask.mappingTaskConf.dataset.name

    state = 'Running'
    eval = Evaluation(state=state)
    db.session.add(eval)
    mappingtask.evaluation = eval
    db.session.commit()

    executor.submit(RunEVO, trajFolder, datasetName, str(eval.id))
    # RunEVO(trajFolder, datasetName, str(eval.id))
    scheduler.add_job(id=str(eval.id), func=CheckEVO, args=[eval.id], trigger="interval", seconds=3)
    return redirect(url_for('index_evaluate_single'))

# CHANGE OK
@app.route('/eval/create/batch', methods=['GET', 'POST'])
def create_evaluate_batch():

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    # 需要筛选一次，将unsuccess的去掉

    data = json.loads(request.get_data())
    print(data)
    mappingtaskIdList = []
    for value in data.values():
        # CHANGE
        # Unsuccess
        current_mappingtask = MappingTask.query.get(value["mappingTaskID"])
        traj_state = current_mappingtask.trajectory_state
        if traj_state == "Success" and current_mappingtask.evaluation == None: # 只会处理轨迹正常的情况
            mappingtaskIdList.append(value["mappingTaskID"])

    if len(mappingtaskIdList) == 0:
        return jsonify(result='no task')
    
    eval_number = len(mappingtaskIdList)
    print(eval_number)
    print(mappingtaskIdList)

    mappingTask = []
    trajFolder = []
    datasetName = []
    eval = []
    eval_id = []
    for i in range(eval_number):
        mappingTask.append(MappingTask.query.get(mappingtaskIdList[i]))
        trajFolder.append(str(mappingtaskIdList[i]))
        datasetName.append(mappingTask[i].mappingTaskConf.dataset.name)
        state = 'Running'
        eval.append(Evaluation(state=state))
        db.session.add(eval[i])
        mappingTask[i].evaluation = eval[i]
        db.session.commit()
        eval_id.append(str(eval[i].id))
    # print(trajFolder)
    # print(datasetName)
    # print(eval_id)
    executor.submit(RunEVO_batch, trajFolder, datasetName, eval_id, mappingtaskIdList)
    # RunEVO_batch(trajFolder, datasetName, eval_id, mappingtaskIdList)
    scheduler.add_job(id=str(eval[0].id), func=CheckEVO_batch, args=[eval_id], trigger="interval", seconds=3)
    # return redirect(url_for('index_evaluate'))
    return jsonify(result='success')

# CHANGE OK
@app.route('/eval/create/multi', methods=['GET', 'POST'])
def create_evaluate_multi():

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    data = json.loads(request.get_data())
    print(data)
    k = len(data)
    multievaluation_name = data[str(k-1)]['MultiEvaluation_Name']
    multievaluation_description = data[str(k-1)]['MultiEvaluation_Description']
    del data[str(k-1)]
    # print(multievaluation_name, multievaluation_description)

    # 创建任务之前，应该先判断是否是同一个数据集

    # 这里的y写法应该是默认了所有eva都是已经存在了

    print(data)
    mappingtaskIdList = []
    evaluationIdList = []
    dataset_set = set()

    print(mappingtaskIdList)

    # 如果eval中出现了轨迹失败的情况，直接忽略他们

    for value in data.values():
        mappingtask = MappingTask.query.get(value['mappingTaskID'])
        
        traj_state = mappingtask.trajectory_state
        if traj_state != "Success": # 轨迹状态失败
            continue

        mappingtaskIdList.append(value['mappingTaskID'])
        print(mappingtask)
        evaluation = mappingtask.evaluation
        if evaluation == None: # 有轨迹，但是还没有进行评估
            return  jsonify(result="please evaluate all tasks first!")

        
        evaluationIdList.append(evaluation.id)

        dataset_set.add(mappingtask.mappingTaskConf.dataset.id)

    if len(mappingtaskIdList) == 0:
        return jsonify(result="no task")

    if len(dataset_set) != 1:
        # 选取的评估任务的数据集不同 无法生成对比图
    
        return jsonify(result='dataset error') 

    eval_number = len(mappingtaskIdList)

    multiEvaluation = MultiEvaluation(
        name = multievaluation_name,
        description = multievaluation_description,
        state = "Running"
    )
    db.session.add(multiEvaluation)
    db.session.commit()
    
    multiEvaluation_id = multiEvaluation.id

    mappingTask = []
    
    
    for i in range(eval_number):
        mappingTask.append(MappingTask.query.get(mappingtaskIdList[i]))
        # mappingTask[i].evaluation = eval[i]
        multiEvaluation.mappingtasks.append(mappingTask[i])
        db.session.commit()

    executor.submit(RunEVO_multi, multiEvaluation_id, mappingtaskIdList, evaluationIdList, mappingTask[0].mappingTaskConf.dataset.name)
    # RunEVO_multi(multiEvaluation_id, mappingtaskIdList, evaluationIdList)
    scheduler.add_job(id="multiEvaluation"+str(multiEvaluation_id), func=CheckEVO_multi, args=[multiEvaluation_id], trigger="interval", seconds=3)
    return jsonify(result='success')


# not use
## abort
# @app.route('/eval/create_combination/<int:id>')
# def create_evaluate_combination(id):

#     # 同时创建一个生成compare task

#     mappingtask = MappingTask.query.get(id)
#     trajFolder = str(id)
#     datasetName = mappingtask.mappingTaskConf.dataset.name

#     state = 'Running'
#     eval = Evaluation(state=state)
#     ## =====================
#     db.session.add(eval)
#     mappingtask.evaluation = eval
#     db.session.commit()
#     ## =====================

#     executor.submit(RunEVO_combination, trajFolder, datasetName, str(eval.id))

#     # RunEVO_combination(trajFolder, datasetName, str(eval.id))

#     sub_dirs = os.listdir("/slam_hive_results/mapping_results/" + trajFolder)
#     total_sub_task = len(sub_dirs)
#     scheduler.add_job(id=str(eval.id), func=CheckEVO_combination, args=[eval.id, total_sub_task], trigger="interval", seconds=3)
#     return redirect(url_for('index_evaluate'))


@app.route('/eval/index')
def index_evaluate():
    form = DeleteEvaluationForm()
    evaluations = Evaluation.query.order_by(Evaluation.id.desc()).all()
    algos = Algorithm.query.order_by(Algorithm.id.desc()).all()
    datasets = Dataset.query.order_by(Dataset.id.desc()).all()
    return render_template('/evaluation/index.html', evaluations=evaluations, form=form,
                           algos = algos, datasets = datasets, version=app.config['CURRENT_VERSION'])

@app.route('/eval/index/single')
def index_evaluate_single():
    form = DeleteEvaluationForm()
    evaluations = Evaluation.query.order_by(Evaluation.id.desc()).all()
    return render_template('/evaluation/index_single.html', evaluations=evaluations, form=form,version=app.config['CURRENT_VERSION'])

@app.route('/eval/index/multi')
def index_evaluate_multi():
    form = DeleteEvaluationForm()
    multiEvaluations = MultiEvaluation.query.order_by(MultiEvaluation.id.desc()).all()
    return render_template('/evaluation/index_multi.html', multiEvaluations=multiEvaluations, form=form,version=app.config['CURRENT_VERSION'])


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

@app.route('/eval/download_single/<int:id>')
def download_eval_single(id):
    download_folder_path = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id))
    download_zip_path = os.path.join(app.config['EVALUATION_RESULTS_PATH'], "resource_single_" + str(id) + ".zip")
    if os.path.exists(download_zip_path):
        return send_from_directory(app.config['EVALUATION_RESULTS_PATH'], "resource_single_" + str(id) + ".zip", as_attachment=True)
    else:
        zipDir(download_folder_path, download_zip_path)
        return send_from_directory(app.config['EVALUATION_RESULTS_PATH'], "resource_single_" + str(id) + ".zip", as_attachment=True)

@app.route('/eval/download_multi/<int:id>')
def download_eval_multi(id):
    download_folder_path = os.path.join(app.config['MULTIEVALUATION_RESULTS_PATH'], str(id))
    download_zip_path = os.path.join(app.config['MULTIEVALUATION_RESULTS_PATH'], "resource_multi_" + str(id) + ".zip")
    if os.path.exists(download_zip_path):
        return send_from_directory(app.config['MULTIEVALUATION_RESULTS_PATH'], "resource_multi_" + str(id) + ".zip", as_attachment=True)
    else:
        zipDir(download_folder_path, download_zip_path)
        return send_from_directory(app.config['MULTIEVALUATION_RESULTS_PATH'], "resource_multi_" + str(id) + ".zip", as_attachment=True)

############################## 记得修改获取usage的方式 TODO
@app.route('/eval/show/<int:id>')
def show_evaluate(id):
    imgfolder = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id))
    
    evo_img_list = []
    # Get all images in a folder and subfolders
    for path, dirnames, filenames in os.walk(imgfolder):
        for filename in filenames:
            if filename.lower().endswith(('.bmp', '.dib', '.png', '.jpg', '.jpeg', '.pbm', '.pgm', '.ppm', '.tif', '.tiff')):
                if filename.lower().endswith(('-img0.png')): ##################################### b
                    continue
                evo_img_list.append(os.path.join(path, filename))
    eval =  Evaluation.query.get(id)
    mappingtask = eval.mappingTask
    config = mappingtask.mappingTaskConf

    mapping_result_folder = str(eval.mappingTask.id)
    config_filename = str(eval.mappingTask.mappingTaskConf.id) + '_' + eval.mappingTask.mappingTaskConf.name + '.yaml'
    config_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/' + config_filename)
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.load(f, Loader=yaml.FullLoader)
    usage_ram_img = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/profiling_ram.png')
    usage_cpu_img = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/profiling_cpu.png')
    mapping_usage_img_list = [usage_ram_img, usage_cpu_img]
    # print(usage_ram_img)
    stats_dict, rpe_stats_dict = extract_error_info(id)
    usage_info = extract_usage_info(eval.mappingTask.id)
    return render_template('/evaluation/show.html', evo_img_list=evo_img_list, 
                                                config_dict = config_dict, 
                                                mapping_usage_img_list=mapping_usage_img_list, 
                                                stats_dict = stats_dict, 
                                                rpe_stats_dict=rpe_stats_dict, 
                                                usage_info=usage_info,
                                                mappingtask = mappingtask,
                                                config = config)


@app.route('/eval/show_multi/<int:id>')
def show_multi_evaluate(id):
    eval = MultiEvaluation.query.get(id)
    mappingtasks = eval.mappingtasks
    evaluations = []
    evoresultses = []
    performanceresultses = []
    for i in range(len(mappingtasks)):
        evaluations.append(mappingtasks[i].evaluation)
        evoresultses.append(mappingtasks[i].evaluation.evoResults)
        performanceresultses.append(mappingtasks[i].performanceresults)
        # print(mappingtasks[i].evaluation.evoResults.id)
    # print(evoresultses)
    eval_number = len(mappingtasks)
    config_filenames = []
    sub_config_paths = []
    config_dicts = []
    for i in range(eval_number):
        config_filename = str(mappingtasks[i].mappingTaskConf.id) + '_' + eval.mappingtasks[i].mappingTaskConf.name + '.yaml'
        sub_config_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtasks[i].id),  config_filename) # 选择一个子任务的config
        config_filenames.append(config_filename)
        sub_config_paths.append(sub_config_path)
        with open(sub_config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.load(f, Loader=yaml.FullLoader)
            config_dicts.append(config_dict)
    # print(config_dicts)

    # print(evoresultses[0].ate_mean)

    # paramValues = eval.mappingTask.mappingTaskConf.paramValues

    # print(paramValues)
    # for paramValue in paramValues:
    #     print(paramValue.value)

    # father_path = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id))
    # sub_dirs = os.listdir(father_path)
    # sub_task_number = len(sub_dirs) - 1



    imgfolder = os.path.join(app.config['MULTIEVALUATION_RESULTS_PATH'], str(id))
    evo_img_list = []
    # Get all images in a folder and subfolders
    for path, dirnames, filenames in os.walk(imgfolder):
        for filename in filenames:
            if filename.lower().endswith(('.bmp', '.dib', '.png', '.jpg', '.jpeg', '.pbm', '.pgm', '.ppm', '.tif', '.tiff')):
                evo_img_list.append(os.path.join(path, filename))

    # sort the list by their filenames
    evo_img_list.sort() 



    return render_template('/evaluation/show_multi.html', eval = eval, config_dicts = config_dicts, eval_number = eval_number, evo_img_list=evo_img_list,
                           mappingtasks = mappingtasks, evaluations = evaluations, evoresultses = evoresultses, performanceresultses = performanceresultses)


## abort
# @app.route('/eval/show_combination/<int:id>')
# def show_evaluate_combination(id):
#     eval = Evaluation.query.get(id)

#     config_filename = str(eval.mappingTask.mappingTaskConf.id) + '_' + eval.mappingTask.mappingTaskConf.name + '.yaml'
#     sub_config_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(eval.mappingTask.id) + '/0/' + config_filename) # 选择一个子任务的config
#     with open(sub_config_path, 'r', encoding='utf-8') as f:
#         config_dict = yaml.load(f, Loader=yaml.FullLoader)

#     paramValues = eval.mappingTask.mappingTaskConf.paramValues

#     print(paramValues)
#     for paramValue in paramValues:
#         print(paramValue.value)

#     father_path = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id))
#     sub_dirs = os.listdir(father_path)
#     sub_task_number = len(sub_dirs) - 1






#     imgfolder = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id) + "/compared/total")
#     evo_img_list = []
#     # Get all images in a folder and subfolders
#     for path, dirnames, filenames in os.walk(imgfolder):
#         for filename in filenames:
#             if filename.lower().endswith(('.bmp', '.dib', '.png', '.jpg', '.jpeg', '.pbm', '.pgm', '.ppm', '.tif', '.tiff')):
#                 evo_img_list.append(os.path.join(path, filename))

#     # sort the list by their filenames
#     evo_img_list.sort() 


#     # 读取每个sub task 的evo结果，判断是否为可以比较的task
#     sub_flags = []
#     flag_value = True
#     flag_number = 0
#     temp_sub_path = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id))
#     for now_number in range(sub_task_number):
#         sub_path = temp_sub_path + "/" + str(now_number) + "/flag.txt"
#         f = open(sub_path, "r")
#         content = f.read()
#         if content == "True":
#             sub_flags.append(True)
#             flag_number += 1
#         else:
#             sub_flags.append(False)

#     if flag_number == sub_task_number:
#         flag_value = True
#     else :
#         flag_value = False



#     # eval =  Evaluation.query.get(id)
#     # mapping_result_folder = str(eval.mappingTask.id)
#     # config_filename = str(eval.mappingTask.mappingTaskConf.id) + '_' + eval.mappingTask.mappingTaskConf.name + '.yaml'
#     # config_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/' + str(sub_id) + '/' + config_filename)
#     # with open(config_path, 'r', encoding='utf-8') as f:
#     #     config_dict = yaml.load(f, Loader=yaml.FullLoader)
#     # usage_ram_img = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/' + str(sub_id) + '/profiling_ram.png')
#     # usage_cpu_img = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/' + str(sub_id) + '/profiling_cpu.png')
#     # mapping_usage_img_list = [usage_ram_img, usage_cpu_img]
#     # print(usage_ram_img)
#     # stats_dict, rpe_stats_dict = extract_error_info_combination(eval_id, sub_id)
#     # usage_info = extract_usage_info_combination(eval.mappingTask.id, sub_id)
#   #  return render_template('/evaluation/show_one.html', evo_img_list=evo_img_list, 
#                                                 # config_dict = config_dict, 
#                                                 # mapping_usage_img_list=mapping_usage_img_list, 
#                                                 # stats_dict = stats_dict, 
#                                                 # rpe_stats_dict=rpe_stats_dict, 
#                                                 #usage_info=usage_info
#    #                                             )





#     return render_template('/evaluation/show_list.html', eval = eval, config_dict = config_dict, paramValues = paramValues, sub_task_number = sub_task_number, evo_img_list=evo_img_list, sub_flags = sub_flags)

#     # 一个总界面，显示当前组合任务有几个分任务
#       # 一个下拉框，选择想要显示的子任务
#       # 一个选择框，选择想要对比的子任务，将他们合并到一张图表中（需要看evo的功能）

## abort
# @app.route('/eval/show_combination/<int:eval_id>/<int:sub_id>')
# def show_one_evo_result(eval_id, sub_id):
#     imgfolder = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(eval_id) + "/" + str(sub_id))
#     evo_img_list = []
#     # Get all images in a folder and subfolders
#     for path, dirnames, filenames in os.walk(imgfolder):
#         for filename in filenames:
#             if filename.lower().endswith(('.bmp', '.dib', '.png', '.jpg', '.jpeg', '.pbm', '.pgm', '.ppm', '.tif', '.tiff')):
#                 evo_img_list.append(os.path.join(path, filename))
#     eval =  Evaluation.query.get(eval_id)
#     mapping_result_folder = str(eval.mappingTask.id)
#     config_filename = str(eval.mappingTask.mappingTaskConf.id) + '_' + eval.mappingTask.mappingTaskConf.name + '.yaml'
#     config_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/' + str(sub_id) + '/' + config_filename)
#     with open(config_path, 'r', encoding='utf-8') as f:
#         config_dict = yaml.load(f, Loader=yaml.FullLoader)
#     usage_ram_img = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/' + str(sub_id) + '/profiling_ram.png')
#     usage_cpu_img = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/' + str(sub_id) + '/profiling_cpu.png')
#     mapping_usage_img_list = [usage_ram_img, usage_cpu_img]
#     # print(usage_ram_img)

#     # stats_dict, rpe_stats_dict = extract_error_info_combination(eval_id, sub_id)
#     # usage_info = extract_usage_info_combination(eval.mappingTask.id, sub_id)
    
#     # read data from mysql;
#     stats_dict = {}
#     rpe_stats_dict = {}
#     for evo in eval.evoResults:
#         stats_dict['rmse'] = evo.ate_rmse
#         stats_dict['mean'] = evo.ate_mean
#         stats_dict['median'] = evo.ate_median
#         stats_dict['std'] = evo.ate_std
#         stats_dict['min'] = evo.ate_min
#         stats_dict['max'] = evo.ate_max
#         stats_dict['sse'] = evo.ate_sse
#         rpe_stats_dict['rmse'] = evo.rpe_rmse
#         rpe_stats_dict['mean'] = evo.rpe_mean
#         rpe_stats_dict['median'] = evo.rpe_median
#         rpe_stats_dict['std'] = evo.rpe_std
#         rpe_stats_dict['min'] = evo.rpe_min
#         rpe_stats_dict['max'] = evo.rpe_max
#         rpe_stats_dict['sse'] = evo.rpe_sse
#     usage_info = {}
#     for performanceresult in eval.mappingTask.performanceresults:
#         usage_info['max_cpu'] = performanceresult.max_cpu
#         usage_info['mean_cpu'] = performanceresult.mean_cpu
#         usage_info['max_ram'] = performanceresult.max_ram




#     return render_template('/evaluation/show_one.html', evo_img_list=evo_img_list, 
#                                                 config_dict = config_dict, 
#                                                 mapping_usage_img_list=mapping_usage_img_list, 
#                                                 stats_dict = stats_dict, 
#                                                 rpe_stats_dict=rpe_stats_dict, 
#                                                 usage_info=usage_info)

# 好像没用了
## abort
# @app.route('/eval/show_compare_combination/<int:eval_id>')
# def show_comparison_evo_result(eval_id):
#     return evo.evo_compare_task_combination()


## abort
# @app.route('/eval/show_certain_compare_combination/<int:eval_id>/<int:sub_task_number>/<string:choose_check>')
# def show_certain_comparison_task(eval_id, sub_task_number, choose_check):

#     ## 1 首先判断文件夹下有无该组合

#     certain_task_path = app.config['EVALUATION_RESULTS_PATH'] + "/" + str(eval_id) + "/compared/" + choose_check

#     if not os.path.exists(certain_task_path):
#         # 没有执行过该组合，需要生成
#         # /slam_hive_results/evaluation_results/183/0-1
#         evo.evo_certain_compare_combination(choose_check, eval_id, sub_task_number)
        


#     # 结果已经存在在文件夹里了，显示


#     eval = Evaluation.query.get(eval_id)

#     config_dicts = []

#     choose_check_list = choose_check.split("-")
#     for now_number in range(len(choose_check_list)):
#         config_filename = str(eval.mappingTask.mappingTaskConf.id) + '_' + eval.mappingTask.mappingTaskConf.name + '.yaml'
#         sub_config_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(eval.mappingTask.id) + '/'+ choose_check_list[now_number] +'/' + config_filename) # 选择一个子任务的config
#         with open(sub_config_path, 'r', encoding='utf-8') as f:
#             config_dicts.append(yaml.load(f, Loader=yaml.FullLoader))

#     paramValues = eval.mappingTask.mappingTaskConf.paramValues



#     imgfolder = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(eval_id) + "/compared/" + choose_check)
#     evo_img_list = []
#     # Get all images in a folder and subfolders
#     for path, dirnames, filenames in os.walk(imgfolder):
#         for filename in filenames:
#             if filename.lower().endswith(('.bmp', '.dib', '.png', '.jpg', '.jpeg', '.pbm', '.pgm', '.ppm', '.tif', '.tiff')):
#                 evo_img_list.append(os.path.join(path, filename))

#     evo_img_list.sort()

#     # eval =  Evaluation.query.get(id)
#     # mapping_result_folder = str(eval.mappingTask.id)
#     # config_filename = str(eval.mappingTask.mappingTaskConf.id) + '_' + eval.mappingTask.mappingTaskConf.name + '.yaml'
#     # config_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/' + str(sub_id) + '/' + config_filename)
#     # with open(config_path, 'r', encoding='utf-8') as f:
#     #     config_dict = yaml.load(f, Loader=yaml.FullLoader)
#     # usage_ram_img = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/' + str(sub_id) + '/profiling_ram.png')
#     # usage_cpu_img = os.path.join(app.config['MAPPING_RESULTS_PATH'], mapping_result_folder + '/' + str(sub_id) + '/profiling_cpu.png')
#     # mapping_usage_img_list = [usage_ram_img, usage_cpu_img]
#     # print(usage_ram_img)
#     # stats_dict, rpe_stats_dict = extract_error_info_combination(eval_id, sub_id)
#     # usage_info = extract_usage_info_combination(eval.mappingTask.id, sub_id)
#   #  return render_template('/evaluation/show_one.html', evo_img_list=evo_img_list, 
#                                                 # config_dict = config_dict, 
#                                                 # mapping_usage_img_list=mapping_usage_img_list, 
#                                                 # stats_dict = stats_dict, 
#                                                 # rpe_stats_dict=rpe_stats_dict, 
#                                                 #usage_info=usage_info
#    #                                             )





#     return render_template('/evaluation/show_list_certain.html', eval = eval, config_dicts = config_dicts, paramValues = paramValues, sub_task_number = sub_task_number, evo_img_list=evo_img_list, choose_check_list = choose_check_list, config_dicts_len = len(config_dicts))


def extract_error_info(id):
    import zipfile, json, os, shutil
    results_path = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id))
    ape_zip_path = os.path.join(results_path, 'ape.zip')
    temp_path = os.path.join(results_path, 'temp')
    with zipfile.ZipFile(ape_zip_path, 'r') as f:
        for file in f.namelist():
            f.extract(file, temp_path)
    with open(temp_path + '/stats.json', 'r') as f:
        stats_dict = json.load(f)
        # print(stats_dict)
    shutil.rmtree(temp_path)

    rpe_zip_path = os.path.join(results_path, 'rpe.zip')
    temp_rpe_path = os.path.join(results_path, 'temp_rpe')
    with zipfile.ZipFile(rpe_zip_path, 'r') as f:
        for file in f.namelist():
            f.extract(file, temp_rpe_path)
    with open(temp_rpe_path + '/stats.json', 'r') as f:
        rpe_stats_dict = json.load(f)
        # print(rpe_stats_dict)
    shutil.rmtree(temp_rpe_path)
    return stats_dict, rpe_stats_dict



## abort
# def extract_error_info_combination(eval_id, sub_id):
#     import zipfile, json, os, shutil
#     results_path = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(eval_id) + "/" + str(sub_id))
#     ape_zip_path = os.path.join(results_path, 'ape.zip')
#     temp_path = os.path.join(results_path, 'temp')
#     with zipfile.ZipFile(ape_zip_path, 'r') as f:
#         for file in f.namelist():
#             f.extract(file, temp_path)
#     with open(temp_path + '/stats.json', 'r') as f:
#         stats_dict = json.load(f)
#         # print(stats_dict)
#     shutil.rmtree(temp_path)

#     rpe_zip_path = os.path.join(results_path, 'rpe.zip')
#     temp_rpe_path = os.path.join(results_path, 'temp_rpe')
#     with zipfile.ZipFile(rpe_zip_path, 'r') as f:
#         for file in f.namelist():
#             f.extract(file, temp_rpe_path)
#     with open(temp_rpe_path + '/stats.json', 'r') as f:
#         rpe_stats_dict = json.load(f)
#         # print(rpe_stats_dict)
#     shutil.rmtree(temp_rpe_path)
#     return stats_dict, rpe_stats_dict


def extract_usage_info(id):
    import csv
    results_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(id))
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


# def extract_usage_info_combination(mappingtask_id, sub_id):
#     import csv
#     results_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_id) + '/' + str(sub_id))
#     usage_csv_path = os.path.join(results_path, 'profiling.csv')
#     with open(usage_csv_path, 'r') as f:
#         reader = csv.reader(f)
#         header_row = next(reader)
#         time = []
#         cpu = []
#         ram = []
#         total_cpu = 0
#         N = 0
#         for row in reader:
#             time.append(float(row[0]))
#             cpu.append(float(row[1]))
#             ram.append(int(row[2])/(1024*1024))
#             total_cpu += float(row[1])
#             N += 1
#     usage_info = {}
#     usage_info["max_cpu"] = max(cpu)
#     usage_info["mean_cpu"] = total_cpu/N
#     usage_info["max_ram"] = max(ram)
#     print(usage_info)
#     return usage_info

@app.route('/eval/show/<path:imgpath>')
def get_img(imgpath):
    return send_from_directory('/', imgpath)

@app.route('/eval/<int:id>/delete', methods=['POST'])
def delete_evaluate(id):

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    form = DeleteEvaluationForm()
    if form.validate_on_submit():
        eval = Evaluation.query.get(id)
        db.session.delete(eval)
        db.session.commit()
        flash('Deleted!')
    return redirect(url_for('index_evaluate_single'))

def delete_evaluate_when_running(id):
    # 如果任务创建失败 执行该代码
    eval = Evaluation.query.get(id)
    ma = Evaluation.query.get(id).mappingTask
    print("failed eval ------------------")
    print(ma)
    ma.trajectory_state = "Unsuccess"
    db.session.delete(eval)
    db.session.commit()
    # flash('Deleted!')
    # return redirect(url_for('index_evaluate_single'))

@app.route('/eval/<int:id>/delete_multi', methods=['POST'])
def delete_multi_evaluate(id):

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)
    form = DeleteEvaluationForm()
    if form.validate_on_submit():
        eval = MultiEvaluation.query.get(id)
        db.session.delete(eval)
        db.session.commit()
        flash('Deleted!')
    return redirect(url_for('index_evaluate_multi'))



##############To do################
#         compare evaluation
###################################
# @app.route('/eval/compare', methods=['POST'])
# def compare_mapping():
#     selected = json.loads(request.get_data())
#     print(selected)
#     # Create a Compare object
#     # state = 'Running'
#     # eval = Compare(state=state)
#     # db.session.add(eval)
#     # db.session.commit()

#     # calEVO
#     compare_list = []
#     for value in selected.values():
#         compare_list.append(value)
#     # executor.submit(RunEVOCompare, compare_list)
#     # scheduler.add_job(id=str(eval.id), func=CheckEvoCompare, args=[eval.id], trigger="interval", seconds=3)
#     return "12"


# def RunEVOCompare(compare_list):
#     print(compare_list)
#     compare_result_path = "_".join(compare_list)
#     compare_result_path =  os.path.join(app.config['EVALUATION_COMPARE_RESULTS_PATH'], compare_result_path)
#     print(compare_result_path)
#     evo.evo_compare_task(compare_list, compare_result_path)
#     print("RunEVOCompare() finish")


# # def CheckEvoCompare(eval_id, compare_list):
# #     compare_result_path = "_".join(compare_list)
# #     compare_result_path =  os.path.join(app.config['EVALUATION_COMPARE_RESULTS_PATH'], compare_result_path)
# #     finished_path = os.path.join(compare_result_path, "finished")
# #     if Path(finished_path).is_file():
# #         eval.state = "finished"
# #         eval.resultPath = compare_result_path
# #         db.session.commit()
# #         print('[EVO Comparing ID: '+str(id)+'] finished!')
# #         scheduler.remove_job(str(id))
# #         #push state to the frontend
# #         socketio.emit('update_eval_state', {'data': str(id)+' is done'})


# @app.route('/eval/compare/result/<path:compare_list>')
# def show_compare_result(compare_list):
#     # print("show_compare_result()")
#     # print(compare_list)
#     return render_template('/evaluation/compare.html')



@app.route('/eval/search/submit', methods=['POST'])
def submit_search_eval():
    data = json.loads(request.get_data())
    print(data)
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

    # min max nolimitation
    

    
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
            if not evo.check_parameters_sql(parameters_list, configs[i]):
                continue
        if not evo.check_results_sql(data, configs[i]):
            continue
        suit_configs.append(configs[i])
    print(suit_configs)
    # evaluations = []
    # for i in range(len(suit_configs)):
    #     evaluation.append()
    
    # for i in range(len(suit_configs)):
    #     print(suit_configs[i].mappingTasks[0].evaluation.evoResults.id)

    return render_template('/evaluation/search_result.html', configs=suit_configs) # , evaluatons = evaluations)








@app.route('/eval/group/index', methods=['POST','GET'])
def index_evaluate_group():
    group_configs = GroupMappingTaskConfig.query.order_by(GroupMappingTaskConfig.id.desc()).all()

    return render_template('/evaluation/index_group.html', group_configs=group_configs) # , mappingTasks_number = mappingTasks_number)


@app.route('/eval/group/show/<int:id>', methods=['POST','GET'])
def show_group_eval(id):
    group_config = GroupMappingTaskConfig.query.get(id)
    configs = group_config.mappingTaskConf
    mappingTasks_number = {}
    evals_number = {}
    for i in range(len(configs)):
        mappingTasks_number.update({configs[i].id: len(configs[i].mappingTasks)})
        if len(configs[i].mappingTasks) == 0:
            evals_number.update({configs[i].id: 0})
        else:
            if configs[i].mappingTasks[0].evaluation != None:
                evals_number.update({configs[i].id: 1})
            else :
                evals_number.update({configs[i].id: 0})
    
    # 返回已经生成的图片
    

    return render_template('/evaluation/show_group.html', group_config = group_config, configs=configs, mappingTasks_number = mappingTasks_number, evals_number = evals_number)




@app.route('/eval/group/multi/<int:id>', methods=['GET', 'POST'])
def submit_group_multi_eval(id):
    group = GroupMappingTaskConfig.query.get(id)



    # 首先判断该groupo是否已经创建或者关联了一个multi evaluation
    if group.multiEvaluation != None:
        return show_group_eval(id)

    print(group)
    # 拿到了group
    # 拿到group的所有config
    group_config_id_list = []
    for i in range(len(group.mappingTaskConf)):
        group_config_id_list.append(group.mappingTaskConf[i].id)
    group_config_id_list = sorted(group_config_id_list)
    print(group_config_id_list)

    # 判断config的数量；上限8个
    if len(group_config_id_list) > 8:
        return show_group_eval(id)

    # 判断evaluation和mapping task是否都已经创建
    for i in range(len(group.mappingTaskConf)):
        if len(group.mappingTaskConf[i].mappingTasks) == 0:
            return show_group_eval(id)
        if group.mappingTaskConf[i].mappingTasks[0].evaluation == None:
            return show_group_eval(id)

    # 首先判断是否存在了相同的multi evaluation
    # 获取全部multi evaluation
    multi_evaluation_exist = MultiEvaluation.query.order_by(MultiEvaluation.id.desc()).all()
    print(multi_evaluation_exist)
    for i in range(len(multi_evaluation_exist)):
        current_config_id_list = []
        if len(multi_evaluation_exist[i].mappingtasks) != len(group_config_id_list):
            continue
        for j in range(len(multi_evaluation_exist[i].mappingtasks)):
            current_config_id_list.append(multi_evaluation_exist[i].mappingtasks[j].mappingTaskConf.id)
        current_config_id_list = sorted(current_config_id_list)
        if current_config_id_list == group_config_id_list:
            
            # 之前已经存在了一个包含相同config的task，无需创建新的task，只需要关联即可
            group.multiEvaluation = multi_evaluation_exist[i]
            db.session.commit()
            return show_group_eval(id)

    # print(multievaluation_name, multievaluation_description)

    # 创建任务之前，应该先判断是否是同一个数据集

    mappingtaskIdList = []
    evaluationIdList = []
    dataset_set = set()
    for i in range(len(group.mappingTaskConf)):
        mappingtaskIdList.append(str(group.mappingTaskConf[i].mappingTasks[0].id))
        mappingtask = MappingTask.query.get(group.mappingTaskConf[i].mappingTasks[0].id)
        print(mappingtask)
        evaluaton = mappingtask.evaluation
        evaluationIdList.append(evaluaton.id)

        dataset_set.add(mappingtask.mappingTaskConf.dataset.id)

    if len(dataset_set) != 1:
        # 选取的评估任务的数据集不同 无法生成对比图
    
        return show_group_eval(id)  ## TODO 后面改成n返回不同的条件

    eval_number = len(mappingtaskIdList)

    multiEvaluation = MultiEvaluation(
        name = group.name,
        description = group.description,
        state = "Running"
    )
    db.session.add(multiEvaluation)
    group.multiEvaluation = multiEvaluation
    db.session.commit()
    
    multiEvaluation_id = multiEvaluation.id

    mappingTask = []
    
    
    for i in range(eval_number):
        mappingTask.append(MappingTask.query.get(mappingtaskIdList[i]))
        # mappingTask[i].evaluation = eval[i]
        multiEvaluation.mappingtasks.append(mappingTask[i])
        db.session.commit()

    executor.submit(RunEVO_multi, multiEvaluation_id, mappingtaskIdList, evaluationIdList, mappingTask[0].mappingTaskConf.dataset.name)
    # RunEVO_multi(multiEvaluation_id, mappingtaskIdList, evaluationIdList, mappingTask[0].mappingTaskConf.dataset.name)
    scheduler.add_job(id="multiEvaluation"+str(multiEvaluation_id), func=CheckEVO_multi, args=[multiEvaluation_id], trigger="interval", seconds=3)
    return redirect(url_for('index_evaluate_multi'))
    
    # 需要创建一个新的multi evaluation

# def return_img_stream(img_local_path):
#     """
#     工具函数:
#     获取本地图片流
#     :param img_local_path:文件单张图片的本地绝对路径
#     :return: 图片流
#     """
#     import base64
#     img_stream = ''
#     with open(img_local_path, 'rb') as img_f:
#         img_stream = img_f.read()
#         img_stream = base64.b64encode(img_stream).decode()
#     return img_stream








# @app.route('/mulfileupload/',methods=['GET','POST'])
# def mulfileupload():
#     if request.method=='POST':
#         files=request.files.getlist('wenjian')
#         filelist=[]
#         urllist=[]
#         for file in files:
#             filename=file.filename
#             filetype=filename.split('.')[-1]
#             print(filename)
#             print(filetype)
#             uploadpath=os.getcwd()+os.sep+'static/file'
#             if not os.path.exists(uploadpath):
#                 os.mkdir(uploadpath)
#             filename=str(uuid.uuid1())+'.'+filetype
#             print(filename)
#             file.save(uploadpath+os.sep+filename)
#             filelist.append(filename)
#             #照片回显url
#             url = url_for("static", filename="file/" + filename)
#             urllist.append(url)
 
#         return render_template('/evaluation/show.html',filelist=filelist,urllist=urllist)
#     else:
#         return render_template('/evaluation/show.html')
 
# @app.route('/down/<filename>/')
# def down(filename):
#     dir=os.getcwd()+os.sep+'static/file/'
#     print(dir+filename)
#     #下载图片设置
#     return send_from_directory(dir,filename,as_attachment=True)


# @app.route('/eval/diagram/dig1/show',methods=['GET','POST'])
# def show_diagram1():
#     data = json.loads(request.get_data())
#     print(data)

#     group_id = data['group_id']
#     x_axis = data['x-axis']
#     y_axis = data['y-axis']

#         # 首先判断group中的config -- algo：任意都可以（但是貌似不是同一个算法意义不大）;dataset: 相同

#     diagram_data = []
#     group = GroupMappingTaskConfig.query.get(group_id)
#     for i in range(len(group.mappingTaskConf)):
#         # 获取x y对应
#         x_v = 0
#         y_v = 0
#         evoResults = group.mappingTaskConf[i].mappingTasks[0].evaluation.evoResults
#         if x_axis == 'ATE-rmse':
#             x_v = evoResults.ate_rmse
#         elif x_axis == 'ATE-mean':
#             x_v = evoResults.ate_mean
#         elif x_axis == 'ATE-median':
#             x_v = evoResults.ate_median
#         elif x_axis == 'ATE-std':
#             x_v = evoResults.ate_std
#         elif x_axis == 'ATE-min':
#             x_v = evoResults.ate_min
#         elif x_axis == 'ATE-max':
#             x_v = evoResults.ate_max
#         elif x_axis == 'ATE-sse':
#             x_v = evoResults.ate_sse
#         elif x_axis == 'RPE-mean':
#             x_v = evoResults.rpe_mean
#         elif x_axis == 'RPE-median':
#             x_v = evoResults.rpe_median
#         elif x_axis == 'RPE-std':
#             x_v = evoResults.rpe_std
#         elif x_axis == 'RPE-min':
#             x_v = evoResults.rpe_min
#         elif x_axis == 'RPE-max':
#             x_v = evoResults.rpe_max
#         elif x_axis == 'RPE-sse':
#             x_v = evoResults.rpe_sse
#         elif x_axis == 'RPE-sse':
#             x_v = evoResults.rpe_sse
        
#         performanceresults = group.mappingTaskConf[i].mappingTasks[0].performanceresults
#         if y_axis == 'CPU-max':
#             y_v = performanceresults.max_cpu
#         elif y_axis == 'CPU-mean':
#             y_v = performanceresults.mean_cpu
#         elif y_axis == 'Memory-max':
#             y_v = performanceresults.max_ram
#         diagram_data.append([x_v, y_v])

#     # bar = (
#     #     Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
#     #     .add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
#     #     .add_yaxis("商家A", [5, 20, 36, 10, 75, 90])
#     #     .add_yaxis("商家B", [15, 25, 30, 18,65, 70])
#     #     .set_global_opts(title_opts=opts.TitleOpts(title="主标题", subtitle="副标题"))
#     #     # 或者直接使用字典参数
#     #     .set_global_opts(title_opts={"text": "主标题", "subtext": "副标题"})
#     # )
#     x_data = [d[0] for d in diagram_data]
#     y_data = [d[1] for d in diagram_data]
    
#     y_new_data = []
#     for i in range(len(y_data)):
#         temp_dict = {'value': y_data[i], "info": "info_" + str(i)}
#         temp_dict = [y_data[i], "info_" + str(i)]
#         y_new_data.append(temp_dict)

#     scatter = (
#         Scatter()
#         .add_xaxis(
#             xaxis_data=x_data,
#         )
#         .add_yaxis(
#             series_name="",
#             y_axis=y_new_data,
#             #symbol_size=20,
#             label_opts=opts.LabelOpts(
#                 is_show=False,
#             #     formatter=JsCode(
#             #     "function(params){return params.value[0] +' : '+ params.value[1];}"
#             # )
#             ),
#         )
#         .set_global_opts(
#             xaxis_opts=opts.AxisOpts(
#                 type_="value", 
#                 axistick_opts=opts.AxisTickOpts(is_show=True),
#                 splitline_opts=opts.SplitLineOpts(is_show=True),
#                 min_='dataMin'
#             ),
#             yaxis_opts=opts.AxisOpts(
#                 type_="value",
#                 axistick_opts=opts.AxisTickOpts(is_show=False),
#                 splitline_opts=opts.SplitLineOpts(is_show=False),
#                 min_='dataMin'),
#             tooltip_opts=opts.TooltipOpts(
#                 formatter=JsCode(
#                     "function (params) {console.log(params.value[2]);return params.value[0] + ' : ' + params.value[1]+' ; '+params.value[2];}"
#                 )
#             ),
#         )
#     )


#     x_t_data = Faker.choose()
#     y_t_data = [list(z) for z in zip(Faker.values(), x_t_data)]
#     print(x_t_data)
#     print(y_t_data)

#     # c = (
#     # Scatter()
#     # .add_xaxis(x_t_data)
#     # .add_yaxis(
#     #     "商家A",
#     #     y_t_data,
#     #     label_opts=opts.LabelOpts(
#     #         is_show=False,
#     #         # formatter=JsCode(
#     #         #     "function(params){return params.value[1] +' : '+ params.value[2];}"
#     #         # )
#     #     ),
#     # )
#     # .set_global_opts(
#     #     title_opts=opts.TitleOpts(title="Scatter-多维度数据"),
#     #     tooltip_opts=opts.TooltipOpts(
#     #         formatter=JsCode(
#     #             "function (params) {return params.name + ' : ' + params.value[1];}"
#     #         )
#     #     ),
#         # visualmap_opts=opts.VisualMapOpts(
#         #     type_="color", max_=150, min_=20, dimension=1
#         # ),
#     # ))
    

#     return Markup(scatter.render_embed())
#     # bar.render('templates\index.html')





# @app.route('/eval/diagram/dig1',methods=['GET','POST'])
# def create_diagram1():
#     data = json.loads(request.get_data())
#     print(data)

#     group_id = data['group_id']
#     x_axis = data['x-axis']
#     y_axis = data['y-axis']

#     # 首先判断group中的config -- algo：任意都可以（但是貌似不是同一个算法意义不大）;dataset: 相同

#     diagram_data = []
#     group = GroupMappingTaskConfig.query.get(group_id)
#     for i in range(len(group.mappingTaskConf)):
#         # 获取x y对应
#         x_v = 0
#         y_v = 0
#         evoResults = group.mappingTaskConf[i].mappingTasks[0].evaluation.evoResults
#         if x_axis == 'ATE-rmse':
#             x_v = evoResults.ate_rmse
#         elif x_axis == 'ATE-mean':
#             x_v = evoResults.ate_mean
#         elif x_axis == 'ATE-median':
#             x_v = evoResults.ate_median
#         elif x_axis == 'ATE-std':
#             x_v = evoResults.ate_std
#         elif x_axis == 'ATE-min':
#             x_v = evoResults.ate_min
#         elif x_axis == 'ATE-max':
#             x_v = evoResults.ate_max
#         elif x_axis == 'ATE-sse':
#             x_v = evoResults.ate_sse
#         elif x_axis == 'RPE-mean':
#             x_v = evoResults.rpe_mean
#         elif x_axis == 'RPE-median':
#             x_v = evoResults.rpe_median
#         elif x_axis == 'RPE-std':
#             x_v = evoResults.rpe_std
#         elif x_axis == 'RPE-min':
#             x_v = evoResults.rpe_min
#         elif x_axis == 'RPE-max':
#             x_v = evoResults.rpe_max
#         elif x_axis == 'RPE-sse':
#             x_v = evoResults.rpe_sse
#         elif x_axis == 'RPE-sse':
#             x_v = evoResults.rpe_sse
        
#         performanceresults = group.mappingTaskConf[i].mappingTasks[0].performanceresults
#         if y_axis == 'CPU-max':
#             y_v = performanceresults.max_cpu
#         elif y_axis == 'CPU-mean':
#             y_v = performanceresults.mean_cpu
#         elif y_axis == 'Memory-max':
#             y_v = performanceresults.max_ram
#         diagram_data.append([x_v, y_v])
    
#     diagram_name_pgf = "Diagram1_x-" + x_axis + "_y-" + y_axis+".pgf"
#     diagram_name_png = "Diagram1_x-" + x_axis + "_y-" + y_axis+".png"
#     diagram_name_pdf = "Diagram1_x-" + x_axis + "_y-" + y_axis+".pdf"
#     diagram_path_pgf = "/slam_hive_results/group/" + str(group_id) + "/" + diagram_name_pgf
#     diagram_path_png = "/slam_hive_results/group/" + str(group_id) + "/" + diagram_name_png
#     diagram_path_pdf = "/slam_hive_results/group/" + str(group_id) + "/" + diagram_name_pdf

#     diagram_data = np.array(diagram_data)
#     # print(diagram_data)
#     # sns.set(color_codes=True)
#     # mean, cov = [0.5, 1], [(1, .5),(.5, 1)]#设置均值(一组参数)和协方差（两组参数）
#     # data = np.random.multivariate_normal(mean, cov, 200)
#     # print(type(data))
#     df = pd.DataFrame(diagram_data, columns=[x_axis, y_axis])
#     # print(type(df))
#     # print(df.head())
#     fig = sns.scatterplot(x=x_axis, y=y_axis, data=df)
#     scatter_fig = fig.get_figure()
#     scatter_fig.savefig(diagram_path_pgf, dpi = 400)
#     scatter_fig.savefig(diagram_path_png, dpi = 400)
#     scatter_fig.savefig(diagram_path_pdf, dpi = 400)
    

#     # plt.show()



#     return jsonify(result='success')


