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

from flask import flash, redirect, url_for, render_template, send_from_directory, request
from slamhive import app, db, socketio
from slamhive.models import MappingTask, Evaluation
from slamhive.forms import DeleteEvaluationForm
from slamhive.task import evo
from concurrent.futures import ThreadPoolExecutor
from flask_apscheduler import APScheduler
from pathlib import Path
import os, json, time, yaml


executor = ThreadPoolExecutor(10)
scheduler = APScheduler()
scheduler.start()

def RunEVO(args1, args2, args3):
    evo.evo_task(args1, args2, args3)
    print('The EVO task is done!')


def CheckEVO(id):
    eval = Evaluation.query.get(id)
    finished_path = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id)+"/finished")
    if Path(finished_path).is_file():
        eval.state = "Finished"
        eval.resultPath = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id))
        db.session.commit()
        print('[EVO ID: '+str(id)+'] finished!')
        scheduler.remove_job(str(id))
        #push state to the frontend
        socketio.emit('update_eval_state', {'data': 'Evaluation task ' + str(id)+' is done'})


@app.route('/eval/create/<int:id>')
def create_evaluate(id):
    mappingtask = MappingTask.query.get(id)
    trajFolder = str(id)
    datasetName = mappingtask.mappingTaskConf.dataset.name

    state = 'Running'
    eval = Evaluation(state=state)
    db.session.add(eval)
    mappingtask.evaluation = eval
    db.session.commit()

    executor.submit(RunEVO, trajFolder, datasetName, str(eval.id))
    scheduler.add_job(id=str(eval.id), func=CheckEVO, args=[eval.id], trigger="interval", seconds=3)
    return redirect(url_for('index_evaluate'))


@app.route('/eval/index')
def index_evaluate():
    form = DeleteEvaluationForm()
    evaluations = Evaluation.query.order_by(Evaluation.id.desc()).all()
    return render_template('/evaluation/index.html', evaluations=evaluations, form=form)


@app.route('/eval/show/<int:id>')
def show_evaluate(id):
    imgfolder = os.path.join(app.config['EVALUATION_RESULTS_PATH'], str(id))
    evo_img_list = []
    # Get all images in a folder and subfolders
    for path, dirnames, filenames in os.walk(imgfolder):
        for filename in filenames:
            if filename.lower().endswith(('.bmp', '.dib', '.png', '.jpg', '.jpeg', '.pbm', '.pgm', '.ppm', '.tif', '.tiff')):
                evo_img_list.append(os.path.join(path, filename))
    eval =  Evaluation.query.get(id)
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
                                                usage_info=usage_info)

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

@app.route('/eval/show/<path:imgpath>')
def get_img(imgpath):
    return send_from_directory('/', imgpath)

@app.route('/eval/<int:id>/delete', methods=['POST'])
def delete_evaluate(id):
    form = DeleteEvaluationForm()
    if form.validate_on_submit():
        eval = Evaluation.query.get(id)
        db.session.delete(eval)
        db.session.commit()
        flash('Deleted!')
    return redirect(url_for('index_evaluate'))





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








