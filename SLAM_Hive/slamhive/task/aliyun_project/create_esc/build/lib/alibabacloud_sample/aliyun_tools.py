# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import os
import sys, time

from typing import List

from alibabacloud_ecs20140526.client import Client as Ecs20140526Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ecs20140526 import models as ecs_20140526_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_console.client import Client as ConsoleClient
from alibabacloud_tea_util.client import Client as UtilClient


from Tea.core import TeaCore

from alibabacloud_darabonba_number.client import Client as NumberClient
from alibabacloud_darabonba_env.client import Client as EnvClient
from alibabacloud_darabonba_array.client import Client as ArrayClient


class Esc_Create:
    def __init__(self):
        pass

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
        region_id: str
    ) -> Ecs20140526Client:
        ## def xxx() -> xxx   to mark the type of the return value
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            # 必填，您的 AccessKey ID,
            access_key_id=access_key_id,
            # 必填，您的 AccessKey Secret,
            access_key_secret=access_key_secret
        )
        # Endpoint 请参考 https://api.aliyun.com/product/Ecs
        ## need to change
        ## config.endpoint = f'ecs.cn-zhangjiakou.aliyuncs.com'
        link_temp = 'ecs.' + region_id + '.aliyuncs.com'
        config.endpoint = link_temp
        return Ecs20140526Client(config)

    @staticmethod
    def create_esc(
        client, disk_parameter_dict, esc_parameter_dict
    ) -> List:
        # 请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID 和 ALIBABA_CLOUD_ACCESS_KEY_SECRET。
        # 工程代码泄露可能会导致 AccessKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html
        client = Esc_Create.create_client(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
        system_disk = ecs_20140526_models.RunInstancesRequestSystemDisk(
            size = disk_parameter_dict['size'], ##1
            category = disk_parameter_dict['category'],  ##2
            disk_name = disk_parameter_dict['disk_name'], ##3
            performance_level = disk_parameter_dict['performance_level'], ####4
        )
        run_instances_request = ecs_20140526_models.RunInstancesRequest(
            region_id = esc_parameter_dict['region_id'], ##1
            image_id = esc_parameter_dict['image_id'], ##2
            instance_type = esc_parameter_dict['instance_type'], ##3
            security_group_id = esc_parameter_dict['security_group_id'], ##4
            v_switch_id='vsw-8vb03rdujwwm1d5qal2gy',###
            instance_name = esc_parameter_dict['instance_name'], ##5
            description = esc_parameter_dict['description'], ##6
            internet_max_bandwidth_in = esc_parameter_dict['internet_max_bandwidth_in'],##7
            internet_max_bandwidth_out = esc_parameter_dict['internet_max_bandwidth_out'],##8
            host_name = esc_parameter_dict['host_name'],##9
            password = esc_parameter_dict['password'], ## 10
            # zone_id = '',
            internet_charge_type='PayByTraffic',
            # Object, 可选,
            system_disk=system_disk,
            spot_strategy='NoSpot',
            # spot_price_limit = esc_parameter_dict['spot_price_limit'], ##11
            io_optimized='optimized',
            amount = esc_parameter_dict['amount'] , ## 13
            min_amount=1,
            instance_charge_type = esc_parameter_dict['instance_charge_type'] ##12
        )
        runtime = util_models.RuntimeOptions()
        # 1.1 buy one server: work node1
        resp = client.run_instances_with_options(run_instances_request, runtime)
        ConsoleClient.log(UtilClient.to_jsonstring(resp))

        # instance id: list[]
        return resp.body.instance_id_sets.instance_id_set

    @staticmethod
    def describe_instance_status(
        client: Ecs20140526Client,
        region_id: str,
        instance_ids: List[str],
    ) -> List[str]:
        """
        查询实例状态
        """
        batch_size = 50
        all_size = len(instance_ids)
        now_start = 0
        all_instance_status_list = []
        while True:
            request = util_models.DescribeInstanceStatusRequest(
                region_id=region_id,
                instance_id=instance_ids[now_start: min(now_start + batch_size - 1, all_size - 1)],
                # 这里有个疑问：如果不设置分页值，可以返回全部吗
            )
            responces = client.describe_instance_status(request)
            instance_status_list = responces.body.instance_statuses.instance_status
            for i in range(len(instance_status_list)):
                all_instance_status_list.append(instance_id_list[i])
            now_start += 50
            if now_start >= all_size:
                break

        return instance_status_list
    

    @staticmethod
    def describe_zones(
        client,
        regionId,
    ) -> None:
        # 请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID 和 ALIBABA_CLOUD_ACCESS_KEY_SECRET。
        # 工程代码泄露可能会导致 AccessKey 泄露，并威胁账号下所有资源的安全性。以下代码示例使用环境变量获取 AccessKey 的方式进行调用，仅供参考，建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html
        # client = Esc_Create.create_client(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
        describe_zones_request = ecs_20140526_models.DescribeZonesRequest(
            region_id = regionId,
            instance_charge_type = 'PostPaid',
            verbose = False,
            accept_language = 'en-US'
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            resp = client.describe_zones_with_options(describe_zones_request, runtime)
            return resp.body.zones.zone
        except Exception as error:
            # 如有需要，请打印 error
            print(error)


    @staticmethod
    def describe_vswitches(
        client,
        regionId
    ) -> None:
        describe_vswitches_request = ecs_20140526_models.DescribeVSwitchesRequest(
            region_id=regionId,
            page_size=50
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            resp = client.describe_vswitches_with_options(describe_vswitches_request, runtime)
            return resp.body.v_switches.v_switch
        except Exception as error:
            # 如有需要，请打印 error
            # UtilClient.assert_as_string(error.message)
            print(error)


    def check_instance_status(instance_status_list):
        running_number = 0
        for i in range(len(instance_status_list)):
            if instance_status_list[i].status == "Running":
                running_number += 1
        if running_number == len(instance_status_list):
            return True
        else :
            return False


    @staticmethod
    def describe_instances_info(
        client,
        region_id,
        instance_ids_str
    ) -> None:
        # 请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID 和 ALIBABA_CLOUD_ACCESS_KEY_SECRET。
        # 工程代码泄露可能会导致 AccessKey 泄露，并威胁账号下所有资源的安全性。以下代码示例使用环境变量获取 AccessKey 的方式进行调用，仅供参考，建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html
        describe_instances_request = ecs_20140526_models.DescribeInstancesRequest(
            region_id=region_id,
            instance_ids=instance_ids_str
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            resp = client.describe_instances_with_options(describe_instances_request, runtime)
            return resp.body.instances.instance
        except Exception as error:
            # 如有需要，请打印 error
            print(error)
    
    @staticmethod
    def create_image(
        client,
        region_id,
        instance_id
    ) -> None:
        # 请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID 和 ALIBABA_CLOUD_ACCESS_KEY_SECRET。
        # 工程代码泄露可能会导致 AccessKey 泄露，并威胁账号下所有资源的安全性。以下代码示例使用环境变量获取 AccessKey 的方式进行调用，仅供参考，建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html
        create_image_request = ecs_20140526_models.CreateImageRequest(
            region_id = region_id,
            instance_id = instance_id
        )
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            resp = client.create_image_with_options(create_image_request, runtime)
            return resp.body.image_id
        except Exception as error:
            # 如有需要，请打印 error
            # UtilClient.assert_as_string(error.message)
            print(error)


region_id = 'cn-zhangjiakou'
client = Esc_Create.create_client(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'], region_id)
# instance_ids_str = '[\"' + "i-8vbb5p693rhnyupk2cq5" + '\"]'
# resp = Esc_Create.describe_instances_info(client, region_id, instance_ids_str)
# print(resp[0].vpc_attributes.private_ip_address.ip_address[0])
instance_id = "i-8vbb5p693rhnyupk2cq5"
image_id = Esc_Create.create_image(client, region_id, instance_id)
print(image_id)



# if __name__ == '__main__':
#     ###################################################################################################################################
#     ## 创建1台或者多台 instance

#     # Esc_Create.main(sys.argv[1:])
#     # 已知参数：地域 region_id；
#     # client：全局直接共用一个client
#     region_id = 'cn-zhangjiakou'
#     client = Esc_Create.create_client(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'], region_id)

#     # 可用区list
#     zone_id_list = []
#     # vswitch list
#     vswitch_list = []
#     # all instance id
#     instance_id_list_total = []
#     # created instance number <= required_esc_number
#     created_esc_number = 0
    
    

#     # 所需要的instance的总数量（通过分配的任务得到，实际能购买的instance的数量可能会小于所需数量）
#     # 设置最小购买数量：
#     #* 当所需量 > 库存量 > 最小需求量时，系统会按照库存量进行购买
#     #* 所以将最小需求量设置为1， 可保证购买的数量为min(所需量，库存量)
#     required_esc_number = 1
    

    

#     # print(Esc_Create.describe_zones('cn-zhangjiakou')[0].zone_id)
#     # 获取当前地域的所有分区（eg：zhangjiakou ：zhangjiakou-a，zhangjiakou-b，zhangjiakou-c）
#     describe_zones_resp = Esc_Create.describe_zones(client, region_id)
    
#     for i in range(len(describe_zones_resp)):
#         zone_id_list.append(describe_zones_resp[i].zone_id)
#         # print(zone_id_list[i])
    
#     vswitch_list = Esc_Create.describe_vswitches(client, region_id)
#     print(vswitch_list)
#     # for i in range(len(vswitch_list)):
#     #     print("vswitch_id:", vswitch_list[i].v_switch_id)
#     #     print("vpc_id", vswitch_list[i].vpc_id)
#     #     print("zone_id", vswitch_list[i].zone_id)
#     #     print()

#     for i in range(len(zone_id_list)):
#         now_need_to_buy_number = required_esc_number - created_esc_number
#         # 设置所要购买服务器的参数配置
#         disk_temp_dict = {}
#         disk_temp_dict.update({"size": 64})
#         disk_temp_dict.update({"category": 'cloud_essd'})
#         disk_temp_dict.update({"disk_name": 'system_disk'})
#         disk_temp_dict.update({"performance_level": 'PL1'})

#         instance_temp_dict = {}
#         instance_temp_dict.update({"region_id": region_id})
#         instance_temp_dict.update({"image_id": 'ubuntu_20_04_x64_20G_alibase_20230718.vhd'})
#         instance_temp_dict.update({"instance_type": 'ecs.u1-c1m1.2xlarge'})
#         instance_temp_dict.update({"security_group_id": 'sg-8vbe4qm8ujcshr9xsqjm'})
#         temp_instance_name = 'slam-hive_first_test_1_[' + created_esc_number + ",4]"
#         instance_temp_dict.update({"instance_name": temp_instance_name})
#         instance_temp_dict.update({"description": 'slam-hive_first_test_1'})
#         instance_temp_dict.update({"internet_max_bandwidth_in": 10})
#         instance_temp_dict.update({"internet_max_bandwidth_out": 10})
#         temp_host_name = 'task-1-[' + created_esc_number + ",4]"
#         instance_temp_dict.update({"host_name": temp_host_name})
#         instance_temp_dict.update({"password": 'slam-hive1'})
#         instance_temp_dict.update({"internet_charge_type": 'PayByTraffic'})
#         # instance_temp_dict.update({"spot_price_limit": 5.0})
#         instance_temp_dict.update({"instance_charge_type": 'PostPaid'})
#         instance_temp_dict.update({"amount": now_need_to_buy_number})
#         instance_temp_dict.update({"v_switch_id": ""})
#         # pass a dict, containing the required paramter (4 + 13)
#         # pass a dict, containing the required paramter (4 + 13)
        
#         # 遍历每个可用区，购买服务器，直到购买的数量满足要求 || 库存用完
        
#         instance_id_list = Esc_Create.create_esc(client, disk_temp_dict, instance_temp_dict)
#         created_esc_number += len(instance_id_list)
#         for i in range(len(created_esc_number)):
#             instance_id_list_total.append(instance_id_list[i])
#         if len(instance_id_list_total) == required_esc_number:
#             break
#     # now instance_id_list_total contains all instance that have bought (number may less than required_number)

#     # 等待实例创建成功
#     while not Esc_Create.check_instance_status(Esc_Create.describe_instance_status(client, instance_temp_dict['region_id'], instance_id_list)):
#         time.sleep(2)
    
#     print("all instance running") # 还没测试



    



