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

import yaml, os, re
from slamhive.models import MappingTaskConfig, AlgoParameter


def save_dict_to_yaml(config_dict, save_path):
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
            else:
                f.write(key + ": " + value + "\n")


def generate_config_dict(id):
    config = MappingTaskConfig.query.get(id)
    config_dict = {}
    config_dict.update({config.algorithm.name:str(config.algorithm.imageTag)})
    config_dict.update({"slam-hive-dataset":str(config.dataset.name)})
    dataset_params_dict = {}
    algo_params_dict = {}
    dataset_remap_dict = {}
    algo_remap_dict = {}
    for paramValue in config.paramValues:
        if(paramValue.algoParam.paramType == "Dataset"):
            value_list = str(paramValue.value).split('\n')
            for value in value_list:
                key_value = value.split(':')
                dataset_params_dict.update({key_value[0]:key_value[1].strip(" ")})
        elif(paramValue.algoParam.paramType == "Algorithm"):
            value_list = str(paramValue.value).split('\n')
            for value in value_list:
                key_value = value.split(':')
                algo_params_dict.update({key_value[0]:key_value[1].strip(" ")})
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


        


    
    

