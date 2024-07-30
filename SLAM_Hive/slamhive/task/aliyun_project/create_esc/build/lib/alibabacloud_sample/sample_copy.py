# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import sys

from typing import List
from Tea.core import TeaCore

from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_darabonba_number.client import Client as NumberClient
from alibabacloud_tea_console.client import Client as ConsoleClient
from alibabacloud_darabonba_env.client import Client as EnvClient
from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ecs20140526 import models as ecs_models
from alibabacloud_darabonba_array.client import Client as ArrayClient


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        """
        创建实例（RunInstances） ->
        【批量】查询实例状态->
        修改实例属性->
        【批量】查询userdata->
        修改实例MetadataOptions->
        修改登录密码->
        【批量】实例关机->
        【批量】查询状态到stopped->
        【批量】实例开机->
        【批量】查询状态到running
        """
        region_id = args[0]
        instance_type = args[1]
        image_id = args[2]
        security_group_id = args[3]
        instance_name = args[4]
        description = args[5]
        zone_id = args[6]
        category = args[7]
        v_switch_id = args[8]
        # 创建ECS实例的数量
        amount_str = args[9]
        amount = 1
        if not UtilClient.equal_string(amount_str, ''):
            try:
                amount = NumberClient.parse_int(amount_str)
            except Exception as err:
                ConsoleClient.log('输入的 amount 不是1~100的数字! 已设置为默认值 1')
        # 预检请求
        # true：发送检查请求，不会创建实例。检查项包括是否填写了必需参数、请求格式、业务限制和ECS库存。如果检查不通过，则返回对应错误。如果检查通过，则返回DryRunOperation错误。
        # false：发送正常请求，通过检查后直接创建实例。
        dry_run_str = args[10]
        dry_run = True
        if UtilClient.equal_string(dry_run_str, 'false'):
            dry_run = False
        access_key_id = EnvClient.get_env('ACCESS_KEY_ID')
        access_key_secret = EnvClient.get_env('ACCESS_KEY_SECRET')
        client = Sample.create_client(access_key_id, access_key_secret, region_id)
        # 创建并与运行实例
        instance_ids = Sample.run_instances(instance_type, image_id, region_id, security_group_id, instance_name, description, zone_id, category, v_switch_id, amount, dry_run, client)
        # 等待实例创建成功
        UtilClient.sleep(2000)
        # 【批量】查询实例状态 查询状态为Running   因为修改实例属性时 实例不能处于创建中（Pending）或启动中（Starting）
        # 修改实例属性->
        instance_name_new = args[11]
        description_new = args[12]
        for instance_id in instance_ids:
            Sample.modify_instance_attribute(client, region_id, instance_id, instance_name_new, description_new)
        vnc_password = args[13]
        # 【批量】查询userdata->
        for instance_id in instance_ids:
            Sample.describe_user_data(client, region_id, instance_id)
            # 修改实例MetadataOptions->
            Sample.modify_instance_metadata_options(client, region_id, instance_id)
            # 修改登录密码->  输入的参数VncPassword必须为6位字符，包括大写字母、小写字母和数字
            Sample.modify_instance_vnc_passwd(client, region_id, instance_id, vnc_password)
        # 【批量】实例关机->
        Sample.stop_instances(client, region_id, instance_ids, False)
        # 【批量】查询状态到stopped->
        Sample.await_instance_status(client, region_id, instance_ids, 'Stopped')
        # 【批量】实例开机->
        Sample.start_instances(client, region_id, instance_ids, False)
        # 【批量】查询状态到running
        Sample.await_instance_status(client, region_id, instance_ids, 'Running')

    @staticmethod
    async def main_async(
        args: List[str],
    ) -> None:
        """
        创建实例（RunInstances） ->
        【批量】查询实例状态->
        修改实例属性->
        【批量】查询userdata->
        修改实例MetadataOptions->
        修改登录密码->
        【批量】实例关机->
        【批量】查询状态到stopped->
        【批量】实例开机->
        【批量】查询状态到running
        """
        region_id = args[0]
        instance_type = args[1]
        image_id = args[2]
        security_group_id = args[3]
        instance_name = args[4]
        description = args[5]
        zone_id = args[6]
        category = args[7]
        v_switch_id = args[8]
        # 创建ECS实例的数量
        amount_str = args[9]
        amount = 1
        if not UtilClient.equal_string(amount_str, ''):
            try:
                amount = NumberClient.parse_int(amount_str)
            except Exception as err:
                ConsoleClient.log('输入的 amount 不是1~100的数字! 已设置为默认值 1')
        # 预检请求
        # true：发送检查请求，不会创建实例。检查项包括是否填写了必需参数、请求格式、业务限制和ECS库存。如果检查不通过，则返回对应错误。如果检查通过，则返回DryRunOperation错误。
        # false：发送正常请求，通过检查后直接创建实例。
        dry_run_str = args[10]
        dry_run = True
        if UtilClient.equal_string(dry_run_str, 'false'):
            dry_run = False
        access_key_id = EnvClient.get_env('ACCESS_KEY_ID')
        access_key_secret = EnvClient.get_env('ACCESS_KEY_SECRET')
        client = await Sample.create_client_async(access_key_id, access_key_secret, region_id)
        # 创建并与运行实例
        instance_ids = await Sample.run_instances_async(instance_type, image_id, region_id, security_group_id, instance_name, description, zone_id, category, v_switch_id, amount, dry_run, client)
        # 等待实例创建成功
        await UtilClient.sleep_async(2000)
        # 【批量】查询实例状态 查询状态为Running   因为修改实例属性时 实例不能处于创建中（Pending）或启动中（Starting）
        # 修改实例属性->
        instance_name_new = args[11]
        description_new = args[12]
        for instance_id in instance_ids:
            await Sample.modify_instance_attribute_async(client, region_id, instance_id, instance_name_new, description_new)
        vnc_password = args[13]
        # 【批量】查询userdata->
        for instance_id in instance_ids:
            await Sample.describe_user_data_async(client, region_id, instance_id)
            # 修改实例MetadataOptions->
            await Sample.modify_instance_metadata_options_async(client, region_id, instance_id)
            # 修改登录密码->  输入的参数VncPassword必须为6位字符，包括大写字母、小写字母和数字
            await Sample.modify_instance_vnc_passwd_async(client, region_id, instance_id, vnc_password)
        # 【批量】实例关机->
        await Sample.stop_instances_async(client, region_id, instance_ids, False)
        # 【批量】查询状态到stopped->
        await Sample.await_instance_status_async(client, region_id, instance_ids, 'Stopped')
        # 【批量】实例开机->
        await Sample.start_instances_async(client, region_id, instance_ids, False)
        # 【批量】查询状态到running
        await Sample.await_instance_status_async(client, region_id, instance_ids, 'Running')

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
        region_id: str,
    ) -> EcsClient:
        config = open_api_models.Config()
        config.access_key_id = access_key_id
        config.access_key_secret = access_key_secret
        config.region_id = region_id
        return EcsClient(config)

    @staticmethod
    async def create_client_async(
        access_key_id: str,
        access_key_secret: str,
        region_id: str,
    ) -> EcsClient:
        config = open_api_models.Config()
        config.access_key_id = access_key_id
        config.access_key_secret = access_key_secret
        config.region_id = region_id
        return EcsClient(config)

    @staticmethod
    def run_instances(
        instance_type: str,
        image_id: str,
        region_id: str,
        security_group_id: str,
        instance_name: str,
        description: str,
        zone_id: str,
        category: str,
        v_switch_id: str,
        amount: int,
        dry_run: bool,
        client: EcsClient,
    ) -> List[str]:
        """
        创建并运行实例
        """
        request = ecs_models.RunInstancesRequest(
            region_id=region_id,
            instance_type=instance_type,
            image_id=image_id,
            security_group_id=security_group_id,
            instance_name=instance_name,
            description=description,
            zone_id=zone_id,
            v_switch_id=v_switch_id,
            amount=amount,
            dry_run=dry_run,
            system_disk=ecs_models.RunInstancesRequestSystemDisk(
                category=category
            )
        )
        ConsoleClient.log(f'--------创建实例开始-----------')
        responces = client.run_instances(request)
        ConsoleClient.log(f'-----------创建实例成功，实例ID:{UtilClient.to_jsonstring(responces.body.instance_id_sets.instance_id_set)}--------------')
        return responces.body.instance_id_sets.instance_id_set

    @staticmethod
    async def run_instances_async(
        instance_type: str,
        image_id: str,
        region_id: str,
        security_group_id: str,
        instance_name: str,
        description: str,
        zone_id: str,
        category: str,
        v_switch_id: str,
        amount: int,
        dry_run: bool,
        client: EcsClient,
    ) -> List[str]:
        """
        创建并运行实例
        """
        request = ecs_models.RunInstancesRequest(
            region_id=region_id,
            instance_type=instance_type,
            image_id=image_id,
            security_group_id=security_group_id,
            instance_name=instance_name,
            description=description,
            zone_id=zone_id,
            v_switch_id=v_switch_id,
            amount=amount,
            dry_run=dry_run,
            system_disk=ecs_models.RunInstancesRequestSystemDisk(
                category=category
            )
        )
        ConsoleClient.log(f'--------创建实例开始-----------')
        responces = await client.run_instances_async(request)
        ConsoleClient.log(f'-----------创建实例成功，实例ID:{UtilClient.to_jsonstring(responces.body.instance_id_sets.instance_id_set)}--------------')
        return responces.body.instance_id_sets.instance_id_set

    @staticmethod
    def await_instance_status(
        client: EcsClient,
        region_id: str,
        instance_ids: List[str],
        expect_instance_status: str,
    ) -> bool:
        """
        等待实例状态为 Running
        """
        time = 0
        flag = True
        while flag and NumberClient.lt(time, 10):
            flag = False
            instance_status_list = Sample.describe_instance_status(client, region_id, instance_ids)
            for instance_status in instance_status_list:
                if not UtilClient.equal_string(instance_status, expect_instance_status):
                    UtilClient.sleep(2000)
                    flag = True
            time = NumberClient.add(time, 1)
        return NumberClient.lt(time, 10)

    @staticmethod
    async def await_instance_status_async(
        client: EcsClient,
        region_id: str,
        instance_ids: List[str],
        expect_instance_status: str,
    ) -> bool:
        """
        等待实例状态为 Running
        """
        time = 0
        flag = True
        while flag and NumberClient.lt(time, 10):
            flag = False
            instance_status_list = await Sample.describe_instance_status_async(client, region_id, instance_ids)
            for instance_status in instance_status_list:
                if not UtilClient.equal_string(instance_status, expect_instance_status):
                    await UtilClient.sleep_async(2000)
                    flag = True
            time = NumberClient.add(time, 1)
        return NumberClient.lt(time, 10)

    @staticmethod
    def describe_instance_status(
        client: EcsClient,
        region_id: str,
        instance_ids: List[str],
    ) -> List[str]:
        """
        查询实例状态
        """
        request = ecs_models.DescribeInstanceStatusRequest(
            region_id=region_id,
            instance_id=instance_ids
        )
        ConsoleClient.log(f'实例: {instance_ids}, 查询状态开始。')
        responces = client.describe_instance_status(request)
        instance_status_list = responces.body.instance_statuses.instance_status
        ConsoleClient.log(f'实例: {instance_ids}, 查询状态成功。状态为: {UtilClient.to_jsonstring(instance_status_list)}')
        status_list = {}
        for instance_status in instance_status_list:
            status_list = ArrayClient.concat(status_list, [
                instance_status.status
            ])
        return status_list

    @staticmethod
    async def describe_instance_status_async(
        client: EcsClient,
        region_id: str,
        instance_ids: List[str],
    ) -> List[str]:
        """
        查询实例状态
        """
        request = ecs_models.DescribeInstanceStatusRequest(
            region_id=region_id,
            instance_id=instance_ids
        )
        ConsoleClient.log(f'实例: {instance_ids}, 查询状态开始。')
        responces = await client.describe_instance_status_async(request)
        instance_status_list = responces.body.instance_statuses.instance_status
        ConsoleClient.log(f'实例: {instance_ids}, 查询状态成功。状态为: {UtilClient.to_jsonstring(instance_status_list)}')
        status_list = {}
        for instance_status in instance_status_list:
            status_list = ArrayClient.concat(status_list, [
                instance_status.status
            ])
        return status_list

    @staticmethod
    def modify_instance_attribute(
        client: EcsClient,
        region_id: str,
        instance_id: str,
        instance_name: str,
        description: str,
    ) -> None:
        """
        修改实例属性  ModifyInstanceAttribute
        """
        request = ecs_models.ModifyInstanceAttributeRequest(
            instance_id=instance_id,
            instance_name=instance_name,
            description=description
        )
        ConsoleClient.log(f'修改实例: {instance_id}, 属性开始。')
        responce = client.modify_instance_attribute(request)
        ConsoleClient.log(f'修改实例: {instance_id}, 属性成功。requestId为：{responce.body.request_id}')

    @staticmethod
    async def modify_instance_attribute_async(
        client: EcsClient,
        region_id: str,
        instance_id: str,
        instance_name: str,
        description: str,
    ) -> None:
        """
        修改实例属性  ModifyInstanceAttribute
        """
        request = ecs_models.ModifyInstanceAttributeRequest(
            instance_id=instance_id,
            instance_name=instance_name,
            description=description
        )
        ConsoleClient.log(f'修改实例: {instance_id}, 属性开始。')
        responce = await client.modify_instance_attribute_async(request)
        ConsoleClient.log(f'修改实例: {instance_id}, 属性成功。requestId为：{responce.body.request_id}')

    @staticmethod
    def describe_user_data(
        client: EcsClient,
        region_id: str,
        instance_id: str,
    ) -> None:
        """
        【批量】查询userdata->   DescribeUserData
        """
        request = ecs_models.DescribeUserDataRequest(
            region_id=region_id,
            instance_id=instance_id
        )
        ConsoleClient.log(f'查询实例: {instance_id}, UserData 开始。')
        responce = client.describe_user_data(request)
        ConsoleClient.log(f'查询实例: {instance_id}, UserData 成功。结果为：{UtilClient.to_jsonstring(TeaCore.to_map(responce.body))}')

    @staticmethod
    async def describe_user_data_async(
        client: EcsClient,
        region_id: str,
        instance_id: str,
    ) -> None:
        """
        【批量】查询userdata->   DescribeUserData
        """
        request = ecs_models.DescribeUserDataRequest(
            region_id=region_id,
            instance_id=instance_id
        )
        ConsoleClient.log(f'查询实例: {instance_id}, UserData 开始。')
        responce = await client.describe_user_data_async(request)
        ConsoleClient.log(f'查询实例: {instance_id}, UserData 成功。结果为：{UtilClient.to_jsonstring(TeaCore.to_map(responce.body))}')

    @staticmethod
    def modify_instance_metadata_options(
        client: EcsClient,
        region_id: str,
        instance_id: str,
    ) -> None:
        """
        修改实例MetadataOptions->  ModifyInstanceMetadataOptions
        """
        request = ecs_models.ModifyInstanceMetadataOptionsRequest(
            region_id=region_id,
            instance_id=instance_id,
            http_endpoint='enabled'
        )
        ConsoleClient.log(f'修改实例: {instance_id}, MetadataOptions 开始。')
        responce = client.modify_instance_metadata_options(request)
        ConsoleClient.log(f'修改实例: {instance_id}, MetadataOptions 成功。requestId为：{responce.body.request_id}')

    @staticmethod
    async def modify_instance_metadata_options_async(
        client: EcsClient,
        region_id: str,
        instance_id: str,
    ) -> None:
        """
        修改实例MetadataOptions->  ModifyInstanceMetadataOptions
        """
        request = ecs_models.ModifyInstanceMetadataOptionsRequest(
            region_id=region_id,
            instance_id=instance_id,
            http_endpoint='enabled'
        )
        ConsoleClient.log(f'修改实例: {instance_id}, MetadataOptions 开始。')
        responce = await client.modify_instance_metadata_options_async(request)
        ConsoleClient.log(f'修改实例: {instance_id}, MetadataOptions 成功。requestId为：{responce.body.request_id}')

    @staticmethod
    def modify_instance_vnc_passwd(
        client: EcsClient,
        region_id: str,
        instance_id: str,
        vnc_password: str,
    ) -> None:
        """
        修改登录密码->  ModifyInstanceVncPasswd
        """
        request = ecs_models.ModifyInstanceVncPasswdRequest(
            region_id=region_id,
            instance_id=instance_id,
            vnc_password=vnc_password
        )
        ConsoleClient.log(f'修改实例: {instance_id}, VncPasswd 开始。')
        responce = client.modify_instance_vnc_passwd(request)
        ConsoleClient.log(f'修改实例: {instance_id}, VncPasswd 成功。requestId为：{responce.body.request_id}')

    @staticmethod
    async def modify_instance_vnc_passwd_async(
        client: EcsClient,
        region_id: str,
        instance_id: str,
        vnc_password: str,
    ) -> None:
        """
        修改登录密码->  ModifyInstanceVncPasswd
        """
        request = ecs_models.ModifyInstanceVncPasswdRequest(
            region_id=region_id,
            instance_id=instance_id,
            vnc_password=vnc_password
        )
        ConsoleClient.log(f'修改实例: {instance_id}, VncPasswd 开始。')
        responce = await client.modify_instance_vnc_passwd_async(request)
        ConsoleClient.log(f'修改实例: {instance_id}, VncPasswd 成功。requestId为：{responce.body.request_id}')

    @staticmethod
    def stop_instances(
        client: EcsClient,
        region_id: str,
        instance_ids: List[str],
        dry_run: bool,
    ) -> None:
        """
        【批量】实例关机->  StopInstances
        """
        request = ecs_models.StopInstancesRequest(
            region_id=region_id,
            instance_id=instance_ids,
            dry_run=dry_run
        )
        ConsoleClient.log(f'停止实例: {instance_ids},  开始。')
        responce = client.stop_instances(request)
        ConsoleClient.log(f'停止实例: {instance_ids},  成功。结果为：{UtilClient.to_jsonstring(TeaCore.to_map(responce.body))}')

    @staticmethod
    async def stop_instances_async(
        client: EcsClient,
        region_id: str,
        instance_ids: List[str],
        dry_run: bool,
    ) -> None:
        """
        【批量】实例关机->  StopInstances
        """
        request = ecs_models.StopInstancesRequest(
            region_id=region_id,
            instance_id=instance_ids,
            dry_run=dry_run
        )
        ConsoleClient.log(f'停止实例: {instance_ids},  开始。')
        responce = await client.stop_instances_async(request)
        ConsoleClient.log(f'停止实例: {instance_ids},  成功。结果为：{UtilClient.to_jsonstring(TeaCore.to_map(responce.body))}')

    @staticmethod
    def start_instances(
        client: EcsClient,
        region_id: str,
        instance_ids: List[str],
        dry_run: bool,
    ) -> None:
        """
        【批量】实例开机-> StartInstances
        """
        request = ecs_models.StartInstancesRequest(
            dry_run=dry_run,
            region_id=region_id,
            instance_id=instance_ids
        )
        responce = client.start_instances(request)
        ConsoleClient.log(f'启动实例: {instance_ids},  成功。结果为：{UtilClient.to_jsonstring(TeaCore.to_map(responce.body))}')

    @staticmethod
    async def start_instances_async(
        client: EcsClient,
        region_id: str,
        instance_ids: List[str],
        dry_run: bool,
    ) -> None:
        """
        【批量】实例开机-> StartInstances
        """
        request = ecs_models.StartInstancesRequest(
            dry_run=dry_run,
            region_id=region_id,
            instance_id=instance_ids
        )
        responce = await client.start_instances_async(request)
        ConsoleClient.log(f'启动实例: {instance_ids},  成功。结果为：{UtilClient.to_jsonstring(TeaCore.to_map(responce.body))}')


# if __name__ == '__main__':
#     Sample.main(sys.argv[1:])
