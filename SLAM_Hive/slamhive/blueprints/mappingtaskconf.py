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

from flask import flash, redirect, url_for, render_template, request, jsonify, send_from_directory, abort
from slamhive import app, db
from slamhive.models import Algorithm, MappingTaskConfig, ParameterValue, AlgoParameter, Dataset, CombMappingTaskConfig, GroupMappingTaskConfig
from slamhive.forms import DeleteMappingTaskConfigForm, DeleteGroupMappingTaskConfigForm,DeleteGroupMappingTaskConfigForm1
from slamhive.blueprints.utils import *
from werkzeug.utils import secure_filename
import json, yaml, os, uuid




@app.route('/config/<int:id>/create_task', methods=['POST','GET'])
def export_config(id):
    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    config = MappingTaskConfig.query.get(id)
    config_dict = generate_config_dict(id)
    filename = str(id) + "_" + config.name + ".yaml"
    save_path = os.path.join(app.config['CONFIGURATIONS_PATH'], filename)
    save_dict_to_yaml(config_dict, save_path)
    directory = save_path.replace(filename, '')
    return send_from_directory(directory, filename, as_attachment=True)



@app.route('/config/create')
def create_config():

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    algos = Algorithm.query.order_by(Algorithm.name).all()
    datasets = Dataset.query.order_by(Dataset.name).all()
    parameters = AlgoParameter.query.order_by(AlgoParameter.id.asc()).all()
    return render_template('/config/create.html', algos=algos, datasets=datasets, parameters=parameters)

    

@app.route('/config/create_combination')
def create_combination_config():
    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    algos = Algorithm.query.order_by(Algorithm.name).all()
    datasets = Dataset.query.order_by(Dataset.name).all()
    parameters = AlgoParameter.query.order_by(AlgoParameter.id.asc()).all()
    return render_template('/config/create_combination.html', algos=algos, datasets=datasets, parameters=parameters)


@app.route('/config/search/submit', methods=['POST'])
def submit_search_configs():
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
    form = DeleteMappingTaskConfigForm()
    mappingTasks_number = {}
    for i in range(len(suit_configs)):
        mappingTasks_number.update({suit_configs[i].id: len(suit_configs[i].mappingTasks)})
    
    ret = []
    for i in range(len(suit_configs)):
        ret.append(suit_configs[i].id)
    
    # return jsonify(data=ret)
    ret.reverse()

    return render_template('/config/search_result.html', configs=suit_configs, form=form, mappingTasks_number = mappingTasks_number, configs_id = ret, version=app.config["CURRENT_VERSION"])




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
                # 判断条件中的parameter的key 对应config中对应的parameter的valuetype是什么类型
                # 之前：parameter template中的valueType
                # 现在：parameter中的valueType
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




@app.route('/config/create/submit', methods=['POST'])
def submit_config(): 

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    #### suit the new database structure

    

    # print("------submit_config()------")
    data = json.loads(request.get_data())

    print(data)

    MappingTaskConfig_Name = data[str(len(data)-2)]['MappingTaskConfig_Name']
    MappingTaskConfig_Description = data[str(len(data)-2)]['MappingTaskConfig_Description']
    Algorithm_Id = data[str(len(data)-1)]['Algorithm_Id']
    Dataset_Id = data[str(len(data)-1)]['Dataset_Id']
    
    # print(data)
    exist_param_ids, exists_config_id = config_match(data)
    # print(str(check_number), str(exist_param_ids), str(exists_config_id))
    # print(check_number)
    if exists_config_id == -1:
        config = MappingTaskConfig(name=MappingTaskConfig_Name, description=MappingTaskConfig_Description)
        algorithm = Algorithm.query.get(Algorithm_Id)   
        dataset = Dataset.query.get(Dataset_Id)     
        db.session.add(config)
        algorithm.mappingTaskConfs.append(config)
        dataset.mappingTaskConfs.append(config)
        #  use append instead of operate foreign key
        db.session.commit()
        # print(data)
        now_number = -1
        for value1 in data.values():
            now_number += 1
            if exist_param_ids[now_number] != -1:
                # print("exist: ", str(exist_param_ids[now_number]))
                paramValue = ParameterValue.query.get(exist_param_ids[now_number])
                config.paramValues.append(paramValue)
                db.session.commit()
            else:
                print('------')
                parameter = []
                for value2 in value1.values():
                    # print(value2)
                    # parameter的顺序：
                    # parameterID; className; keyName; valueType; value; 
                    parameter.append(value2)
                # print(parameter[0])#algoParameter id
                # print(parameter[3])#ParameterValue value
                param = AlgoParameter.query.get(parameter[0])
                print(parameter[2])
                paramValue = ParameterValue(name=param.name, className=parameter[1], keyName=parameter[2], value=standard_value(parameter[3], parameter[4]), valueType = parameter[3])        
                config.paramValues.append(paramValue)
                param.paramValues.append(paramValue)
                db.session.add(paramValue)
                db.session.commit()       
        return jsonify(result='success')
    else:
        # return jsonify(result='already exist, config id is ' + str(exists_config_id))
        return jsonify(result='exist')
        
# 创建combination mapping task
@app.route('/config/create_combination/submit', methods=['POST'])
def submit_combination_config(): 
    # 暂时先把参数写到description里
    # 注释掉数据库

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    data = json.loads(request.get_data())

    print(data)
    # print(data)

    MappingTaskConfig_Name = data[str(len(data)-2)]['MappingTaskConfig_Name']
    MappingTaskConfig_Description = data[str(len(data)-2)]['MappingTaskConfig_Description']
    MappingTaskConfig_Resolution = data[str(len(data)-2)]['MappingTaskConfig_Resolution']
    MappingTaskConfig_Frequency = data[str(len(data)-2)]['MappingTaskConfig_Frequency']
    Algorithm_Id = data[str(len(data)-1)]['Algorithm_Id']
    Dataset_Id = data[str(len(data)-1)]['Dataset_Id']

    #print(MappingTaskConfig_Description)
    dd = yaml.safe_load(MappingTaskConfig_Resolution)

    # print(dd)

########################    
#s
    combMappingTaskConfig = CombMappingTaskConfig(name = MappingTaskConfig_Name, description = MappingTaskConfig_Description)
    db.session.add(combMappingTaskConfig)
    db.session.commit()    
#e

    data_dict = {}
    # 修改主要在楼下这个函数里面
    generate_each_config_dict(data, data_dict) 
    print(len(data_dict))
    print(data_dict["0"])

    #print(data_dict)
    # with open('/slam_hive_results/ttt.yaml', 'w', encoding="utf-8") as f:
    #     f.write(yaml.dump(data_dict, indent = 2))


    # for d in data_dict.values():
    #     for v in d.values():
    #         if 'keyName' in v.keys():
    #             if v['paramType'] == 'Dataset frequency':
    #                 print(v['keyName'], v['value'], v['paramType'], v['valueType'])
    #     print()
    # print(data_dict)
    # for key, value in data_dict.items():
    #     print(key, value)
    # return jsonify(result='success')

######################################
    config_number = len(data_dict)
    for i in range(config_number):
        print(data_dict[str(i)])
        exist_param_ids, exists_config_id = config_match(data_dict[str(i)])

        if exists_config_id != -1:
            current_mappingtaskconfig = MappingTaskConfig.query.get(exists_config_id)
            combMappingTaskConfig.mappingTaskConf.append(current_mappingtaskconfig)
        else:
            config = MappingTaskConfig(name=MappingTaskConfig_Name + "-" + str(i), description=MappingTaskConfig_Description)
            algorithm = Algorithm.query.get(Algorithm_Id)   
            dataset = Dataset.query.get(Dataset_Id)     
            db.session.add(config)
            algorithm.mappingTaskConfs.append(config)
            dataset.mappingTaskConfs.append(config)
            combMappingTaskConfig.mappingTaskConf.append(config)
            #  use append instead of operate foreign key
            db.session.commit()
            # print(data)
            now_number = -1
            for value1 in data_dict[str(i)].values():
                now_number += 1
                if exist_param_ids[now_number] != -1:
                    # print("exist: ", str(exist_param_ids[now_number]))
                    paramValue = ParameterValue.query.get(exist_param_ids[now_number])
                    config.paramValues.append(paramValue)
                    db.session.commit()
                else:
                    print('------')
                    parameter = []
                    for value2 in value1.values():
                        # print(value2)
                        parameter.append(value2)
                    # print(parameter[0])#algoParameter id
                    # print(parameter[3])#ParameterValue value
                    param = AlgoParameter.query.get(parameter[0])
                    paramValue = ParameterValue(name=param.name,className=parameter[5] ,keyName=parameter[2], value=standard_value(parameter[3], parameter[4]), valueType=parameter[3])        
                    config.paramValues.append(paramValue)
                    param.paramValues.append(paramValue)
                    db.session.add(paramValue)
                    db.session.commit()       
    db.session.commit()   


    return jsonify(result='success')

@app.route('/config/index', methods=['GET', 'POST'])
def index_config():
    form = DeleteMappingTaskConfigForm()
    
    # 获取前端的页码参数，默认第一页
    page = request.args.get('page', '1')  # 默认值改成字符串 '1'
    try:
        page = int(page)
    except ValueError:
        page = 1  # 如果转换失败（如 'NaN'），默认回到第一页
    
    per_page = 10  # 每页显示 10 个 config
    total_configs = MappingTaskConfig.query.count()  # 获取 config 总数
    total_pages = int(total_configs / per_page) if total_configs % per_page == 0 else int(total_configs / per_page) + 1  # 计算总页数
    
    # 分页获取 config
    configs = (MappingTaskConfig.query
               .order_by(MappingTaskConfig.id.desc())
               .offset((page - 1) * per_page)
               .limit(per_page)
               .all())
    
    algos = Algorithm.query.order_by(Algorithm.id.desc()).all()
    datasets = Dataset.query.order_by(Dataset.id.desc()).all()
    
    mappingTasks_number = {config.id: len(config.mappingTasks) for config in configs}
    
    # db.session.commit()

    return render_template('/config/index.html', 
                           configs=configs, 
                           form=form, 
                           mappingTasks_number=mappingTasks_number, 
                           algos=algos, 
                           datasets=datasets, 
                           total_configs=total_configs, 
                           total_pages=total_pages, 
                           current_page=page, 
                           version=app.config['CURRENT_VERSION'])

@app.route('/config/index_combination', methods=['POST','GET'])
def index_combination_config():
    form = DeleteMappingTaskConfigForm()
    # configs = MappingTaskConfig.query.order_by(MappingTaskConfig.id.desc()).all()
    comb_configs = CombMappingTaskConfig.query.order_by(CombMappingTaskConfig.id.desc()).all()

    # mappingTasks_number = {}
    # for i in range(len(configs)):
    #     mappingTasks_number.update({configs[i].id: len(configs[i].mappingTasks)})
    return render_template('/config/index_combination.html', comb_configs=comb_configs, form=form) # , mappingTasks_number = mappingTasks_number)

## abort
# @app.route('/config/create_group/index', methods=['POST','GET'])
# def index_create_group_config():
#     form = DeleteMappingTaskConfigForm()
#     configs = MappingTaskConfig.query.order_by(MappingTaskConfig.id.desc()).all()
#     algos = Algorithm.query.order_by(Algorithm.id.desc()).all()
#     datasets = Dataset.query.order_by(Dataset.id.desc()).all()

#     comb_configs = CombMappingTaskConfig.query.order_by(CombMappingTaskConfig.id.desc()).all()

#     mappingTasks_number = {}
#     for i in range(len(configs)):
#         mappingTasks_number.update({configs[i].id: len(configs[i].mappingTasks)})
#     db.session.commit()
#     return render_template('/config/create_group.html', configs=configs, form=form, mappingTasks_number = mappingTasks_number, 
#                            algos = algos, datasets = datasets, comb_configs = comb_configs)

## abort
# @app.route('/config/create_group/submit', methods=['POST','GET'])
# def index_submit_group_config():
#     data = json.loads(request.get_data())
#     print(data)
#     real_mappingtaskconfigIdList_set = set()
#     real_mappingtaskconfigIdList = []
#     for value in data['config'].values():
#         real_mappingtaskconfigIdList_set.add(int(value["parameterID"]))
#     for value in data['combconfig'].values():
#         # real_mappingtaskconfigIdList_set.add(int(value["parameterID"]))
#         temp_comb = CombMappingTaskConfig.query.get(int(value["parameterID"]))
#         for i in range(len(temp_comb.mappingTaskConf)):
#             real_mappingtaskconfigIdList_set.add(temp_comb.mappingTaskConf[i].id)
#     ## create a group
#     print(real_mappingtaskconfigIdList_set)

#     name = data['name']
#     description = data['description']



#     group = GroupMappingTaskConfig()
#     group.name = name
#     group.description = description
#     for id in real_mappingtaskconfigIdList_set:
#         group.mappingTaskConf.append(MappingTaskConfig.query.get(id))
#     db.session.add(group)
#     db.session.commit()


#     # 创建1个文件夹
#     os.mkdir("/slam_hive_results/group/" + str(group.id))


#     return jsonify(result='success')
#     # batchMappingTask_id = batchMappingTask.id
#     # batchMappingTask_path = os.path.join(app.config['BATCHMAPPINGTASK_PATH'], str(batchMappingTask_id))
#     # if not os.path.exists(batchMappingTask_path):
#     #     os.mkdir(batchMappingTask_path)
#     # batchMappingTask.path = batchMappingTask_path

#     # config_filename_list = []
#     # mappingtaskIdList = []

## abort
@app.route('/config/group/index', methods=['POST','GET'])
# def index_group_config():
#     form = DeleteGroupMappingTaskConfigForm()
#     group_configs = GroupMappingTaskConfig.query.order_by(GroupMappingTaskConfig.id.desc()).all()

#     return render_template('/config/index_group.html', group_configs=group_configs, form=form) # , mappingTasks_number = mappingTasks_number)

## abort
# @app.route('/config/group/show/<int:id>', methods=['POST','GET'])
# def show_group_config(id):
#     form = DeleteGroupMappingTaskConfigForm1()
#     group_config = GroupMappingTaskConfig.query.get(id)
#     configs = group_config.mappingTaskConf
#     mappingTasks_number = {}
#     for i in range(len(configs)):
#         mappingTasks_number.update({configs[i].id: len(configs[i].mappingTasks)})

#     return render_template('/config/show_group.html', group_config = group_config, configs=configs, mappingTasks_number = mappingTasks_number, form = form)

## abort
# @app.route('/config/group/<int:group_id>/<int:config_id>/delete', methods=['POST'])
# def delete_group_config(group_id, config_id):
#     form = DeleteGroupMappingTaskConfigForm()
#     if form.validate_on_submit():
#         group = GroupMappingTaskConfig.query.get(group_id)
#         config = MappingTaskConfig.query.get(config_id)
#         group.mappingTaskConf.remove(config)
#         # db.session.delete(group)
#         db.session.commit()
#     # return redirect(url_for('show_group_config', group_id))
#     return show_group_config(group_id)

## abort
# @app.route('/config/group/<int:id>/delete', methods=['POST'])
# def delete_group(id):
#     form = DeleteGroupMappingTaskConfigForm1()
#     if form.validate_on_submit():
#         group = GroupMappingTaskConfig.query.get(id)
#         db.session.delete(group)
#         db.session.commit()
#     return redirect(url_for('index_group_config'))




@app.route('/config/<int:id>/show', methods=['GET', 'POST'])
def show_config(id):
    config = MappingTaskConfig.query.get(id)
    algos = Algorithm.query.order_by(Algorithm.name).all()
    datasets = Dataset.query.order_by(Dataset.name).all()
    parameters = AlgoParameter.query.order_by(AlgoParameter.id.asc()).all()
    return render_template('/config/show.html', algos=algos, datasets=datasets, parameters=parameters, config=config)

@app.route('/config/<int:id>/show_combination', methods=['GET', 'POST'])
def show_combination_config(id):
    comb_config = CombMappingTaskConfig.query.get(id)
    configs = CombMappingTaskConfig.query.get(id).mappingTaskConf
    mappingTasks_number = {}
    for i in range(len(configs)):
        mappingTasks_number.update({configs[i].id: len(configs[i].mappingTasks)})
    db.session.commit()
    return render_template('/config/show_combination.html', comb_config = comb_config, configs=configs, mappingTasks_number = mappingTasks_number)

@app.route('/config/<int:id>/delete', methods=['POST'])
def delete_config(id):

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    form = DeleteMappingTaskConfigForm()
    if form.validate_on_submit():
        config = MappingTaskConfig.query.get(id)
        db.session.delete(config)
        db.session.commit()
    return redirect(url_for('index_config'))


@app.route('/config/<int:id>/copy', methods=['GET', 'POST'])
def copy_config(id):

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    config = MappingTaskConfig.query.get(id)
    algos = Algorithm.query.order_by(Algorithm.name).all()
    datasets = Dataset.query.order_by(Dataset.name).all()
    parameters = AlgoParameter.query.order_by(AlgoParameter.id.asc()).all()
    return render_template('/config/copy.html', algos=algos, datasets=datasets, parameters=parameters, config=config)

@app.route('/config/<int:id>/copy_combination', methods=['GET', 'POST'])
def copy_combination_config(id):

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    config = MappingTaskConfig.query.get(id)
    algos = Algorithm.query.order_by(Algorithm.name).all()
    datasets = Dataset.query.order_by(Dataset.name).all()
    parameters = AlgoParameter.query.order_by(AlgoParameter.id.asc()).all()
    return render_template('/config/copy_combination.html', algos=algos, datasets=datasets, parameters=parameters, config=config)


##############To do################
#         upload config yaml
###################################
# app.config['MAX_CONTENT_LENGTH'] = 3*1024*1024
# app.config['UPLOAD_PATH'] = os.path.join(app.root_path, 'uploads')

# def random_filename(filename):
#     ext = os.path.splitext(filename)[1]
#     new_filename = uuid.uuid4().hex + ext
#     return new_filename

# @app.route('/config/upload', methods=['POST','GET'])
# def upload_config():
#     form = UploadForm()
#     print("success: form = UploadForm()")
#     if form.validate_on_submit():
#         f = form.config.data
#         filename = random_filename(f.filename)
#         f.save(os.path.join(app.config['UPLOAD_PATH'], filename))
#         flash('Upload success.')
#         print("Upload success"+'\n')
#         return redirect(url_for('show_config', filename=filename))
#     return render_template('/config/upload.html', form=form)

# app.jinja_env.globals.update(isinstance=isinstance)
# @app.route('/config/uploaded/show/<path:filename>')
# def show_config(filename):
#     yaml_file = os.path.join(app.config['UPLOAD_PATH'], filename)
#     with open(yaml_file, encoding='utf-8') as file:
#         content = file.read()
#         print(content)
#         data = yaml.load(content, Loader=yaml.FullLoader)
#         print(data)
#         # print(type(data))
#         ##############To do################
#         #store to database
#         ###################################
#     return render_template('/config/uploaded.html', filename=filename, data=data)

# @app.route('/config/uploaded/<path:filename>')
# def get_file(filename):
#     return send_from_directory(app.config['UPLOAD_PATH'], filename)

def standard_value(valueType,value):
    # print("---", valueType,value)
    if valueType == 'int':
        value = str(int(value))
    elif valueType == 'float':
        value = str(float(value))
    elif valueType == 'string':
        pass
    elif valueType == 'matrix':
        temp_matrix = eval(value)
        for i in range(len(temp_matrix)):
            temp_matrix[i] = str(temp_matrix[i]).strip()
            if "." in temp_matrix[i] :
                # float
                temp_matrix[i] = float(temp_matrix[i])
            else :
                # int
                temp_matrix[i] = int(temp_matrix[i])
        value = str(temp_matrix)
    return value

def config_match(data):
    # print(data)

        # # get last element: mappingtaskconfID, then delete
    MappingTaskConfig_Name = data[str(len(data)-2)]['MappingTaskConfig_Name']
    MappingTaskConfig_Description = data[str(len(data)-2)]['MappingTaskConfig_Description']
    Algorithm_Id = data[str(len(data)-1)]['Algorithm_Id']
    Dataset_Id = data[str(len(data)-1)]['Dataset_Id']
    del data[str(len(data)-1)]
    del data[str(len(data)-1)]

    # print(data)
    # print(type(data))
    # print(data["0"]["valueType"])

    # standradization the value

    for i in range(len(data)):
        # print(data[str(i)])
        temp_param = data[str(i)]
        temp_keyName = temp_param['keyName']
        temp_valueType = temp_param['valueType']
        temp_value = temp_param['value']
        print(temp_keyName, temp_valueType, temp_value)
        new_value = standard_value(temp_valueType, temp_value)
        
        # ap = AlgoParameter.query.get(temp_param['parameterID'])
        # print(temp_value, ap.value, standard_value(ap.valueType, ap.value) == new_value)

        data[str(i)]['value'] = new_value


    # 1. check if all the new parameters are in db already
    # check_number: 0 - all new ; 1 - parts new ; 2 - all in db
    
    db_params = ParameterValue.query.all()
    db_ids = []
    db_keyNames = []
    db_standrad_value = []
    db_param_template_ids = []
    db_hash = {}
    print("------------------- parameters ----------------")
    # print(db_params)
    for i in range(len(db_params)):
        db_ids.append(db_params[i].id)
        db_keyNames.append(db_params[i].keyName)
        # valueType修改
        db_standrad_value.append(standard_value(db_params[i].valueType, db_params[i].value))
        db_param_template_ids.append(db_params[i].algoParam.id)
        hash_key = str(db_params[i].algoParam.id) + ": " + db_params[i].keyName + ": " + standard_value(db_params[i].valueType, db_params[i].value) + ": " + (db_params[i].valueType if db_params[i].valueType is not None else "") + ": " + (db_params[i].className if db_params[i].className is not None else "")
        
        db_hash[hash_key] = db_params[i].id
    
    param_exist_ids = []
    check_number = 0
    exist_number = 0


    # print(db_hash)

    for i in range(len(data)):
        param_exist_ids.append(-1) #init
        temp_param = data[str(i)]

        temp_keyName = temp_param['keyName']
        temp_value = temp_param['value']
        temp_valueType = temp_param['valueType']
        temp_className = temp_param['className']
        temp_template_id = temp_param['parameterID'] # 这个其实对应的是template的id 

        # 修改一下；加上value type 和 class name
        temp_hash = temp_template_id + ": " + temp_keyName + ": " + temp_value + ": " + temp_valueType + ": " + temp_className


        if temp_hash in db_hash.keys():
            param_exist_ids[i] = db_hash[temp_hash]
            check_number = 1
            exist_number += 1
        else :
            pass
    if exist_number == len(data):
        check_number = 2
    
    # print(check_number)
    exist_config_id = -1

    if check_number == 2:

        exist_configs = MappingTaskConfig.query.all()
        exist_configs_checks = []
        for i in range(len(exist_configs)):
            exist_configs_checks.append(1)
            if len(data) != len(exist_configs[i].paramValues) or str(Algorithm_Id) != str(exist_configs[i].algorithm_id) or str(Dataset_Id) != str(exist_configs[i].dataset_id):
                exist_configs_checks[i] = 0
        
        for i in range(len(data)):
            for j in range(len(exist_configs)):
                if exist_configs_checks[j] == 0:
                    continue
                temp_check = 0
                for k in range(len(exist_configs[j].paramValues)):
                    config_keyName = exist_configs[j].paramValues[k].keyName
                    config_standard_value = standard_value(exist_configs[j].paramValues[k].valueType, exist_configs[j].paramValues[k].value)
                    config_valueType = exist_configs[j].paramValues[k].valueType
                    config_className = exist_configs[j].paramValues[k].className
                    config_template_id = exist_configs[j].paramValues[k].algoParam.id
                    if str(config_template_id) == data[str(i)]['parameterID'] and config_standard_value == data[str(i)]['value'] and config_keyName == data[str(i)]['keyName'] and config_valueType == data[str(i)]['valueType'] and config_className == data[str(i)]['className']:
                        temp_check = 1
                        break
                if temp_check == 0:
                    exist_configs_checks[j] = 0
        
        
        for i in range(len(exist_configs)):
            if exist_configs_checks[i] == 1:
                exist_config_id = exist_configs[i].id
        
    print("exist config id: ", str(exist_config_id))
    
    return param_exist_ids, exist_config_id



        
        

