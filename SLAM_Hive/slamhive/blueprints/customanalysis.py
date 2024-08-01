
from flask import flash, redirect, url_for, render_template, request, jsonify, send_from_directory, render_template_string
from slamhive import app, db
from slamhive.models import Algorithm, MappingTaskConfig, ParameterValue, AlgoParameter, Dataset, CombMappingTaskConfig, GroupMappingTaskConfig
from slamhive.forms import DeleteCustomAnalysisGroup, DeleteMappingTaskConfigForm, DeleteGroupMappingTaskConfigForm,DeleteGroupMappingTaskConfigForm1
from slamhive.blueprints.utils import *
import json, yaml, os, uuid, shutil

from slamhive.task import custom_analysis_resolver

####
import zipfile

import numpy as np
import pandas as pd # pandas == 2.0.3
import seaborn as sns # seaborn == 0.13.0
import matplotlib.pyplot as plt
from scipy import stats, integrate # scipy == 1.10.1

from pyecharts.charts import Bar, Scatter ,Scatter3D# pyecharts == 2.0.4
from pyecharts import options as opts
from pyecharts.globals import ThemeType
from jinja2 import Markup, Environment, FileSystemLoader
from pyecharts.commons.utils import JsCode
from pyecharts.faker import Faker

@app.route('/analysis/index', methods=['POST','GET'])
def index_customanalysis():


    # # 修改每一个参数 and 配置文件

    # config_ids = [2160, 2161, 2162, 2163, 2164, 2165, 2166, 2167, 2168, 2169, 2170, 2171, 2172, 2173, 2174, 2175, 2176, 2177, 2178, 2179, 2180, 2181, 2182, 2183, 2184, 2185, 2186, 2187, 2188, 2189, 2190, 2191, 2192, 2193, 2194, 2195, 2196, 2197, 2198, 2199, 2200, 2201, 2202, 2203, 2204, 2205, 2206, 2207, 2208, 2209, 2210, 2211, 2212, 2213, 2214, 2215, 2216, 2217, 2218, 2219, 2220, 2221, 2222, 2223, 2224, 2225, 2226, 2227, 2228, 2229, 2230, 2231, 2232, 2233, 2234, 2235, 2236, 2237, 2238, 2239, 2240, 2241, 2242, 2243, 2244, 2245, 2246, 2247, 2248, 2249, 2250, 2251, 2252, 2253, 2254, 2255, 2256, 2257, 2258, 2259, 2260, 2261, 2262, 2263, 2264, 2265, 2266, 2267, 2268, 2269, 2270, 2271, 2272, 2273, 2274, 2275, 2276, 2277, 2278, 2279, 2280, 2281, 2282, 2283, 2284, 2285, 2286, 2287, 2288, 2289, 2290, 2291, 2292, 2293, 2294, 2295, 2296, 2297, 2298, 2299, 2300, 2301, 2302, 2303, 2304, 2305, 2306, 2307, 2308, 2309]

    # newValues = []

    # for i in range(len(config_ids)):
    #     config = MappingTaskConfig.query.get(config_ids[i])

    #     # 首先读取到 name为的 dataset_frequency+image0_frequency 
    #     value = 0
    #     for paramValue in config.paramValues:
    #         if paramValue.name == "dataset_frequency+image0_frequency":
    #             value = paramValue.value
    #             break
        
    #     for paramValue in config.paramValues:
    #         if paramValue.name == "general+image_frequency":
    #             newValues.append(int(20 / int(value)))
    #             paramValue.value = 20 # newValues[i]
    #             db.session.commit()
    #             print(paramValue.value)
    #             break
        
      
    
    # print(newValues)
    # for i in range(len(config_ids)):
    #     config = MappingTaskConfig.query.get(config_ids[i])
        
    #     for paramValue in config.paramValues:
    #         if paramValue.name == "general+image_frequency":
    #             print(paramValue.value)
    #             break
    
#先把数据改回去
    # for i in range(len(config_ids)):
    #     # 读取 YAML 文件
    #     config = MappingTaskConfig.query.get(config_ids[i])
    #     task = config.mappingTasks[0]
    #     folder_path = "/slam_hive_results/mapping_results/" + str(task.id)

    #     # 查找所有 .yaml 文件
    #     import glob
    #     yaml_file = glob.glob(os.path.join(folder_path, '*.yaml'))[0]
    #     with open(yaml_file, 'r') as file:
    #         data = yaml.safe_load(file)

    #     # 修改特定的键值
        

    #     data['dataset-parameters']['image_frequency'] = newValues[i]  # 修改为你想要的值

    #     # 将修改后的数据写回 YAML 文件
    #     with open(yaml_file, 'w') as file:
    #         yaml.safe_dump(data, file, default_flow_style=False)


    form = DeleteCustomAnalysisGroup()

    ################################
    ## 解析所有的yaml file，显示出来 ##
    ################################

    # 1. 读取对应路径下的所有yaml file
    # 2. 依次解析每个file
      # 2.1 configs列表
      # 2.2 约束条件

    # yaml file的名字 、
    # group name； timestamp；detailed；delete
    group_dict = {}
    group_dict.update({"id":[]})
    group_dict.update({"time":[]})
    group_dict.update({"name":[]})
    folder_path = "/slam_hive_results/custom_analysis_group"
    sub_folder_list = os.listdir(folder_path)
    print(sub_folder_list)
    sub_folder_list.sort(reverse=True)
    for folder_name in sub_folder_list: ####
        if os.path.isdir(folder_path + "/" +folder_name):
            # 判断该文件夹是否完成
            if os.path.exists(folder_path + "/" +folder_name+"/finished"):
                print(folder_name)
                
                # 读取yaml file
                yaml_files = []
                for filename in os.listdir(folder_path + "/" +folder_name):
                    if filename.startswith(str(folder_name)) and filename.endswith(".yaml"):
                        yaml_files.append(os.path.join(folder_path + "/" +folder_name, filename))
                if len(yaml_files) != 1:
                    return jsonify(result='success')

                yaml_file = yaml_files[0]

                with open(yaml_file, 'r') as yf:
                    data = yaml.safe_load(yf)

                    if 'is_visualized' not in data:
                        continue
                    if data['is_visualized'] == 0:
                        continue
                    


                f = open(folder_path + "/" +folder_name+"/info.txt", "r")
                content = f.read()
                group_dict["id"].append(folder_name)
                group_dict["time"].append(content.split("\n")[1].split("time:")[1])
                group_dict["name"].append(content.split("\n")[2].split(":")[1])
                f.close()
                


    # configs = MappingTaskConfig.query.order_by(MappingTaskConfig.id.desc()).all()
    # algos = Algorithm.query.order_by(Algorithm.id.desc()).all()
    # datasets = Dataset.query.order_by(Dataset.id.desc()).all()
    # mappingTasks_number = {}
    # for i in range(len(configs)):
    #     mappingTasks_number.update({configs[i].id: len(configs[i].mappingTasks)})
    # db.session.commit()
    # 排个序

    return render_template('/customanalysis/index.html', group_dict = group_dict, length = len(group_dict['id']))

@app.route('/analysis/create', methods=['POST','GET'])
def create_analysis_group():
    return render_template('/customanalysis/create.html')

@app.route('/analysis/create/submit', methods=['POST', 'GET'])
def submit_analysis_group():
    # print(json.loads(request.get_data()))
    try:
        data = yaml.load(json.loads(request.get_data())['0'], Loader=yaml.FullLoader)
    except Exception as e:
        print("error: ", e)
        return False, "File format error, please check the yaml file!"
    # print(data)
    configs = MappingTaskConfig.query.order_by(MappingTaskConfig.id.desc()).all()
    comb_configs = CombMappingTaskConfig.query.order_by(CombMappingTaskConfig.id.desc()).all()
    print(comb_configs)

    check_result, return_str = custom_analysis_resolver.check_resolver(data, configs, comb_configs)
    
    if check_result:
        return jsonify(result='success@@@'+return_str)
    else:
        return jsonify(result=return_str)

@app.route('/analysis/show/<int:id>', methods=['POST', 'GET'])
def show_custom_analysis(id):
    status = ""

    # # 首先读取状态
    # if os.path.exists("/slam_hive_results/custom_analysis_group/" + str(id) + "/finished"):
    #     status = "finished"
    # elif os.path.exists("/slam_hive_results/custom_analysis_group/" + str(id) + "/running"):
    #     status = "running"
    #     return render_template('/customanalysis/show.html', status = status)
    # else: # os.path.exists("/slam_hive_results/custom_analysis_group/" + str(id) + "/failed"):
    #     status = "falied"
    #     return render_template('/customanalysis/show.html', status = status)       

    # 根据这个id
    # 读取analysis_index.txt文件，看看都有哪些定制化分析
    f = open("/slam_hive_results/custom_analysis_group/" + str(id) + "/analysis_index.txt")
    content = f.read()
    f.close()



    analysis_choose = content.split('\n')
    img_list_list = []
    folder_name = []
    folder_name.append("evo_stuff")
    folder_name.append("evo_stuff")
    folder_name.append("accuracy_metrics_comparison")
    folder_name.append("usage_comparison")
    folder_name.append("scatter")
    folder_name.append("3d_scatter")
    folder_name.append("repeatability_test")
    title_name = []
    title_name.append("1_trajectory_comparison")
    title_name.append("2_accuracy_metrics_comparison")
    title_name.append("3_accuracy_metrics_comparison")
    title_name.append("4_usage_metrics_comparison")
    title_name.append("6_scatter_diagram")
    title_name.append("7_3d_scatter_diagram")
    title_name.append("8_repeatability_test")
    k_v = {}
    k_v.update({1:["evo_stuff", "1_trajectory_comparison"]})
    k_v.update({2:["evo_stuff", "2_accuracy_metrics_comparison"]})
    k_v.update({3:["accuracy_metrics_comparison", "3_accuracy_metrics_comparison"]})
    k_v.update({4:["usage_comparison", "4_usage_metrics_comparison"]})
    k_v.update({6:["scatter", "6_scatter_diagram"]})
    k_v.update({7:["3d_scatter", "7_3d_scatter_diagram"]})
    k_v.update({8:["repeatability_test", "8_repeatability_test"]})
    img_number = []

    # 1 2; 3; 4; 5 6;
    # i_number = [1,2,3,4,6,7]
    # for i in range(7):
    for i in range(len(analysis_choose)):
        print(analysis_choose[i])
        img_list_list.append([])
        # 这里要a改一次：首先要判断一下有没有这个key（解决历史遗留问题，并且后续添加也要在这里改）

        if analysis_choose[i] == "":
            continue

        if analysis_choose[i].split(':')[1] == "1":
            # 参考另外一张图片的
            # 需要的是图片路径的列表
            # 二维数组 存储每一个的图片

            current_id = int(analysis_choose[i].split(':')[0])

            imgfolder = "/slam_hive_results/custom_analysis_group/" + str(id) + "/" + k_v[current_id][0] # folder_name[i]
                # Get all images in a folder and subfolders
            for path, dirnames, filenames in os.walk(imgfolder):
                for filename in filenames:
                    if filename.lower().endswith(('.bmp', '.dib', '.png', '.jpg', '.jpeg', '.pbm', '.pgm', '.ppm', '.tif', '.tiff')):
                        if filename.lower().endswith(('-img0.png')): ##################################### b
                            continue
                        if current_id == 1 and ("ape" in filename or "rpe" in filename):
                            continue
                        if current_id == 2 and "traj" in filename:
                            continue
                        img_list_list[i].append(os.path.join(path, filename))
        img_number.append(len(img_list_list[i]))
        
        yaml_content = ""
        for path, dirnames, filenames in os.walk("/slam_hive_results/custom_analysis_group/" + str(id)):
            for filename in filenames:
                if filename.lower().endswith(('.yaml')):
                    f = open("/slam_hive_results/custom_analysis_group/" + str(id) + "/" + filename)
                    yaml_content = f.read()
                    f.close()

    f = open("/slam_hive_results/custom_analysis_group/" + str(id) + "/info.txt")
    
    content = f.read()
    f.close()
    import ast
    config_id_list = ast.literal_eval((content.split("\n")[3].split(":")[1]))

    parameters_list = ast.literal_eval((content.split("\n")[4].split(":")[1]))

    # 还需要一个parameter列表
    evaluation_list = []
    performance_list = []
    if analysis_choose[6].split(':')[1] == "1":
        for task in MappingTaskConfig.query.get(config_id_list[0]).mappingTasks:
            evaluation_list.append(task.evaluation.evoResults)
            performance_list.append(task.performanceresults)
    config_number = len(config_id_list)

    return render_template('/customanalysis/show.html', status = status, analysis_id = id,
                                                    config_id_list = config_id_list,
                                                    yaml_content = yaml_content,
                                                    img_list_list = img_list_list,
                                                    title_name = title_name,
                                                    number = len(title_name),
                                                    img_number = img_number,
                                                    parameters_list = parameters_list,
                                                    evaluation_list = evaluation_list,
                                                    performance_list = performance_list,
                                                    config_number = config_number)

@app.route('/analysis/download_single/<int:id>')
def download_custom_analysis(id):
    download_folder_path = os.path.join("/slam_hive_results/custom_analysis_group", str(id))
    download_zip_path = os.path.join("/slam_hive_results/custom_analysis_group", str(id) + ".zip")
    # if os.path.exists(download_zip_path):
    #     return send_from_directory(download_zip_path, as_attachment=True)
    # else:
    zipDir(download_folder_path, download_zip_path)
    return send_from_directory("/slam_hive_results/custom_analysis_group", str(id) + ".zip", as_attachment=True)


# for task5 6 traj success
@app.route('/analysis/diagram/digt/show',methods=['GET','POST'])
def show_diagramt():
    data = json.loads(request.get_data())
    print(data)

    custom_id = data['custom_id']
    x_axis = data['x-axis']

    f = open("/slam_hive_results/custom_analysis_group/" + str(custom_id) + "/info.txt")
    
    content = f.read()
    f.close()
    import ast
    config_id_list = ast.literal_eval((content.split("\n")[3].split(":")[1]))

    print(config_id_list)

    tray_unsuccess_id_list = ast.literal_eval((content.split("\n")[5].split(":")[1]))
    print(tray_unsuccess_id_list)

    # config_id_list_old = config_id_list
    # config_id_list  = []
    # for id in config_id_list_old:
    #     if id not in  tray_unsuccess_id_list:
    #         config_id_list.append(id)
 

    # 二维数组
    # x+1行，number+1列
    x_number_list = []
    config_value_dict = {}
    for id in config_id_list:
        config = MappingTaskConfig.query.get(id)
        for paramValue in config.paramValues:
            if x_axis == paramValue.name:
                x_v = float(paramValue.value)
                config_value_dict.update({id: x_v})
                if x_v not in x_number_list:
                    
                    x_number_list.append(x_v)
                    
                    break
    
    row_number = 0
    for i in range(len(x_number_list)):
        curr = 0
        for j in range(len(config_id_list)):
            if config_value_dict[config_id_list[j]] == x_number_list[i]:
                curr += 1
        
        row_number = max(row_number, curr)

    print("R", row_number)
    print(x_number_list)

    table_list = []
    table_list.append([])
    for i in range(len(x_number_list)):
        table_list[0].append("id")
        table_list[0].append(x_number_list[i])
    print(config_value_dict)

    for i in range(row_number):
        table_list.append([])
        for j in range(len(x_number_list) * 2):
            table_list[i+1].append("")
    
    rate_list = []

    for i in range(len(x_number_list)):
        idx = 1
        dui = 0
        cuo = 0
        for j in range(len(config_id_list)):
            id = config_id_list[j]
            # print("idx ",idx)
            if config_value_dict[id] == x_number_list[i]:
                table_list[idx][2*i] = id
                if id in tray_unsuccess_id_list:
                    table_list[idx][2*i+1] = "×"
                    cuo += 1
                else:
                    table_list[idx][2*i+1] = "√"
                    dui += 1
                idx += 1
        cc = str(dui) + "/" + str(dui + cuo) + "; " + str(dui/(dui+cuo))
        rate_list.append(cc)
    
    table_list.append([])
    for i in range(len(x_number_list)):
        table_list[len(table_list) - 1].append("success rate")
        table_list[len(table_list) - 1].append(rate_list[i])



    # for i in range(len(config_id_list)):
    #     for j in range(len(x_number_list) + 1):
    #         id = config_id_list[i]
    #         if config_value_dict[id] != x_number_list[j-1]:
    #             table_list[i+1].append("/")
    #         else:
    #             if id in tray_unsuccess_id_list:
    #                 table_list[i+1].append("Unsuccess")
    #             else:
    #                 table_list[i+1].append("Success")

    print(table_list)
  
    # 定义表头和表格数据
    headers = table_list[0]
    rows = []
    for i in range(len(table_list) - 1):
        rows.append(table_list[i+1])

      # 创建表格的 HTML 代码
    table_html = '<table border="1">'
    
    # 添加表头
    table_html += '<tr>'
    for header in headers:
        table_html += f'<th>{header}</th>'
    table_html += '</tr>'
    
    # 添加表格数据
    for row in rows:
        table_html += '<tr>'
        for cell in row:
            table_html += f'<td>{cell}</td>'
        table_html += '</tr>'
    
    table_html += '</table>'

    # 定义自定义样式
    style = """
    <style>
    table {
        border-collapse: collapse;
        width: 100%;
    }
    table, th, td {
        border: 1px solid black;
    }
    th, td {
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
    }
    tr:first-child th, th:first-child {
        background-color: #ffcccc;
    }
    </style>
    """

    # 定义 HTML 模板
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Table Example</title>
        {style}
    </head>
    <body>
        <h1>Table Example</h1>
        {table_html}
    </body>
    </html>
    """

    return render_template_string(html_template)



    # return Markup(scatter.render_embed())
    # bar.render('templates\index.html')




# 需要获取数据的步骤一样

# for task5 6
@app.route('/analysis/diagram/dig1/show',methods=['GET','POST'])
def show_diagram1():
    data = json.loads(request.get_data())
    print(data)

    custom_id = data['custom_id']
    x_axis = data['x-axis']
    y_axis = data['y-axis']

    x_unit = ""
    y_unit = ""

    Extend_axis = [0,0,0]
    Extend_attribute = ['', '', '']

    if "ATE" in x_axis or "RPE" in x_axis:
        x_unit = "(m)"
        Extend_axis[0] = 1
        Extend_attribute[0] = x_axis
    elif "CPU" in x_axis:
        x_unit = "(cores)"
    elif "Memory" in x_axis:
        x_unit = "(MB)"
    elif "frequency" in x_axis:
        x_unit = "(Hz)"

    if "ATE" in y_axis or "RPE" in y_axis:
        y_unit = "(m)"
        Extend_axis[1] = 1
        Extend_attribute[1] = y_axis
    elif "CPU" in y_axis:
        y_unit = "(cores)"
    elif "Memory" in y_axis:
        y_unit = "(MB)"
    elif "frequency" in y_axis:
        y_unit = "(Hz)"

    f = open("/slam_hive_results/custom_analysis_group/" + str(custom_id) + "/info.txt")
    
    content = f.read()
    f.close()
    import ast
    config_id_list = ast.literal_eval((content.split("\n")[3].split(":")[1]))

    print(config_id_list)

    tray_unsuccess_id_list = ast.literal_eval((content.split("\n")[5].split(":")[1]))
    print(tray_unsuccess_id_list)

    config_id_list_old = config_id_list
    config_id_list  = []
    for id in config_id_list_old:
        if id not in  tray_unsuccess_id_list:
            config_id_list.append(id)
 

    # 需要解析custom的id


        # 首先判断group中的config -- algo：任意都可以（但是貌似不是同一个算法意义不大）;dataset: 相同

    diagram_data = []
    diagram_data_param = []
    for i in range(len(config_id_list)):
        # 获取x y对应
        x_v = 0
        y_v = 0
        current_config = MappingTaskConfig.query.get(config_id_list[i])
        evoResults = current_config.mappingTasks[0].evaluation.evoResults
        performanceresults = current_config.mappingTasks[0].performanceresults
        if x_axis == 'ATE-rmse':
            x_v = evoResults.ate_rmse
        elif x_axis == 'ATE-mean':
            x_v = evoResults.ate_mean
        elif x_axis == 'ATE-median':
            x_v = evoResults.ate_median
        elif x_axis == 'ATE-std':
            x_v = evoResults.ate_std
        elif x_axis == 'ATE-min':
            x_v = evoResults.ate_min
        elif x_axis == 'ATE-max':
            x_v = evoResults.ate_max
        elif x_axis == 'ATE-sse':
            x_v = evoResults.ate_sse
        elif x_axis == 'RPE-mean':
            x_v = evoResults.rpe_mean
        elif x_axis == 'RPE-median':
            x_v = evoResults.rpe_median
        elif x_axis == 'RPE-std':
            x_v = evoResults.rpe_std
        elif x_axis == 'RPE-min':
            x_v = evoResults.rpe_min
        elif x_axis == 'RPE-max':
            x_v = evoResults.rpe_max
        elif x_axis == 'RPE-sse':
            x_v = evoResults.rpe_sse
        elif x_axis == 'RPE-rmse':
            x_v = evoResults.rpe_rmse
        elif x_axis == 'CPU-max':
            x_v = performanceresults.max_cpu
        elif x_axis == 'CPU-mean':
            x_v = performanceresults.mean_cpu
        elif x_axis == 'Memory-max':
            x_v = performanceresults.max_ram
        else:
            # parameter
            for paramValue in current_config.paramValues:
                if x_axis == paramValue.name:
                    x_v = float(paramValue.value)
                    break

        if y_axis == 'ATE-rmse':
            y_v = evoResults.ate_rmse
        elif y_axis == 'ATE-mean':
            y_v = evoResults.ate_mean
        elif y_axis == 'ATE-median':
            y_v = evoResults.ate_median
        elif y_axis == 'ATE-std':
            y_v = evoResults.ate_std
        elif y_axis == 'ATE-min':
            y_v = evoResults.ate_min
        elif y_axis == 'ATE-max':
            y_v = evoResults.ate_max
        elif y_axis == 'ATE-sse':
            y_v = evoResults.ate_sse
        elif y_axis == 'RPE-mean':
            y_v = evoResults.rpe_mean
        elif y_axis == 'RPE-median':
            y_v = evoResults.rpe_median
        elif y_axis == 'RPE-std':
            y_v = evoResults.rpe_std
        elif y_axis == 'RPE-min':
            y_v = evoResults.rpe_min
        elif y_axis == 'RPE-max':
            y_v = evoResults.rpe_max
        elif y_axis == 'RPE-sse':
            y_v = evoResults.rpe_sse
        elif y_axis == 'RPE-rmse':
            y_v = evoResults.rpe_rmse
        elif y_axis == 'CPU-max':
            y_v = performanceresults.max_cpu
        elif y_axis == 'CPU-mean':
            y_v = performanceresults.mean_cpu
        elif y_axis == 'Memory-max':
            y_v = performanceresults.max_ram
        else:
            # parameter
            for paramValue in current_config.paramValues:
                if y_axis == paramValue.name:
                    y_v = float(paramValue.value)
                    break        
        diagram_data.append([x_v, y_v])
        diagram_data_param.append(current_config.paramValues)


    x_data = [d[0] for d in diagram_data]
    y_data = [d[1] for d in diagram_data]

    print(diagram_data)

    # 需要按照算法进行分类
    #因为知道数据集一定是一样的
    
    y_new_data = []
    x_new_data = []

    y_max = -10000
    y_min = 1000000
    x_max = -100000
    x_min = 1000000


    category_list = []
    param_list = []
    for i in range(len(y_data)):
        # algo_id = MappingTaskConfig.query.get(config_id_list[i]).algorithm.id
        algo_imageTag = MappingTaskConfig.query.get(config_id_list[i]).algorithm.imageTag
        dataset_name = MappingTaskConfig.query.get(config_id_list[i]).dataset.name
        
        
        # category =  + "  " +  algo_imageTag
        category = algo_imageTag + "  " +  dataset_name
        
        if category not in category_list:
            category_list.append(category)
            param_list.append(MappingTaskConfig.query.get(config_id_list[i]).paramValues)
            y_new_data.append([])
            x_new_data.append([])

        y_max = max(y_max, y_data[i])
        y_min = min(y_min, y_data[i])
        x_max = max(x_max, x_data[i])
        x_min = min(x_max, x_data[i])

        # temp_dict = {'value': y_data[i], "data": ["config id: _" + str(config_id_list[i]), 111]}
        param_str = ""
        params = MappingTaskConfig.query.get(config_id_list[i]).paramValues
        for param in params:
            # if param.valueType == "int" or param.valueType == "float":
            # print(param.algoParam.paramType)
            if param.algoParam.paramType == "Algorithm" or param.algoParam.paramType == "Dataset" or param.algoParam.paramType == "Dataset remap":
                param_str += param.keyName + ":  " + param.value + "<br>"

        temp_dict = [y_data[i], param_str]
        for j in range(len(category_list)):
            if category == category_list[j]:

                y_new_data[j].append(temp_dict)
        
                x_new_data[j].append([x_data[i]])


    # print(y_new_data)
    # print(x_new_data)
    scatter = (
        Scatter(init_opts=opts.InitOpts(width="1700px",height="750px",))
        .add_xaxis(
            # xaxis_data=[8,8,8,8,8,8],
            xaxis_data=[],
        )
        .set_global_opts(

            xaxis_opts=opts.AxisOpts(
                type_="value", 
                axistick_opts=opts.AxisTickOpts(is_show=True),
                splitline_opts=opts.SplitLineOpts(is_show=True),
                min_='dataMin',
                max_='dataMax',
                name=x_axis + " " + x_unit,
                name_location = "middle",
                name_textstyle_opts=opts.LabelOpts(font_family="DejaVu Sans", font_size=20)
            ),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
                min_='dataMin',
                max_ = "dataMax",
                name=y_axis + " " + y_unit,
                name_location = "middle",
                name_textstyle_opts=opts.LabelOpts(font_family="DejaVu Sans", font_size=20)
                ),

            tooltip_opts=opts.TooltipOpts(
                formatter=JsCode(
                    "function (params) {console.log(params.value[2]);return '('+params.value[0] + ' :' + params.value[1]+') ; <br> '+params.value[2];}"
                )
            ),
            legend_opts=opts.LegendOpts(
                type_ = "scroll"
            ),
        )
    )



   # 基础颜色映射（按B分类）
    unique_categories = category_list
    unique_A = sorted(set(cat.split('  ')[0] for cat in unique_categories))
    unique_B = sorted(set(cat.split('  ')[1] for cat in unique_categories))


    # 基础调色板husl  hsv
    base_palette = sns.color_palette("dark", len(unique_A))

    # 创建颜色字典，按A和B分类
    color_dict = {}
    for i, a in enumerate(unique_A):
        # sub_palette = sns.light_palette(base_palette[i], n_colors=len(unique_B))
        sub_palette = sns.light_palette(base_palette[i], len(unique_B) * 5)
        for j, b in enumerate(unique_B):
            color_dict[f"{a}  {b}"] = sub_palette[j*5 + 4]    


    def rgb_to_hex(rgb_tuple):
        # 将每个浮点数乘以255并四舍五入成整数
        r, g, b = [int(round(x * 255)) for x in rgb_tuple]
        
        # 将整数转换为两位的16进制数，并连接在一起
        return f'#{r:02x}{g:02x}{b:02x}'

    for i in range(len(category_list)):
        # print(color_dict[category_list[i]])
        scatter.add_xaxis(x_new_data[i])
        scatter.add_yaxis(
            series_name=str(category_list[i]),
            y_axis=y_new_data[i],
            #symbol_size=20,
            label_opts=opts.LabelOpts(
                is_show=False,
            #     formatter=JsCode(
            #     "function(params){return params.value[0] +' : '+ params.value[1];}"
            # )
            ),
            color=rgb_to_hex(color_dict[category_list[i]]),
            symbol_size = 15,
            
        )
  ####

    return Markup(scatter.render_embed())
    # bar.render('templates\index.html')

@app.route('/analysis/diagram/dig1_extend/show',methods=['GET','POST'])
def show_diagram1_extend():
    data = json.loads(request.get_data())
    print(data)

    custom_id = data['custom_id']
    x_axis = data['x-axis']
    y_axis = data['y-axis']

    x_unit = ""
    y_unit = ""

    Extend_axis = [0,0,0]
    Extend_attribute = ['', '', '']

    if "ATE" in x_axis or "RPE" in x_axis:
        x_unit = "(m)"
        Extend_axis[0] = 1
        Extend_attribute[0] = x_axis
    elif "CPU" in x_axis:
        x_unit = "(cores)"
    elif "Memory" in x_axis:
        x_unit = "(MB)"
    elif "frequency" in x_axis:
        x_unit = "(Hz)"

    if "ATE" in y_axis or "RPE" in y_axis:
        y_unit = "(m)"
        Extend_axis[1] = 1
        Extend_attribute[1] = y_axis
    elif "CPU" in y_axis:
        y_unit = "(cores)"
    elif "Memory" in y_axis:
        y_unit = "(MB)"
    elif "frequency" in y_axis:
        y_unit = "(Hz)"

    f = open("/slam_hive_results/custom_analysis_group/" + str(custom_id) + "/info.txt")
    
    content = f.read()
    f.close()
    import ast
    config_id_list = ast.literal_eval((content.split("\n")[3].split(":")[1]))

    print(config_id_list)

    tray_unsuccess_id_list = ast.literal_eval((content.split("\n")[5].split(":")[1]))
    print(tray_unsuccess_id_list)

    config_id_list_old = config_id_list
    config_id_list  = []
    for id in config_id_list_old:
        if id not in  tray_unsuccess_id_list:
            config_id_list.append(id)
 
    folder_path = "/slam_hive_results/custom_analysis_group/" + str(custom_id)
    yaml_files = []
    for filename in os.listdir(folder_path):
        if filename.startswith(str(custom_id)) and filename.endswith(".yaml"):
            yaml_files.append(os.path.join(folder_path, filename))
    if len(yaml_files) != 1:
        return jsonify(result='success')

    file_name = yaml_files[0]

    extend_choose = 0
    extend_threshold = []
    extend_multiple = []
    data = ""

    with open(file_name, 'r') as f:
        data = yaml.safe_load(f)
        if "extend_choose" in data['evaluation_form']['6_scatter_diagram']:
            if  data['evaluation_form']['6_scatter_diagram']['extend_choose'] == 1:
                extend_choose = 1
                extend_threshold = data['evaluation_form']['6_scatter_diagram']['extend_threshold']
                extend_multiple = data['evaluation_form']['6_scatter_diagram']['extend_multiple']
            else:
                extend_choose = 0    

    old_suit_configs_list = []
    suit_configs_list = []
    for i in range(len(config_id_list_old)):
        old_suit_configs_list.append(MappingTaskConfig.query.get(config_id_list_old[i]))
    
    for i in range(len(config_id_list)):
        suit_configs_list.append(MappingTaskConfig.query.get(config_id_list[i]))
    
    
    for i in range(len(Extend_attribute)):
        if Extend_axis[i] == 1:
            new_val = ""
            if Extend_attribute[i].split("-")[0] == "ATE":
                new_val += "ate_"
            else:
                new_val += "rpe_"

            new_val += Extend_attribute[i].split("-")[1]
            Extend_attribute[i] = new_val

    ret = custom_analysis_resolver.get_Extend_accuracy(old_suit_configs_list, suit_configs_list, Extend_axis, Extend_attribute, extend_threshold,extend_multiple)

    algorithm_id_dict = {}
    for config in old_suit_configs_list:
        # 给config分类
        if config.algorithm.imageTag not in algorithm_id_dict.keys():
            algorithm_id_dict.update({config.algorithm.imageTag: [config]})
        else:
            algorithm_id_dict[config.algorithm.imageTag].append(config)
    dataset_id_dict = {}
    for config in old_suit_configs_list:
        if config.dataset.name not in dataset_id_dict.keys():
            dataset_id_dict.update({config.dataset.name: [config]})
        else:
            dataset_id_dict[config.dataset.name].append(config)


    diagram_data = []


    for key, value in dataset_id_dict.items(): # algorithm_id_dict.items():
        # 生成一个color
        # 其他dataset的color以这个为中心
        for dkey, dvalue in dataset_id_dict.items(): # dataset_id_dict.items():
            for config in value:
                # 这个config必须在dvalue中
                flag = False
                for dconfig in dvalue:
                    if config.id == dconfig.id:
                        flag = True
                        break
                if flag == False:
                    continue

                # 获取x y对应
                x_v = 0
                y_v = 0
                # category = key + "  " + dkey
                category = dkey + "  " + key


                # print(x_axis, y_axis)


                if Extend_axis[0] == 1:
                    x_v = ret[0][config.id][2]
                else:
                    # print("?????????")
                    performanceresults = config.mappingTasks[0].performanceresults

                    if x_axis == 'CPU-max':
                        x_v = performanceresults.max_cpu
                    elif x_axis == 'CPU-mean':
                        x_v = performanceresults.mean_cpu
                    elif x_axis == 'Memory-max':
                        x_v = performanceresults.max_ram
                    else:
                        # parameter
                        for paramValue in config.paramValues:
                            if x_axis == paramValue.name:
                                x_v = float(paramValue.value)
                                break
                

                if Extend_axis[1] == 1:
                    y_v = ret[1][config.id][2]  
                else:
                    # print("?????????")
                    performanceresults = config.mappingTasks[0].performanceresults
                 
                    if y_axis == 'cpu_max':
                        y_v = performanceresults.max_cpu
                    elif y_axis == 'cpu_mean':
                        y_v = performanceresults.mean_cpu
                    elif y_axis == 'ram_max':
                        y_v = performanceresults.max_ram
                    else:
                        # parameter
                        for paramValue in config.paramValues:
                            if y_axis == paramValue.name:
                                y_v = float(paramValue.value)
                                break    
  


                # diagram_data.append([x_v, y_v, key])
                diagram_data.append([x_v, y_v])       

    print(diagram_data)
    x_data = [d[0] for d in diagram_data]
    y_data = [d[1] for d in diagram_data]
    
    y_new_data = []
    x_new_data = []

    y_max = -10000
    y_min = 1000000
    x_max = -100000
    x_min = 1000000


    category_list = []
    param_list = []
    for i in range(len(y_data)):
        # algo_id = MappingTaskConfig.query.get(config_id_list[i]).algorithm.id
        algo_imageTag = MappingTaskConfig.query.get(config_id_list_old[i]).algorithm.imageTag
        dataset_name = MappingTaskConfig.query.get(config_id_list_old[i]).dataset.name
        # category = dataset_name + "  " +  algo_imageTag
        category = algo_imageTag + "  " +  dataset_name
        
        
        if category not in category_list:
            category_list.append(category)
            param_list.append(MappingTaskConfig.query.get(config_id_list_old[i]).paramValues)
            y_new_data.append([])
            x_new_data.append([])
        # print("sfdssd", y_data[i])
        y_max = max(y_max, y_data[i])
        y_min = min(y_min, y_data[i])
        x_max = max(x_max, x_data[i])
        x_min = min(x_max, x_data[i])

        # temp_dict = {'value': y_data[i], "data": ["config id: _" + str(config_id_list[i]), 111]}
        param_str = ""
        params = MappingTaskConfig.query.get(config_id_list_old[i]).paramValues
        for param in params:
            # if param.valueType == "int" or param.valueType == "float":
            # print(param.algoParam.paramType)
            if param.algoParam.paramType == "Algorithm" or param.algoParam.paramType == "Dataset" or param.algoParam.paramType == "Dataset remap":
                param_str += param.keyName + ":  " + param.value + "<br>"

        temp_dict = [y_data[i], param_str]
        for j in range(len(category_list)):
            if category == category_list[j]:

                y_new_data[j].append(temp_dict)
        
                x_new_data[j].append([x_data[i]])


    # print(y_new_data)
    # print(x_new_data)
    scatter = (
        Scatter(init_opts=opts.InitOpts(width="1700px",height="850px",))
        .add_xaxis(
            # xaxis_data=[8,8,8,8,8,8],
            xaxis_data=[],
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="Extend",
                pos_left="center",
                pos_top="bottom"  # 标题位置设置在底部
            ),
            xaxis_opts=opts.AxisOpts(
                type_="value", 
                axistick_opts=opts.AxisTickOpts(is_show=True),
                splitline_opts=opts.SplitLineOpts(is_show=True),
                min_='dataMin',
                max_='dataMax',
                name=x_axis + " " + x_unit,
                name_location = "middle",
                name_textstyle_opts=opts.LabelOpts(font_family="DejaVu Sans", font_size=20)
            ),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                axistick_opts=opts.AxisTickOpts(is_show=False),
                splitline_opts=opts.SplitLineOpts(is_show=False),
                min_='dataMin',
                max_ = "dataMax",
                name=y_axis + " " + y_unit,
                name_location = "middle",
                name_textstyle_opts=opts.LabelOpts(font_family="DejaVu Sans", font_size=20)
                ),

            tooltip_opts=opts.TooltipOpts(
                formatter=JsCode(
                    "function (params) {console.log(params.value[2]);return '('+params.value[0] + ' :' + params.value[1]+') ; <br> '+params.value[2];}"
                )
            ),
            legend_opts=opts.LegendOpts(
                type_ = "scroll"
            ),

        )
    )



   # 基础颜色映射（按B分类）
    unique_categories = category_list
    unique_A = sorted(set(cat.split('  ')[0] for cat in unique_categories))
    unique_B = sorted(set(cat.split('  ')[1] for cat in unique_categories))


    # 基础调色板husl  hsv
    base_palette = sns.color_palette("dark", len(unique_A))

    # 创建颜色字典，按A和B分类
    color_dict = {}
    for i, a in enumerate(unique_A):
        # sub_palette = sns.light_palette(base_palette[i], n_colors=len(unique_B))
        sub_palette = sns.light_palette(base_palette[i], len(unique_B) * 5)
        for j, b in enumerate(unique_B):
            color_dict[f"{a}  {b}"] = sub_palette[j*5 + 4]    


    def rgb_to_hex(rgb_tuple):
        # 将每个浮点数乘以255并四舍五入成整数
        r, g, b = [int(round(x * 255)) for x in rgb_tuple]
        
        # 将整数转换为两位的16进制数，并连接在一起
        return f'#{r:02x}{g:02x}{b:02x}'

    for i in range(len(category_list)):
        # print(color_dict[category_list[i]])
        scatter.add_xaxis(x_new_data[i])
        scatter.add_yaxis(
            series_name=str(category_list[i]),
            y_axis=y_new_data[i],
            #symbol_size=20,
            label_opts=opts.LabelOpts(
                is_show=False,
            #     formatter=JsCode(
            #     "function(params){return params.value[0] +' : '+ params.value[1];}"
            # )
            ),
            color=rgb_to_hex(color_dict[category_list[i]]),
            symbol_size = 15,
            
        )
  ####

    return Markup(scatter.render_embed())
    # bar.render('templates\index.html')


# 步骤和那边一样

# /如果选择的话，然后这个有的话 就直接生成
# 算了 不管有没有 都直接创建

# 同时保存一个表格文件

@app.route('/analysis/diagram/dig1',methods=['GET','POST'])
def create_diagram1():
    data = json.loads(request.get_data())
    print(data)

    custom_id = data['custom_id']
    x_axis = data['x-axis']
    y_axis = data['y-axis']

    x_unit = ""
    y_unit = ""
    z_unit = ""

    Extend_axis = [0,0,0]
    Extend_attribute = ['', '', '']

    if "ATE" in x_axis or "RPE" in x_axis:
        x_unit = "(m)"
        Extend_axis[0] = 1
        Extend_attribute[0] = x_axis
    elif "CPU" in x_axis:
        x_unit = "(cores)"
    elif "Memory" in x_axis:
        x_unit = "(MB)"
    elif "frequency" in x_axis:
        x_unit = "(Hz)"

    if "ATE" in y_axis or "RPE" in y_axis:
        y_unit = "(m)"
        Extend_axis[1] = 1
        Extend_attribute[1] = y_axis
    elif "CPU" in y_axis:
        y_unit = "(cores)"
    elif "Memory" in y_axis:
        y_unit = "(MB)"
    elif "frequency" in y_axis:
        y_unit = "(Hz)"
      


    f = open("/slam_hive_results/custom_analysis_group/" + str(custom_id) + "/info.txt")
    
    content = f.read()
    f.close()
    import ast
    config_id_list = ast.literal_eval((content.split("\n")[3].split(":")[1]))

    print(config_id_list)

    tray_unsuccess_id_list = ast.literal_eval((content.split("\n")[5].split(":")[1]))
    print(tray_unsuccess_id_list)

    config_id_list_old = config_id_list
    config_id_list  = []
    for id in config_id_list_old:
        if id not in  tray_unsuccess_id_list:
            config_id_list.append(id)

    diagram_data = []
    x_data = []
    y_data = []
    algorithm_id_list = []
    category_list = []
    for i in range(len(config_id_list)):
        # 获取x y对应
        x_v = 0
        y_v = 0
        current_config = MappingTaskConfig.query.get(config_id_list[i])
        evoResults = current_config.mappingTasks[0].evaluation.evoResults
        performanceresults = current_config.mappingTasks[0].performanceresults
        if x_axis == 'ATE-rmse':
            x_v = evoResults.ate_rmse
        elif x_axis == 'ATE-mean':
            x_v = evoResults.ate_mean
        elif x_axis == 'ATE-median':
            x_v = evoResults.ate_median
        elif x_axis == 'ATE-std':
            x_v = evoResults.ate_std
        elif x_axis == 'ATE-min':
            x_v = evoResults.ate_min
        elif x_axis == 'ATE-max':
            x_v = evoResults.ate_max
        elif x_axis == 'ATE-sse':
            x_v = evoResults.ate_sse
        elif x_axis == 'RPE-mean':
            x_v = evoResults.rpe_mean
        elif x_axis == 'RPE-median':
            x_v = evoResults.rpe_median
        elif x_axis == 'RPE-std':
            x_v = evoResults.rpe_std
        elif x_axis == 'RPE-min':
            x_v = evoResults.rpe_min
        elif x_axis == 'RPE-max':
            x_v = evoResults.rpe_max
        elif x_axis == 'RPE-sse':
            x_v = evoResults.rpe_sse
        elif x_axis == 'RPE-rmse':
            x_v = evoResults.rpe_rmse
        elif x_axis == 'CPU-max':
            x_v = performanceresults.max_cpu
        elif x_axis == 'CPU-mean':
            x_v = performanceresults.mean_cpu
        elif x_axis == 'Memory-max':
            x_v = performanceresults.max_ram
        else:
            # parameter
            for paramValue in current_config.paramValues:
                if x_axis == paramValue.name:
                    x_v = float(paramValue.value)
                    break

        if y_axis == 'ATE-rmse':
            y_v = evoResults.ate_rmse
        elif y_axis == 'ATE-mean':
            y_v = evoResults.ate_mean
        elif y_axis == 'ATE-median':
            y_v = evoResults.ate_median
        elif y_axis == 'ATE-std':
            y_v = evoResults.ate_std
        elif y_axis == 'ATE-min':
            y_v = evoResults.ate_min
        elif y_axis == 'ATE-max':
            y_v = evoResults.ate_max
        elif y_axis == 'ATE-sse':
            y_v = evoResults.ate_sse
        elif y_axis == 'RPE-mean':
            y_v = evoResults.rpe_mean
        elif y_axis == 'RPE-median':
            y_v = evoResults.rpe_median
        elif y_axis == 'RPE-std':
            y_v = evoResults.rpe_std
        elif y_axis == 'RPE-min':
            y_v = evoResults.rpe_min
        elif y_axis == 'RPE-max':
            y_v = evoResults.rpe_max
        elif y_axis == 'RPE-sse':
            y_v = evoResults.rpe_sse
        elif y_axis == 'RPE-rmse':
            y_v = evoResults.rpe_rmse
        elif y_axis == 'CPU-max':
            y_v = performanceresults.max_cpu
        elif y_axis == 'CPU-mean':
            y_v = performanceresults.mean_cpu
        elif y_axis == 'Memory-max':
            y_v = performanceresults.max_ram
        else:
            # parameter
            for paramValue in current_config.paramValues:
                if y_axis == paramValue.name:
                    y_v = float(paramValue.value)
                    break        
        diagram_data.append([x_v, y_v])

        # 表格形式
        # config_id  ||  x_axis(value)  | y_axis(value)  |  algorithm_tag  |  dataset_name
        # 111        ||  1              |  1             |   orb           |  euroc
        # ...

        # category = current_config.dataset.name + "  " +   current_config.algorithm.imageTag

        category = current_config.algorithm.imageTag + "  " +   current_config.dataset.name 

        if category not in category_list:
            category_list.append(category)
            x_data.append([])
            y_data.append([])
        
        for j in range(len(category_list)):
            if category == category_list[j]:
                x_data[j].append(x_v)
                y_data[j].append(y_v)

        # x_data.append(x_v)
        # y_data.append(y_v)
    csv_data = []
    config_id_title = "Config ID"
    x_axis_title = "X Axis(" + x_axis + ")"
    y_axis_title = "Y Axis(" + y_axis + ")"
    algorithm_title = "Algorithm Name"
    dataset_title = "Dataset Name"
    

    for i in range(len(config_id_list)):
        config = MappingTaskConfig.query.get(config_id_list[i])
        
        config_id = config_id_list[i]
        x_value = diagram_data[i][0]
        y_value = diagram_data[i][1]
        algorithm_name_value = config.algorithm.imageTag
        dataset_name_value = config.dataset.name

        csv_data.append({
            config_id_title: config_id,
            x_axis_title: x_value,
            y_axis_title: y_value,
            algorithm_title: algorithm_name_value,
            dataset_title: dataset_name_value
            })

    

    sub_folder_path = "/slam_hive_results/custom_analysis_group/" + str(custom_id) + "/dynamic_diagram"

    if not os.path.exists(sub_folder_path):
        os.mkdir(sub_folder_path)

    csv_path = sub_folder_path + "/" + "RawData1_x-" + x_axis + "_y-" + y_axis+".csv"

    dff = pd.DataFrame(csv_data)

    # 将DataFrame保存为CSV文件
    dff.to_csv(csv_path, index=False)


    diagram_name_pgf = "Diagram1_x-" + x_axis + "_y-" + y_axis+".pgf"
    diagram_name_png = "Diagram1_x-" + x_axis + "_y-" + y_axis+".png"
    diagram_name_pdf = "Diagram1_x-" + x_axis + "_y-" + y_axis+".pdf"
    diagram_path_pgf = sub_folder_path + "/" + diagram_name_pgf
    diagram_path_png = sub_folder_path + "/" + diagram_name_png
    diagram_path_pdf = sub_folder_path + "/" + diagram_name_pdf

    diagram_data = np.array(diagram_data)


    import matplotlib as mpl
    from matplotlib import font_manager


    # 加载DejaVuSans字体
    font_path = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    dejavusans = [f for f in font_path if 'DejaVuSans.ttf' in f][0]
    font_prop = font_manager.FontProperties(fname=dejavusans, size=12)  # 小四相当于12号字体

    mpl1 = mpl.rcParams['pdf.fonttype']
    mpl2 = mpl.rcParams['ps.fonttype']
    mpl3 = mpl.rcParams['font.family']
    mpl4 =16


    # 设置全局字体属性
    mpl.rcParams['pdf.fonttype'] = 42
    mpl.rcParams['ps.fonttype'] = 42
    mpl.rcParams['font.family'] = font_prop.get_name()
    mpl.rcParams['font.size'] = 30 # 16  # 小四字体




    fig, ax = plt.subplots(figsize=(60, 20))
  
  # 基础颜色映射（按B分类）
    unique_categories = category_list
    unique_A = sorted(set(cat.split('  ')[0] for cat in unique_categories))
    unique_B = sorted(set(cat.split('  ')[1] for cat in unique_categories))

     # 基础调色板husl  hsv
    base_palette = sns.color_palette("dark", len(unique_A))

    # 创建颜色字典，按A和B分类
    color_dict = {}
    for i, a in enumerate(unique_A):
        # sub_palette = sns.light_palette(base_palette[i], n_colors=len(unique_B))
        sub_palette = sns.light_palette(base_palette[i], len(unique_B) * 5)
        for j, b in enumerate(unique_B):
            color_dict[f"{a}  {b}"] = sub_palette[j*5 + 4]    


    for i in range(len(category_list)):
        algo = Algorithm.query.get(category[i])
        plt.scatter(x=x_data[i], y=y_data[i],edgecolor=['w'], label=category_list[i], color = color_dict[category_list[i]], s = 300)
    plt.xlabel(x_axis + " " + x_unit)
    plt.ylabel(y_axis + " " + y_unit)
    # 添加图例
    handles, labels = ax.get_legend_handles_labels()
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    legend = ax.legend(
        handles, labels,
        loc='upper left',
        bbox_to_anchor=(1, 1),
        borderaxespad=0.
    )


    # 设置图例的字体大小和边框
    legend.prop.set_size(6)
    legend.get_frame().set_edgecolor('black')
    legend.get_frame().set_linewidth(0.5)

    # 调整子图的布局
    plt.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)

    # 设置坐标轴的长宽比
    # ax.set_aspect(aspect=1.0/ax.get_data_ratio(), adjustable='datalim')
    # fig = sns.scatterplot(x=x_axis, y=y_axis, data=df)
    #scatter_fig = fig.get_figure()
    plt.savefig(diagram_path_pgf, dpi = 400)
    plt.savefig(diagram_path_png, dpi = 400)
    plt.savefig(diagram_path_pdf, dpi = 400)


    ####
    # 读取文件 判断是否有
    # 读取前缀为id.后缀为yaml
    folder_path = "/slam_hive_results/custom_analysis_group/" + str(custom_id)
    yaml_files = []
    for filename in os.listdir(folder_path):
        if filename.startswith(str(custom_id)) and filename.endswith(".yaml"):
            yaml_files.append(os.path.join(folder_path, filename))
    if len(yaml_files) != 1:
        return jsonify(result='success')

    file_name = yaml_files[0]

    extend_choose = 0
    extend_threshold = []
    extend_multiple = []
    data = ""

    with open(file_name, 'r') as f:
        data = yaml.safe_load(f)
        if "extend_choose" in data['evaluation_form']['6_scatter_diagram']:
            if  data['evaluation_form']['6_scatter_diagram']['extend_choose'] == 1:
                extend_choose = 1
                extend_threshold = data['evaluation_form']['6_scatter_diagram']['extend_threshold']
                extend_multiple = data['evaluation_form']['6_scatter_diagram']['extend_multiple']
            else:
                extend_choose = 0
    
    if 1 not in Extend_axis or extend_choose == 0:
        return jsonify(result='success')
    
    # 输入，原始的数据 + 筛选过后的数据
    # 返回，修正后的数据（直接返回一个diagram_data的数据就好了）
    # config_id_list_old = config_id_list
    old_suit_configs_list = []
    suit_configs_list = []
    for i in range(len(config_id_list_old)):
        old_suit_configs_list.append(MappingTaskConfig.query.get(config_id_list_old[i]))
    
    for i in range(len(config_id_list)):
        suit_configs_list.append(MappingTaskConfig.query.get(config_id_list[i]))
    
    
    for i in range(len(Extend_attribute)):
        if Extend_axis[i] == 1:
            new_val = ""
            if Extend_attribute[i].split("-")[0] == "ATE":
                new_val += "ate_"
            else:
                new_val += "rpe_"

            new_val += Extend_attribute[i].split("-")[1]
            Extend_attribute[i] = new_val




    ret = custom_analysis_resolver.get_Extend_accuracy(old_suit_configs_list, suit_configs_list, Extend_axis, Extend_attribute, extend_threshold,extend_multiple)
    # 应该要返回3个列表的列表，每个列表里有新的数据（列表里面的元素是字典）
    print(1)

    algorithm_id_dict = {}
    for config in old_suit_configs_list:
        # 给config分类
        if config.algorithm.imageTag not in algorithm_id_dict.keys():
            algorithm_id_dict.update({config.algorithm.imageTag: [config]})
        else:
            algorithm_id_dict[config.algorithm.imageTag].append(config)
    dataset_id_dict = {}
    for config in old_suit_configs_list:
        if config.dataset.name not in dataset_id_dict.keys():
            dataset_id_dict.update({config.dataset.name: [config]})
        else:
            dataset_id_dict[config.dataset.name].append(config)


    old_diagram_data = diagram_data

    diagram_data = {}
    diagram_data.update({x_axis: []})
    diagram_data.update({y_axis: []})
    diagram_data.update({"category": []})


    for key, value in dataset_id_dict.items(): # 
        # 生成一个color
        # 其他dataset的color以这个为中心
        for dkey, dvalue in algorithm_id_dict.items(): # 
            for config in value:
                # 这个config必须在dvalue中
                flag = False
                for dconfig in dvalue:
                    if config.id == dconfig.id:
                        flag = True
                        break
                if flag == False:
                    continue

                # 获取x y对应
                x_v = 0
                y_v = 0
                # category = key + "  " + dkey
                category = dkey + "  " + key


                # print(x_axis, y_axis)


                if Extend_axis[0] == 1:
                    x_v = ret[0][config.id][2]
                else:
                    # print("?????????")
                    performanceresults = config.mappingTasks[0].performanceresults

                    if x_axis == 'CPU-max':
                        x_v = performanceresults.max_cpu
                    elif x_axis == 'CPU-mean':
                        x_v = performanceresults.mean_cpu
                    elif x_axis == 'Memory-max':
                        x_v = performanceresults.max_ram
                    else:
                        # parameter
                        for paramValue in config.paramValues:
                            if x_axis == paramValue.name:
                                x_v = float(paramValue.value)
                                break
                

                if Extend_axis[1] == 1:
                    y_v = ret[1][config.id][2]  
                else:
                    # print("?????????")
                    performanceresults = config.mappingTasks[0].performanceresults
                 
                    if y_axis == 'cpu_max':
                        y_v = performanceresults.max_cpu
                    elif y_axis == 'cpu_mean':
                        y_v = performanceresults.mean_cpu
                    elif y_axis == 'ram_max':
                        y_v = performanceresults.max_ram
                    else:
                        # parameter
                        for paramValue in config.paramValues:
                            if y_axis == paramValue.name:
                                y_v = float(paramValue.value)
                                break    
  


                # diagram_data.append([x_v, y_v, key])
                diagram_data[x_axis].append(x_v)
                diagram_data[y_axis].append(y_v)
                diagram_data['category'].append(category)

    csv_data = []
    config_id_title = "Config ID"
    x_axis_title = "X Axis(" + x_axis + ")"
    y_axis_title = "Y Axis(" + y_axis + ")"
    algorithm_title = "Algorithm Name"
    dataset_title = "Dataset Name"

    for i in range(len(config_id_list_old)):
        config = MappingTaskConfig.query.get(config_id_list_old[i])
        
        config_id = config_id_list_old[i]
        x_value = diagram_data[x_axis][i]
        y_value = diagram_data[y_axis][i]
        algorithm_name_value = config.algorithm.imageTag
        dataset_name_value = config.dataset.name

        csv_data.append({
            config_id_title: config_id,
            x_axis_title: x_value,
            y_axis_title: y_value,
            algorithm_title: algorithm_name_value,
            dataset_title: dataset_name_value
            })

    csv_path = sub_folder_path + "/" + "RawData1_x-" + x_axis + "_y-" + y_axis+"_Extend.csv"
    dff = pd.DataFrame(csv_data)
    dff.to_csv(csv_path, index=False)



    # 调整绘图的边距，以确保图例不重叠
    diagram_name_pgf = "Diagram1_x-" + x_axis + "_y-" + y_axis+"-Extend.pgf"
    diagram_name_png = "Diagram1_x-" + x_axis + "_y-" + y_axis+"-Extend.png"
    diagram_name_pdf = "Diagram1_x-" + x_axis + "_y-" + y_axis+"-Extend.pdf"
    # diagram_path_pgf = folder_path + "/scatter/" + diagram_name_pgf
    # diagram_path_png = folder_path + "/scatter/" + diagram_name_png
    # diagram_path_pdf = folder_path + "/scatter/" + diagram_name_pdf
    diagram_path_pgf = sub_folder_path + "/"  + diagram_name_pgf
    diagram_path_png = sub_folder_path + "/"  + diagram_name_png
    diagram_path_pdf = sub_folder_path + "/"  + diagram_name_pdf

    df = pd.DataFrame(diagram_data)#, columns=[x_axis, y_axis])
    
    # 绘制散点图
    fig, ax = plt.subplots(figsize=(60, 20))


    unique_categories = df['category'].unique()
    unique_A = sorted(set(cat.split('  ')[0] for cat in unique_categories))
    unique_B = sorted(set(cat.split('  ')[1] for cat in unique_categories))

    # 基础调色板husl  hsv
    base_palette = sns.color_palette("dark", len(unique_A))

    # 创建颜色字典，按A和B分类
    color_dict = {}
    for i, a in enumerate(unique_A):
        sub_palette = sns.light_palette(base_palette[i], len(unique_B) * 5)
        for j, b in enumerate(unique_B):
            color_dict[f"{a}  {b}"] = sub_palette[j*5 + 4]  


    for i in range(len(category_list)):
        algo = Algorithm.query.get(category[i])
        plt.scatter(x=x_data[i], y=y_data[i],edgecolor=['w'], label=category_list[i], color = color_dict[category_list[i]], s = 300)
    plt.xlabel(x_axis + " " + x_unit)
    plt.ylabel(y_axis + " " + y_unit)
    # 添加图例
    handles, labels = ax.get_legend_handles_labels()
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    legend = ax.legend(
        handles, labels,
        loc='upper left',
        bbox_to_anchor=(1, 1),
        borderaxespad=0.
    )


    # 设置图例的字体大小和边框
    legend.prop.set_size(6)
    legend.get_frame().set_edgecolor('black')
    legend.get_frame().set_linewidth(0.5)

    # 调整子图的布局
    plt.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)

    # 设置坐标轴的长宽比
    # ax.set_aspect(aspect=1.0/ax.get_data_ratio(), adjustable='datalim')
    # fig = sns.scatterplot(x=x_axis, y=y_axis, data=df)
    #scatter_fig = fig.get_figure()
    plt.savefig(diagram_path_pgf, dpi = 400)
    plt.savefig(diagram_path_png, dpi = 400)
    plt.savefig(diagram_path_pdf, dpi = 400)







    mpl.rcParams['pdf.fonttype'] = mpl1
    mpl.rcParams['ps.fonttype'] = mpl2
    mpl.rcParams['font.family'] = mpl3
    mpl.rcParams['font.size'] = mpl4
    return jsonify(result='success')








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




@app.route('/analysis/diagram/dig2/show',methods=['GET','POST'])
def show_diagram2():
    data = json.loads(request.get_data())
    print(data)

    custom_id = data['custom_id']
    x_axis = data['x-axis']
    y_axis = data['y-axis']
    z_axis = data['z-axis']

    x_unit = ""
    y_unit = ""
    z_unit = ""
    if "ATE" in x_axis or "RPE" in x_axis:
        x_unit = "(m)"
    elif "CPU" in x_axis:
        x_unit = "(cores)"
    elif "Memory" in x_axis:
        x_unit = "(MB)"
    elif "frequency" in x_axis:
        x_unit = "(Hz)"

    if "ATE" in y_axis or "RPE" in y_axis:
        y_unit = "(m)"
    elif "CPU" in y_axis:
        y_unit = "(cores)"
    elif "Memory" in y_axis:
        y_unit = "(MB)"
    elif "frequency" in y_axis:
        y_unit = "(Hz)"

    if "ATE" in z_axis or "RPE" in z_axis:
        z_unit = "(m)"
    elif "CPU" in z_axis:
        z_unit = "(cores)"
    elif "Memory" in z_axis:
        z_unit = "(MB)"
    elif "frequency" in z_axis:
        z_unit = "(Hz)"        

    f = open("/slam_hive_results/custom_analysis_group/" + str(custom_id) + "/info.txt")
    
    content = f.read()
    f.close()
    import ast
    config_id_list = ast.literal_eval((content.split("\n")[3].split(":")[1]))

    print(config_id_list)

    tray_unsuccess_id_list = ast.literal_eval((content.split("\n")[5].split(":")[1]))
    print(tray_unsuccess_id_list)

    config_id_list_old = config_id_list
    config_id_list  = []
    for id in config_id_list_old:
        if id not in  tray_unsuccess_id_list:
            config_id_list.append(id)
 

    # 需要解析custom的id


        # 首先判断group中的config -- algo：任意都可以（但是貌似不是同一个算法意义不大）;dataset: 相同

    diagram_data = []
    for i in range(len(config_id_list)):
        # 获取x y对应
        x_v = 0
        y_v = 0
        current_config = MappingTaskConfig.query.get(config_id_list[i])
        evoResults = current_config.mappingTasks[0].evaluation.evoResults
        performanceresults = current_config.mappingTasks[0].performanceresults
        if x_axis == 'ATE-rmse':
            x_v = evoResults.ate_rmse
        elif x_axis == 'ATE-mean':
            x_v = evoResults.ate_mean
        elif x_axis == 'ATE-median':
            x_v = evoResults.ate_median
        elif x_axis == 'ATE-std':
            x_v = evoResults.ate_std
        elif x_axis == 'ATE-min':
            x_v = evoResults.ate_min
        elif x_axis == 'ATE-max':
            x_v = evoResults.ate_max
        elif x_axis == 'ATE-sse':
            x_v = evoResults.ate_sse
        elif x_axis == 'RPE-mean':
            x_v = evoResults.rpe_mean
        elif x_axis == 'RPE-median':
            x_v = evoResults.rpe_median
        elif x_axis == 'RPE-std':
            x_v = evoResults.rpe_std
        elif x_axis == 'RPE-min':
            x_v = evoResults.rpe_min
        elif x_axis == 'RPE-max':
            x_v = evoResults.rpe_max
        elif x_axis == 'RPE-sse':
            x_v = evoResults.rpe_sse
        elif x_axis == 'RPE-rmse':
            x_v = evoResults.rpe_rmse
        elif x_axis == 'CPU-max':
            x_v = performanceresults.max_cpu
        elif x_axis == 'CPU-mean':
            x_v = performanceresults.mean_cpu
        elif x_axis == 'Memory-max':
            x_v = performanceresults.max_ram
        else:
            # parameter
            for paramValue in current_config.paramValues:
                if x_axis == paramValue.name:
                    x_v = float(paramValue.value)
                    break

        if y_axis == 'ATE-rmse':
            y_v = evoResults.ate_rmse
        elif y_axis == 'ATE-mean':
            y_v = evoResults.ate_mean
        elif y_axis == 'ATE-median':
            y_v = evoResults.ate_median
        elif y_axis == 'ATE-std':
            y_v = evoResults.ate_std
        elif y_axis == 'ATE-min':
            y_v = evoResults.ate_min
        elif y_axis == 'ATE-max':
            y_v = evoResults.ate_max
        elif y_axis == 'ATE-sse':
            y_v = evoResults.ate_sse
        elif y_axis == 'RPE-mean':
            y_v = evoResults.rpe_mean
        elif y_axis == 'RPE-median':
            y_v = evoResults.rpe_median
        elif y_axis == 'RPE-std':
            y_v = evoResults.rpe_std
        elif y_axis == 'RPE-min':
            y_v = evoResults.rpe_min
        elif y_axis == 'RPE-max':
            y_v = evoResults.rpe_max
        elif y_axis == 'RPE-sse':
            y_v = evoResults.rpe_sse
        elif y_axis == 'RPE-rmse':
            y_v = evoResults.rpe_rmse
        elif y_axis == 'CPU-max':
            y_v = performanceresults.max_cpu
        elif y_axis == 'CPU-mean':
            y_v = performanceresults.mean_cpu
        elif y_axis == 'Memory-max':
            y_v = performanceresults.max_ram
        else:
            # parameter
            for paramValue in current_config.paramValues:
                if y_axis == paramValue.name:
                    y_v = float(paramValue.value)
                    break   

        if z_axis == 'ATE-rmse':
            z_v = evoResults.ate_rmse
        elif z_axis == 'ATE-mean':
            z_v = evoResults.ate_mean
        elif z_axis == 'ATE-median':
            z_v = evoResults.ate_median
        elif z_axis == 'ATE-std':
            z_v = evoResults.ate_std
        elif z_axis == 'ATE-min':
            z_v = evoResults.ate_min
        elif z_axis == 'ATE-max':
            z_v = evoResults.ate_max
        elif z_axis == 'ATE-sse':
            z_v = evoResults.ate_sse
        elif z_axis == 'RPE-mean':
            z_v = evoResults.rpe_mean
        elif z_axis == 'RPE-median':
            z_v = evoResults.rpe_median
        elif z_axis == 'RPE-std':
            z_v = evoResults.rpe_std
        elif z_axis == 'RPE-min':
            z_v = evoResults.rpe_min
        elif z_axis == 'RPE-max':
            z_v = evoResults.rpe_max
        elif z_axis == 'RPE-sse':
            z_v = evoResults.rpe_sse
        elif z_axis == 'RPE-rmse':
            z_v = evoResults.rpe_rmse
        elif z_axis == 'CPU-max':
            z_v = performanceresults.max_cpu
        elif z_axis == 'CPU-mean':
            z_v = performanceresults.mean_cpu
        elif z_axis == 'Memory-max':
            z_v = performanceresults.max_ram
        else:

            
            # TODO 现在还不能string类型

            # parameter
            for paramValue in current_config.paramValues:
                if z_axis == paramValue.name:
                    if paramValue.valueType == "int" or paramValue.valueType == "float" or paramValue.valueType == "double": 
                        z_v = float(paramValue.value)
                    else:
                        return "<div> The type of parameter is string, we can not show this type now </div>"
                    break  

              

        diagram_data.append([x_v, y_v, z_v, current_config.paramValues])

    x_data = [d[0] for d in diagram_data]
    y_data = [d[1] for d in diagram_data]
    z_data = [d[2] for d in diagram_data]

    c_data = []
    

    print(diagram_data)

    # 需要按照算法进行分类
    #因为知道数据集一定是一样的
    
    y_new_data = []
    x_new_data = []

    y_max = -10000
    y_min = 1000000
    x_max = -100000
    x_min = 1000000

    category_list = []
    for i in range(len(y_data)):
        algo_imageTag = MappingTaskConfig.query.get(config_id_list[i]).algorithm.imageTag
        dataset_name = MappingTaskConfig.query.get(config_id_list[i]).dataset.name
        # category = dataset_name  + "  " +   algo_imageTag
        category = algo_imageTag   + "  " +   dataset_name


        c_data.append(category)
        if category not in category_list:
            category_list.append(category)
            y_new_data.append([])
            x_new_data.append([])

        y_max = max(y_max, y_data[i])
        y_min = min(y_min, y_data[i])
        x_max = max(x_max, x_data[i])
        x_min = min(x_max, x_data[i])

        temp_dict = {'value': y_data[i], "info": "config id: _" + str(config_id_list[i])}
        temp_dict = [y_data[i], "config id: " + str(config_id_list[i])]
        for j in range(len(category_list)):
            if category == category_list[j]:

                y_new_data[j].append(temp_dict)
        
                x_new_data[j].append([x_data[i]])


    # print(y_new_data)
    # print(x_new_data)

    data = []
    for i in range(len(x_data)):
        data.append([])
        data[i].append(x_data[i])
        data[i].append(y_data[i])
        data[i].append(z_data[i])
        data[i].append(c_data[i])
        # config_id_list_content = " config id: "  +str(config_id_list[i]) + "\n"
        # config_id_list_content += "  (x axis) - " + x_axis + ": " + str(x_data[i]) + "\n"
        # config_id_list_content += "  (y axis) - " + y_axis + ": " + str(y_data[i]) + "\n"
        # config_id_list_content += "  (z axis) - " + z_axis + ": " + str(z_data[i]) + "\n"
        

        data[i].append(config_id_list[i])
        data[i].append(diagram_data[i][3])


    # data = [
    #     [10, 20, 30, 0, "Point A"],
    #     [20, 30, 40, 1, "Point B"],
    #     [30, 40, 50, 0, "Point C"],
    #     [40, 50, 60, 2, "Point D"],
    #     [50, 60, 70, 1, "Point E"],
    # ]
    
   # 基础颜色映射（按B分类）
    unique_categories = category_list
    unique_A = sorted(set(cat.split('  ')[0] for cat in unique_categories))
    unique_B = sorted(set(cat.split('  ')[1] for cat in unique_categories))


    # 基础调色板husl  hsv
    base_palette = sns.color_palette("dark", len(unique_A))

    # 创建颜色字典，按A和B分类
    color_dict = {}
    for i, a in enumerate(unique_A):
        # sub_palette = sns.light_palette(base_palette[i], n_colors=len(unique_B))
        sub_palette = sns.light_palette(base_palette[i], len(unique_B) * 5)
        for j, b in enumerate(unique_B):
            color_dict[f"{a}  {b}"] = sub_palette[j*5 + 4]      


    def rgb_to_hex(rgb_tuple):
        # 将每个浮点数乘以255并四舍五入成整数
        r, g, b = [int(round(x * 255)) for x in rgb_tuple]
        
        # 将整数转换为两位的16进制数，并连接在一起
        return f'#{r:02x}{g:02x}{b:02x}'
    
    # 为每个数据点添加颜色信息和独特的名字
    data_dict = {}
    series_data_dict = {}
    for point in data:
        x, y, z, category, name, param = point
        if category not in data_dict.keys():
            data_dict.update({category: []})
            series_data_dict.update({category: []})

        data_dict[category].append(point) 
        
    i = -1
    for point in data:
        x, y, z, category, name, params = point
        color = rgb_to_hex(color_dict[category])

        value1 = []
        value1.append(x)
        value1.append(y)
        value1.append(z)
        for param in params:
            # if param.valueType == "int" or param.valueType == "float":
            if param.algoParam.paramType == "Algorithm" or param.algoParam.paramType == "Dataset" or param.algoParam.paramType == "Dataset Remap":
                value1.append(param.name + ": " + param.value)


        i+=1
        series_data_dict[category].append({
            "name": " config id: "  +str(config_id_list[i]) + "  ("+ str(x) +", " +str(y) + ", " + str(z) +")",
            "value": value1, # [x, y, z],
            # "category": category,
            "itemStyle": {"color": color}
        })



    scatter3d = Scatter3D(init_opts=opts.InitOpts(width="1700px", height="750px"))
    
    for key, value in series_data_dict.items():
        print(series_data_dict[key])
        scatter3d.add(
            series_name=key,
            data=series_data_dict[key],

            itemstyle_opts=opts.ItemStyleOpts(color=series_data_dict[key][0]["itemStyle"]["color"]),


            xaxis3d_opts=opts.Axis3DOpts(
                name=x_axis + " " + x_unit,
                #name_textstyle_opts=opts.TextStyleOpts(font_family="DejaVu Sans", font_size=12)
            ),
            yaxis3d_opts=opts.Axis3DOpts(
                name=y_axis + " " + y_unit,
                #name_textstyle_opts=opts.TextStyleOpts(font_family="DejaVu Sans", font_size=12)
            ),
            zaxis3d_opts=opts.Axis3DOpts(
                name=z_axis + " " + z_unit,
                #name_textstyle_opts=opts.TextStyleOpts(font_family="DejaVu Sans", font_size=12)
            )
            
    # )
        )

    return Markup(scatter3d.render_embed())
    # bar.render('templates\index.html')

@app.route('/analysis/diagram/dig2_extend/show',methods=['GET','POST'])
def show_diagram2_extend():
    data = json.loads(request.get_data())
    print(data)

    custom_id = data['custom_id']
    x_axis = data['x-axis']
    y_axis = data['y-axis']
    z_axis = data['z-axis']

    x_unit = ""
    y_unit = ""
    z_unit = ""
    Extend_axis = [0,0,0]
    Extend_attribute = ['', '', '']

    if "ATE" in x_axis or "RPE" in x_axis:
        x_unit = "(m)"
        Extend_axis[0] = 1
        Extend_attribute[0] = x_axis        
    elif "CPU" in x_axis:
        x_unit = "(cores)"
    elif "Memory" in x_axis:
        x_unit = "(MB)"
    elif "frequency" in x_axis:
        x_unit = "(Hz)"

    if "ATE" in y_axis or "RPE" in y_axis:
        y_unit = "(m)"
        Extend_axis[1] = 1
        Extend_attribute[1] = y_axis        
    elif "CPU" in y_axis:
        y_unit = "(cores)"
    elif "Memory" in y_axis:
        y_unit = "(MB)"
    elif "frequency" in y_axis:
        y_unit = "(Hz)"

    if "ATE" in z_axis or "RPE" in z_axis:
        z_unit = "(m)"
        Extend_axis[2] = 1
        Extend_attribute[2] = z_axis        
    elif "CPU" in z_axis:
        z_unit = "(cores)"
    elif "Memory" in z_axis:
        z_unit = "(MB)"
    elif "frequency" in z_axis:
        z_unit = "(Hz)"        

    f = open("/slam_hive_results/custom_analysis_group/" + str(custom_id) + "/info.txt")
    
    content = f.read()
    f.close()
    import ast
    config_id_list = ast.literal_eval((content.split("\n")[3].split(":")[1]))

    print(config_id_list)

    tray_unsuccess_id_list = ast.literal_eval((content.split("\n")[5].split(":")[1]))
    print(tray_unsuccess_id_list)

    config_id_list_old = config_id_list
    config_id_list  = []
    for id in config_id_list_old:
        if id not in  tray_unsuccess_id_list:
            config_id_list.append(id)
 

    folder_path = "/slam_hive_results/custom_analysis_group/" + str(custom_id)
    yaml_files = []
    for filename in os.listdir(folder_path):
        if filename.startswith(str(custom_id)) and filename.endswith(".yaml"):
            yaml_files.append(os.path.join(folder_path, filename))
    if len(yaml_files) != 1:
        return jsonify(result='success')

    file_name = yaml_files[0]

    extend_choose = 0
    extend_threshold = []
    extend_multiple = []
    data = ""

    with open(file_name, 'r') as f:
        data = yaml.safe_load(f)
        if "extend_choose" in data['evaluation_form']['7_3d_scatter_diagram']:
            if  data['evaluation_form']['7_3d_scatter_diagram']['extend_choose'] == 1:
                extend_choose = 1
                extend_threshold = data['evaluation_form']['7_3d_scatter_diagram']['extend_threshold']
                extend_multiple = data['evaluation_form']['7_3d_scatter_diagram']['extend_multiple']
            else:
                extend_choose = 0    

    old_suit_configs_list = []
    suit_configs_list = []
    for i in range(len(config_id_list_old)):
        old_suit_configs_list.append(MappingTaskConfig.query.get(config_id_list_old[i]))
    
    for i in range(len(config_id_list)):
        suit_configs_list.append(MappingTaskConfig.query.get(config_id_list[i]))
    
    
    for i in range(len(Extend_attribute)):
        if Extend_axis[i] == 1:
            new_val = ""
            if Extend_attribute[i].split("-")[0] == "ATE":
                new_val += "ate_"
            else:
                new_val += "rpe_"

            new_val += Extend_attribute[i].split("-")[1]
            Extend_attribute[i] = new_val

    ret = custom_analysis_resolver.get_Extend_accuracy(old_suit_configs_list, suit_configs_list, Extend_axis, Extend_attribute, extend_threshold,extend_multiple)

    algorithm_id_dict = {}
    for config in old_suit_configs_list:
        # 给config分类
        if config.algorithm.imageTag not in algorithm_id_dict.keys():
            algorithm_id_dict.update({config.algorithm.imageTag: [config]})
        else:
            algorithm_id_dict[config.algorithm.imageTag].append(config)
    dataset_id_dict = {}
    for config in old_suit_configs_list:
        if config.dataset.name not in dataset_id_dict.keys():
            dataset_id_dict.update({config.dataset.name: [config]})
        else:
            dataset_id_dict[config.dataset.name].append(config)
    # 需要解析custom的id


        # 首先判断group中的config -- algo：任意都可以（但是貌似不是同一个算法意义不大）;dataset: 相同

    diagram_data = []
    for i in range(len(config_id_list_old)):
        # 获取x y对应
        x_v = 0
        y_v = 0
        current_config = MappingTaskConfig.query.get(config_id_list_old[i])
        
        performanceresults = current_config.mappingTasks[0].performanceresults

        if Extend_axis[0] == 1:
            x_v = ret[0][current_config.id][2]
        else:  
          
            if x_axis == 'CPU-max':
                x_v = performanceresults.max_cpu
            elif x_axis == 'CPU-mean':
                x_v = performanceresults.mean_cpu
            elif x_axis == 'Memory-max':
                x_v = performanceresults.max_ram
            else:
                # parameter
                for paramValue in current_config.paramValues:
                    if x_axis == paramValue.name:
                        x_v = float(paramValue.value)
                        break
        
        if Extend_axis[1] == 1:
            y_v = ret[1][current_config.id][2]
        else:  
          
            if y_axis == 'CPU-max':
                y_v = performanceresults.max_cpu
            elif y_axis == 'CPU-mean':
                y_v = performanceresults.mean_cpu
            elif y_axis == 'Memory-max':
                y_v = performanceresults.max_ram
            else:
                # parameter
                for paramValue in current_config.paramValues:
                    if y_axis == paramValue.name:
                        y_v = float(paramValue.value)
                        break   
      
        if Extend_axis[2] == 1:
            z_v = ret[2][current_config.id][2]
        else: 
        
            if z_axis == 'CPU-max':
                z_v = performanceresults.max_cpu
            elif z_axis == 'CPU-mean':
                z_v = performanceresults.mean_cpu
            elif z_axis == 'Memory-max':
                z_v = performanceresults.max_ram
            else:

                
                # TODO 现在还不能string类型

                # parameter
                for paramValue in current_config.paramValues:
                    if z_axis == paramValue.name:
                        if paramValue.valueType == "int" or paramValue.valueType == "float" or paramValue.valueType == "double": 
                            z_v = float(paramValue.value)
                        else:
                            return "<div> The type of parameter is string, we can not show this type now </div>"
                        break  

              

        diagram_data.append([x_v, y_v, z_v, current_config.paramValues])

    x_data = [d[0] for d in diagram_data]
    y_data = [d[1] for d in diagram_data]
    z_data = [d[2] for d in diagram_data]

    c_data = []
    

    print(diagram_data)
    
    y_new_data = []
    x_new_data = []

    y_max = -10000
    y_min = 1000000
    x_max = -100000
    x_min = 1000000

    category_list = []
    for i in range(len(y_data)):
        algo_imageTag = MappingTaskConfig.query.get(config_id_list_old[i]).algorithm.imageTag
        dataset_name = MappingTaskConfig.query.get(config_id_list_old[i]).dataset.name
        # category = dataset_name  + "  " +   algo_imageTag
        category = algo_imageTag  + "  " +   dataset_name


        c_data.append(category)
        if category not in category_list:
            category_list.append(category)
            y_new_data.append([])
            x_new_data.append([])

        y_max = max(y_max, y_data[i])
        y_min = min(y_min, y_data[i])
        x_max = max(x_max, x_data[i])
        x_min = min(x_max, x_data[i])

        temp_dict = {'value': y_data[i], "info": "config id: _" + str(config_id_list_old[i])}
        temp_dict = [y_data[i], "config id: " + str(config_id_list_old[i])]
        for j in range(len(category_list)):
            if category == category_list[j]:

                y_new_data[j].append(temp_dict)
        
                x_new_data[j].append([x_data[i]])


    print(y_new_data)
    print(x_new_data)

    data = []
    for i in range(len(x_data)):
        data.append([])
        data[i].append(x_data[i])
        data[i].append(y_data[i])
        data[i].append(z_data[i])
        data[i].append(c_data[i])

        data[i].append(config_id_list_old[i])
        data[i].append(diagram_data[i][3])

   # 基础颜色映射（按B分类）
    unique_categories = category_list
    unique_A = sorted(set(cat.split('  ')[0] for cat in unique_categories))
    unique_B = sorted(set(cat.split('  ')[1] for cat in unique_categories))


    # 基础调色板husl  hsv
    base_palette = sns.color_palette("dark", len(unique_A))

    # 创建颜色字典，按A和B分类
    color_dict = {}
    for i, a in enumerate(unique_A):
        # sub_palette = sns.light_palette(base_palette[i], n_colors=len(unique_B))
        sub_palette = sns.light_palette(base_palette[i], len(unique_B) * 5)
        for j, b in enumerate(unique_B):
            color_dict[f"{a}  {b}"] = sub_palette[j*5 + 4]      


    def rgb_to_hex(rgb_tuple):
        # 将每个浮点数乘以255并四舍五入成整数
        r, g, b = [int(round(x * 255)) for x in rgb_tuple]
        
        # 将整数转换为两位的16进制数，并连接在一起
        return f'#{r:02x}{g:02x}{b:02x}'
    
    # 为每个数据点添加颜色信息和独特的名字
    data_dict = {}
    series_data_dict = {}
    for point in data:
        x, y, z, category, name, param = point
        if category not in data_dict.keys():
            data_dict.update({category: []})
            series_data_dict.update({category: []})

        data_dict[category].append(point) 
        
    i = -1
    for point in data:
        x, y, z, category, name, params = point
        color = rgb_to_hex(color_dict[category])

        value1 = []
        value1.append(x)
        value1.append(y)
        value1.append(z)
        for param in params:
            # if param.valueType == "int" or param.valueType == "float":
            if param.algoParam.paramType == "Algorithm" or param.algoParam.paramType == "Dataset" or param.algoParam.paramType == "Dataset Remap":
                value1.append(param.name + ": " + param.value)
        i+=1
        series_data_dict[category].append({
            "name": " config id: "  +str(config_id_list_old[i]) + "  ("+ str(x) +", " +str(y) + ", " + str(z) +")",
            "value": value1, # [x, y, z],
            # "category": category,
            "itemStyle": {"color": color}
        })

    scatter3d = Scatter3D(
        init_opts=opts.InitOpts(width="1700px", height="750px"),
        ).set_global_opts(
            title_opts=opts.TitleOpts(
                title="Extend",
                pos_left="center",
                pos_top="bottom"  # 标题位置设置在底部
            ),
        )
    
    for key, value in series_data_dict.items():
        print(series_data_dict[key])
        scatter3d.add(
            series_name=key,
            data=series_data_dict[key],

            itemstyle_opts=opts.ItemStyleOpts(color=series_data_dict[key][0]["itemStyle"]["color"]),


            xaxis3d_opts=opts.Axis3DOpts(
                name=x_axis + " " + x_unit,
                #name_textstyle_opts=opts.TextStyleOpts(font_family="DejaVu Sans", font_size=12)
            ),
            yaxis3d_opts=opts.Axis3DOpts(
                name=y_axis + " " + y_unit,
                #name_textstyle_opts=opts.TextStyleOpts(font_family="DejaVu Sans", font_size=12)
            ),
            zaxis3d_opts=opts.Axis3DOpts(
                name=z_axis + " " + z_unit,
                #name_textstyle_opts=opts.TextStyleOpts(font_family="DejaVu Sans", font_size=12)
            )
            
    # )
        )


    return Markup(scatter3d.render_embed())
    # bar.render('templates\index.html')    

@app.route('/analysis/diagram/dig2/',methods=['GET','POST'])
def create_diagram2():
    data = json.loads(request.get_data())
    print(data)

    custom_id = data['custom_id']
    x_axis = data['x-axis']
    y_axis = data['y-axis']
    z_axis = data['z-axis']

    x_unit = ""
    y_unit = ""
    z_unit = ""

    Extend_axis = [0,0,0]
    Extend_attribute = ['', '', '']    
    if "ATE" in x_axis or "RPE" in x_axis:
        x_unit = "(m)"
        Extend_axis[0] = 1
        Extend_attribute[0] = x_axis
    elif "CPU" in x_axis:
        x_unit = "(cores)"
    elif "Memory" in x_axis:
        x_unit = "(MB)"
    elif "frequency" in x_axis:
        x_unit = "(Hz)"

    if "ATE" in y_axis or "RPE" in y_axis:
        y_unit = "(m)"
        Extend_axis[1] = 1
        Extend_attribute[1] = y_axis
    elif "CPU" in y_axis:
        y_unit = "(cores)"
    elif "Memory" in y_axis:
        y_unit = "(MB)"
    elif "frequency" in y_axis:
        y_unit = "(Hz)"

    if "ATE" in z_axis or "RPE" in z_axis:
        z_unit = "(m)"
        Extend_axis[2] = 1
        Extend_attribute[2] = z_axis
    elif "CPU" in z_axis:
        z_unit = "(cores)"
    elif "Memory" in z_axis:
        z_unit = "(MB)"
    elif "frequency" in z_axis:
        z_unit = "(Hz)"        


    f = open("/slam_hive_results/custom_analysis_group/" + str(custom_id) + "/info.txt")
    
    content = f.read()
    f.close()
    import ast
    config_id_list = ast.literal_eval((content.split("\n")[3].split(":")[1]))

    print(config_id_list)

    tray_unsuccess_id_list = ast.literal_eval((content.split("\n")[5].split(":")[1]))
    print(tray_unsuccess_id_list)

    config_id_list_old = config_id_list
    config_id_list  = []
    for id in config_id_list_old:
        if id not in  tray_unsuccess_id_list:
            config_id_list.append(id)
 

    # 需要解析custom的id


        # 首先判断group中的config -- algo：任意都可以（但是貌似不是同一个算法意义不大）;dataset: 相同

    diagram_data = {}
    diagram_data.update({x_axis: []})
    diagram_data.update({y_axis: []})
    diagram_data.update({z_axis: []})
    diagram_data.update({"category": []})
    for i in range(len(config_id_list)):
        # 获取x y对应
        x_v = 0
        y_v = 0
        current_config = MappingTaskConfig.query.get(config_id_list[i])
        evoResults = current_config.mappingTasks[0].evaluation.evoResults
        performanceresults = current_config.mappingTasks[0].performanceresults
        # category = current_config.dataset.name + "  " + current_config.algorithm.imageTag
        category = current_config.algorithm.imageTag + "  " + current_config.dataset.name
        if x_axis == 'ATE-rmse':
            x_v = evoResults.ate_rmse
        elif x_axis == 'ATE-mean':
            x_v = evoResults.ate_mean
        elif x_axis == 'ATE-median':
            x_v = evoResults.ate_median
        elif x_axis == 'ATE-std':
            x_v = evoResults.ate_std
        elif x_axis == 'ATE-min':
            x_v = evoResults.ate_min
        elif x_axis == 'ATE-max':
            x_v = evoResults.ate_max
        elif x_axis == 'ATE-sse':
            x_v = evoResults.ate_sse
        elif x_axis == 'RPE-mean':
            x_v = evoResults.rpe_mean
        elif x_axis == 'RPE-median':
            x_v = evoResults.rpe_median
        elif x_axis == 'RPE-std':
            x_v = evoResults.rpe_std
        elif x_axis == 'RPE-min':
            x_v = evoResults.rpe_min
        elif x_axis == 'RPE-max':
            x_v = evoResults.rpe_max
        elif x_axis == 'RPE-sse':
            x_v = evoResults.rpe_sse
        elif x_axis == 'RPE-rmse':
            x_v = evoResults.rpe_rmse
        elif x_axis == 'CPU-max':
            x_v = performanceresults.max_cpu
        elif x_axis == 'CPU-mean':
            x_v = performanceresults.mean_cpu
        elif x_axis == 'Memory-max':
            x_v = performanceresults.max_ram
        else:
            # parameter
            for paramValue in current_config.paramValues:
                if x_axis == paramValue.name:
                    x_v = float(paramValue.value)
                    break

        if y_axis == 'ATE-rmse':
            y_v = evoResults.ate_rmse
        elif y_axis == 'ATE-mean':
            y_v = evoResults.ate_mean
        elif y_axis == 'ATE-median':
            y_v = evoResults.ate_median
        elif y_axis == 'ATE-std':
            y_v = evoResults.ate_std
        elif y_axis == 'ATE-min':
            y_v = evoResults.ate_min
        elif y_axis == 'ATE-max':
            y_v = evoResults.ate_max
        elif y_axis == 'ATE-sse':
            y_v = evoResults.ate_sse
        elif y_axis == 'RPE-mean':
            y_v = evoResults.rpe_mean
        elif y_axis == 'RPE-median':
            y_v = evoResults.rpe_median
        elif y_axis == 'RPE-std':
            y_v = evoResults.rpe_std
        elif y_axis == 'RPE-min':
            y_v = evoResults.rpe_min
        elif y_axis == 'RPE-max':
            y_v = evoResults.rpe_max
        elif y_axis == 'RPE-sse':
            y_v = evoResults.rpe_sse
        elif y_axis == 'RPE-rmse':
            y_v = evoResults.rpe_rmse
        elif y_axis == 'CPU-max':
            y_v = performanceresults.max_cpu
        elif y_axis == 'CPU-mean':
            y_v = performanceresults.mean_cpu
        elif y_axis == 'Memory-max':
            y_v = performanceresults.max_ram
        else:
            # parameter
            for paramValue in current_config.paramValues:
                if y_axis == paramValue.name:
                    y_v = float(paramValue.value)
                    break   

        if z_axis == 'ATE-rmse':
            z_v = evoResults.ate_rmse
        elif z_axis == 'ATE-mean':
            z_v = evoResults.ate_mean
        elif z_axis == 'ATE-median':
            z_v = evoResults.ate_median
        elif z_axis == 'ATE-std':
            z_v = evoResults.ate_std
        elif z_axis == 'ATE-min':
            z_v = evoResults.ate_min
        elif z_axis == 'ATE-max':
            z_v = evoResults.ate_max
        elif z_axis == 'ATE-sse':
            z_v = evoResults.ate_sse
        elif z_axis == 'RPE-mean':
            z_v = evoResults.rpe_mean
        elif z_axis == 'RPE-median':
            z_v = evoResults.rpe_median
        elif z_axis == 'RPE-std':
            z_v = evoResults.rpe_std
        elif z_axis == 'RPE-min':
            z_v = evoResults.rpe_min
        elif z_axis == 'RPE-max':
            z_v = evoResults.rpe_max
        elif z_axis == 'RPE-sse':
            z_v = evoResults.rpe_sse
        elif z_axis == 'RPE-rmse':
            z_v = evoResults.rpe_rmse
        elif z_axis == 'CPU-max':
            z_v = performanceresults.max_cpu
        elif z_axis == 'CPU-mean':
            z_v = performanceresults.mean_cpu
        elif z_axis == 'Memory-max':
            z_v = performanceresults.max_ram
        else:
            # parameter
            for paramValue in current_config.paramValues:
                if z_axis == paramValue.name:
                    z_v = float(paramValue.value)
                    break    

        diagram_data[x_axis].append(x_v)
        diagram_data[y_axis].append(y_v)
        diagram_data[z_axis].append(z_v)
        diagram_data['category'].append(category)

    
    print(diagram_data)

    sub_folder_path = "/slam_hive_results/custom_analysis_group/" + str(custom_id) + "/dynamic_diagram/"
    if not os.path.exists(sub_folder_path):
        os.mkdir(sub_folder_path)


    csv_data = []
    config_id_title = "Config ID"
    x_axis_title = "X Axis(" + x_axis + ")"
    y_axis_title = "Y Axis(" + y_axis + ")"
    z_axis_title = "Z Axis(" + z_axis + ")"
    algorithm_title = "Algorithm Name"
    dataset_title = "Dataset Name"    
    for i in range(len(config_id_list)):
        config = MappingTaskConfig.query.get(config_id_list[i])
        
        config_id = config_id_list[i]
        x_value = diagram_data[x_axis][i]
        y_value = diagram_data[y_axis][i]
        z_value = diagram_data[z_axis][i]
        algorithm_name_value = config.algorithm.imageTag
        dataset_name_value = config.dataset.name

        csv_data.append({
            config_id_title: config_id,
            x_axis_title: x_value,
            y_axis_title: y_value,
            z_axis_title: z_value,
            algorithm_title: algorithm_name_value,
            dataset_title: dataset_name_value
            })
    csv_path = sub_folder_path + "/" + "RawData2_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis+".csv"
    dff = pd.DataFrame(csv_data)

    # 将DataFrame保存为CSV文件
    dff.to_csv(csv_path, index=False)    
    


    df = pd.DataFrame(diagram_data)#, columns=[x_axis, y_axis])
    # plt.figure(figsize=(10, 8))
    # fig = sns.scatterplot(x=x_axis, y=y_axis, data=df, hue='category')

    import matplotlib as mpl
    from matplotlib import font_manager


    # 加载DejaVuSans字体
    font_path = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    dejavusans = [f for f in font_path if 'DejaVuSans.ttf' in f][0]
    font_prop = font_manager.FontProperties(fname=dejavusans, size=12)  # 小四相当于12号字体

    mpl1 = mpl.rcParams['pdf.fonttype']
    mpl2 = mpl.rcParams['ps.fonttype']
    mpl3 = mpl.rcParams['font.family']
    mpl4 = 16

    # 设置全局字体属性
    mpl.rcParams['pdf.fonttype'] = 42
    mpl.rcParams['ps.fonttype'] = 42
    mpl.rcParams['font.family'] = font_prop.get_name()
    mpl.rcParams['font.size'] = 48  # 小四字体





   # 基础颜色映射（按B分类）
    unique_categories = df['category'].unique()
    unique_A = sorted(set(cat.split('  ')[0] for cat in unique_categories))
    unique_B = sorted(set(cat.split('  ')[1] for cat in unique_categories))

    # 基础调色板husl  hsv
    base_palette = sns.color_palette("dark", len(unique_A))

    # 创建颜色字典，按A和B分类
    color_dict = {}
    for i, a in enumerate(unique_A):
        # sub_palette = sns.light_palette(base_palette[i], n_colors=len(unique_B))
        sub_palette = sns.light_palette(base_palette[i], len(unique_B) * 5)
        for j, b in enumerate(unique_B):
            color_dict[f"{a}  {b}"] = sub_palette[j*5 + 4]    

    # 创建图形对象
    fig = plt.figure(figsize=(60, 20))
    ax = fig.add_subplot(111, projection='3d')

    # 绘制三维散点图
    for cat in df['category'].unique():
        subset = df[df['category'] == cat]
        ax.scatter(subset[x_axis], subset[y_axis], subset[z_axis], color=color_dict[cat], label=cat, s = 500)

    handles, labels = ax.get_legend_handles_labels()
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))

    legend = ax.legend(
        handles, labels,
        loc='upper left',  # 图例的位置：右上角
        bbox_to_anchor=(1, 1),  # 设置图例框的位置：右上角
        borderaxespad=5.  # 图例与坐标轴之间的距离
    )

    # 设置图例的字体大小和边框
    legend.prop.set_size(6)
    legend.get_frame().set_edgecolor('black')
    legend.get_frame().set_linewidth(0.5)
    plt.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)
    # 设置坐标轴标签
    ax.set_xlabel(x_axis + " " + x_unit)
    ax.set_ylabel(y_axis + " " + y_unit)
    ax.set_zlabel(z_axis + " " + z_unit)

    # # 设置刻度线的位置和标签
    # ax.set_xticks(np.arange(0, 1.1, 0.1))
    # ax.set_yticks(np.arange(0, 1.1, 0.1))
    # ax.set_zticks(np.arange(0, 1.1, 0.1))

    # ax.set_xticklabels([f'{i:.1f}' for i in np.arange(0, 1.1, 0.1)])
    # ax.set_yticklabels([f'{i:.1f}' for i in np.arange(0, 1.1, 0.1)])
    # ax.set_zticklabels([f'{i:.1f}' for i in np.arange(0, 1.1, 0.1)])

    # 添加图例
    # ax.legend(title="Category")
    
    diagram_name_pgf = "Diagram2_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis + ".pgf"
    diagram_name_png = "Diagram2_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis + ".png"
    diagram_name_pdf = "Diagram2_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis + ".pdf"
    diagram_path_pgf = sub_folder_path + diagram_name_pgf
    diagram_path_png = sub_folder_path + diagram_name_png
    diagram_path_pdf = sub_folder_path + diagram_name_pdf

    plt.savefig(diagram_path_pgf, dpi = 800)
    plt.savefig(diagram_path_png, dpi = 800)
    plt.savefig(diagram_path_pdf, dpi = 800)




    folder_path = "/slam_hive_results/custom_analysis_group/" + str(custom_id)
    yaml_files = []
    for filename in os.listdir(folder_path):
        if filename.startswith(str(custom_id)) and filename.endswith(".yaml"):
            yaml_files.append(os.path.join(folder_path, filename))
    if len(yaml_files) != 1:
        return jsonify(result='success')

    file_name = yaml_files[0]

    extend_choose = 0
    extend_threshold = []
    extend_multiple = []
    data = ""
    with open(file_name, 'r') as f:
        data = yaml.safe_load(f)
        if "extend_choose" in data['evaluation_form']['7_3d_scatter_diagram']:
            if  data['evaluation_form']['7_3d_scatter_diagram']['extend_choose'] == 1:
                extend_choose = 1
                extend_threshold = data['evaluation_form']['7_3d_scatter_diagram']['extend_threshold']
                extend_multiple = data['evaluation_form']['7_3d_scatter_diagram']['extend_multiple']
            else:
                extend_choose = 0
    
    if 1 not in Extend_axis or extend_choose == 0:
        return jsonify(result='success')

    old_suit_configs_list = []
    suit_configs_list = []
    for i in range(len(config_id_list_old)):
        old_suit_configs_list.append(MappingTaskConfig.query.get(config_id_list_old[i]))
    
    for i in range(len(config_id_list)):
        suit_configs_list.append(MappingTaskConfig.query.get(config_id_list[i]))

    for i in range(len(Extend_attribute)):
        if Extend_axis[i] == 1:
            new_val = ""
            if Extend_attribute[i].split("-")[0] == "ATE":
                new_val += "ate_"
            else:
                new_val += "rpe_"

            new_val += Extend_attribute[i].split("-")[1]
            Extend_attribute[i] = new_val

    ret = custom_analysis_resolver.get_Extend_accuracy(old_suit_configs_list, suit_configs_list, Extend_axis, Extend_attribute, extend_threshold,extend_multiple)
    # 应该要返回3个列表的列表，每个列表里有新的数据（列表里面的元素是字典）
    print(1)

    algorithm_id_dict = {}
    for config in old_suit_configs_list:
        # 给config分类
        if config.algorithm.imageTag not in algorithm_id_dict.keys():
            algorithm_id_dict.update({config.algorithm.imageTag: [config]})
        else:
            algorithm_id_dict[config.algorithm.imageTag].append(config)
    dataset_id_dict = {}
    for config in old_suit_configs_list:
        if config.dataset.name not in dataset_id_dict.keys():
            dataset_id_dict.update({config.dataset.name: [config]})
        else:
            dataset_id_dict[config.dataset.name].append(config)


    old_diagram_data = diagram_data

    diagram_data = {}
    diagram_data.update({x_axis: []})
    diagram_data.update({y_axis: []})
    diagram_data.update({z_axis: []})
    diagram_data.update({"category": []})
    for i in range(len(config_id_list_old)):
        # 获取x y对应
        x_v = 0
        y_v = 0
        current_config = MappingTaskConfig.query.get(config_id_list_old[i])
        # category = current_config.dataset.name + "  " + current_config.algorithm.imageTag
        category = current_config.algorithm.imageTag + "  " + current_config.dataset.name
        
        if Extend_axis[0] == 1:
            x_v = ret[0][current_config.id][2]
        else:    
            performanceresults = current_config.mappingTasks[0].performanceresults    
            if x_axis == 'CPU-max':
                x_v = performanceresults.max_cpu
            elif x_axis == 'CPU-mean':
                x_v = performanceresults.mean_cpu
            elif x_axis == 'Memory-max':
                x_v = performanceresults.max_ram
            else:
                # parameter
                for paramValue in current_config.paramValues:
                    if x_axis == paramValue.name:
                        x_v = float(paramValue.value)
                        break
        if Extend_axis[1] == 1:
            y_v = ret[1][current_config.id][2]  
        else:
            performanceresults = current_config.mappingTasks[0].performanceresults
            if y_axis == 'CPU-max':
                y_v = performanceresults.max_cpu
            elif y_axis == 'CPU-mean':
                y_v = performanceresults.mean_cpu
            elif y_axis == 'Memory-max':
                y_v = performanceresults.max_ram
            else:
                # parameter
                for paramValue in current_config.paramValues:
                    if y_axis == paramValue.name:
                        y_v = float(paramValue.value)
                        break   
        if Extend_axis[2] == 1:
            z_v = ret[2][current_config.id][2]  
        else:
            performanceresults = current_config.mappingTasks[0].performanceresults
        
    
            if z_axis == 'CPU-max':
                z_v = performanceresults.max_cpu
            elif z_axis == 'CPU-mean':
                z_v = performanceresults.mean_cpu
            elif z_axis == 'Memory-max':
                z_v = performanceresults.max_ram
            else:
                # parameter
                for paramValue in current_config.paramValues:
                    if z_axis == paramValue.name:
                        z_v = float(paramValue.value)
                        break    

        diagram_data[x_axis].append(x_v)
        diagram_data[y_axis].append(y_v)
        diagram_data[z_axis].append(z_v)
        diagram_data['category'].append(category)


    csv_data = []
    config_id_title = "Config ID"
    x_axis_title = "X Axis(" + x_axis + ")"
    y_axis_title = "Y Axis(" + y_axis + ")"
    z_axis_title = "Z Axis(" + z_axis + ")"
    algorithm_title = "Algorithm Name"
    dataset_title = "Dataset Name"    
    for i in range(len(config_id_list_old)):
        config = MappingTaskConfig.query.get(config_id_list_old[i])
        
        config_id = config_id_list_old[i]
        x_value = diagram_data[x_axis][i]
        y_value = diagram_data[y_axis][i]
        z_value = diagram_data[z_axis][i]
        algorithm_name_value = config.algorithm.imageTag
        dataset_name_value = config.dataset.name

        csv_data.append({
            config_id_title: config_id,
            x_axis_title: x_value,
            y_axis_title: y_value,
            z_axis_title: z_value,
            algorithm_title: algorithm_name_value,
            dataset_title: dataset_name_value
            })
    csv_path = sub_folder_path + "/" + "RawData2_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis+"_Eetend.csv"
    dff = pd.DataFrame(csv_data)

    # 将DataFrame保存为CSV文件
    dff.to_csv(csv_path, index=False)    

    
    print(diagram_data)
    df = pd.DataFrame(diagram_data)
   # 基础颜色映射（按B分类）
    unique_categories = df['category'].unique()
    unique_A = sorted(set(cat.split('  ')[0] for cat in unique_categories))
    unique_B = sorted(set(cat.split('  ')[1] for cat in unique_categories))

    # 基础调色板husl  hsv
    base_palette = sns.color_palette("dark", len(unique_A))

    base_palette_algo = sns.color_palette("dark", 16)

    # 创建颜色字典，按A和B分类
    color_dict = {}
    for i, a in enumerate(unique_A):
        # sub_palette = sns.light_palette(base_palette[i], n_colors=len(unique_B))
        sub_palette = sns.light_palette(base_palette[i], len(unique_B) * 5)

        

        # category = current_config.algorithm.imageTag + "  " + current_config.dataset.name
        # a是name
        num = -1
        if "orb-slam2" in a:
            num = 0
        if "orb-slam3" in a:
            num = 4
        if "vins-mono" in a:
            num = 8
        if "vins-fusion" in a:
            num = 12 

        for j, b in enumerate(unique_B):
            color_dict[f"{a}  {b}"] = sub_palette[j*5 + 4]  
            if num != -1:
                sub_palette_algo = sns.light_palette(base_palette_algo[num], len(unique_B) * 5)
                color_dict[f"{a}  {b}"] = sub_palette_algo[j*5 + 4]  

    # 创建图形对象
    fig = plt.figure(figsize=(60, 20))
    ax = fig.add_subplot(111, projection='3d')

    # 绘制三维散点图
    for cat in df['category'].unique():
        subset = df[df['category'] == cat]
        ax.scatter(subset[x_axis], subset[y_axis], subset[z_axis], color=color_dict[cat], label=cat, s = 600)

    handles, labels = ax.get_legend_handles_labels()
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))

    legend = ax.legend(
        handles, labels,
        loc='upper left',  # 图例的位置：右上角
        bbox_to_anchor=(1, 1),  # 设置图例框的位置：右上角
        borderaxespad=5.  # 图例与坐标轴之间的距离
    )

    # 设置图例的字体大小和边框
    legend.prop.set_size(6)
    legend.get_frame().set_edgecolor('black')
    legend.get_frame().set_linewidth(0.5)
    plt.subplots_adjust(left=0.1, right=0.8, top=0.9, bottom=0.1)
    # 设置坐标轴标签
    ax.set_xlabel(x_axis + " " + x_unit, labelpad=50)
    ax.set_ylabel(y_axis + " " + y_unit, labelpad=50)
    ax.set_zlabel(z_axis + " " + z_unit, labelpad=50)

    

    # # 设置刻度线的位置和标签
    # ax.set_xticks(np.arange(0, 1.1, 0.1))
    # ax.set_yticks(np.arange(0, 1.1, 0.1))
    # ax.set_zticks(np.arange(0, 1.1, 0.1))

    # ax.set_xticklabels([f'{i:.1f}' for i in np.arange(0, 1.1, 0.1)])
    # ax.set_yticklabels([f'{i:.1f}' for i in np.arange(0, 1.1, 0.1)])
    # ax.set_zticklabels([f'{i:.1f}' for i in np.arange(0, 1.1, 0.1)])

    # 添加图例
    # ax.legend(title="Category")
    
    diagram_name_pgf = "Diagram2_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis + "-Extend.pgf"
    diagram_name_png = "Diagram2_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis + "-Extend.png"
    diagram_name_pdf = "Diagram2_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis + "-Extend.pdf"
    diagram_path_pgf = sub_folder_path + diagram_name_pgf
    diagram_path_png = sub_folder_path + diagram_name_png
    diagram_path_pdf = sub_folder_path + diagram_name_pdf

    plt.savefig(diagram_path_pgf, dpi = 800)
    plt.savefig(diagram_path_png, dpi = 800)
    plt.savefig(diagram_path_pdf, dpi = 800)


    mpl.rcParams['pdf.fonttype'] = mpl1
    mpl.rcParams['ps.fonttype'] = mpl2
    mpl.rcParams['font.family'] = mpl3
    mpl.rcParams['font.size'] = mpl4

    return jsonify(result='success')


@app.route('/analysis/diagram/dig2/download/<int:id>',methods=['GET','POST'])
def download_diagram2(id):
  
    
    sub_folder_path = "/slam_hive_results/custom_analysis_group/" + str(id) + "/dynamic_diagram"



    download_folder_path =sub_folder_path
    download_zip_path =  "/slam_hive_results/custom_analysis_group/" + str(id) + "/dynamic_diagram.zip"
    # if os.path.exists(download_zip_path):
    #     return send_from_directory(download_folder_path, "/dynamic_diagram.zip", as_attachment=True)
    # else:
    zipDir(download_folder_path,  download_zip_path)
    return send_from_directory("/slam_hive_results/custom_analysis_group/" + str(id), "dynamic_diagram.zip", as_attachment=True)

@app.route('/analysis/diagram/dig1/download/<int:id>',methods=['GET','POST'])
def download_diagram1(id):
  
    
    sub_folder_path = "/slam_hive_results/custom_analysis_group/" + str(id) + "/dynamic_diagram"



    download_folder_path =sub_folder_path
    download_zip_path =  "/slam_hive_results/custom_analysis_group/" + str(id) + "/dynamic_diagram.zip"
    # if os.path.exists(download_zip_path):
    #     return send_from_directory(download_folder_path, "/dynamic_diagram.zip", as_attachment=True)
    # else:
    zipDir(download_folder_path,  download_zip_path)
    return send_from_directory("/slam_hive_results/custom_analysis_group/" + str(id), "dynamic_diagram.zip", as_attachment=True)

# download trajectory file
@app.route('/analysis/diagram/task1/download/<int:id>',methods=['GET','POST'])
def download_analysis_1_resource(id):
    # 读取文件，info.txt里包含config的id们
    # 下载所有的轨迹文件 和 真值文件

    info_path = "/slam_hive_results/custom_analysis_group/" + str(id) +"/info.txt"
    config_ids = []
    with open(info_path, "r") as f:
        content = f.read()
        import ast
        config_ids = ast.literal_eval((content.split("\n")[3].split(":")[1]))
    print(config_ids)

    results_path = "/slam_hive_results/custom_analysis_group/" + str(id) + "/trajectory_results"
    if not os.path.exists(results_path):
        os.mkdir(results_path)

        config0 = MappingTaskConfig.query.get(config_ids[0])
        dataset_name = config0.dataset.name
        dataset_path = "/slam_hive_datasets/" + dataset_name +"/groundtruth.txt"
        destination_folder = results_path
        new_filename = 'groundtruth.txt'
        destination_file = os.path.join(destination_folder, new_filename)
        # 复制文件
        shutil.copy2(dataset_path, destination_file)        

        for i in range(len(config_ids)):
            config = MappingTaskConfig.query.get(config_ids[i])
            task = config.mappingTasks[0]
            task_id = task.id
            current_traj_path = "/slam_hive_results/mapping_results/" + str(task_id) + "/traj.txt"
            # copy到目录
            # 源文件路径
            # 目标文件夹路径
            destination_folder = results_path
            # 新文件名
            new_filename = str(task_id)+'_traj.txt'
            # 创建目标文件路径
            destination_file = os.path.join(destination_folder, new_filename)
            # 复制文件
            shutil.copy2(current_traj_path, destination_file)

        download_zip_path =  "/slam_hive_results/custom_analysis_group/" + str(id) + "/trajectory_results.zip"
        zipDir(results_path,  download_zip_path)
    download_zip_path =  "/slam_hive_results/custom_analysis_group/" + str(id) + "/trajectory_results.zip"
    return send_from_directory("/slam_hive_results/custom_analysis_group/" + str(id), "trajectory_results.zip", as_attachment=True)
    

# download trajectory file
@app.route('/analysis/diagram/task2/download/<int:id>',methods=['GET','POST'])
def download_analysis_2_resource(id):
    # 读取文件，info.txt里包含config的id们
    # 下载所有的Evo相关的文件 和 真值文件

    info_path = "/slam_hive_results/custom_analysis_group/" + str(id) +"/info.txt"
    config_ids = []
    with open(info_path, "r") as f:
        content = f.read()
        import ast
        config_ids = ast.literal_eval((content.split("\n")[3].split(":")[1]))
    print(config_ids)

    results_path = "/slam_hive_results/custom_analysis_group/" + str(id) + "/evo_results"
    if not os.path.exists(results_path):
        os.mkdir(results_path)
     

        for i in range(len(config_ids)):
            config = MappingTaskConfig.query.get(config_ids[i])
            task = config.mappingTasks[0]
            evo = config.mappingTasks[0].evaluation
            config_id = config.id
            task_id = task.id
            evo_id = evo.id
            current_evo_path = "/slam_hive_results/evaluation_results/" + str(evo_id)
            # copy到目录
            # 源文件路径
            # 目标文件夹路径
            destination_folder = results_path
            # 新文件名
            new_filename = str(config_id) + "_" + str(task_id) + "_" + str(evo_id)
            # 创建目标文件路径
            destination_file = os.path.join(destination_folder, new_filename)
            # 复制文件
            shutil.copytree(current_evo_path, destination_file)

            # 删除轨迹文件
            if os.path.exists(results_path + "/" + new_filename + "/groundtruth.tum"):
                os.remove(results_path + "/" + new_filename + "/groundtruth.tum")
            if os.path.exists(results_path + "/" + new_filename + "/traj.tum"):
                os.remove(results_path + "/" + new_filename + "/traj.tum")

        download_zip_path =  "/slam_hive_results/custom_analysis_group/" + str(id) + "/evo_results.zip"
        zipDir(results_path,  download_zip_path)
    download_zip_path =  "/slam_hive_results/custom_analysis_group/" + str(id) + "/evo_results.zip"
    return send_from_directory("/slam_hive_results/custom_analysis_group/" + str(id), "evo_results.zip", as_attachment=True)
            


# download trajectory file
@app.route('/analysis/diagram/task4/download/<int:id>',methods=['GET','POST'])
def download_analysis_4_resource(id):
    # 读取文件，info.txt里包含config的id们
    # 下载所有的轨迹文件 和 真值文件

    info_path = "/slam_hive_results/custom_analysis_group/" + str(id) +"/info.txt"
    config_ids = []
    with open(info_path, "r") as f:
        content = f.read()
        import ast
        config_ids = ast.literal_eval((content.split("\n")[3].split(":")[1]))
    print(config_ids)

    results_path = "/slam_hive_results/custom_analysis_group/" + str(id) + "/profiling_results"
    if not os.path.exists(results_path):
        os.mkdir(results_path)       

        for i in range(len(config_ids)):
            config = MappingTaskConfig.query.get(config_ids[i])
            task = config.mappingTasks[0]
            task_id = task.id
            current_pro_path = "/slam_hive_results/mapping_results/" + str(task_id) + "/profiling.csv"
            # copy到目录
            # 源文件路径
            # 目标文件夹路径
            destination_folder = results_path
            # 新文件名
            new_filename = str(task_id)+'_profiling.csv'
            # 创建目标文件路径
            destination_file = os.path.join(destination_folder, new_filename)
            # 复制文件
            shutil.copy2(current_pro_path, destination_file)

        download_zip_path =  "/slam_hive_results/custom_analysis_group/" + str(id) + "/profiling_results.zip"
        zipDir(results_path,  download_zip_path)
    download_zip_path =  "/slam_hive_results/custom_analysis_group/" + str(id) + "/profiling_results.zip"
    return send_from_directory("/slam_hive_results/custom_analysis_group/" + str(id), "profiling_results.zip", as_attachment=True)

# download trajectory file
@app.route('/analysis/diagram/task8/download/<int:id>',methods=['GET','POST'])
def download_analysis_8_resource(id):
    # 读取文件，info.txt里包含config的id们
    # 下载所有的Evo相关的文件 和 真值文件

    info_path = "/slam_hive_results/custom_analysis_group/" + str(id) +"/info.txt"
    config_ids = []
    with open(info_path, "r") as f:
        content = f.read()
        import ast
        config_ids = ast.literal_eval((content.split("\n")[3].split(":")[1]))
    print(config_ids) # 只有1个

    results_path = "/slam_hive_results/custom_analysis_group/" + str(id) + "/repeatability_results"
    if not os.path.exists(results_path):
        os.mkdir(results_path)
     
        tasks = MappingTaskConfig.query.get(config_ids[0]).mappingTasks
        for i in range(len(tasks)):
            task = tasks[i]
            evo = task.evaluation
            task_id = task.id
            evo_id = evo.id
            current_evo_path = "/slam_hive_results/evaluation_results/" + str(evo_id)
            # copy到目录
            # 源文件路径
            # 目标文件夹路径
            destination_folder = results_path
            # 新文件名
            new_filename = str(task_id) + "_" + str(evo_id)
            # 创建目标文件路径
            destination_file = os.path.join(destination_folder, new_filename)
            # 复制文件
            shutil.copytree(current_evo_path, destination_file)

            # 删除轨迹文件
            if os.path.exists(results_path + "/" + new_filename + "/groundtruth.tum"):
                os.remove(results_path + "/" + new_filename + "/groundtruth.tum")
            if os.path.exists(results_path + "/" + new_filename + "/traj.tum"):
                os.remove(results_path + "/" + new_filename + "/traj.tum")

        download_zip_path =  "/slam_hive_results/custom_analysis_group/" + str(id) + "/repeatability_results.zip"
        zipDir(results_path,  download_zip_path)
    download_zip_path =  "/slam_hive_results/custom_analysis_group/" + str(id) + "/repeatability_results.zip"
    return send_from_directory("/slam_hive_results/custom_analysis_group/" + str(id), "repeatability_results.zip", as_attachment=True)
