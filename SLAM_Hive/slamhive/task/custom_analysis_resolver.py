import docker, time, os, yaml, requests, json, datetime, csv, math
import numpy as np
import matplotlib.pyplot as plt
from dateutil import parser
from slamhive import app
from slamhive.task.utils import *
from pathlib import Path

from slamhive.task import evo

from slamhive.models import CombMappingTaskConfig, MappingTaskConfig, Algorithm, Dataset

from concurrent.futures import ThreadPoolExecutor

#用来多线程评测同一个combination task中的不同sub task
executor = ThreadPoolExecutor(10)

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

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

#用来多线程评测同一个combination task中的不同sub task
executor = ThreadPoolExecutor(10)



def check_resolver(data, configs, comb_configs):
    # print(type(data))
    # if "group_name" in data:
    #     print("ddddddddddddddddddddddddd")
    # return 
    print("in check resolver")
    print(comb_configs)
    try:
        group_name = data['group_name']
        if group_name is None:
            return False, "group name is null!"
        group_discription = data['group_description']
        if group_discription is None:
            return False, "group description is null!"
        

        # 所以可以先求config？
        # 分别筛选出3个方式选中的id
        config_all_list = []

        config_all_list_list = []
        config_all_list_1 = []
        config_all_list_2 = []
        config_all_list_3 = []
        # 换成一个二维listTODO

        # 1 直接是config的id
        configuration_ids = data['configuration_choose']['configuration_id']
        if configuration_ids is not None or len(set(configuration_ids)) == 0:
            config_all_list_1 = (list(set(configuration_ids))) # 筛选出重复的id
        else :
            # config_all_list_1.append(set([]))
            pass
            
        
        # 2 根据comb config的id来添加（即批量的方式）
        comb_configuration_ids = data['configuration_choose']['comb_configuration_id']
        print(type(comb_configuration_ids))
        print(len(comb_configuration_ids))
        
        if comb_configuration_ids is None or len(set(comb_configuration_ids)) == 0:
            # config_all_list_2.append(set([]))
            pass
        
        
        else :
            
            all_ids = []

            for comb_configuration_id in comb_configuration_ids:
                # 根据id找到对应的comb config
                this_comb_config = ""
                for comb_config in comb_configs:
                    if comb_configuration_id == comb_config.id:
                        this_comb_config = comb_config
                        break
                print("sdfs",this_comb_config)
                if this_comb_config != "":
                    for config in this_comb_config.mappingTaskConf:
                        all_ids.append(config.id)

            #         
            config_all_list_2 = (list(set(all_ids)))


                # 将这个comb中的config id都加入all_id



        sql_data = data['configuration_choose']['limitation_rules']

        
        

        algo_flag = False
        algo_list = sql_data['algorithm_id']
        if algo_list != None:
            if "All" in algo_list:
                algo_flag = True
        else:
            algo_list = []
        
        dataset_flag = False
        dataset_list = sql_data['dataset_id']
        if dataset_list != None:
            if "All" in dataset_list:
                dataset_flag = True
        else:
            dataset_list = []
        
        # raw_parameters = sql_data['parameters_value']

        #     param_flag = True
        
        # parameters_list = raw_parameters.split("\n")
        parameters_list = sql_data['parameters_value']
        param_flag = False
        if len(parameters_list) == 0 :
            param_flag = True

        # min max nolimitation
        

        
        suit_configs = []

        configs = MappingTaskConfig.query.order_by(MappingTaskConfig.id.desc()).all()
        for i in range(len(configs)):
            # algorithm
            if algo_flag == False:
                if configs[i].algorithm.id not in algo_list:
                    continue
            if dataset_flag == False:
                if configs[i].dataset.id not in dataset_list:
                    continue
            if param_flag == False:
                if not evo.check_parameters_sql(parameters_list, configs[i]):
                    continue
            if not evo.check_results_sql(sql_data['evaluation_value'], configs[i]):
                continue
            # suit_configs.append(configs[i])
            suit_configs.append(configs[i].id)
        # print(suit_configs)
        config_all_list_3 = suit_configs

        print("aaaaaaaaa")
        print(config_all_list_1)
        print(config_all_list_2)
        print(config_all_list_3)
        # return 
        config_all_list_list.append(config_all_list_1)
        config_all_list_list.append(config_all_list_2)
        config_all_list_list.append(config_all_list_3)
        


                ####
        # 根据交并补集得到id list
        # TODO
        # 3
        # 通过规则进行筛选
        # 先不做了 后面脑子清醒的时候在写
        # TODO
        # 规则制定：三种规则，并集 交集 补集
        # 1 2 3
        # () - ()
        # 规则：两个括号，分别填写交集或者并集（使用U和I）
        # 例子

        first_list_set = set()
        second_list_set = set()

        combination_rule = data['configuration_choose']['combination_rule']
        print(combination_rule)
        #() - ()
        # 首先判断字符串是否合规
        first_one_list = combination_rule['first_one']
        for f in first_one_list:
            if f not in [0,1,2]:
                return False, "configuration choose error, the number should be in [0,1,2]!"
        # 还要根据数量判断
        first_rule_list = combination_rule['first_rule']
        for f in first_rule_list:
            if f not in ["U", "I"]:
                return False, "configuration choose error, the sign should be in [U, I]!"
        # 根据元素的个数解析
        if len(first_one_list) == 0:
            pass
        elif len(first_one_list) == 1:
            # 不需要管符号了
            # 直接赋值
            first_list_set = set(config_all_list_list[first_one_list[0]])
        if len(first_one_list) >= 2:
            first_list_0_set = set(config_all_list_list[first_one_list[0]])
            first_list_1_set = set(config_all_list_list[first_one_list[1]])
            if first_rule_list[0] == "U":
                first_list_set = set(list(first_list_0_set | first_list_1_set))
            else:
                first_list_set = set(list(first_list_0_set & first_list_1_set))
        if len(first_one_list) == 3:
            first_list_2_set = set(config_all_list_list[first_one_list[2]])
            if first_rule_list[1] == "U":
                first_list_set = set(list(first_list_set | first_list_2_set))
            else:
                first_list_set = set(list(first_list_set & first_list_2_set))

        second_one_list = combination_rule['second_one']
        for f in second_one_list:
            if f not in [0,1,2]:
                return False, "configuration choose error, the number should be in [0,1,2]!"
        # 还要根据数量判断
        second_rule_list = combination_rule['second_rule']
        for f in second_rule_list:
            if f not in ["U", "I"]:
                return False, "configuration choose error, the sign should be in [U, I]!"
        # 根据元素的个数解析
        if len(second_one_list) == 0:
            pass
        elif len(second_one_list) == 1:
            # 不需要管符号了
            # 直接赋值
            second_list_set = set(config_all_list_list[second_one_list[0]])
        if len(second_one_list) >= 2:
            second_list_0_set = set(config_all_list_list[second_one_list[0]])
            second_list_1_set = set(config_all_list_list[second_one_list[1]])
            if second_rule_list[0] == "U":
                second_list_set = set(list(second_list_0_set | second_list_1_set))
            else:
                second_list_set = set(list(second_list_0_set & second_list_1_set))
        if len(second_one_list) == 3:
            second_list_2_set = set(config_all_list_list[second_one_list[2]])
            if second_rule_list[1] == "U":
                second_list_set = set(list(second_list_set | second_list_2_set))
            else:
                second_list_set = set(list(second_list_set & second_list_2_set))
        
        #得到了前后两个集合 差集
        final_config_id_list = list(first_list_set  - second_list_set)
        # print("config list")
        # print(first_list_set)
        # print(second_list_set)
        # print(final_config_id_list)

#### 根据长度再筛选一次
#######################################################3
#######################################################
#######################################################

        filter_traj_config_id_list = []

        # 首先判断是否有相应的key'
        unsuccess_number = 0
        print("origin config number: ",len(final_config_id_list))
        new_final_config_id_list = []
        if "trajectory_length_lower_bound" not in data['configuration_choose']:
            # 认为没有限制
            pass
        else:
            trajectory_length_lower_bound = data['configuration_choose']['trajectory_length_lower_bound']
            for id in final_config_id_list:
                config = MappingTaskConfig.query.get(id)
                current_traj_len = config.mappingTasks[0].traj_length
                if current_traj_len > float(trajectory_length_lower_bound):
                    # 符合条件
                    new_final_config_id_list.append(id)
                else:
                    filter_traj_config_id_list.append(id)
                if config.mappingTasks[0].trajectory_state == "Unsuccess":
                    unsuccess_number += 1
            final_config_id_list = new_final_config_id_list
        
####


        if len(final_config_id_list) == 0: # 规则筛选出的config的数量为0，无法评估
            return False, "the config number is zero now!"

        print("new config number: ",len(final_config_id_list))
        print("unsuccess number: ",unsuccess_number)
        # origin config number:  1500
        # new config number:  818
        # unsuccess number:  429
        # 记得还要筛选掉ate or rpe太大的（设置一个上限）
        ## 这个在search中体现
        ## ate的上限多试试几组 e找一个比较好看的

        # +上ate max后，然后修改extend的范围，就可以画一张图了；没问题就可以逐个完善了；做完之后就可以做其他的了

        # return 

        suit_configs_list = []
        for config in configs:
            if config.id in final_config_id_list:
                suit_configs_list.append(config)
        
        # 后面的所有结果应该都存储在这个list里了
        # suit_configs_list是config的列表
        # final_config_id_list是config id的列表
        
    
        # 得到的结果存储在下面这个列表里面0

        # check evaluation form

        algorithm_dataset_type = data['evaluation_form']['algorithm_dataset_type']
        if algorithm_dataset_type is None:
            return False, "Please input algorithm_dataset_type!"
        algorithm_dataset_type = int(algorithm_dataset_type)
        if algorithm_dataset_type < 0 or algorithm_dataset_type >= 4 :
            return False, "Please input right type!"
        evaluation_type = []
        # evaluation_type.append([1, 2, 4, 6, 8, 3]) #下面那几行代码感觉有点问题，我先改改
        # # type_1.append([1, 2, 4, 6, 8])
        # # type_2.append([9])
        # # type_3.append([3, 7])
        # evaluation_type.append([1, 2, 4, 6, 8, 3])
        # evaluation_type.append([9])
        # evaluation_type.append([3, 7])

        # 8 专门针对于Fake的，所以config中只能有1个config

        # 9 Extend_ATE 专门针对于6 7的 不需要一个额外的功能（但是写成一个一个单独的函数）

        # 增量两参数
    # 6_scatter_diagram:
    # choose: 1
    # x-axis: general+image_frequency
    # y-axis: ate_mean
    # extend_choose: 1
    # extend_threshold: [0.75, 0.5, 0.25]
    # extend_multiple: [1, 2, 5, 10]




    # 一个很好的例子
    # （）就是那个大表格上的左下角哪个：其实已经g了 只跑了最后一段
    # 明天：把代码写完，用那个大例子，跑一个结果出来


        # 包括的参数：
        ## 是否使用
        ## 有两种情况：1 (1)   0.75  (2.5)   0.5   (5)   0.25  (10)  实际应该不用这么大（看情况）  0 [] 直接输入两个数组
        # 将这个作为参数输入进来（哪个区间内，对数据进行多少的缩放）
        ## 分成若干个段：
        # 然后，轨迹失败的，直接归为最后一类

        evaluation_type.append([1, 2, 4, 6, 7, 3, 8]) #下面那几行代码感觉有点问题，我先改改
        # type_1.append([1, 2, 4, 6, 8])
        # type_2.append([9])
        # type_3.append([3, 7])
        evaluation_type.append([1, 2, 4, 6, 7, 3]) # 不同的算法在同一个数据集上
        evaluation_type.append([6, 7]) # 这个应该是同一个算法在不同的数据集上
        evaluation_type.append([3,6, 7])


        # 有了评估类型后，可以判断得到的一组config是否满足条件
        # 可以有一个parameter的字典，用来存储所有的parameter以及他们的数量
        #   用来判断是否所有的config都有同一个参数（问题：可能有名字一样，但是含义不同的parameter（暂时不考虑 TODO））

        # 先用 configs 创建一个字典
        all_configs_dict = {}
        for config in configs:
            all_configs_dict.update({config.id: config})

        # 判断是否所有的config都已经有了task以及evo结果

        # 如果存在traj unsuccess的情况，放行，但是将失败的单独存起来


        ## 保证configs中的config都可以进行后续的评估
        # 判断是否有config没有完全w做完
        traj_unsuccess_configs_id_list = []

        for config_id in final_config_id_list:
            current_config = all_configs_dict[config_id]

            if len(current_config.mappingTasks) == 0:
                return False, "configuration " + str(current_config.id) + " haven't created mapping task!"
            else:
                if current_config.mappingTasks[0].trajectory_state == "Unsuccess":
                    traj_unsuccess_configs_id_list.append(str(config_id))
                    continue

                if current_config.mappingTasks[0].evaluation is None:
                    return False, "configuration " + str(current_config.id) + "'s task haven't created evaluation!"
        
        # if len(traj_unsuccess_configs_id_list) == len(final_config_id_list):
        #     return False ## 轨迹全都失败了，也没有比较的必要了？有吗

        # 判断是否符合 algo+dataset的条件
        algorithm_id = all_configs_dict[final_config_id_list[0]].algorithm.id
        dataset_id = all_configs_dict[final_config_id_list[0]].dataset.id
        for config_id in final_config_id_list:
            if algorithm_dataset_type in [0,2]: # same algo
                if algorithm_id != all_configs_dict[config_id].algorithm.id:
                    # 所筛选出的config不满足same algorithm and same dataset
                    return False, "Your provided configurations can't satisfy the algorithm_dataset type!"
            if algorithm_dataset_type in [0,1]: # same data
                if dataset_id != all_configs_dict[config_id].dataset.id:
                    return False, "Your provided configurations can't satisfy the algorithm_dataset type!"
        # configs符合了algo和dataset的条件
        # 为了后续判断，还需要parameter的信息
        configs_parameter_dict = {}

        

        for config_id in final_config_id_list:
            config = all_configs_dict[config_id]
            fre_number = 0
            for i in range(len(config.paramValues)):
                
                current_key = config.paramValues[i].name
                current_value = config.paramValues[i].value
                # 如果字典中还没有该parameter 则添加
                # 如果已经有了 则value+1

                if (config.paramValues[i].valueType != "float" and config.paramValues[i].valueType != "int" and config.paramValues[i].valueType != "double"):
                    if config.paramValues[i].algoParam.paramType != "Dataset remap":
                        continue

                if current_key not in configs_parameter_dict.keys():
                # if not configs_parameter_dict.has_key(current_key):
                    configs_parameter_dict.update({current_key: 1})
                else:
                    configs_parameter_dict[current_key] = configs_parameter_dict[current_key] + 1
                
                if current_key == "general+image_frequency":
                    fre_number += 1
            if fre_number != 1:
                print(fre_number, config.id)
        

        print("--- parameter dict ----")
        print(configs_parameter_dict)
                


        accuracy_list = ['ate_rmse', 'ate_mean', 'ate_median', 'ate_std', 'ate_min', 'ate_max', 'ate_sse', 'rpe_rmse', 'rpe_mean', 'rpe_median', 'rpe_std', 'rpe_min', 'rpe_max', 'rpe_sse']

        usage_list = ['cpu_mean', 'cpu_max', 'ram_max']

        ana_content = ""

        TRAJ_MAX_NUMBER = 100
        analysis_1 = int(data['evaluation_form']['1_trajectory_comparison']['choose'])
        if analysis_1 != 0 and analysis_1 != 1:
            return False, "Wrong 1_trajectory_comparison choose!"
        if analysis_1 == 1:
            # 判断选择是否合法
            if 1 not in evaluation_type[algorithm_dataset_type]:
                return False, "You can't choose 1_trajectory_comparison"
            # 数量限制
            if len(final_config_id_list) > TRAJ_MAX_NUMBER:
                return False, "Too many trajectories!"
            # 根据之前的判断，一定存在task和evo结果
        ana_content += "1:"+str(analysis_1) + "\n"
        print(111)

        analysis_2 = int(data['evaluation_form']['2_accuracy_metrics_comparison']['choose'])
        if analysis_2 != 0 and analysis_2 != 1:
            return False, "Wrong 2_accuracy_metrics_comparison choose!"
        if analysis_2 == 1:
            # 判断选择是否合法
            if 2 not in evaluation_type[algorithm_dataset_type]:
                return False, "You can't choose 2_accuracy_metrics_comparison"
            # 数量限制
            if len(final_config_id_list) > TRAJ_MAX_NUMBER:
                return False, "Too many trajectories!"
        ana_content += "2:"+str(analysis_2) + "\n"
        print(222)

        analysis_3 = int(data['evaluation_form']['3_accuracy_metrics_comparison']['choose'])
        if analysis_3 != 0 and analysis_3 != 1:
            return False, "Wrong 3_accuracy_metrics_comparison choose!"
        if analysis_3 == 1:
            # 判断选择是否合法
            if 3 not in evaluation_type[algorithm_dataset_type]:
                return False, "You can't choose 3_accuracy_metrics_comparison"         
            analysis_3_calculate_method = int(data['evaluation_form']['3_accuracy_metrics_comparison']['calculate_method'])
            if analysis_3_calculate_method != 0 and analysis_3_calculate_method != 1: 
                return False, "Wrong 3_accuracy_metrics_comparison calculation method!"
            analysis_3_metric = (data['evaluation_form']['3_accuracy_metrics_comparison']['metric'])
            print("dddd", analysis_3_metric)
            if analysis_3_metric not in accuracy_list and analysis_3_metric not in usage_list:
                return False, "Please input correct metric!"
            # TODO 这里应该还有一个判断algorithm和dataset list是否合法的逻辑
            
            # 这里应该还是要选择到的吧
            ## final_parameter_array, algorithm_id_list, dataset_id_list = pre_handle_accuracy_metrics_comparison(data, configs)
            final_parameter_array, algorithm_id_list, dataset_id_list, config_array_3 = pre_handle_accuracy_metrics_comparison(data, suit_configs_list, traj_unsuccess_configs_id_list)
            if final_parameter_array == False:
                return False, "Can't generate 3_accuracy_metrics_comparison!"
            print("parameter: ---------------")
            print(final_parameter_array)
            # return 
        
        ana_content += "3:"+str(analysis_3) + "\n"
        print(333)        
        
        analysis_4 = int(data['evaluation_form']['4_usage_metrics_comparison']['choose'])
        if analysis_4 != 0 and analysis_4 != 1:
            return False, "Wrong 4_usage_metrics_comparison choose!"
        if analysis_4 == 1:
            # 判断选择是否合法
            if 4 not in evaluation_type[algorithm_dataset_type]:
                return False  , "You can't choose 4_usage_metrics_comparison!"
        ana_content += "4:"+str(analysis_4) + "\n"
        print(444)


        # add的新功能：可以添加属性

        # 如果是算法的属性的话，该如何判断

        ## 设定规则：
        ## 统计所有的config中都有的 or 只要有了就要
        ## 还是前者吧 简单一点
        ## 如果选择了没有的参数，就直接返回报错

        # configs_parameter_dict # name: number
        # for i in range()
        # 有了这个参数
        configs_parameter_dict_copy = configs_parameter_dict
        configs_parameter_dict = {}
        for d in configs_parameter_dict_copy.items():
            if d[1] == len(final_config_id_list):
                configs_parameter_dict.update({d[0]: d[1]})

        print("--- parameter dict ----")
        print(configs_parameter_dict)
        
        

        # analysis_5 = int(data['evaluation_form']['5_scatter_diagram']['choose'])
        # if analysis_5 != 0 and analysis_5 != 1:
        #     return False
        # if analysis_5 == 1:
        #     # 判断选择是否合法
        #     print("in 5 check")
        #     if 5 not in evaluation_type[algorithm_dataset_type]:
        #         return False     
        # # 需要思考一下：如果坐标轴不是metric 而是 parameter的话，要如何判断（判断应该要提到后面config的时候判断）
        
        #     analysis_5_x = data['evaluation_form']['5_scatter_diagram']['x-axis']
        #     analysis_5_x_type = 0 # x和y的type不能一样
        #     if analysis_5_x not in accuracy_list and  analysis_5_x not in usage_list:
        #         # 暂时认为该参数为parameter 到后面的时候需要重新判断
        #         analysis_5_x_type = 2
        #         # 判断是否在字典中
        #         if analysis_5_x not in configs_parameter_dict.keys():
        #             return False
        #         # 并且需要所有的configs都有这个pamrater
        #         if configs_parameter_dict[analysis_5_x] != len(final_config_id_list):
        #             return False
        #     if analysis_5_x in accuracy_list:
        #         analysis_5_x_type = 0
        #     if analysis_5_x in usage_list:
        #         analysis_5_x_type = 1
            
        #     analysis_5_y = data['evaluation_form']['5_scatter_diagram']['y-axis']
        #     analysis_5_y_type = 0 # x和y的type不能一样
        #     if analysis_5_y not in accuracy_list and  analysis_5_y not in usage_list:
        #         # 暂时认为该参数为parameter 到后面的时候需要重新判断
        #         analysis_5_y_type = 2
        #         # 判断是否在字典中
        #         if analysis_5_y not in configs_parameter_dict.keys():
        #             return False
        #         # 并且需要所有的configs都有这个pamrater(根据数量判断)
        #         if configs_parameter_dict[analysis_5_y] != len(final_config_id_list):
        #             return False
        #     if analysis_5_y in accuracy_list:
        #         analysis_5_y_type = 0
        #     if analysis_5_y in usage_list:
        #         analysis_5_y_type = 1
        #     if analysis_5_y_type == analysis_5_x_type and analysis_5_y_type != 2 and  analysis_5_x_type != 2 :
        #         return False

        #     # 判断参数
        #     #  现在不需要这个了；因为简化了条件：必须只能选择每个config都有的parameter
        #     # if not pre_handle_scatter(data, final_config_id_list, 5, analysis_5_x_type, analysis_5_y_type):
        #     #     return False
        # ana_content += "5:"+str(analysis_5) + "\n"
        # print(555)


### 本来：只能同一个数据集的可以b对比
### 现在：多个数据集也可以

        analysis_6 = int(data['evaluation_form']['6_scatter_diagram']['choose'])
        if analysis_6 != 0 and analysis_6 != 1:
            return False, "Wrong 6_scatter_diagram choose!"
        if analysis_6 == 1:
            # 判断选择是否合法
            if 6 not in evaluation_type[algorithm_dataset_type]:
                return False, "You can't choose 6_scatter_diagram"  
        # 需要思考一下：如果坐标轴不是metric 而是 parameter的话，要如何判断（判断应该要提到后面config的时候判断）

            analysis_6_x = data['evaluation_form']['6_scatter_diagram']['x-axis']
            analysis_6_x_type = 0 # x和y的type不能一样
            if analysis_6_x not in accuracy_list and  analysis_6_x not in usage_list:
                # 暂时认为该参数为parameter 到后面的时候需要重新判断
                analysis_6_x_type = 2
                # 判断是否在字典中
                if analysis_6_x not in configs_parameter_dict.keys():
                    return False, "error x axis!"
                # 并且需要所有的configs都有这个pamrater
                if configs_parameter_dict[analysis_6_x] != len(final_config_id_list):
                    return False, "error x axis!"
            if analysis_6_x in accuracy_list:
                analysis_6_x_type = 0
            if analysis_6_x in usage_list:
                analysis_6_x_type = 1
            analysis_6_y = data['evaluation_form']['6_scatter_diagram']['y-axis']
            analysis_6_y_type = 0 # x和y的type不能一样
            if analysis_6_y not in accuracy_list and  analysis_6_y not in usage_list:
                # 暂时认为该参数为parameter 到后面的时候需要重新判断
                analysis_6_y_type = 2
                # 判断是否在字典中
                if analysis_6_y not in configs_parameter_dict.keys():
                    return False, "error y axis!"
                # 并且需要所有的configs都有这个pamrater
                if configs_parameter_dict[analysis_6_y] != len(final_config_id_list):
                    return False, "error y axis!"
            if analysis_6_y in accuracy_list:
                analysis_6_y_type = 0
            if analysis_6_y in usage_list:
                analysis_6_y_type = 1
            if analysis_6_y_type == analysis_6_x_type:
                return False, "error x axis and y sxis (shouldn't be same)!"
            ## TODO 是否需要判断paramter是否属于不同的algorithm的具有不同意义的parameter
            # if not pre_handle_scatter(data, final_config_id_list, 6, analysis_6_x_type, analysis_6_y_type):
            #     return False


            # 判断extend
            extend_threshold = []
            extend_multiple = []
            if "extend_choose" in data['evaluation_form']['6_scatter_diagram']:
                extend_choose_6 = data['evaluation_form']['6_scatter_diagram']['extend_choose']
                if extend_choose_6 != 0 and extend_choose_6 != 1:
                    return False, "Wrong 6_scatter_diagram extend choose!"
                if extend_choose_6 == 1:
                    extend_threshold = data['evaluation_form']['6_scatter_diagram']['extend_threshold']
                    extend_multiple = data['evaluation_form']['6_scatter_diagram']['extend_multiple']
            # 这里没咋写false的情况

        ana_content += "6:"+str(analysis_6) + "\n"
        print("666")




        analysis_7 = int(data['evaluation_form']['7_3d_scatter_diagram']['choose'])
        if analysis_7 != 0 and analysis_7 != 1:
            return False, "Wrong 7_3d_scatter_diagram choose!"
        if analysis_7 == 1:
            # 判断选择是否合法
            if 7 not in evaluation_type[algorithm_dataset_type]:
                return False, "You can't choose 7_3d_scatter_diagram"       
        # 需要思考一下：如果坐标轴不是metric 而是 parameter的话，要如何判断（判断应该要提到后面config的时候判断）

            analysis_7_x = data['evaluation_form']['7_3d_scatter_diagram']['x-axis']
            analysis_7_x_type = 0 # x和y的type不能一样
            if analysis_7_x not in accuracy_list and  analysis_7_x not in usage_list:
                # 暂时认为该参数为parameter 到后面的时候需要重新判断
                analysis_7_x_type = 2
                # 判断是否在字典中
                if analysis_7_x not in configs_parameter_dict.keys():
                    return False, "error x axis!"
                # 并且需要所有的configs都有这个pamrater
                if configs_parameter_dict[analysis_7_x] != len(final_config_id_list):
                    return False, "error x axis!"
            if analysis_7_x in accuracy_list:
                analysis_7_x_type = 0
            if analysis_7_x in usage_list:
                analysis_7_x_type = 1
            
            analysis_7_y = data['evaluation_form']['7_3d_scatter_diagram']['y-axis']
            analysis_7_y_type = 0 # x和y的type不能一样
            if analysis_7_y not in accuracy_list and  analysis_7_y not in usage_list:
                # 暂时认为该参数为parameter 到后面的时候需要重新判断
                analysis_7_y_type = 2
                # 判断是否在字典中
                if analysis_7_y not in configs_parameter_dict.keys():
                    return False, "error y axis!"
                # 并且需要所有的configs都有这个pamrater
                if configs_parameter_dict[analysis_7_y] != len(final_config_id_list):
                    return False, "error y axis!"
            if analysis_7_y in accuracy_list:
                analysis_7_y_type = 0
            if analysis_7_y in usage_list:
                analysis_7_y_type = 1

            analysis_7_z = data['evaluation_form']['7_3d_scatter_diagram']['z-axis']
            analysis_7_y_type = 0 # x和y的type不能一样
            if analysis_7_z not in accuracy_list and  analysis_7_z not in usage_list:
                # 暂时认为该参数为parameter 到后面的时候需要重新判断
                analysis_7_z_type = 2
                # 判断是否在字典中
                if analysis_7_z not in configs_parameter_dict.keys():
                    return False, "error z axis!"
                # 并且需要所有的configs都有这个pamrater
                if configs_parameter_dict[analysis_7_z] != len(final_config_id_list):
                    return False, "error z axis!"
            if analysis_7_z in accuracy_list:
                analysis_7_z_type = 0
            if analysis_7_z in usage_list:
                analysis_7_z_type = 1

            
            if analysis_7_x == analysis_7_y or analysis_7_y == analysis_7_z or analysis_7_z == analysis_7_x:
                return False, "error x y z axis (shouldn't be the same type)!"

            # 判断extend
            extend_threshold_7 = []
            extend_multiple_7 = []
            if "extend_choose" in data['evaluation_form']['7_3d_scatter_diagram']:
                extend_choose_7 = data['evaluation_form']['7_3d_scatter_diagram']['extend_choose']
                if extend_choose_7 != 0 and extend_choose_7 != 1:
                    return False, "Wrong 7_3d_scatter_diagram extend choose!"
                if extend_choose_7 == 1:
                    extend_threshold_7 = data['evaluation_form']['7_3d_scatter_diagram']['extend_threshold']
                    extend_multiple_7 = data['evaluation_form']['7_3d_scatter_diagram']['extend_multiple']

            ## TODO 是否需要判断paramter是否属于不同的algorithm的具有不同意义的parameter
            # if not pre_handle_scatter(data, final_config_id_list, 7, analysis_7_x_type, analysis_7_y_type):
            #     return False
        ana_content += "7:"+str(analysis_7) + "\n"
        print("777")

        analysis_8 = int(data['evaluation_form']['8_repeatability_test']['choose'])
        if analysis_8 != 0 and analysis_8 != 1:
            return False, "Wrong 8_repeatability_test choose!"
        if analysis_8 == 1:
            # 判断选择是否合法
            if 8 not in evaluation_type[algorithm_dataset_type]:
                return False, "You can't choose 8_repeatability_test"     
            # 数量限制
            if len(suit_configs_list) != 1:
                return False, "8_repeatability_test: configuration must have at least 2 tasks!"
            # 保证每一个task都有
            for task in suit_configs_list[0].mappingTasks:
                if task.trajectory_state == "Unsuccess":
                    continue
                if task.evaluation == None:
                    return False, "8_repeatability_test: task " + str(task.id) + " haven't create evaluation!"
            analysis_8_metric = (data['evaluation_form']['8_repeatability_test']['metric'])
            print("8d8d8d", analysis_8_metric)
            if analysis_8_metric not in accuracy_list and analysis_8_metric not in usage_list:
                print("FFFF")
                return False, "8_repeatability_test: wrong metric!"

        ana_content += "8:"+str(analysis_8) + "\n"
        print(888)

## 如果后面要用，使用别的a编号
        # analysis_7 = int(data['evaluation_form']['7_comparison_table']['choose'])
        # if analysis_7 != 0 and analysis_7 != 1:
        #     return False
        # if analysis_7 == 1:
        #     # 判断选择是否合法
        #     if 7 not in evaluation_type[algorithm_dataset_type]:
        #         return False  
        #     analysis_7_metrics = (data['evaluation_form']['7_comparison_table']['metrics'])
        #     if analysis_7_metrics is None:
        #         return False
        #     for metric in analysis_7_metrics:
        #         if metric not in accuracy_list and metric not in usage_list:
        #             return False
        #     analysis_7_calculate_method = int(data['evaluation_form']['7_comparison_table']['calculate_method'])
        #     if analysis_7_calculate_method != 0 and analysis_7_calculate_method != 1:
        #         return False
        
####
        # analysis_8 = int(data['evaluation_form']['8_comparison_table']['choose'])
        # if analysis_8 != 0 and analysis_8 != 1:
        #     return False        
        # if analysis_8 == 1:
        #     if 8 not in evaluation_type[algorithm_dataset_type]:
        #         return False
        #     analysis_8_parameter = data['evaluation_form']['8_comparison_table']['parameter']
        #     ## TODO 需要判断是否合法的parameter
        #     if analysis_8_parameter is None:
        #         return False
        #     analysis_8_metrics = data['evaluation_form']['8_comparison_table']['metrics']
        #     for metric in analysis_8_metrics:
        #         if metric not in accuracy_list and metric not in usage_list:
        #             return False


        # analysis_9 = int(data['evaluation_form']['9_comparison_table']['choose'])
        # if analysis_9 != 0 and analysis_9 != 1:
        #     return False        
        # if analysis_9 == 1:
        #     if 9 not in evaluation_type[algorithm_dataset_type]:
        #         return False
        #     analysis_9_parameter = data['evaluation_form']['9_comparison_table']['parameter']
        #     ## TODO 需要判断是否合法的parameter
        #     ## TODO 需要先思考明白（应该可以参考之前怎么搜索parameter的（就是判断这组config里有没有这个参数））
        #     if analysis_9_parameter is None:
        #         return False
        #     analysis_9_metrics = data['evaluation_form']['9_comparison_table']['metrics']
        #     for metric in analysis_9_metrics:
        #         if metric not in accuracy_list and metric not in usage_list:
        #             return False
####        

        # 想明白要return 啥
        # 或者直接接一个实现的函数 TODO
        #   将config存储
        #   根据约束生成内容


        # 1 将文件存储到本地
        # 因为写入数据库，所以考虑另一种方式用来区分（时间戳）
        # 文件夹名称：时间+group_name


        now = datetime.datetime.now()
        timestamp = int(datetime.datetime.timestamp(now) * 1000000)
        print("当前时间戳:", timestamp)

        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))

        folder_name = str(timestamp)
        now_time = str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
        file_name = str(timestamp)+"+"+now_time+"+"+str(group_name)+".yaml"
        folder_path = "/slam_hive_results/custom_analysis_group/" + folder_name
        os.mkdir(folder_path)
        # 将内容写入到一个yaml file中


        data.update({"is_visualized": 0})


        file_path = folder_path + "/" + file_name
        with open(file_path,'w') as f:
            yaml.dump(data=data, stream=f, allow_unicode=True)

        content = ""
        content += "id:"+folder_name+"\n"
        content += "time:"+now_time+"\n"
        content += "name:"+data["group_name"]+"\n"
        content += "config_id:["
        for i in range(len(final_config_id_list)-1):
            content += str(final_config_id_list[i])+","
        content += str(final_config_id_list[len(final_config_id_list)-1]) + "]\n"


        para_list = []
        for d in configs_parameter_dict.items():
            para_list.append(d[0])
        content += "parameters_list:" + str(para_list) + "\n"

        
        content += "unsuccess_traj_config:["
        if len(traj_unsuccess_configs_id_list) == 0:
            content += "]\n"
        else:
            for i in range(len(traj_unsuccess_configs_id_list)-1):
                print(i)
                content += str(traj_unsuccess_configs_id_list[i])+","
            content += str(traj_unsuccess_configs_id_list[len(traj_unsuccess_configs_id_list)-1]) + "]\n"

        content += "filter_traj_config:[" # 第7行
        if len(filter_traj_config_id_list) == 0:
            content += "]\n"
        else:
            for i in range(len(filter_traj_config_id_list)-1):
                print(i)
                content += str(filter_traj_config_id_list[i])+","
            content += str(filter_traj_config_id_list[len(filter_traj_config_id_list)-1]) + "]\n"

        # 将config写入
        with open(folder_path + "/info.txt", "w") as f:
            f.write(content)
        # 2 开始逐个生成内容（或者将内容拷贝；或者打个链接文件标记）

        with open(folder_path + "/analysis_index.txt", "w") as f:
            f.write(ana_content)
        

        

        # 应该不会产生错误了



        ## 就是这里之后，如果选中的config中的eval有问题怎么办；好像在之前j就已经给pass掉了

#在这里加入一个多线程

# 只有evo的部分会耗时 单独处理
        if analysis_1 == 1 or analysis_2 == 1:
            os.mkdir(folder_path + "/evo_stuff")
            resultPath = "/SLAM-Hive/slam_hive_results/custom_analysis_group/" + folder_name + "/evo_stuff"
            # submit
            generation_evo_stuff(suit_configs_list, folder_name, file_name, traj_unsuccess_configs_id_list, resultPath)
        if analysis_3 == 1:
            # 之前的y想法有问题：这个评估不需要指定configs，x只需要指定algorithm和dataset即可
            # 直接在这么处理了吧
            print("in 3")
            os.mkdir(folder_path + "/accuracy_metrics_comparison")
            # 这个要试一试，能不能处理unsuccess的n情况
            new_folder_path = folder_path + "/accuracy_metrics_comparison/"
            generation_accuracy_metrics_comparison(data, suit_configs_list, new_folder_path, file_name, final_parameter_array, algorithm_id_list, dataset_id_list, traj_unsuccess_configs_id_list, config_array_3)
        if analysis_4 == 1:       # 可以不用管，反正轨迹失败了也有结果
            # 生成cpu 和 ram usage
            # 参考之前的代码，将多个轨迹画在一张图上
            os.mkdir(folder_path + "/usage_comparison")
            new_folder_path = folder_path + "/usage_comparison/"
            generation_usage_comparison(data, suit_configs_list, new_folder_path, file_name)
        # if analysis_5 == 1:
        #     os.mkdir(folder_path + "/scatter")
        #     generation_scatter(data, suit_configs_list,folder_path, file_name,5, traj_unsuccess_configs_id_list)
        if analysis_6 == 1:
            os.mkdir(folder_path + "/scatter")
            new_folder_path = folder_path + "/scatter/"
            generation_scatter(data, suit_configs_list,new_folder_path, file_name,6, traj_unsuccess_configs_id_list,   extend_threshold,extend_multiple, filter_traj_config_id_list)

        if analysis_7 == 1:
            os.mkdir(folder_path + "/3d_scatter")
            new_folder_path = folder_path + "/3d_scatter/"
            generation_3d_scatter(data, suit_configs_list,new_folder_path, file_name,7, traj_unsuccess_configs_id_list  , extend_threshold_7,extend_multiple_7, filter_traj_config_id_list)       

        if analysis_8 == 1:
            os.mkdir(folder_path + "/repeatability_test")
            generatiion_repeatability_test(data, suit_configs_list, folder_path, file_name, traj_unsuccess_configs_id_list, folder_name, analysis_8_metric)
    
        file_temp = open(folder_path+"/finished", "w")
        file_temp.close()
    except Exception as e:
        print("error: ", e)
        return False, "Unknown error, please check the yaml file!"



    return True, folder_name #"create success!"


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


def generation_evo_stuff(suit_configs_list, folder_name, file_name, traj_unsuccess_configs_id_list, resultPath): # folder_namen实际上是一个i时间戳
    # 生成这些轨迹的对比
    # 应该可以直接调用接口

    evo_number = len(suit_configs_list) - len(traj_unsuccess_configs_id_list)
    datasetName = suit_configs_list[0].dataset.name
    groundtruth = '/SLAM-Hive/slam_hive_datasets/' + datasetName + "/groundtruth.txt"

    # resultPath = "/SLAM-Hive/slam_hive_results/custom_analysis_group/" + folder_name + "/evo_stuff"

    mappingtaskIdList = []
    evaluationIdList = []
    for config in suit_configs_list:
        if str(config.id) in traj_unsuccess_configs_id_list:
            continue
        mappingtaskIdList.append(str(config.mappingTasks[0].id))
        evaluationIdList.append(str(config.mappingTasks[0].evaluation.id))
    
    successful_number = 0
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
            
    print(resultPath)

    # executor.submit(evo.evo_compare_task_multi, resultPath, evo_number, mappingtaskIdList, evaluationIdList, sub_evo_flags, groundtruth)
    evo_compare_task_multi(resultPath, evo_number, mappingtaskIdList, evaluationIdList, sub_evo_flags, groundtruth)

def pre_handle_accuracy_metrics_comparison(data, configs, traj_unsuccess_configs_id_list):

    # 注意 这里的config中可能会存在没有trajectory的情况

    algorithm_id_list = data['evaluation_form']['3_accuracy_metrics_comparison']['algorithm_id']
    dataset_id_list = data['evaluation_form']['3_accuracy_metrics_comparison']['dataset_id']

    # 找到给定configs中 满足这些algo和dataset的
    suit_configs = []
    for config in configs:
        if config.algorithm.id in algorithm_id_list and config.dataset.id in dataset_id_list:
            suit_configs.append(config)
    
    # [[[[], []], []], []]: 最外层 algo id；内层 dataset id；元素 config的list; 加一层：config的不同task
    # 顺序按照两个list的顺序
    config_array = []
    parameter_array = []
    final_parameter_array = []
    for i in range(len(algorithm_id_list)):
        config_array.append([])
        parameter_array.append([])
        final_parameter_array.append([])
        for j in range(len(dataset_id_list)):
            config_array[i].append([])
            parameter_array[i].append([])
            final_parameter_array[i].append([])
    # 构建了1个二维数组

    for config in suit_configs:
        algo_num = 0
        data_num = 0
        for i in range(len(algorithm_id_list)):
            if config.algorithm.id == algorithm_id_list[i]:
                algo_num = i
                break
        for i in range(len(dataset_id_list)):
            if config.dataset.id == dataset_id_list[i]:
                data_num = i
                break
        # 并且这个config应该是四肢健全的  应该 传进来的只存在正常 or 没有traj的
        # if len(config.mappingTasks) == 0:
        #     continue
        # if config.mappingTasks[0].trajectory_state == "Unsuccess" or config.mappingTasks[0].evaluation == None:
        #     continue

        config_array[algo_num][data_num].append(config)
        # TODO 评估这个 需要再n创建几个config 运行在不同的算法上
    
    print(config_array)
    for i in range(len(algorithm_id_list)):
        for j in range(len(dataset_id_list)):   
            if len(config_array[i][j]) == 0:
                print(algorithm_id_list[i], dataset_id_list[j])

    # 然后再遍历一次，看是否二维数组的每一个位置都有至少一个config
    for i in range(len(algorithm_id_list)):
        for j in range(len(dataset_id_list)):
            if len(config_array[i][j]) == 0:
                # 存在空缺情况 某个算法没有在某个数据集上运行过

                # 这里假定了config一定运行过

                # 但是存在 运行了 但是unsuccess的n情况，这种情况特殊判断
                return False, False, False, False
    # 都有了
    for i in range(len(algorithm_id_list)):
        for j in range(len(dataset_id_list)):
            # ate_mean
            print(i, j)
            metric = data['evaluation_form']['3_accuracy_metrics_comparison']['metric']
            # 可能会
            
            for k in range(len(config_array[i][j])):
                parameter_array[i][j].append([])
                print(config_array[i][j][k].mappingTasks)
                for l in range(len(config_array[i][j][k].mappingTasks)):
                    print("l",l)
                    

                    if config_array[i][j][k].mappingTasks[l].trajectory_state == "Unsuccess":
                        parameter_array[i][j][k].append("Unsuccess")
                        continue
                    # print("-------")
                    # print(config_array[i][j][k].id)

                    if metric == 'ate_rmse':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.ate_rmse)
                    if metric == 'ate_mean':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.ate_mean)
                    if metric == 'ate_median':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.ate_median)
                    if metric == 'ate_std':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.ate_std)
                    if metric == 'ate_min':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.ate_min)
                    if metric == 'ate_max':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.ate_max)
                    if metric == 'ate_sse':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.ate_sse)
                    if metric == 'rpe_rmse':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.rpe_rmse)
                    if metric == 'rpe_mean':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.rpe_mean)
                    if metric == 'rpe_median':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.rpe_median)
                    if metric == 'rpe_std':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.rpe_std)
                    if metric == 'rpe_min':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.rpe_min)
                    if metric == 'rpe_max':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.rpe_max)
                    if metric == 'rpe_sse':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].evaluation.evoResults.rpe_sse)
                    if metric == 'cpu_mean':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].performanceresults.mean_cpu)
                    if metric == 'cpu_max':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].performanceresults.max_cpu)
                    if metric == 'ram_max':
                        parameter_array[i][j][k].append(config_array[i][j][k].mappingTasks[l].performanceresults.max_ram)
    # for i in range(len(algorithm_id_list)):
    #     for j in range(len(dataset_id_list)):
    #         calculate_method = data['evaluation_form']['3_accuracy_metrics_comparison']['calculate_method']
    #         current_result = 0
    #         if calculate_method == 0: # average
    #             current_number = len(parameter_array[i][j])
    #             for parameter in parameter_array[i][j]:
    #                 if current_result != "Unsuccess":
    #                     current_result += parameter
    #                 else:
    #                      current_result += 0
    #             if current_result != 0:
    #                 current_result /= current_number
    #             else:
    #                 current_result = 0
    #                 # TODO 给予假设：不会有一个正常的数据 为 0
    #         else: # min
    #             current_result = 9999999
    #             for parameter in parameter_array[i][j]:
    #                 if parameter != "Unsuccess":
    #                     if parameter < current_result:
    #                         current_result = parameter
    #             if current_result == 9999999:
    #                 current_result = 0
    #         final_parameter_array[i][j] = current_result
    # print("analysis 3 pre handle result")
    # print(final_parameter_array)
    # # 下载这个
    # return final_parameter_array, algorithm_id_list, dataset_id_list
    return parameter_array, algorithm_id_list, dataset_id_list, config_array


#然后再遍历一遍，根据z平均值还是最小值，计算出final的array 然后返回
# 然后有了这个结果，就可以绘制图标了（同时把横纵轴，和每个算法的信息 和均值和std传出去）        

# 4 cpu的绘制参考之前
# 5 直接用
# 6 差不多
# 7 类似3

def generation_accuracy_metrics_comparison(data, suit_configs_list, folder_path, file_name, final_parameter_array, algorithm_id_list, dataset_id_list, config_id, config_array_3):
    # 现在有了一个二维数组，要计算每个algorithm的均值和std
    mean_list = []
    std_list = []
    algorithm_name_list = []
    dataset_name_list = []
    for i in range(len(algorithm_id_list)):
        
        current_values = []
        for j in range(len(dataset_id_list)):
            for k in range(len(final_parameter_array[i][j])):
                
                for l in range(len(final_parameter_array[i][j][k])):
                    # print(len(final_parameter_array[i][j][k]))
                    current_values.append(final_parameter_array[i][j][k][l])
        mean_list.append(np.mean(current_values))
        std_list.append(np.std(current_values))
    
    # print("(((((((((((())))))))))))")
    
    # 绘制箱线图
    # 示例数据
    attributes = []
    for i in range(len(algorithm_id_list)):
        attributes.append(Algorithm.query.get(algorithm_id_list[i]).imageTag)
    y = mean_list
    errors = std_list

    # 绘制误差棒图
    plt.figure(figsize=(7,6))
    plt.errorbar(attributes, y, yerr=errors, fmt='o', color='black', ecolor='red', elinewidth=2, capsize=4)

    # 添加标题和标签
    plt.title('Mean and standard sevisation of ' + data['evaluation_form']['3_accuracy_metrics_comparison']['metric'] + " over " + str(len(dataset_id_list)) + " sequences")
    plt.xlabel('Sensors combination')
    plt.ylabel(data['evaluation_form']['3_accuracy_metrics_comparison']['metric'] + " (m)")

    # 设置横轴标签
    plt.xticks([])  # 不显示横轴标签

    # 绘制柱形
    for i, attr in enumerate(attributes):
        color = plt.cm.viridis(i / len(attributes))  # 使用颜色映射获取不同颜色
        plt.bar(attr, y[i], color=color, width = 0.1, label=f'{attr}')

    # 添加注释
    # for i, attr in enumerate(attributes):
    #     color = plt.cm.viridis(i / len(attributes))  # 获取对应的颜色
    #     plt.plot(label=f'Data {i+1} - CPU', color=color)
    #     #plt.text(0.65, 0.9 - i * 0.05, f'{attr}', transform=plt.gca().transAxes)
    #     #plt.plot([0.60], [0.91 - i * 0.05], color=color, marker='s', markersize=10, linestyle='', transform=plt.gca().transAxes)  # 添加颜色标记
    #     # TODO 找一个更好的方式添加注释
    
    diagram_name_pgf = data['evaluation_form']['3_accuracy_metrics_comparison']['metric']+".pgf"
    diagram_name_png = data['evaluation_form']['3_accuracy_metrics_comparison']['metric']+".png"
    diagram_name_pdf = data['evaluation_form']['3_accuracy_metrics_comparison']['metric']+".pdf"
    # diagram_path_pgf = folder_path + "/accuracy_metrics_comparison/" + diagram_name_pgf
    # diagram_path_png = folder_path + "/accuracy_metrics_comparison/" + diagram_name_png
    # diagram_path_pdf = folder_path + "/accuracy_metrics_comparison/" + diagram_name_pdf
    diagram_path_pgf = folder_path + diagram_name_pgf
    diagram_path_png = folder_path + diagram_name_png
    diagram_path_pdf = folder_path + diagram_name_pdf

    plt.legend()
    plt.savefig(diagram_path_pgf, dpi = 400)
    plt.savefig(diagram_path_png, dpi = 400)
    plt.savefig(diagram_path_pdf, dpi = 400)

    # save the final
    # 纵轴是算法；横轴是数据集
    for i in range(len(algorithm_id_list)):
        algo = Algorithm.query.get(int(algorithm_id_list[i]))
        algorithm_name_list.append(algo.imageTag)
    for i in range(len(dataset_id_list)):
        dataset = Dataset.query.get(int(dataset_id_list[i]))
        dataset_name_list.append(dataset.name)

    # 打开一个CSV文件用于写入
    csv_name = data['evaluation_form']['3_accuracy_metrics_comparison']['metric']+".csv"
    csv_path = folder_path + csv_name

    with open(csv_path, 'w', newline='') as file:
        writer = csv.writer(file)
        
        # 写入第一行（包含数据集ID）
        writer.writerow(["Mapping Task ID", "Config ID", "algorithm", "dataset", data['evaluation_form']['3_accuracy_metrics_comparison']['metric']])
        
        for i in range(len(algorithm_id_list)):
            current_values = []
            for j in range(len(dataset_id_list)):
                for k in range(len(final_parameter_array[i][j])):
                    config = config_array_3[i][j][k]
                    for l in range(len(final_parameter_array[i][j][k])):
                        # 每一个task写入一行
                        task_id = config.mappingTasks[l].id
                        config_id = config.id
                        algo_name = config.algorithm.imageTag
                        dataset_name = config.dataset.name
                        writer.writerow([task_id, config_id, algo_name, dataset_name, final_parameter_array[i][j][k][l]])

        # # 写入每一行（包含算法ID和对应的数据）
        # for alg_id, row in zip(algorithm_name_list, final_parameter_array):
        #     writer.writerow([alg_id] + row)

def generation_usage_comparison(data, suit_configs_list, folder_path, file_name):
    csv_files = []
    for config in suit_configs_list:
        csv_files.append('/slam_hive_results/mapping_results/' + str(config.mappingTasks[0].id) + "/profiling.csv")
    
    data_frames = []

    for file in csv_files:
        file_path = os.path.join(file)
        df = pd.read_csv(file_path)
        data_frames.append(df)



    

    # 绘制折线图
    plt.figure(figsize=(10, 6))  # 设置图形大小

    for i, df in enumerate((data_frames)):
        color = np.random.rand(3,)  # 使用颜色映射获取不同颜色
        plt.plot(df['time'], df['cpu_usage'], label=f'Task {suit_configs_list[i].mappingTasks[0].id} - CPU Usage', color=color)  # 绘制CPU使用率折线
        # plt.plot(df['time'], df['ram_usage'], label=f'Data {i+1} - RAM', linestyle='dashed', color=color)  # 绘制内存使用率折线
    
    plt.xlabel("Time (sec)")
    plt.ylabel("CPU usage (cores)")    
    plt.title("CPU usage over Time")
    plt.legend()  # 显示图例
    plt.grid(True)  # 添加网格线
    plt.xticks(rotation=45)  # 旋转x轴刻度，使其更易读

    diagram_name_pgf = "cpu_usage.pgf"
    diagram_name_png = "cpu_usage.png"
    diagram_name_pdf = "cpu_usage.pdf"
    # diagram_path_pgf = folder_path + "/usage_comparison/" + diagram_name_pgf
    # diagram_path_png = folder_path + "/usage_comparison/" + diagram_name_png
    # diagram_path_pdf = folder_path + "/usage_comparison/" + diagram_name_pdf
    diagram_path_pgf = folder_path + diagram_name_pgf
    diagram_path_png = folder_path + diagram_name_png
    diagram_path_pdf = folder_path + diagram_name_pdf

    plt.legend()
    plt.savefig(diagram_path_pgf, dpi = 400)
    plt.savefig(diagram_path_png, dpi = 400)
    plt.savefig(diagram_path_pdf, dpi = 400)  
    plt.close()

    for i, df in enumerate((data_frames)):
        color = np.random.rand(3,)  # 使用颜色映射获取不同颜色
        plt.plot(df['time'], df['memory_usage']/(1024*1024), label=f'Task {suit_configs_list[i].mappingTasks[0].id} - Memory Usage', color=color)  # 绘制CPU使用率折线
        # plt.plot(df['time'], df['ram_usage'], label=f'Data {i+1} - RAM', linestyle='dashed', color=color)  # 绘制内存使用率折线
    
    plt.xlabel("Time (sec)")
    plt.ylabel("RAM usage (MiB)")    
    plt.title("RAM usage over Time")
    plt.legend()  # 显示图例
    plt.grid(True)  # 添加网格线
    plt.xticks(rotation=45)  # 旋转x轴刻度，使其更易读

    diagram_name_pgf = "memory_usage.pgf"
    diagram_name_png = "memory_usage.png"
    diagram_name_pdf = "memory_usage.pdf"
    # diagram_path_pgf = folder_path + "/usage_comparison/" + diagram_name_pgf
    # diagram_path_png = folder_path + "/usage_comparison/" + diagram_name_png
    # diagram_path_pdf = folder_path + "/usage_comparison/" + diagram_name_pdf
    diagram_path_pgf = folder_path + diagram_name_pgf
    diagram_path_png = folder_path + diagram_name_png
    diagram_path_pdf = folder_path + diagram_name_pdf

    plt.legend()
    plt.savefig(diagram_path_pgf, dpi = 400)
    plt.savefig(diagram_path_png, dpi = 400)
    plt.savefig(diagram_path_pdf, dpi = 400)  

    plt.close()

def pre_handle_scatter(data, final_config_id_list, flag, x_type, y_type):
    # 预处理数据
    # 0 accuracy
    # 1 performance
    # 2 parameter
    x_key = 0
    y_key = 0
    if flag == 5:
        x_key = data['evaluation_form']['5_scatter_diagram']['x-axis']
        y_key = data['evaluation_form']['5_scatter_diagram']['y-axis']
    else:
        x_key = data['evaluation_form']['6_scatter_diagram']['x-axis']
        y_key = data['evaluation_form']['6_scatter_diagram']['y-axis']     

    if x_type == 2 or y_type == 2:
        parameter_check = "lxztsl"
        if x_type == 2:
            parameter_check = x_key
        if y_type == 2:
            parameter_check = y_key
        try:

            para_key = float(parameter_check)
            # 判断这个parameter是不是个数字
        except Exception as e:
            print("error: ", e)
            return False

        if parameter_check != "lxztsl":
            for config in final_config_id_list:
                parameters = config.paramValues
                parameter_keys = []
                for parameter in parameters:
                    parameter_keys.append(parameter.keyName)
                if parameter_check not in parameter_keys:
                    return False
    

    # 如果有parameter的话 每个config都有这个parameter
    return True


# 输入两个列表

def save_2d_scatter_raw_data(x_axis, x_list, y_axis, y_list, save_path, raw_data):
    # 检查 x_list 和 y_list 的长度是否一致
    if len(x_list) != len(y_list):
        raise ValueError("x_list and y_list must have the same length")
    
    # 创建 DataFrame
    data = {"config id": raw_data["config id"],"task id": raw_data["task id"], "algo name": raw_data["algo name"], "dataset name": raw_data["dataset name"],x_axis: x_list, y_axis: y_list}
    df = pd.DataFrame(data)
    
    # 保存到指定路径
    df.to_csv(save_path, index=False)
    print(f"Data saved to {save_path}")

def save_3d_scatter_raw_data(x_axis, x_list, y_axis, y_list, z_axis, z_list, save_path, raw_data):
    # 检查 x_list, y_list 和 z_list 的长度是否一致
    if len(x_list) != len(y_list) or len(y_list) != len(z_list):
        raise ValueError("x_list, y_list, and z_list must have the same length")
    
    # 创建 DataFrame
    data = {"config id": raw_data["config id"],"task id": raw_data["task id"], "algo name": raw_data["algo name"], "dataset name": raw_data["dataset name"],x_axis: x_list, y_axis: y_list, z_axis: z_list}
    df = pd.DataFrame(data)
    
    # 保存到指定路径
    df.to_csv(save_path, index=False)
    print(f"Data saved to {save_path}")

def update_raw_other_data(config):
    config_id = config.id
    task_id = config.mappingTasks[0].id
    algo_name = config.algorithm.imageTag
    dataset_name = config.dataset.name
    return config_id, task_id, algo_name, dataset_name

def generation_scatter(data, suit_configs_list,folder_path, file_name,flag, traj_unsuccess_configs_id_list,  extend_threshold,extend_multiple, filter_traj_config_id_list):
    
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

    
    old_suit_configs_list = suit_configs_list
    suit_configs_list = []
    for conf in old_suit_configs_list:
        if str(conf.id) not in traj_unsuccess_configs_id_list:
            suit_configs_list.append(conf)


    # old_suit_configs_list存储了包括轨迹失败的

    # 只针对于选择了ate或者rpe指标的
    # 如果没选，直接无视

    # 如果只有usage的，就和之前一样，轨迹失败的就不用管了（ 因为失败了内存啥的也不太会增长了）


    x_key = ""
    y_key = ""
    if flag == 5:
        x_key = data['evaluation_form']['5_scatter_diagram']['x-axis']
        y_key = data['evaluation_form']['5_scatter_diagram']['y-axis']
    else:
        x_key = data['evaluation_form']['6_scatter_diagram']['x-axis']
        y_key = data['evaluation_form']['6_scatter_diagram']['y-axis']     

    x_axis = x_key
    y_axis = y_key

    x_unit = ""
    y_unit = ""
    
    Extend_axis = [0,0,0]
    Extend_attribute = ['', '', '']

    if "ate" in x_axis or "rpe" in x_axis:
        x_unit = "(m)"
        Extend_axis[0] = 1
        Extend_attribute[0] = x_axis
    elif "cpu" in x_axis:
        x_unit = "(cores)"
    elif "memory" in x_axis:
        x_unit = "(MB)"
    elif "frequency" in x_axis:
        x_unit = "(Hz)"

    if "ate" in y_axis or "rpe" in y_axis:
        Extend_axis[1] = 1
        Extend_attribute[1] = y_axis
        y_unit = "(m)"
    elif "cpu" in y_axis:
        y_unit = "(cores)"
    elif "memory" in y_axis:
        y_unit = "(MB)"
    elif "frequency" in y_axis:
        y_unit = "(Hz)"


    # 如果y轴不是ate or rpe的话，就不管filter了
    if "ate" not in y_axis and "rpe" not in y_axis:
        filter_traj_config_id_list = []
    if "ate" in x_axis or "rpe" in x_axis:
        filter_traj_config_id_list = []

    algorithm_id_dict = {}
    for config in suit_configs_list:
        # 给config分类
        if config.algorithm.imageTag not in algorithm_id_dict.keys():
            algorithm_id_dict.update({config.algorithm.imageTag: [config]})
        else:
            algorithm_id_dict[config.algorithm.imageTag].append(config)

    dataset_id_dict = {}
    for config in suit_configs_list:
        if config.dataset.name not in dataset_id_dict.keys():
            dataset_id_dict.update({config.dataset.name: [config]})
        else:
            dataset_id_dict[config.dataset.name].append(config)
    
    # filter一定是之前没有过的！！！
    for id in filter_traj_config_id_list:
        config = MappingTaskConfig.query.get(id)
        # 给config分类
        if config.algorithm.imageTag not in algorithm_id_dict.keys():
            algorithm_id_dict.update({config.algorithm.imageTag: [config]})
        else:
            algorithm_id_dict[config.algorithm.imageTag].append(config)

    for id in filter_traj_config_id_list:
        config = MappingTaskConfig.query.get(id)
        if config.dataset.name not in dataset_id_dict.keys():
            dataset_id_dict.update({config.dataset.name: [config]})
        else:
            dataset_id_dict[config.dataset.name].append(config)

    # 首先判断group中的config -- algo：任意都可以（但是貌似不是同一个算法意义不大）;dataset: 相同

    diagram_data = {}
    diagram_data.update({x_axis: []})
    diagram_data.update({y_axis: []})
    diagram_data.update({"category": []})

    raw_data = {}
    raw_data.update({"config id": []})
    raw_data.update({"task id": []})
    raw_data.update({"algo name": []})
    raw_data.update({"dataset name": []})


    max_y = -99999
    for key, value in dataset_id_dict.items(): # algorithm_id_dict.items():
        # 生成一个color
        # 其他dataset的color以这个为中心
        for dkey, dvalue in algorithm_id_dict.items(): # dataset_id_dict.items():

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
                # print("--", config.mappingTasks[0].id)

                if config.id not in filter_traj_config_id_list:
                    evoResults = config.mappingTasks[0].evaluation.evoResults
                performanceresults = config.mappingTasks[0].performanceresults

                # print(x_axis, y_axis)

                # 如果x轴是ate or rpe 就不会有filter traj了             

                if x_axis == 'ate_rmse':
                    x_v = evoResults.ate_rmse
                elif x_axis == 'ate_mean':
                    x_v = evoResults.ate_mean
                elif x_axis == 'ate_median':
                    x_v = evoResults.ate_median
                elif x_axis == 'ate_std':
                    x_v = evoResults.ate_std
                elif x_axis == 'ate_min':
                    x_v = evoResults.ate_min
                elif x_axis == 'ate_max':
                    x_v = evoResults.ate_max
                elif x_axis == 'ate_sse':
                    x_v = evoResults.ate_sse
                elif x_axis == 'rpe_mean':
                    x_v = evoResults.rpe_mean
                elif x_axis == 'rpe_median':
                    x_v = evoResults.rpe_median
                elif x_axis == 'rpe_std':
                    x_v = evoResults.rpe_std
                elif x_axis == 'rpe_min':
                    x_v = evoResults.rpe_min
                elif x_axis == 'rpe_max':
                    x_v = evoResults.rpe_max
                elif x_axis == 'rpe_sse':
                    x_v = evoResults.rpe_sse
                elif x_axis == 'rpe_rmse':
                    x_v = evoResults.rpe_rmse
                elif x_axis == 'cpu_max':
                    x_v = performanceresults.max_cpu
                elif x_axis == 'cpu_mean':
                    x_v = performanceresults.mean_cpu
                elif x_axis == 'ram_max':
                    x_v = performanceresults.max_ram
                else:
                    # parameter
                    for paramValue in config.paramValues:
                        if x_axis == paramValue.name:
                            x_v = float(paramValue.value)
                            break

                if config.id in filter_traj_config_id_list:
                    y_v = -1
                else:

                    if y_axis == 'ate_rmse':
                        y_v = evoResults.ate_rmse
                    elif y_axis == 'ate_mean':
                        y_v = evoResults.ate_mean
                    elif y_axis == 'ate_median':
                        y_v = evoResults.ate_median
                    elif y_axis == 'ate_std':
                        y_v = evoResults.ate_std
                    elif y_axis == 'ate_min':
                        y_v = evoResults.ate_min
                    elif y_axis == 'ate_max':
                        y_v = evoResults.ate_max
                    elif y_axis == 'ate_sse':
                        y_v = evoResults.ate_sse
                    elif y_axis == 'rpe_mean':
                        y_v = evoResults.rpe_mean
                    elif y_axis == 'rpe_median':
                        y_v = evoResults.rpe_median
                    elif y_axis == 'rpe_std':
                        y_v = evoResults.rpe_std
                    elif y_axis == 'rpe_min':
                        y_v = evoResults.rpe_min
                    elif y_axis == 'rpe_max':
                        y_v = evoResults.rpe_max
                    elif y_axis == 'rpe_sse':
                        y_v = evoResults.rpe_sse
                    elif y_axis == 'rpe_rmse':
                        y_v = evoResults.rpe_rmse
                    elif y_axis == 'cpu_max':
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

                max_y = max(max_y, y_v)

                # diagram_data.append([x_v, y_v, key])
                diagram_data[x_axis].append(x_v)
                diagram_data[y_axis].append(y_v)
                diagram_data['category'].append(category)

                config_id, task_id, algo_name, dataset_name = update_raw_other_data(config)
                raw_data["config id"].append(config_id)
                raw_data["task id"].append(task_id)
                raw_data["algo name"].append(algo_name)
                raw_data["dataset name"].append(dataset_name)

    # 用max_y更新所有的filter
    # print(type(raw_data["config id"][0]), type(filter_traj_config_id_list[0]))
    for i in range(len(diagram_data[y_axis])):
        if raw_data["config id"][i] in filter_traj_config_id_list:
            diagram_data[y_axis][i] = 1.2 * max_y
    # 后面都一样了


    temp_name = "2d_raw_data_x-" + x_axis + "_y-" + y_axis+".csv"
    # 还有mapping task or config ID
    save_2d_scatter_raw_data(x_axis, diagram_data[x_axis], y_axis, diagram_data[y_axis], folder_path + temp_name, raw_data)

    # ln_numbers = [math.log(y) for y in diagram_data[y_axis]]
    # diagram_data[y_axis] = ln_numbers


    df = pd.DataFrame(diagram_data)#, columns=[x_axis, y_axis])

    for i in range(2):
    ## TODO 为什么第一个表格 没有背景线

    # 下午：在线的；3D；在线生成；然后然后生成一个最基础版本的新实验
    # 修改custom的显示（Viwe-only的u单独判断）
    #今天争取开始写论文


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

        # 绘制散点图
        fig, ax = plt.subplots(figsize=(22, 14.1))

        fig, ax = plt.subplots(figsize=(22, 14.1))

        sns.set(style="whitegrid")

        

        # 绘制带有颜色编码的散点图
        for cat in color_dict:
            subset = df[df['category'] == cat]
            ax.scatter(subset[x_axis], subset[y_axis], color=color_dict[cat], label=cat)

        # 设置坐标系的文字
        # ax.set_title('Scatter Plot of X vs Y', fontsize=14)
        # ax.set_xlabel('X', fontsize=12)
        # ax.set_ylabel('Y', fontsize=12)
        ax.set_xlabel(x_axis + " " + x_unit)
        ax.set_ylabel(y_axis + " " + y_unit)

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



        # 调整绘图的边距，以确保图例不重叠
        
        diagram_name_pgf = "Diagram1_x-" + x_axis + "_y-" + y_axis+".pgf"
        diagram_name_png = "Diagram1_x-" + x_axis + "_y-" + y_axis+".png"
        diagram_name_pdf = "Diagram1_x-" + x_axis + "_y-" + y_axis+".pdf"
        # diagram_path_pgf = folder_path + "/scatter/" + diagram_name_pgf
        # diagram_path_png = folder_path + "/scatter/" + diagram_name_png
        # diagram_path_pdf = folder_path + "/scatter/" + diagram_name_pdf
        diagram_path_pgf = folder_path + diagram_name_pgf
        diagram_path_png = folder_path + diagram_name_png
        diagram_path_pdf = folder_path + diagram_name_pdf


        scatter_fig = fig.get_figure()
        scatter_fig.savefig(diagram_path_pgf, dpi = 400)
        scatter_fig.savefig(diagram_path_png, dpi = 400)
        scatter_fig.savefig(diagram_path_pdf, dpi = 400)


    # 
    if 1 not in Extend_axis:
        return 
    
    # 输入，原始的数据 + 筛选过后的数据
    # 返回，修正后的数据（直接返回一个diagram_data的数据就好了）

    ret = get_Extend_accuracy(old_suit_configs_list, suit_configs_list, Extend_axis, Extend_attribute, extend_threshold,extend_multiple)
    # 应该要返回3个列表的列表，每个列表里有新的数据（列表里面的元素是字典）

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

    raw_data = {}
    raw_data.update({"config id": []})
    raw_data.update({"task id": []})
    raw_data.update({"algo name": []})
    raw_data.update({"dataset name": []})
    for key, value in dataset_id_dict.items(): # algorithm_id_dict.items():
        # 生成一个color
        # 其他dataset的color以这个为中心
        for dkey, dvalue in algorithm_id_dict.items(): # dataset_id_dict.items():
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


                print(x_axis, y_axis)


                if Extend_axis[0] == 1:
                    x_v = ret[0][config.id][2]
                else:
                    # print("?????????")
                    performanceresults = config.mappingTasks[0].performanceresults

                    if x_axis == 'cpu_max':
                        x_v = performanceresults.max_cpu
                    elif x_axis == 'cpu_mean':
                        x_v = performanceresults.mean_cpu
                    elif x_axis == 'ram_max':
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
                
                config_id, task_id, algo_name, dataset_name = update_raw_other_data(config)
                raw_data["config id"].append(config_id)
                raw_data["task id"].append(task_id)
                raw_data["algo name"].append(algo_name)
                raw_data["dataset name"].append(dataset_name)

    
    temp_name = "Extend_2d_raw_data_x-" + x_axis + "_y-" + y_axis+".csv"
    save_2d_scatter_raw_data(x_axis, diagram_data[x_axis], y_axis, diagram_data[y_axis], folder_path + temp_name, raw_data)
    
    # ln_numbers = [math.log(y) for y in diagram_data[y_axis]]
    # diagram_data[y_axis] = ln_numbers


    df = pd.DataFrame(diagram_data)#, columns=[x_axis, y_axis])
    

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

    # 绘制散点图
    fig, ax = plt.subplots(figsize=(22, 16))

    sns.set(style="whitegrid")

    plt.title("Extend")

    # 绘制带有颜色编码的散点图
    for cat in color_dict:
        subset = df[df['category'] == cat]
        ax.scatter(subset[x_axis], subset[y_axis], color=color_dict[cat], label=cat)

    # 设置坐标系的文字
    # ax.set_title('Scatter Plot of X vs Y', fontsize=14)
    # ax.set_xlabel('X', fontsize=12)
    # ax.set_ylabel('Y', fontsize=12)
    ax.set_xlabel(x_axis + " " + x_unit)
    ax.set_ylabel(y_axis + " " + y_unit)

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



    # 调整绘图的边距，以确保图例不重叠
    
    diagram_name_pgf = "Diagram1_x-" + x_axis + "_y-" + y_axis+"-Extend.pgf"
    diagram_name_png = "Diagram1_x-" + x_axis + "_y-" + y_axis+"-Extend.png"
    diagram_name_pdf = "Diagram1_x-" + x_axis + "_y-" + y_axis+"-Extend.pdf"
    # diagram_path_pgf = folder_path + "/scatter/" + diagram_name_pgf
    # diagram_path_png = folder_path + "/scatter/" + diagram_name_png
    # diagram_path_pdf = folder_path + "/scatter/" + diagram_name_pdf
    diagram_path_pgf = folder_path + diagram_name_pgf
    diagram_path_png = folder_path + diagram_name_png
    diagram_path_pdf = folder_path + diagram_name_pdf


    scatter_fig = fig.get_figure()
    scatter_fig.savefig(diagram_path_pgf, dpi = 400)
    scatter_fig.savefig(diagram_path_png, dpi = 400)
    scatter_fig.savefig(diagram_path_pdf, dpi = 400)    

    # 明天测试一下



    ####################### 开一个新的模块，用来生成这个图标（写一个函数 生成新的数据）
    # 在线选择那里也加上（如果某个轴上有ate或者rpe的话）


def generation_3d_scatter(data, suit_configs_list,folder_path, file_name,flag, traj_unsuccess_configs_id_list, extend_threshold,extend_multiple, filter_traj_config_id_list):
    old_suit_configs_list = suit_configs_list
    suit_configs_list = []
    for conf in old_suit_configs_list:
        if str(conf.id) not in traj_unsuccess_configs_id_list:
            suit_configs_list.append(conf)

    x_key = ""
    y_key = ""
    x_key = data['evaluation_form']['7_3d_scatter_diagram']['x-axis']
    y_key = data['evaluation_form']['7_3d_scatter_diagram']['y-axis'] 
    z_key = data['evaluation_form']['7_3d_scatter_diagram']['z-axis'] 

    x_axis = x_key
    y_axis = y_key
    z_axis = z_key

    x_unit = ""
    y_unit = ""
    z_unit = ""

    Extend_axis = [0,0,0]
    Extend_attribute = ['', '', '']

    if "ate" in x_axis or "rpe" in x_axis:
        x_unit = "(m)"
        Extend_axis[0] = 1
        Extend_attribute[0] = x_axis
    elif "cpu" in x_axis:
        x_unit = "(cores)"
    elif "memory" in x_axis:
        x_unit = "(MB)"
    elif "frequency" in x_axis:
        x_unit = "(Hz)"

    if "ate" in y_axis or "rpe" in y_axis:
        y_unit = "(m)"
        Extend_axis[1] = 1
        Extend_attribute[1] = y_axis
    elif "cpu" in y_axis:
        y_unit = "(cores)"
    elif "memory" in y_axis:
        y_unit = "(MB)"
    elif "frequency" in y_axis:
        y_unit = "(Hz)"

    if "ate" in z_axis or "rpe" in z_axis:
        z_unit = "(m)"
        Extend_axis[2] = 1
        Extend_attribute[2] = z_axis
    elif "cpu" in z_axis:
        z_unit = "(cores)"
    elif "memory" in z_axis:
        z_unit = "(MB)"
    elif "frequency" in z_axis:
        z_unit = "(Hz)" 
    # 增加分类条件：
    # algorithm + dataset

    # 如果y轴不是ate or rpe的话，就不管filter了
    if "ate" not in z_axis and "rpe" not in z_axis:
        filter_traj_config_id_list = []
    if "ate" in x_axis or "rpe" in x_axis:
        filter_traj_config_id_list = []
    if "ate" in y_axis or "rpe" in y_axis:
        filter_traj_config_id_list = []

    algorithm_id_dict = {}
    for config in suit_configs_list:
        # 给config分类
        if config.algorithm.imageTag not in algorithm_id_dict.keys():
            algorithm_id_dict.update({config.algorithm.imageTag: [config]})
        else:
            algorithm_id_dict[config.algorithm.imageTag].append(config)

    dataset_id_dict = {}
    for config in suit_configs_list:
        if config.dataset.name not in dataset_id_dict.keys():
            dataset_id_dict.update({config.dataset.name: [config]})
        else:
            dataset_id_dict[config.dataset.name].append(config)

    # filter一定是之前没有过的！！！
    for id in filter_traj_config_id_list:
        config = MappingTaskConfig.query.get(id)
        # 给config分类
        if config.algorithm.imageTag not in algorithm_id_dict.keys():
            algorithm_id_dict.update({config.algorithm.imageTag: [config]})
        else:
            algorithm_id_dict[config.algorithm.imageTag].append(config)

    for id in filter_traj_config_id_list:
        config = MappingTaskConfig.query.get(id)
        if config.dataset.name not in dataset_id_dict.keys():
            dataset_id_dict.update({config.dataset.name: [config]})
        else:
            dataset_id_dict[config.dataset.name].append(config)



    # 首先判断group中的config -- algo：任意都可以（但是貌似不是同一个算法意义不大）;dataset: 相同

    diagram_data = {}
    diagram_data.update({x_axis: []})
    diagram_data.update({y_axis: []})
    diagram_data.update({z_axis: []})
    diagram_data.update({"category": []})

    raw_data = {}
    raw_data.update({"config id": []})
    raw_data.update({"task id": []})
    raw_data.update({"algo name": []})
    raw_data.update({"dataset name": []})
    # 这里o重新遍历 每次遍历设置一个新的color
    max_z = -99999
    for key, value in dataset_id_dict.items(): # algorithm_id_dict.items():
        # 生成一个color
        # 其他dataset的color以这个为中心
        for dkey, dvalue in algorithm_id_dict.items(): # dataset_id_dict.items():

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
                if config.id not in filter_traj_config_id_list:
                    evoResults = config.mappingTasks[0].evaluation.evoResults
                performanceresults = config.mappingTasks[0].performanceresults

                print(x_axis, y_axis)

                if x_axis == 'ate_rmse':
                    x_v = evoResults.ate_rmse
                elif x_axis == 'ate_mean':
                    x_v = evoResults.ate_mean
                elif x_axis == 'ate_median':
                    x_v = evoResults.ate_median
                elif x_axis == 'ate_std':
                    x_v = evoResults.ate_std
                elif x_axis == 'ate_min':
                    x_v = evoResults.ate_min
                elif x_axis == 'ate_max':
                    x_v = evoResults.ate_max
                elif x_axis == 'ate_sse':
                    x_v = evoResults.ate_sse
                elif x_axis == 'rpe_mean':
                    x_v = evoResults.rpe_mean
                elif x_axis == 'rpe_median':
                    x_v = evoResults.rpe_median
                elif x_axis == 'rpe_std':
                    x_v = evoResults.rpe_std
                elif x_axis == 'rpe_min':
                    x_v = evoResults.rpe_min
                elif x_axis == 'rpe_max':
                    x_v = evoResults.rpe_max
                elif x_axis == 'rpe_sse':
                    x_v = evoResults.rpe_sse
                elif x_axis == 'rpe_rmse':
                    x_v = evoResults.rpe_rmse
                elif x_axis == 'cpu_max':
                    x_v = performanceresults.max_cpu
                elif x_axis == 'cpu_mean':
                    x_v = performanceresults.mean_cpu
                elif x_axis == 'ram_max':
                    x_v = performanceresults.max_ram
                else:
                    # parameter
                    for paramValue in config.paramValues:
                        if x_axis == paramValue.name:
                            x_v = float(paramValue.value)
                            break

                if y_axis == 'ate_rmse':
                    y_v = evoResults.ate_rmse
                elif y_axis == 'ate_mean':
                    y_v = evoResults.ate_mean
                elif y_axis == 'ate_median':
                    y_v = evoResults.ate_median
                elif y_axis == 'ate_std':
                    y_v = evoResults.ate_std
                elif y_axis == 'ate_min':
                    y_v = evoResults.ate_min
                elif y_axis == 'ate_max':
                    y_v = evoResults.ate_max
                elif y_axis == 'ate_sse':
                    y_v = evoResults.ate_sse
                elif y_axis == 'rpe_mean':
                    y_v = evoResults.rpe_mean
                elif y_axis == 'rpe_median':
                    y_v = evoResults.rpe_median
                elif y_axis == 'rpe_std':
                    y_v = evoResults.rpe_std
                elif y_axis == 'rpe_min':
                    y_v = evoResults.rpe_min
                elif y_axis == 'rpe_max':
                    y_v = evoResults.rpe_max
                elif y_axis == 'rpe_sse':
                    y_v = evoResults.rpe_sse
                elif y_axis == 'rpe_rmse':
                    y_v = evoResults.rpe_rmse
                elif y_axis == 'cpu_max':
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


                if config.id in filter_traj_config_id_list:
                    z_v = -1
                else:


                    if z_axis == 'ate_rmse':
                        z_v = evoResults.ate_rmse
                    elif z_axis == 'ate_mean':
                        z_v = evoResults.ate_mean
                    elif z_axis == 'ate_median':
                        z_v = evoResults.ate_median
                    elif z_axis == 'ate_std':
                        z_v = evoResults.ate_std
                    elif z_axis == 'ate_min':
                        z_v = evoResults.ate_min
                    elif z_axis == 'ate_max':
                        z_v = evoResults.ate_max
                    elif z_axis == 'ate_sse':
                        z_v = evoResults.ate_sse
                    elif z_axis == 'rpe_mean':
                        z_v = evoResults.rpe_mean
                    elif z_axis == 'rpe_median':
                        z_v = evoResults.rpe_median
                    elif z_axis == 'rpe_std':
                        z_v = evoResults.rpe_std
                    elif z_axis == 'rpe_min':
                        z_v = evoResults.rpe_min
                    elif z_axis == 'rpe_max':
                        z_v = evoResults.rpe_max
                    elif z_axis == 'rpe_sse':
                        z_v = evoResults.rpe_sse
                    elif z_axis == 'rpe_rmse':
                        z_v = evoResults.rpe_rmse
                    elif z_axis == 'cpu_max':
                        z_v = performanceresults.max_cpu
                    elif z_axis == 'cpu_mean':
                        z_v = performanceresults.mean_cpu
                    elif z_axis == 'ram_max':
                        z_v = performanceresults.max_ram
                    else:
                        # parameter
                        for paramValue in config.paramValues:
                            if z_axis == paramValue.name:
                                z_v = float(paramValue.value)
                                break    
                
                max_z = max(max_z, z_v)
                # diagram_data.append([x_v, y_v, key])
                diagram_data[x_axis].append(x_v)
                diagram_data[y_axis].append(y_v)
                diagram_data[z_axis].append(z_v)
                diagram_data['category'].append(category)
                
                config_id, task_id, algo_name, dataset_name = update_raw_other_data(config)
                raw_data["config id"].append(config_id)
                raw_data["task id"].append(task_id)
                raw_data["algo name"].append(algo_name)
                raw_data["dataset name"].append(dataset_name)


    # 用max_y更新所有的filter
    for i in range(len(diagram_data[z_axis])):
        if raw_data["config id"][i] in filter_traj_config_id_list:
            diagram_data[z_axis][i] = 1.2 * max_z
    # 后面都一样了

    # ln_numbers = [math.log(z) for z in diagram_data[z_axis]]
    # diagram_data[z_axis] = ln_numbers
    
    temp_name = "3d_raw_data_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis +".csv"
    save_3d_scatter_raw_data(x_axis, diagram_data[x_axis], y_axis, diagram_data[y_axis],z_axis, diagram_data[z_axis], folder_path + temp_name, raw_data)

    print(diagram_data)
    df = pd.DataFrame(diagram_data)#, columns=[x_axis, y_axis])
    # plt.figure(figsize=(10, 8))
    # fig = sns.scatterplot(x=x_axis, y=y_axis, data=df, hue='category')

  # 创建颜色映射
    # palette = sns.color_palette("husl", len(df['category'].unique()))
    # colors = {cat: palette[i] for i, cat in enumerate(df['category'].unique())}


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
        print("sub_palette111")
        print(sub_palette)
        for j, b in enumerate(unique_B):
            color_dict[f"{a}  {b}"] = sub_palette[j*5 + 4]    

    # 创建图形对象
    # fig = plt.figure(figsize=(18, 8))
    fig = plt.figure(figsize=(18, 12))
    ax = fig.add_subplot(111, projection='3d')

    # 绘制三维散点图
    # for cat in colors:
    #     subset = df[df['category'] == cat]
    #     ax.scatter(subset[x_axis], subset[y_axis], subset[z_axis], color=colors[cat], label=cat)


    for cat in df['category'].unique():
        subset = df[df['category'] == cat]
        ax.scatter(subset[x_axis], subset[y_axis], subset[z_axis], color=color_dict[cat], label=cat)


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
    # diagram_path_pgf = folder_path + "/3d_scatter/" + diagram_name_pgf
    # diagram_path_png = folder_path + "/3d_scatter/" + diagram_name_png
    # diagram_path_pdf = folder_path + "/3d_scatter/" + diagram_name_pdf
    diagram_path_pgf = folder_path + diagram_name_pgf
    diagram_path_png = folder_path + diagram_name_png
    diagram_path_pdf = folder_path + diagram_name_pdf

    plt.savefig(diagram_path_pgf, dpi = 800)
    plt.savefig(diagram_path_png, dpi = 800)
    plt.savefig(diagram_path_pdf, dpi = 800)



    if 1 not in Extend_axis:
        return   

    ret = get_Extend_accuracy(old_suit_configs_list, suit_configs_list, Extend_axis, Extend_attribute, extend_threshold,extend_multiple)
    algorithm_id_dict = {}
    for config in old_suit_configs_list:
        # 给config分类
        if config.algorithm.imageTag not in algorithm_id_dict.keys():
            algorithm_id_dict.update({config.algorithm.imageTag: [config]})
        else:
            algorithm_id_dict[config.algorithm.imageTag].append(config)
    print(1)
    dataset_id_dict = {}
    for config in old_suit_configs_list:
        if config.dataset.name not in dataset_id_dict.keys():
            dataset_id_dict.update({config.dataset.name: [config]})
        else:
            dataset_id_dict[config.dataset.name].append(config)

    print(1)

    old_diagram_data = diagram_data
    diagram_data = {}
    diagram_data.update({x_axis: []})
    diagram_data.update({y_axis: []})
    diagram_data.update({z_axis: []})
    diagram_data.update({"category": []})
    raw_data = {}
    raw_data.update({"config id": []})
    raw_data.update({"task id": []})
    raw_data.update({"algo name": []})
    raw_data.update({"dataset name": []})

    # 这里o重新遍历 每次遍历设置一个新的color
    for key, value in dataset_id_dict.items(): # algorithm_id_dict.items():
        # 生成一个color
        # 其他dataset的color以这个为中心
        for dkey, dvalue in algorithm_id_dict.items(): #  dataset_id_dict.items():

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
                # evoResults = config.mappingTasks[0].evaluation.evoResults
                # performanceresults = config.mappingTasks[0].performanceresults

                print(x_axis, y_axis)
                if Extend_axis[0] == 1:
                    x_v = ret[0][config.id][2]
                else:
                    performanceresults = config.mappingTasks[0].performanceresults
    
                    if x_axis == 'cpu_max':
                        x_v = performanceresults.max_cpu
                    elif x_axis == 'cpu_mean':
                        x_v = performanceresults.mean_cpu
                    elif x_axis == 'ram_max':
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
                if Extend_axis[2] == 1:
                    z_v = ret[2][config.id][2]  
                else:
                    performanceresults = config.mappingTasks[0].performanceresults
                    
                  
                    if z_axis == 'cpu_max':
                        z_v = performanceresults.max_cpu
                    elif z_axis == 'cpu_mean':
                        z_v = performanceresults.mean_cpu
                    elif z_axis == 'ram_max':
                        z_v = performanceresults.max_ram
                    else:
                        # parameter
                        for paramValue in config.paramValues:
                            if z_axis == paramValue.name:
                                z_v = float(paramValue.value)
                                break    
                # diagram_data.append([x_v, y_v, key])
                diagram_data[x_axis].append(x_v)
                diagram_data[y_axis].append(y_v)
                diagram_data[z_axis].append(z_v)
                diagram_data['category'].append(category)

                config_id, task_id, algo_name, dataset_name = update_raw_other_data(config)
                raw_data["config id"].append(config_id)
                raw_data["task id"].append(task_id)
                raw_data["algo name"].append(algo_name)
                raw_data["dataset name"].append(dataset_name)

    temp_name = "Extend_3d_raw_data_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis +".csv"
    save_3d_scatter_raw_data(x_axis, diagram_data[x_axis], y_axis, diagram_data[y_axis],z_axis, diagram_data[z_axis], folder_path + temp_name, raw_data)
    print(diagram_data)
    df = pd.DataFrame(diagram_data)#, columns=[x_axis, y_axis])
    # plt.figure(figsize=(10, 8))
    # fig = sns.scatterplot(x=x_axis, y=y_axis, data=df, hue='category')

  # 创建颜色映射
    # palette = sns.color_palette("husl", len(df['category'].unique()))
    # colors = {cat: palette[i] for i, cat in enumerate(df['category'].unique())}


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
        print("sub_palette111")
        print(sub_palette)
        for j, b in enumerate(unique_B):
            color_dict[f"{a}  {b}"] = sub_palette[j*5 + 4]    

    # 创建图形对象
    fig = plt.figure(figsize=(18, 12))
    ax = fig.add_subplot(111, projection='3d')

    plt.title("Extend")

    # 绘制三维散点图
    # for cat in colors:
    #     subset = df[df['category'] == cat]
    #     ax.scatter(subset[x_axis], subset[y_axis], subset[z_axis], color=colors[cat], label=cat)


    for cat in df['category'].unique():
        subset = df[df['category'] == cat]
        ax.scatter(subset[x_axis], subset[y_axis], subset[z_axis], color=color_dict[cat], label=cat)


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
    
    diagram_name_pgf = "Diagram2_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis + "-Extend.pgf"
    diagram_name_png = "Diagram2_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis + "-Extend.png"
    diagram_name_pdf = "Diagram2_x-" + x_axis + "_y-" + y_axis+ "_z-" + z_axis + "-Extend.pdf"
    # diagram_path_pgf = folder_path + "/3d_scatter/" + diagram_name_pgf
    # diagram_path_png = folder_path + "/3d_scatter/" + diagram_name_png
    # diagram_path_pdf = folder_path + "/3d_scatter/" + diagram_name_pdf
    diagram_path_pgf = folder_path + diagram_name_pgf
    diagram_path_png = folder_path + diagram_name_png
    diagram_path_pdf = folder_path + diagram_name_pdf

    plt.savefig(diagram_path_pgf, dpi = 800)
    plt.savefig(diagram_path_png, dpi = 800)
    plt.savefig(diagram_path_pdf, dpi = 800)


    # 保存图形到本地文件
    # plt.savefig('3d_scatter_plot_with_categories.pdf')


# 还需要获取哪个轴是；是哪一个参数
def get_Extend_accuracy(old_suit_configs_list ,suit_configs_list, Extend_axis, Extend_attribute, extend_threshold,extend_multiple):
    # 需要每个数据集对应的真值文件
    # 需要每个task的轨迹结果

    # 明天上午来
    # 必须把这个函数写完，至少到能测试为止

    print("-------------")
    print(Extend_axis)
    print(Extend_attribute)
    print(extend_threshold)
    print(extend_multiple)

    ret = [{}, {}, {}]
    Max_values = [-1,-1,-1]
    for i in range(len(Extend_axis)):
        if Extend_axis[i] == 0:
            continue
        
        # {file_path: [start_time, end_time]}
        dataset_file_content = {}

        for j in range(len(old_suit_configs_list)): #里面存的是sql对象
            config = old_suit_configs_list[j]
            # print(config)
            task = config.mappingTasks[0]
            
            task_traj_file_path = "/slam_hive_results/mapping_results/" + str(task.id) + "/traj.txt"
            groundtruth_file_path = "/slam_hive_datasets/" + config.dataset.name + "/groundtruth.txt"
            
            # groundtruth_start_timestamp = 0
            # groundtruth_end_timestamp = 0
            # task_traj_start_timestamp = 0
            # task_traj_end_timestamp = 0

            # if groundtruth_file_path not in dataset_file_content:
            #     # 读取文件
            #     with open(groundtruth_file_path, "r") as file:
            #         lines = file.readlines()
            #         start_timestamp = float(lines[0].split()[0])
            #         end_timestamp = float(lines[-1].split()[0])
                    
            #         dataset_file_content.update({groundtruth_file_path: [start_timestamp, end_timestamp]})

            #         groundtruth_start_timestamp = start_timestamp
            #         groundtruth_end_timestamp = end_timestamp
            # else :
            #     groundtruth_start_timestamp = dataset_file_content[groundtruth_file_path][0]
            #     groundtruth_end_timestamp = dataset_file_content[groundtruth_file_path][1]
            

            # # 然后对origin value进行处理

            # thredhold_value = 0

            # # 首先判断是否是unsuccess的
            # if task.trajectory_state == "Unsuccess": 
            #     task_traj_start_timestamp = groundtruth_start_timestamp
            #     task_traj_end_timestamp = groundtruth_start_timestamp
            #     thredhold_value = 0
            # elif task.trajectory_state == "Success":
            #     # 读取文件
            #     with open(task_traj_file_path, "r") as file:
            #         try:
            #             lines = file.readlines()
            #             task_traj_start_timestamp = float(lines[0].split()[0])
            #             task_traj_end_timestamp = float(lines[-1].split()[0])
            #             thredhold_value = (task_traj_end_timestamp - task_traj_start_timestamp) / (groundtruth_end_timestamp - groundtruth_start_timestamp)
            #         except Exception as e:
            #             thredhold_value = 0.0
            # 现在获取了4个时间戳，然后根据输入的信息，判断新的值

            thredhold_value = task.traj_length
            
            # 判断要获取哪个值
            origin_value = 0




            if task.trajectory_state == "Unsuccess": 
                origin_value = -1
                thredhold_value = extend_threshold[len(extend_threshold) - 1]
                new_value = -1
                ret[i].update({config.id : [origin_value, thredhold_value, new_value]})
                continue

            evoResults = task.evaluation.evoResults
            # print(evoResults)

            if Extend_attribute[i] == 'ate_rmse':
                origin_value = evoResults.ate_rmse
                # print(evoResults.ate_rmse)
            elif Extend_attribute[i] == 'ate_mean':
                origin_value = evoResults.ate_mean
            elif Extend_attribute[i] == 'ate_median':
                origin_value = evoResults.ate_median
            elif Extend_attribute[i] == 'ate_std':
                origin_value = evoResults.ate_std
            elif Extend_attribute[i] == 'ate_min':
                origin_value = evoResults.ate_min
            elif Extend_attribute[i] == 'ate_max':
                origin_value = evoResults.ate_max
            elif Extend_attribute[i] == 'ate_sse':
                origin_value = evoResults.ate_sse
            elif Extend_attribute[i] == 'rpe_mean':
                origin_value = evoResults.rpe_mean
            elif Extend_attribute[i] == 'rpe_median':
                origin_value = evoResults.rpe_median
            elif Extend_attribute[i] == 'rpe_std':
                origin_value = evoResults.rpe_std
            elif Extend_attribute[i] == 'rpe_min':
                origin_value = evoResults.rpe_min
            elif Extend_attribute[i] == 'rpe_max':
                origin_value = evoResults.rpe_max
            elif Extend_attribute[i] == 'rpe_sse':
                origin_value = evoResults.rpe_sse
            elif Extend_attribute[i] == 'rpe_rmse':
                origin_value = evoResults.rpe_rmse
            
            new_value = origin_value
            extend_threshold.append(0)
            for k in range(len(extend_threshold)):
                current_bound = extend_threshold[k]
                if thredhold_value >= current_bound:
                    new_value *= extend_multiple[k]
                    Max_values[i] = max(Max_values[i], new_value)
                    break
            
        
            ret[i].update({config.id : [origin_value, thredhold_value, new_value]})

        for j in range(len(old_suit_configs_list)):

            config = old_suit_configs_list[j]
            task = config.mappingTasks[0]

            if task.trajectory_state == "Unsuccess": 


                ret[i][config.id][2] = Max_values[i] * 1.1 #  * extend_multiple[1] # TODO 需要输入至少有2个         


    print("----------")

    print(ret)
    return ret
  


            # 然后存储到ret[i]中  ret[i].append([origin_vlue, percentage, new_value])
# 今天下午
#代码写完；测试完；然后写3d的
#然后写一下wiki；过一遍还有哪些事情没做
#然后就是实验部分 + 论文 （ 在wiki上加一些例子）


# 上面都整完就是github的备份


                
            

            # 还需要判断是否是unsuccess的轨迹

            # 然后将楼上那些数据保存下来

            # 之后也要保存数据（通过哪些数据生成的这些图标 保存到表格文件里应该可以（或者包含各种东西的文件夹 - 在任务创建时打包好一个文件夹））



# 本质上是evo，所以同evo的下载 加一个按钮
def generatiion_repeatability_test(data, suit_configs_list, folder_path, file_name, traj_unsuccess_configs_id_list, folder_name, analysis_8_metric):

    this_config = suit_configs_list[0]
    mappingtask_list = this_config.mappingTasks

    # 轨迹对比 analysis1，2
    # 可能存在轨迹不成功的情况
    evo_number = 0
    mappingtaskIdList = []
    evaluationIdList = []
    sub_evo_flags = []
    for task in mappingtask_list:
        if task.trajectory_state == "Success":
            evo_number += 1
            mappingtaskIdList.append(str(task.id))
            evaluationIdList.append(str(task.evaluation.id))
            sub_evo_flags.append(True)
        else:
            sub_evo_flags.append(False)
            # 理论上全是True，因为evo那里没有判断，都是输入进入合法的

    datasetName = suit_configs_list[0].dataset.name
    groundtruth = '/SLAM-Hive/slam_hive_datasets/' + datasetName + "/groundtruth.txt"

    resultPath = folder_path +  "/repeatability_test"
    # os.mkdir(resultPath) 
    resultPath = "/SLAM-Hive/slam_hive_results/custom_analysis_group/" + folder_name + "/repeatability_test"
    print(resultPath)
    evo_compare_task_multi(resultPath, evo_number, mappingtaskIdList, evaluationIdList, sub_evo_flags, groundtruth)

###############
    

    # 返回箱线图
    # 现在有了一个二维数组，要计算每个algorithm的均值和std

    final_parameter_array = []
    
    for task in mappingtask_list:
        value = ""
        evoResults = task.evaluation.evoResults
        performanceresults = task.performanceresults
        if analysis_8_metric == 'ate_rmse':
            value = evoResults.ate_rmse
        elif analysis_8_metric == 'ate_mean':
            value = evoResults.ate_mean
        elif analysis_8_metric == 'ate_median':
            value = evoResults.ate_median
        elif analysis_8_metric == 'ate_std':
            value = evoResults.ate_std
        elif analysis_8_metric == 'ate_min':
            value = evoResults.ate_min
        elif analysis_8_metric == 'ate_max':
            value = evoResults.ate_max
        elif analysis_8_metric == 'ate_sse':
            value = evoResults.ate_sse
        elif analysis_8_metric == 'rpe_mean':
            value = evoResults.rpe_mean
        elif analysis_8_metric == 'rpe_median':
            value = evoResults.rpe_median
        elif analysis_8_metric == 'rpe_std':
            value = evoResults.rpe_std
        elif analysis_8_metric == 'rpe_min':
            value = evoResults.rpe_min
        elif analysis_8_metric == 'rpe_max':
            value = evoResults.rpe_max
        elif analysis_8_metric == 'rpe_sse':
            value = evoResults.rpe_sse
        elif analysis_8_metric == 'rpe_rmse':
            value = evoResults.rpe_rmse
        elif analysis_8_metric == 'cpu_max':
            value = performanceresults.max_cpu
        elif analysis_8_metric == 'cpu_mean':
            value = performanceresults.mean_cpu
        elif analysis_8_metric == 'ram_max':
            value = performanceresults.max_ram
        
        final_parameter_array.append(value)

    mean = np.mean(final_parameter_array)
    std = np.std(final_parameter_array)
    
    # 绘制箱线图
    # 示例数据
    attributes = []
    attributes.append(str(suit_configs_list[0].id))

    mean_list = []
    mean_list.append(mean)
    error_list = []
    error_list.append(std)
    y = mean_list
    errors = error_list


    import matplotlib as mpl
    from matplotlib import font_manager


    # 加载DejaVuSans字体
    font_path = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    dejavusans = [f for f in font_path if 'DejaVuSans.ttf' in f][0]
    font_prop = font_manager.FontProperties(fname=dejavusans, size=12)  # 小四相当于12号字体

    # 设置全局字体属性
    mpl.rcParams['pdf.fonttype'] = 42
    mpl.rcParams['ps.fonttype'] = 42
    mpl.rcParams['font.family'] = font_prop.get_name()
    mpl.rcParams['font.size'] = 16  # 小四字体

    mpl1 = mpl.rcParams['pdf.fonttype']
    mpl2 = mpl.rcParams['ps.fonttype']
    mpl3 = mpl.rcParams['font.family']
    mpl4 = mpl.rcParams['font.size']



    # 绘制误差棒图
    plt.figure(figsize=(10,6))
    plt.errorbar(attributes, y, yerr=errors, fmt='o', color='black', ecolor='red', elinewidth=2, capsize=4)

    print(attributes[0])
    print(y,errors)

    # 添加标题和标签
    plt.title('Mean and standard sevisation of ' + analysis_8_metric + " over Configuration: " + str(suit_configs_list[0].id))
    plt.xlabel(str(suit_configs_list[0].id))
    plt.ylabel(analysis_8_metric)

    # plt.xlabel('Sensors combination')
    plt.ylabel(data['evaluation_form']['3_accuracy_metrics_comparison']['metric'] + " (m)")

    # 设置横轴标签
    plt.xticks([])  # 不显示横轴标签

    # 绘制柱形
    for i, attr in enumerate(attributes):
        color = plt.cm.viridis(i / len(attributes))  # 使用颜色映射获取不同颜色
        plt.bar(attr, y[i], color=color, width = 0.1, label=f'{attr}')
    
    # resultPath = folder_path +  "/repeatability_test/metric_repeatability"
    # os.mkdir(resultPath) 
    
    diagram_name_pgf = analysis_8_metric+".pgf"
    diagram_name_png = analysis_8_metric+".png"
    diagram_name_pdf = analysis_8_metric+".pdf"
    # diagram_path_pgf = folder_path + "/accuracy_metrics_comparison/" + diagram_name_pgf
    # diagram_path_png = folder_path + "/accuracy_metrics_comparison/" + diagram_name_png
    # diagram_path_pdf = folder_path + "/accuracy_metrics_comparison/" + diagram_name_pdf
    diagram_path_pgf = folder_path + "/repeatability_test/" + diagram_name_pgf
    diagram_path_png = folder_path + "/repeatability_test/" + diagram_name_png
    diagram_path_pdf = folder_path + "/repeatability_test/" + diagram_name_pdf

    plt.legend()
    plt.savefig(diagram_path_pgf, dpi = 400)
    plt.savefig(diagram_path_png, dpi = 400)
    plt.savefig(diagram_path_pdf, dpi = 400)

    # usage 4

    mpl.rcParams['pdf.fonttype'] = mpl1
    mpl.rcParams['ps.fonttype'] = mpl2
    mpl.rcParams['font.family'] = mpl3
    mpl.rcParams['font.size'] = mpl4

  