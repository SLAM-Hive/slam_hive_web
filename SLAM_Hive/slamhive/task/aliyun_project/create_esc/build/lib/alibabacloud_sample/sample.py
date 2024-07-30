# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import os
import sys

from typing import List

from alibabacloud_ecs20140526.client import Client as Ecs20140526Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ecs20140526 import models as ecs_20140526_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_console.client import Client as ConsoleClient
from alibabacloud_tea_util.client import Client as UtilClient


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
    ) -> Ecs20140526Client:
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
        config.endpoint = f'ecs.cn-zhangjiakou.aliyuncs.com'
        return Ecs20140526Client(config)

    @staticmethod
    def create_client_with_sts(
        access_key_id: str,
        access_key_secret: str,
        security_token: str,
    ) -> Ecs20140526Client:
        """
        使用STS鉴权方式初始化账号Client，推荐此方式。
        @param access_key_id:
        @param access_key_secret:
        @param security_token:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            # 必填，您的 AccessKey ID,
            access_key_id=access_key_id,
            # 必填，您的 AccessKey Secret,
            access_key_secret=access_key_secret,
            # 必填，您的 Security Token,
            security_token=security_token,
            # 必填，表明使用 STS 方式,
            type='sts'
        )
        # Endpoint 请参考 https://api.aliyun.com/product/Ecs
        config.endpoint = f'ecs.cn-zhangjiakou.aliyuncs.com'
        return Ecs20140526Client(config)

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        # 请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID 和 ALIBABA_CLOUD_ACCESS_KEY_SECRET。
        # 工程代码泄露可能会导致 AccessKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html
        client = Sample.create_client(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
        system_disk = ecs_20140526_models.RunInstancesRequestSystemDisk(
            size='64',
            category='cloud_essd',
            disk_name='system_disk',
            performance_level='PL1',
            auto_snapshot_policy_id=''
        )
        run_instances_request = ecs_20140526_models.RunInstancesRequest(
            region_id='cn-zhangjiakou',
            image_id='ubuntu_20_04_x64_20G_alibase_20230815.vhd',
            image_family='',
            instance_type='ecs.u1-c1m1.2xlarge',
            security_group_id='sg-8vbe4qm8ujcshr9xsqjm',
            v_switch_id='',
            instance_name='slam-hive_first_test_1',
            description='slam-hive_first_test_1',
            internet_max_bandwidth_in=1,
            internet_max_bandwidth_out=1,
            host_name='task_1',
            password='',
            zone_id='',
            internet_charge_type='PayByTraffic',
            # Object, 可选,
            system_disk=system_disk,
            spot_strategy='NoSpot',
            spot_price_limit=0.97,
            io_optimized='none',
            amount=1,
            min_amount=1,
            instance_charge_type='PostPaid'
        )
        runtime = util_models.RuntimeOptions()
        resp = client.run_instances_with_options(run_instances_request, runtime)
        ConsoleClient.log(UtilClient.to_jsonstring(resp))

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        # 请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID 和 ALIBABA_CLOUD_ACCESS_KEY_SECRET。
        # 工程代码泄露可能会导致 AccessKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html
        client = Sample.create_client(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
        system_disk = ecs_20140526_models.RunInstancesRequestSystemDisk(
            size='64',
            category='cloud_essd',
            disk_name='system_disk',
            performance_level='PL1',
            auto_snapshot_policy_id=''
        )
        run_instances_request = ecs_20140526_models.RunInstancesRequest(
            region_id='cn-zhangjiakou',
            image_id='ubuntu_20_04_x64_20G_alibase_20230815.vhd',
            image_family='',
            instance_type='ecs.u1-c1m1.2xlarge',
            security_group_id='sg-8vbe4qm8ujcshr9xsqjm',
            v_switch_id='',
            instance_name='slam-hive_first_test_1',
            description='slam-hive_first_test_1',
            internet_max_bandwidth_in=1,
            internet_max_bandwidth_out=1,
            host_name='task_1',
            password='',
            zone_id='',
            internet_charge_type='PayByTraffic',
            # Object, 可选,
            system_disk=system_disk,
            spot_strategy='NoSpot',
            spot_price_limit=0.97,
            io_optimized='none',
            amount=1,
            min_amount=1,
            instance_charge_type='PostPaid'
        )
        runtime = util_models.RuntimeOptions()
        resp = await client.run_instances_with_options_async(run_instances_request, runtime)
        ConsoleClient.log(UtilClient.to_jsonstring(resp))


if __name__ == '__main__':
    Sample.main(sys.argv[1:])
