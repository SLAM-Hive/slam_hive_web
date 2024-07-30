from aliyun_tools import Esc_Create
import os, time, paramiko

if __name__ == '__main__':

    #### 假设：
    # 主服务器以后部署成功，现在的操作是在主服务器上（先买一个周的服务器）
    # 部署好 docker + kubernetes（注意版本）
    # 做好一系列限制条件（见文档）
    # 1个数据集 + 1个算法镜像 （先在本地跑通这个实验）
    # 同时构建g一个image，用于后续的移植
    # 已经j创建好了work node 的初始镜像

    #### 1. 准备好流程所需要的全部参数
    client = Esc_Create.create_client(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
    
    # 1.1 master node相关：region（cn-zhangjiakou）；局域网IP；
    MASTER_REGION = "cn-zhangjiakou"
    MASTER_IP = ""
    
    # 1.2 账号相关：可用区，交换机（这些暂时写死成zhangjiakou，在账号中提前创建好了这些地域的交换机）
    zone_id_list = [] # 可用区list
    vswitch_list = [] # vswitch list
    instance_id_list_total = [] # all instance id
    # 获取当前地域的所有分区（eg：zhangjiakou ：zhangjiakou-a，zhangjiakou-b，zhangjiakou-c）
    describe_zones_resp = Esc_Create.describe_zones(client, MASTER_REGION)
    for i in range(len(describe_zones_resp)):
        zone_id_list.append(describe_zones_resp[i].zone_id)
    vswitch_list = Esc_Create.describe_vswitches(client, MASTER_REGION)
    
    # 1.3 work node相关：购买数量；局域网IP；型号（暂时写死，后续可以提供选择功能）
    # created instance number <= required_esc_number
    created_esc_number = 0
    required_esc_number = 2
    
    # 1.4 task所在的node 以及其他
    task_node = {}
    task_node.update({0: 0})
    task_node.update({1: 1})
    task_node.update({2: 0})
    task_node.update({3: 1})
    # 后续将该对应关系写入到配置文件中
    task_signal = "batch1"

    

    #### 2. 购买1个work node
    # 2.1 根据上述的参数，购买一个work node
    ####################################################################################
    disk_temp_dict = {}
    disk_temp_dict.update({"size": 128})
    disk_temp_dict.update({"category": 'cloud_essd'})
    disk_temp_dict.update({"disk_name": 'system_disk'})
    disk_temp_dict.update({"performance_level": 'PL1'})

    instance_temp_dict = {}
    instance_temp_dict.update({"region_id": MASTER_REGION})
    instance_temp_dict.update({"image_id": 'ubuntu_20_04_x64_20G_alibase_20230718.vhd'}) # TO CHANGE
    instance_temp_dict.update({"instance_type": 'ecs.u1-c1m1.2xlarge'})
    instance_temp_dict.update({"security_group_id": 'sg-8vbe4qm8ujcshr9xsqjm'})
    temp_instance_name = 'slam-hive_first_test_' + task_signal +'_0'
    instance_temp_dict.update({"instance_name": temp_instance_name})
    instance_temp_dict.update({"description": 'slam-hive_first_test_1'})
    instance_temp_dict.update({"internet_max_bandwidth_in": 1})
    instance_temp_dict.update({"internet_max_bandwidth_out": 1})
    temp_host_name = 'task-' + task_signal + '-0'
    instance_temp_dict.update({"host_name": temp_host_name})
    instance_temp_dict.update({"password": 'slam-hive1'})
    instance_temp_dict.update({"internet_charge_type": 'PayByTraffic'})
    # instance_temp_dict.update({"spot_price_limit": 5.0})
    instance_temp_dict.update({"instance_charge_type": 'PostPaid'})
    instance_temp_dict.update({"amount": 1})
    instance_temp_dict.update({"v_switch_id": vswitch_list[0]})
    ####################################################################################
    work_node1_id_list = Esc_Create.create_esc(client, disk_temp_dict, instance_temp_dict) # 1个
    # 2.2 等待节点运行就绪
    while not Esc_Create.check_instance_status(Esc_Create.describe_instance_status(client, instance_temp_dict['region_id'], work_node1_id_list)):
        time.sleep(2)
    # 2.3 master noden将：algo image、dataset、config等通过局域网传输到work node1
    instance_ids_str = '[\"' + work_node1_id_list[0] + '\"]'
    work_node1_infos = Esc_Create.describe_instances_info(client, MASTER_REGION, instance_ids_str)
    work_node1_inner_IP = work_node1_infos[0].vpc_attributes.vpc_attributes.private_ip_address.ip_address[0]
    trans = paramiko.Transport(
        sock=(work_node1_inner_IP,22)
    )
    trans.connect(
        username="root",
        password="slam-hive1"
    )
    # 通过ssh传输文件
    # ...

    
    # 2.4 加入master node所在的kubernetes集群
    # 应该要在work node的初始image中e写一个启动脚本；或者在master node中写一个启动脚本，然后传输过去 + ssh启动

    # 2.5 生成镜像
    #aliyun

    # 2.6 开始task

    #### 3. 购买 其余n-1个 work node
    # 3.1 依据2.5生成的image，创建剩余的work node
    # 3.2 等待节点运行就绪
    # 3.3 加入集群
    # 3.4 开始task

    #### 4. 将结果回传给master node
    # 4.1 结束
