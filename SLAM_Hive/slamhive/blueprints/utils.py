### note
# Dataset resolution intrinsic 和 Dataset resolution size是服务于resolution的参数，并不会实际写入到config中

# 逻辑梳理
# config中的某些parameter代表了分辨率和频率
# 当我们通过dataset resolution和dataset frequency修改：key代表对应的parameter，value代表了对应的修改数值（通过比例，1表示没有修改）
  # 如果是单一创建：直接将修改后的频率和分辨率填入
  # 如果是组合创建：则填入原始频率和分辨率，然后在程序中生成对应的数值
# 创建出来的config，包含的频率和分辨率都是修改后的

# 对于resolution来说，对应的图片大小和相机内参同时需要修改

  # 如果组合创建：同上，在config中将会填入修改后的参数
  # 单独创建：i直接填入修改后的参数

### 然后 在controller，对数据集进行修改


# todo 实际关联频率和分辨率的话题（比如freq）#### 重要，作为
# 一个idea：
#比如 orb2中 freq表示frequency；orb3中 frequency表示frequency
# key和value都是可填入：改动较大  也不是不行
# 这种情况，我们使用一个更general的参数（）


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

import yaml, os, re
from slamhive.models import MappingTaskConfig, AlgoParameter, Algorithm, Dataset

# config_dict_combination：存储整个参数字典 静态
# algorithm_parameters_key_list：存储每一个key 静态
# row_number: key的数量（行数）
# now_number：当前层所在的行（从0开始）
# temp_result：dict；每次到最后一层，在该dict前添加好key（algorithm-parameters ），然后将该dict加入到algorithm_parameters_dict_list中
# algorithm_parameters_dict_list：最终结果；存储一个list - dict (dict里的value是dict)
# abort
def dfs_generate_combination(config_dict_combination, algorithm_parameters_key_list, row_number, now_number, temp_result, algorithm_parameters_dict_list):
    if now_number == row_number:
        # 生成一条结果
        new_temp_result = {}
        for key, value in temp_result.items():
            new_key = key
            new_value = value
            new_temp_result.update({new_key: new_value})
        algorithm_parameters_dict_list.append({'algorithm-parameters': new_temp_result})
        return ;
    # 找到这一层对应的key
    # now_key = config_dict_combination['algorithm-parameters'][now_number].value[0 1 2 3]
    # 遍历最里层的list
    for inner_value in  config_dict_combination['algorithm-parameters'][algorithm_parameters_key_list[now_number]]:
        #inner_value就是具体的数值了
        temp_result.update({algorithm_parameters_key_list[now_number]: inner_value})
        dfs_generate_combination(config_dict_combination, algorithm_parameters_key_list, row_number, now_number + 1, temp_result, algorithm_parameters_dict_list)
        temp_result.pop(algorithm_parameters_key_list[now_number])



# abort
def save_dict_to_yaml_combination(config_dict_combination, mapping_result_dir, config_filename):

    # 统计出第一维的number


    # 遍历config_dict_combination[algorithm-parameters]
        # 统计algo的行数
        # 将其中的每个字典的key保存成一个list
    row_number = 0
    algorithm_parameters_key_list = []
    for algo_key, algo_value in config_dict_combination['algorithm-parameters'] .items():
    #     # algo_value存储的是一个list
        row_number += 1
        algorithm_parameters_key_list.append(algo_key)


    # 生成一个list，列表里的类型是dict
    temp_result = {}
    algorithm_parameters_dict_list = []
    dfs_generate_combination(config_dict_combination, algorithm_parameters_key_list, row_number, 0, temp_result,  algorithm_parameters_dict_list)

    # algorithm_parameters_dict_list: algorithm-parameters字典的列表
    ## {'algorithm-parameters': {'nFeatures': '1000', 'scaleFactor': '1.2', 'nLevels': '8', 'iniThFAST': '20', 'minThFAST': '7'}}
    ## {'algorithm-parameters': {'nFeatures': '1000', 'scaleFactor': '1.2', 'nLevels': '9', 'iniThFAST': '20', 'minThFAST': '7'}}
    ## {'algorithm-parameters': {'nFeatures': '1000', 'scaleFactor': '1.5', 'nLevels': '8', 'iniThFAST': '20', 'minThFAST': '7'}}



    algo_number = len(algorithm_parameters_dict_list) # algo的总数；代表要生成这么多个文件


    for now_algo_number in range(algo_number):
        # 构建save_path
        sub_path = os.path.join(mapping_result_dir, str(now_algo_number) )
        if not os.path.exists(sub_path):
            os.mkdir(sub_path)
        save_path = os.path.join(mapping_result_dir, str(now_algo_number), config_filename)
        with open(save_path, "w") as f:
            for key, value in config_dict_combination.items():
                if key == "dataset-parameters":
                    f.write(key + ":" + "\n")
                    for data_key, data_value in value.items():
                        f.write("  " + data_key + ": " + data_value + "\n")
                elif key == "algorithm-parameters": #### 修改 使用刚才生成的list
                    f.write(key + ":" + "\n")
                    for algo_key, algo_value in algorithm_parameters_dict_list[now_algo_number]['algorithm-parameters'].items():# value.items():
                        f.write("  " + algo_key + ": " + algo_value + "\n")
                elif key == "dataset-remap":
                    f.write(key + ":" + "\n")
                    for remap_key, remap_value in value.items():
                        f.write("  " + remap_key + ": " + remap_value + "\n")
                elif key == "algorithm-remap":
                    f.write(key + ":" + "\n")
                    for remap_key, remap_value in value.items():
                        f.write("  " + remap_key + ": " + remap_value + "\n")
                else:
                    f.write(key + ": " + value + "\n")
    return algo_number
# todo
def save_dict_to_yaml(config_dict, save_path):
    # print(config_dict)
    # 疑惑：是不是写不进去size 和 intrinsic
    with open(save_path, "w") as f:
        for key, value in config_dict.items():
            if key == "dataset-parameters":
                f.write(key + ":" + "\n")
                for data_key, data_value in value.items():
                    f.write("  " + data_key + ": " + data_value + "\n")
            elif key == "algorithm-parameters":
                f.write(key + ":" + "\n")
                for algo_key, algo_value in value.items():
                    f.write("  " + algo_key + ": " + algo_value + "\n")
            elif key == "dataset-remap":
                f.write(key + ":" + "\n")
                for remap_key, remap_value in value.items():
                    f.write("  " + remap_key + ": " + remap_value + "\n")
            elif key == "algorithm-remap":
                f.write(key + ":" + "\n")
                for remap_key, remap_value in value.items():
                    f.write("  " + remap_key + ": " + remap_value + "\n")
            elif key == "dataset-frequency":
                f.write(key + ":" + "\n")
                for remap_key, remap_value in value.items():
                    f.write("  " + remap_key + ": " + remap_value + "\n")
            elif key == "dataset-resolution":
                f.write(key + ":" + "\n")
                for remap_key, remap_value in value.items():
                    f.write("  " + remap_key + ": " + remap_value + "\n")
            elif key == "general-parameter":
                f.write(key + ":" + "\n")
                for remap_key, remap_value in value.items():
                    f.write("  " + remap_key + ": " + remap_value + "\n")
            else:
                if value == "" or value == None:
                    f.write(key + ": " + "" + "\n") # dataset and algorhtm attribute # TODO 这里感觉还是要写入数据库里
                else:
                    f.write(key + ": " + value + "\n") # dataset and algorhtm attribute # TODO 这里感觉还是要写入数据库里

# todo
def generate_config_dict(id):
    config = MappingTaskConfig.query.get(id)
    config_dict = {}
    config_dict.update({config.algorithm.name:str(config.algorithm.imageTag)})
    config_dict.update({"slam-hive-dataset":str(config.dataset.name)})
    dataset_params_dict = {}
    algo_params_dict = {}
    dataset_remap_dict = {}
    algo_remap_dict = {}
    dataset_frequency_dict = {}
    dataset_resolution_dict = {}
    general_parameter_dict = {}
    for paramValue in config.paramValues:
        # change: don't use algoParam.paramType
        if(paramValue.algoParam.paramType == "Dataset"):
            dataset_params_dict.update({paramValue.keyName: paramValue.value.strip(" ")})

        elif(paramValue.algoParam.paramType == "Algorithm"):
                algo_params_dict.update({paramValue.keyName: paramValue.value.strip(" ")})

        elif(paramValue.algoParam.paramType == "Dataset remap"):
                dataset_remap_dict.update({paramValue.keyName: paramValue.value.strip(" ")})

        elif(paramValue.algoParam.paramType == "Algorithm remap"):
            value_list = str(paramValue.value).split('\n')
            for value in value_list:
                key_value = value.split(':')
                algo_remap_dict.update({paramValue.keyName: paramValue.value.strip(" ")})
                
        elif(paramValue.algoParam.paramType == "Dataset matrix"):
            dataset_params_dict.update({paramValue.keyName: paramValue.value.strip(" ")})

        ##DOING provide dataset frequency and resolution function
        ##single config
        elif(paramValue.algoParam.paramType == "Dataset frequency"):
            dataset_frequency_dict.update({paramValue.keyName: paramValue.value.strip(" ")})

        elif(paramValue.algoParam.paramType == "Dataset resolution"):
            dataset_resolution_dict.update({paramValue.keyName: paramValue.value.strip(" ")})

        
        elif(paramValue.algoParam.paramType == "General parameter"):
            general_parameter_dict.update({paramValue.keyName: paramValue.value.strip(" ")})


        config_dict.update({'algorithm-parameters': algo_params_dict})
        config_dict.update({'dataset-parameters': dataset_params_dict})
        config_dict.update({'algorithm-remap': algo_remap_dict})
        config_dict.update({'dataset-remap': dataset_remap_dict})
        config_dict.update({'dataset-frequency': dataset_frequency_dict})
        config_dict.update({'dataset-resolution': dataset_resolution_dict})
        config_dict.update({'general-parameter': general_parameter_dict})
    
    return config_dict

###########################################################
# resolution_values_dict: 存储分辨率相关参数的对应值，格式参考文件
###########################################################

def dfs_generate_each_config_dict(data_dict, data, now_number, parameter_number, temp_dict, resolution_values_dict, frequency_same_list_list):
    if now_number == parameter_number:
        # update data_dict
        now_data_dict_number = len(data_dict)
        # print(temp_dict)
        current_dict = {}
        dataset_resolution_size_dict = {}
        dataset_resolution_intrinsic_dict = {}
        dataset_resolution_dict = {}

        dataset_frequency_dict = {}
        dataset_frequency_remap_dict = {}

        # 首先根据frequency判断是否是相同的
        
        print("type: ", type(temp_dict[str(0)]['parameterID']))
        for i in range(len(frequency_same_list_list)):
            check_set = set()
            
            for k in range(len(temp_dict)):
                if temp_dict[str(k)]['parameterID'] in frequency_same_list_list[i]:
                    check_set.add(temp_dict[str(k)]['value'])
            print("ddd", check_set)
            if len(check_set) != 1: # 有不同的数字
                return ;

        for key, value in temp_dict.items(): # 遍历每一个参数
            new_key = key
            new_value = value
            new_value = {}
            new_value.update({'parameterID': value['parameterID']})
            new_value.update({'paramType': value['paramType']})
            new_value.update({'keyName':value['keyName']})
            new_value.update({'valueType': value['valueType']})
            new_value.update({'value': value['value']})
            new_value.update({'className': value['className']})
            current_dict.update({new_key: new_value})
            if value['paramType'] == 'Dataset resolution size':
                #dataset_resolution_size_dict.update({value['keyName']: value['value']})
                # key：该参数的keyname；value：该参数的全部信息
                # size：需要修改的参数--跟size有关（width；height）
                dataset_resolution_size_dict.update({value['keyName']: value})
            elif value['paramType'] == 'Dataset resolution intrinsic':
                #dataset_resolution_intrinsic_dict.update({value['keyName']: value['value']})
                dataset_resolution_intrinsic_dict.update({value['keyName']: value})
            elif value['paramType'] == 'Dataset resolution':
                #dataset_resolution_dict.update({value['keyName']: value['value']})
                dataset_resolution_dict.update({value['keyName']: value})
            elif value['paramType'] == 'Dataset frequency':
                dataset_frequency_dict.update({value['keyName']: value})
            elif value['paramType'] == 'Dataset frequency remap':
                dataset_frequency_remap_dict.update({value['keyName']: value})

        # print("*************************")
        # print(dataset_resolution_dict)
        # print(dataset_resolution_size_dict)
        # print(dataset_resolution_intrinsic_dict)
        # print(dataset_frequency_dict)
        # print(dataset_frequency_remap_dict)


        for key, value in current_dict.items():
            # 这个循环的目的应该就是为了处理resolution相关的

            # 这里不需要标准化了，都是str
            if value["keyName"] in dataset_resolution_size_dict.keys() and value['paramType'] != "Dataset resolution size":
                # image height or width
                ## current_dict[key]["value"] = str(int(int(current_dict[key]["value"]) * float(dataset_resolution_dict[dataset_resolution_size_dict[value["keyName"]]['value']]['value'])))
                print("--------resoluiton--------")
                print(current_dict[key]["keyName"], current_dict[key]["value"])
                current_dict[key]["value"] = str(resolution_values_dict[int(dataset_resolution_dict[dataset_resolution_size_dict[value["keyName"]]['value']]['parameterID'])][float(dataset_resolution_dict[dataset_resolution_size_dict[value["keyName"]]['value']]['value'])][int(value['parameterID'])])
                # print("sass")
                # 楼上的变量的key的含义：参考楼下的print
                print(current_dict[key]["keyName"], current_dict[key]["value"])
                print("--------resoluiton--------")
                print()
                # # 146
                # print(value['parameterID'])
                # # 0,5
                # print(dataset_resolution_dict[dataset_resolution_size_dict[value["keyName"]]['value']]['value'])
                # # 258
                # print(dataset_resolution_dict[dataset_resolution_size_dict[value["keyName"]]['value']]['parameterID'])
                # #print(resolution_values_dict[])

            elif value["keyName"] in dataset_resolution_intrinsic_dict.keys() and value['paramType'] != "Dataset resolution intrinsic":
                # image intrinsic (fx fy cx cy)
                # current_dict[key]["value"] = str(float(float(current_dict[key]["value"]) * float(dataset_resolution_dict[dataset_resolution_intrinsic_dict[value["keyName"]]['value']]['value'])))
                print("--------resoluiton--------")
                print(current_dict[key]["keyName"], current_dict[key]["value"])  
                current_dict[key]["value"] = str(resolution_values_dict[int(dataset_resolution_dict[dataset_resolution_intrinsic_dict[value["keyName"]]['value']]['parameterID'])][float(dataset_resolution_dict[dataset_resolution_intrinsic_dict[value["keyName"]]['value']]['value'])][int(value['parameterID'])])
                
                print(current_dict[key]["keyName"], current_dict[key]["value"])  
                print("--------resoluiton--------")
                print()


            if value["keyName"] in dataset_frequency_remap_dict.keys() and value['paramType'] != "Dataset frequency remap":
                # image height or width
                ## current_dict[key]["value"] = str(int(int(current_dict[key]["value"]) * float(dataset_resolution_dict[dataset_resolution_size_dict[value["keyName"]]['value']]['value'])))
                print("--------frequency--------")
                print(current_dict[key]["keyName"], current_dict[key]["value"])
                current_dict[key]["value"] = str(resolution_values_dict[int(dataset_frequency_dict[dataset_frequency_remap_dict[value["keyName"]]['value']]['parameterID'])][float(dataset_frequency_dict[dataset_frequency_remap_dict[value["keyName"]]['value']]['value'])][int(value['parameterID'])])
                # print("sass")
                # 楼上的变量的key的含义：参考楼下的print
                print(current_dict[key]["keyName"], current_dict[key]["value"])
                print("--------frequency--------")
                print()
                # # 146
                # print(value['parameterID'])
                # # 0,5
                # print(dataset_resolution_dict[dataset_resolution_size_dict[value["keyName"]]['value']]['value'])
                # # 258
                # print(dataset_resolution_dict[dataset_resolution_size_dict[value["keyName"]]['value']]['parameterID'])
                # #print(resolution_values_dict[])



        #print("---------")      
        MappingTaskConfig_Name = data[str(len(data)-2)]['MappingTaskConfig_Name']
        MappingTaskConfig_Description = data[str(len(data)-2)]['MappingTaskConfig_Description']
        Algorithm_Id = data[str(len(data)-1)]['Algorithm_Id']
        Dataset_Id = data[str(len(data)-1)]['Dataset_Id']
        temp_1 = {}
        temp_1.update({'MappingTaskConfig_Name': MappingTaskConfig_Name})
        temp_1.update({'MappingTaskConfig_Description': MappingTaskConfig_Description})
        current_dict.update({str(len(current_dict)): temp_1})
        temp_2 = {}
        temp_2.update({'Algorithm_Id': Algorithm_Id})
        temp_2.update({'Dataset_Id': Dataset_Id})        
        current_dict.update({str(len(current_dict)): temp_2})

        # need to check if need to change the image size and intrinsic (by dataset-resolution-size and dataset-resolution-intrinsic)
        # if current_dict[]


        data_dict.update({str(now_data_dict_number): current_dict})
        return ;

    # 在遍历每一个参数的时候，目前看起来和resolution的全局参数没有关系

    current_paramter = {}
    current_paramter.update({'parameterID': data[str(now_number)]['parameterID']})
    current_paramter.update({'paramType': data[str(now_number)]['paramType']})
    current_paramter.update({'keyName': data[str(now_number)]['keyName']})
    current_paramter.update({'valueType': data[str(now_number)]['valueType']})
    current_paramter.update({'value': data[str(now_number)]['value']})
    current_paramter.update({'className': data[str(now_number)]['className']})
    current_value = current_paramter['value']

    if "|" not in current_value :
        # to next value
        temp_dict.update({str(now_number): current_paramter})
        dfs_generate_each_config_dict(data_dict, data, now_number + 1, parameter_number, temp_dict, resolution_values_dict, frequency_same_list_list)
        del temp_dict[str(now_number)]
    else :
        current_value_list = current_value.split('|')
        current_value_number = len(current_value_list)
        for i in range(current_value_number):
            current_paramter["value"] = current_value_list[i]
            temp_dict.update({str(now_number): current_paramter})
            dfs_generate_each_config_dict(data_dict, data, now_number + 1, parameter_number, temp_dict, resolution_values_dict, frequency_same_list_list)
            del temp_dict[str(now_number)]


def generate_each_config_dict(data, data_dict):


    # print(data)
    MappingTaskConfig_Name = data[str(len(data)-2)]['MappingTaskConfig_Name']
    MappingTaskConfig_Description = data[str(len(data)-2)]['MappingTaskConfig_Description']
    MappingTaskConfig_Resolution = data[str(len(data)-2)]['MappingTaskConfig_Resolution']
    MappingTaskConfig_Frequency = data[str(len(data)-2)]['MappingTaskConfig_Frequency']
    Algorithm_Id = data[str(len(data)-1)]['Algorithm_Id']
    Dataset_Id = data[str(len(data)-1)]['Dataset_Id']
    algo = Algorithm.query.get(Algorithm_Id)
    dataset = Dataset.query.get(Dataset_Id)
    config_dict = {}
    config_dict.update({algo.name: str(algo.imageTag)})
    config_dict.update({"slam-hive-dataset": str(dataset.name)})

    resolution_values_dict = yaml.safe_load(MappingTaskConfig_Resolution)
    # print(type(resolution_values_dict["258"]))

    # 得到frequency的信息
    frequency_same_list_list = []
    if MappingTaskConfig_Frequency != "":
        for fre in MappingTaskConfig_Frequency.split("\n"):
            frequency_same_list_list.append([])
            for id in fre.split(","):
                frequency_same_list_list[len(frequency_same_list_list) - 1].append(id)


    parameter_number = len(data) - 2
    temp_dict = {}
    # dfs中，替换掉计算resolution的过程，在dict查找对应的值
    dfs_generate_each_config_dict(data_dict, data, 0, parameter_number, temp_dict, resolution_values_dict, frequency_same_list_list)

# abort
def generate_config_dict_combination(id):
    config = MappingTaskConfig.query.get(id)
    config_dict = {}
    config_dict.update({config.algorithm.name:str(config.algorithm.imageTag)})
    config_dict.update({"slam-hive-dataset":str(config.dataset.name)})
    dataset_params_dict = {}

    algo_params_dict = {} ####这个需要修改；value存储的是一个list

    dataset_remap_dict = {}
    algo_remap_dict = {}
    for paramValue in config.paramValues:
        if(paramValue.algoParam.paramType == "Dataset"):
            value_list = str(paramValue.value).split('\n')
            for value in value_list:
                key_value = value.split(':')
                dataset_params_dict.update({key_value[0]:key_value[1].strip(" ")})

        elif(paramValue.algoParam.paramType == "Algorithm"): ###################################
            value_list = str(paramValue.value).split('\n')
            for value in value_list: 
                key_value = value.split(':') 
                in_values = key_value[1].strip(" ")
                # 将values变成list，按照“,”分割
                in_values_list = in_values.split(',')
                algo_params_dict.update({key_value[0]:in_values_list})

        elif(paramValue.algoParam.paramType == "Dataset remap"):
            value_list = str(paramValue.value).split('\n')
            for value in value_list:
                key_value = value.split(':')
                dataset_remap_dict.update({key_value[0]:key_value[1].strip(" ")})
        elif(paramValue.algoParam.paramType == "Algorithm remap"):
            value_list = str(paramValue.value).split('\n')
            for value in value_list:
                key_value = value.split(':')
                algo_remap_dict.update({key_value[0]:key_value[1].strip(" ")})
        elif(paramValue.algoParam.paramType == "Dataset matrix"):
            key_value = str(paramValue.value).split(':')
            dataset_params_dict.update({key_value[0]:key_value[1].strip(" ")})
        config_dict.update({'algorithm-parameters': algo_params_dict})
        config_dict.update({'dataset-parameters': dataset_params_dict})
        config_dict.update({'algorithm-remap': algo_remap_dict})
        config_dict.update({'dataset-remap': dataset_remap_dict})
    return config_dict


def getHardwareInfo():
    return 1


        


    
    

