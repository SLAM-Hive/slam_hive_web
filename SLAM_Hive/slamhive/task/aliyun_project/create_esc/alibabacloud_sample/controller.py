from slamhive.task.aliyun_project.create_esc.alibabacloud_sample.aliyun_tools import Esc_Create
import os, time, paramiko, yaml
from kubernetes import config
from kubernetes import client as kube_client

from slamhive import app

from slamhive.models import Algorithm, MappingTaskConfig, ParameterValue, AlgoParameter, Dataset, CombMappingTaskConfig, GroupMappingTaskConfig


def put_all_files_in_remote_dir(sftp, local_dir, remote_dir):

    # create folder in local path
    flag = True
    try:
        sftp.stat(remote_dir)
    except IOError:
        flag = False
    
    if not flag: # not exists
        sftp.mkdir(remote_dir)


    # 去掉路径字符串最后的字符'/'，如果有的话
    if remote_dir[-1] == '/':
        remote_dir = remote_dir[0:-1]
    if local_dir[-1] == '/':
        local_dir = local_dir[0:-1]

    # 获取当前指定目录下的所有目录及文件，包含属性值
    files = os.listdir(local_dir)
    for x in files:
        filename = local_dir + '/' + x
        # 如果是目录，则递归处理该目录，这里用到了stat库中的S_ISDIR方法，与linux中的宏的名字完全一致
        if os.path.isdir(filename):
            put_all_files_in_remote_dir(sftp, filename, remote_dir + '/' + x)
        else:
            # get
            sftp.put(filename, remote_dir + '/' + x)

class Aliyun_controller:
    # 根据需求服务器的数量，购买服务器并配置好服务器，返回实际购买的服务器数量
    

    # 删除work node
    # 删除image
    # 将节点从k8s集群中删除
    @staticmethod
    def after_process(
        MASTER_REGION,
        instance_id_list,
        image_id,
        task_signal
    ):
        config.load_kube_config()
        v1 = kube_client.CoreV1Api()
        # temp_host_name = 'task-' + task_signal + '-0000'
        nodes = v1.list_node().items
        k8s_node_name_list = []
        for i in range(len(nodes)):
            # print(nodes[i].metadata.name)
            # print(nodes[i].status.conditions[len(nodes[i].status.conditions) - 1].type)
            if nodes[i].metadata.name.split('-')[1] == task_signal:
                k8s_node_name_list.append(nodes[i].metadata.name)
        
        print(k8s_node_name_list)
        for i in range(len(k8s_node_name_list)):
            v1.delete_node(k8s_node_name_list[i])
            while True:
                check_delete = True
                temp_nodes = v1.list_node().items
                for j in range(len(temp_nodes)):
                    if k8s_node_name_list[i] == temp_nodes[j].metadata.name:
                        check_delete = False
                        break
                if check_delete:
                    print(k8s_node_name_list[i], "deleted")
                    break
                else :
                    time.sleep(0.1)
        print("all node remove from the k8s")

        client = Esc_Create.create_client(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'], MASTER_REGION)

        for i in range(len(instance_id_list)):
            Esc_Create.delete_instance(client, instance_id_list[i])
        time.sleep(1)

        Esc_Create.delete_image(client, image_id, MASTER_REGION)
        time.sleep(1)
        print("release all the work nodes and generated iamge")

    @staticmethod
    def prepare_process(
        MASTER_REGION, # 需要创建的服务器的数量
        MASTER_IP, # master node IP
        required_esc_number, # 需要购买的服务器数量
        task_signal, # batch task 的编号：batchxxx

        batch_task_id, # /SLAM-Hive/slam-hive-results/batch_mappingtask/batch_task_id
        work_node_image_id,
        final_node_template, final_config_node, final_task_node, template_algo_dict, template_dataset_dict, template_number, node_number, aliyun_configuration
    ):
        #### 1. 准备好流程所需要的全部参数
        print("batch task start time",time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
        
        # 1.1 master node相关：region（cn-zhangjiakou）；局域网IP；
        client = Esc_Create.create_client(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'], MASTER_REGION)
####
        # 1.2 账号相关：可用区，交换机（这些暂时写死成zhangjiakou，在账号中提前创建好了这些地域的交换机）
        zone_id_list = [] # 可用区list
        vswitch_list = [] # vswitch list
        instance_id_list_total = [] # all instance id
        # 获取当前地域的所有分区（eg：zhangjiakou ：zhangjiakou-a，zhangjiakou-b，zhangjiakou-c）
        describe_zones_resp = Esc_Create.describe_zones(client, MASTER_REGION)
        for i in range(len(describe_zones_resp)):
            zone_id_list.append(describe_zones_resp[i].zone_id)
        vswitch_list = Esc_Create.describe_vswitches(client, MASTER_REGION)
####1  
        # 1.3 work node相关：购买数量；局域网IP；型号（暂时写死，后续可以提供选择功能）
        # created instance number <= required_esc_number
        created_esc_number = 0

        #### 2. 购买1个work node(修改：购买指定数量的初始work node)
        # 2.1 根据上述的参数，购买一个work node
        ####################################################################################
        # 暂时先把参数写死，便于测试

        # 因为命名的原因 需要创建多次

        init_work_node_id_list = []
        start_node_index_of_each_template = []

        for i in range(template_number):

            final_node_template
            # 找到template相同的node中，编号最小的
            init_node_index = 99999
            for key, value in final_node_template.items():
                if value == i:
                    init_node_index = min(init_node_index, key)
            start_node_index_of_each_template.append(init_node_index)
            disk_temp_dict = {}
            disk_temp_dict.update({"size": int(aliyun_configuration['disk_size'])})
            disk_temp_dict.update({"category": aliyun_configuration['disk_category']})
            disk_temp_dict.update({"disk_name": 'system_disk'})
            disk_temp_dict.update({"performance_level": aliyun_configuration['disk_performance_level']}) ##
            instance_temp_dict = {}
            instance_temp_dict.update({"region_id": MASTER_REGION})
            # instance_temp_dict.update({"image_id": 'ubuntu_20_04_x64_20G_alibase_20230718.vhd'}) # TO CHANGE
            instance_temp_dict.update({"image_id": aliyun_configuration['instance_image_id']}) # TO CHANGE
            # instance_temp_dict.update({"instance_type": 'ecs.u1-c1m1.2xlarge'}) # 4核8GB
            instance_temp_dict.update({"instance_type": aliyun_configuration['instance_type']}) # 4核8GB
            # instance_temp_dict.update({"instance_type": 'ecs.e-c1m1.large'})
            instance_temp_dict.update({"security_group_id": aliyun_configuration['instance_security_group_id']})
            # temp_instance_name = 'slam-hive_first_test_' + task_signal +'_0000'
            temp_instance_name = 'slam-hive_first_test_' + task_signal +'_[' + str(init_node_index) + ",4]"
            instance_temp_dict.update({"instance_name": temp_instance_name})
            instance_temp_dict.update({"description": 'slam-hive_first_test_1'})
            instance_temp_dict.update({"internet_max_bandwidth_in": 1})
            instance_temp_dict.update({"internet_max_bandwidth_out": 1})
            # temp_host_name = 'task-' + task_signal + '-0000'
            temp_host_name = 'task-' + task_signal + '-[' + str(init_node_index) + ",4]"
            instance_temp_dict.update({"host_name": temp_host_name})
            instance_temp_dict.update({"password": 'slam-hive1'})
            instance_temp_dict.update({"internet_charge_type": 'PayByTraffic'})
            # instance_temp_dict.update({"spot_price_limit": 5.0})
            instance_temp_dict.update({"instance_charge_type": 'PostPaid'})
            instance_temp_dict.update({"amount": 1})   ###################### 购买的数量：template_number
            instance_temp_dict.update({"v_switch_id": vswitch_list[0]})
            ####################################################################################

            ## 原来：work_node0_id_list = 存储一个work node的id
            ## 现在：init_work_node_id_list = 存储template_number个work node的id 

            # work_node0_id_list = Esc_Create.create_esc(client, disk_temp_dict, instance_temp_dict) # 多个
            try:
                init_work_node_id_list0 = Esc_Create.create_esc(client, disk_temp_dict, instance_temp_dict)
            except Exception as error:
                print(error)
                return "error",1,1,1
            init_work_node_id_list.append(init_work_node_id_list0[0])

        for i in range(len(init_work_node_id_list)):
            instance_id_list_total.append(init_work_node_id_list)
            print("init work node:", init_work_node_id_list) ##################################### i下次记得看这个打印
####        
        
        time.sleep(5)
        # 2.2 等待节点运行就绪
        # work_node0_id_list = ["i-8vb4cw3ep9it52c5d0i6"] # TO DELETE
        # instance_id_list_total.append("i-8vb4cw3ep9it52c5d0i6") # TO DELETE
        # instance_id_list_total.append("i-8vbh7zy8amprtqovgh6v") # TO DELETE
####1
        while not Esc_Create.check_instance_status(Esc_Create.describe_instance_status(client, MASTER_REGION, work_node0_id_list)):
            #该函数能判断多个实例的status
            time.sleep(2)
            print("starting")
        print("buy init node OK")
        time.sleep(2)
        #print("end time:",time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
        # 2.3 master noden将：algo image、dataset、config等通过局域网传输到work node1

        #先写成for循环，串行n传输；之后可以改成并行传输maybe
        # TODO
        ######################################
        ## transfer resources to init nodes ##
        ######################################

        image_id_list = [] # 用来判断image的创建情况

        for init_node_number in range(template_number):
            #init_node_number == template_index

            print("work node" + str(init_node_number) + " transfer start time",time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
            instance_ids_str = '[\"' + init_work_node_id_list[init_node_number] + '\"]'
            work_node_infos = []
            while True:
                work_node_infos = Esc_Create.describe_instances_info(client, MASTER_REGION, instance_ids_str)
                if len(work_node_infos) != 0:
                    break
                time.sleep(0.5)
                # print(work_node0_infos[0].vpc_attributes)
            work_node_inner_IP = work_node_infos[0].vpc_attributes.private_ip_address.ip_address[0]
            print("work node inner IP:", work_node_inner_IP)
            time.sleep(5)
            while True:
                try:
                    # 可能出现连接失败的情况：等待连接成功
                    time.sleep(2)
                    trans = paramiko.Transport(
                        sock=(work_node_inner_IP,10000) ####################### TODO ssh的端口号需要double check
                    )
                    trans.connect(
                        username="root",
                        password="slam-hive1"
                    )
                    sftp = paramiko.SFTPClient.from_transport(trans) #############3\

                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(hostname=work_node0_inner_IP, port=10000, username='root', password='slam-hive1')
                    break
                except Exception as error:
                    print(error)
            time.sleep(1)
            trans = paramiko.Transport(
                sock=(work_node0_inner_IP,10000)
            )
            trans.connect(
                username="root",
                password="slam-hive1"
            )
            sftp = paramiko.SFTPClient.from_transport(trans) #############3\

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=work_node0_inner_IP, port=10000, username='root', password='slam-hive1')

            print("start to transfer...")
            # 通过ssh传输文件
            # ...
            # /SLAM-Hive/slam-hive-results/batch_mappingtask/task_id
            src_batch_mappingtask_path = "/slam_hive_results/batch_mappingtask/" + str(batch_task_id)
            dest_batch_mappingtask_path = "/SLAM-Hive/slam_hive_results/batch_mappingtask/" + str(batch_task_id)
            # /SLAM-Hive/slam-hive-algos/xxxalgo
            put_all_files_in_remote_dir(sftp ,src_batch_mappingtask_path, dest_batch_mappingtask_path)
            print("transfer batch_mappingtask finish")



            # slam_hive_controller
            src_slam_hive_controller_path = "/slam_hive_controller"
            dest_slam_hive_controller_path = "/SLAM-Hive/slam_hive_controller"
            put_all_files_in_remote_dir(sftp, src_slam_hive_controller_path, dest_slam_hive_controller_path)
            print("transfer slam_hive_controller finish")

            # algo + dataset

            # 此处认为：所有的task均使用同一个dataset和algo
            # 现在不这么认为了，需要搞清楚自己所需要的资源
            subTask_id_list = []
            subTaskConfig_id_list = []
            with open(os.path.join(src_batch_mappingtask_path, "subTask_Aliyun.yaml"), 'r', encoding = 'utf-8') as f:
                content = yaml.load(f, Loader=yaml.FullLoader)
                # subTaskConfig_id_list = content.split('\n')[0].split(',')
                # subTask_id_list = content.split('\n')[1].split(',')
                node_template_dict = content['node_template']
                current_nodes_list = []
                for key, value in node_template_dict.items():
                    if value == init_node_number:
                        current_nodes_list.append(key)

                subTask_id_dict = content['task_node']
                for key, value in subTask_id_dict.items():
                    if value in current_nodes_list:
                        subTask_id_list.append(key)
                subTaskConfig_id_dict = content['config_node']
                for key, value in subTaskConfig_id_dict.items():
                    if value in current_nodes_list:
                        subTaskConfig_id_list.append(key)

            # transfer all results(包含了该模版i对应的所有node的所有task，eg：1个模版 4个node 10个task，那么其中就包含10次传输)
            for i in range(len(subTask_id_list)):
                src_results_path = '/slam_hive_results/mapping_results/' + subTask_id_list[i]
                dest_results_path = '/SLAM-Hive/slam_hive_results/mapping_results/' + subTask_id_list[i]
                put_all_files_in_remote_dir(sftp, src_results_path, dest_results_path)
            print("transfer mapping_results finish")
            
            temp_task_id = subTask_id_list[0]
            # 现在不需要config来判断需要传输的算法镜像和dataset


            # 下面获取configname的操作 是为了得知需要传输的algo和dataset；现在通过参数i已知
            # 楼下整个传输过程修改
            # copy algo and dataset

            #algo
            algo_id_list = template_algo_dict[init_node_number]
            algo_dest_path_list = []
                # value存储了template[key]对应的所有algo的id
            for algo_id in algo_id_list:
                algo = Algorithm.query.get(algo_id) 
                algo_imageTag = algo.imageTag


                # store the image.tar in the related algo folder
                algo_src_path = os.path.join("/slam_hive_algos", algo_imageTag)
                algo_dest_path = os.path.join("/SLAM-Hive/slam_hive_algos", algo_imageTag)
                algo_dest_path_list.append(algo_dest_path)
                print("------ put algo folder "+ algo_imageTag +" to template "+ str(init_node_number) +"------")
                put_all_files_in_remote_dir(sftp, algo_src_path, algo_dest_path)
            
                # load the images
                # os.system("docker load < " + algo_dest_path + "/image.tar"
                print("------ successful ------")
                stdin, stdout, stderr = ssh.exec_command('python3 ' + algo_dest_path + "/docker_loader.py")
                # print(stdout.read())
                # print(stderr.read())
                print("loading the image...")
            
            dataset_id_list = template_dataset_dict[init_node_number]
            for dataset_id in dataset_id_list:
                dataset = Dataset.query.get(dataset_id) 
                dataset_name = dataset.name
                dataset_src_path = os.path.join("/slam_hive_datasets", dataset_name)
                dataset_dest_path = os.path.join("/SLAM-Hive/slam_hive_datasets", dataset_name)
                print("------ put dataset folder ------")
                put_all_files_in_remote_dir(sftp, dataset_src_path, dataset_dest_path)

            print("------ successful ------")
            # waiting docker loader


            while True:
                time.sleep(5)
                #flag = True
                flag_number = 0
                try:
                    for j in range(len(algo_dest_path_list)):
                        sftp.stat(algo_dest_path + "/docker_loader_finish")
                        flag_number += 1
                except IOError:
                    # flag = False
                    pass
                
                # if flag: # not exists
                if flag_number == len(algo_dest_path_list):
                    print("docker loader finish")
                    break
            print("work node " + str(init_node_number) + " transfer ok")

            print("work node transfer end time",time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
        
            # 下面的一些部分应该也要写到for循环里

            # # 2.4 生成镜像
            # #aliyun


            # Esc_Create.stop_instances(client, MASTER_REGION, work_node0_id_list) ########### 这里写的很奇怪 按理说应该是id 但是我传入了列表
            # for j in range(len(init_work_node_id_list)):
            #     Esc_Create.stop_instances(client, MASTER_REGION, init_work_node_id_list[j])
            # 停止当前node
            time.sleep(1)
            Esc_Create.stop_instances(client, MASTER_REGION, init_work_node_id_list[init_node_number])
            temp_instance_list = []
            temp_instance_list.append(init_work_node_id_list[init_node_number])
            while not Esc_Create.check_instance_status_stopped(Esc_Create.describe_instance_status(client, MASTER_REGION, temp_instance_list)):
                time.sleep(2)
                print("stopping")
            print("work node stop OK")
            time.sleep(2)

        # waiting the esc stopped

            ##################
            # 生成image 前 先停机
            ####################

            ################################################################
            ## 现在生成的image的数量不止一个, 但是在这个的外层循环中，还是1个image ##
            ## 变化：阻塞判断image生成情况的地方，需要移动到循环外面
            ###############################

            # work_node_batch999_0_image
            temp_image_name = "work_node_" + task_signal + "_" + str(init_node_number) + "_image"
            print("start generating the image " + temp_image_name)
            print("image generate start time",time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
            image_id = Esc_Create.create_image(
                client = client,
                region_id = MASTER_REGION,
                instance_id = work_node0_id_list[0],
                image_name = temp_image_name,
            )
            image_id_list.append(image_id)

        # for循环结束：循环外等待所有image创建完成



        # image create test
        time.sleep(5)
        while True:
            res = Esc_Create.describe_status_image(client, MASTER_REGION, "Creating") # 这个benlai接口有问题
            res1 = Esc_Create.describe_status_image(client, MASTER_REGION, "Available")
            ready_number = 0
            total_number = 0
            # 判断每一个image
            for i in range(len(image_id_list)):
                for j in range(len(res)):
                    if image_id_list[i] == res[j].image_id:
                        print(res[j].status,"process:",res[j].progress)
                        this_status = 0
                        total_number += 1
                        for k in range(len(res1)):
                            if image_id_list[i] == res1[k].image_id:
                                this_status = 1 # 已经n创建完成
                                break
                        if this_status == 1:
                            ready_number += 1
                                
                        # ready_number += 1   
            print()
            if ready_number == len(image_id_list):
                break
            
            if total_number != len(image_id_list):
                print("aliyun bug")
                break
            time.sleep(10)

        print("image all generate ok")
        print("image generate end time:",time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
        
       
        ############
        ## 开机
            ############
        for i in range(template_number):
            Esc_Create.start_instance(client, init_work_node_id_list[i])
        time.sleep(5)
        while not Esc_Create.check_instance_status(Esc_Create.describe_instance_status(client, MASTER_REGION, init_work_node_id_list)):
            time.sleep(2)
            print("starting")
        print("image work node restart OK")

        # image_id = 'm-8vbh7zy8amprtgtqunrb' # TO DELETE

        # #### 3. 购买 其余n-1个 work node
        # # 3.1 依据2.5生成的image，创建剩余的work node
####1
        created_esc_number = template_number # node 0

        print("require number:", required_esc_number, "created number:", created_esc_number)


        for template_index in range(template_number):

            now_create_esc_number = 1
            now_required_esc_number = 0
            required_esc_id_list = []
            for key, value in final_node_template.items():
                if value == template_index:
                    now_required_esc_number += 1
                    required_esc_id_list.append(key)
            
            start_node_index = start_node_index_of_each_template[template_index]

            for i in range(len(zone_id_list)):
                now_need_to_buy_number = now_required_esc_number - now_created_esc_number
                # 设置所要购买服务器的参数配置
                disk_temp_dict = {}
                disk_temp_dict.update({"size": int(aliyun_configuration['disk_size'])})
                disk_temp_dict.update({"category": aliyun_configuration['disk_category']})
                disk_temp_dict.update({"disk_name": 'system_disk'})
                disk_temp_dict.update({"performance_level": aliyun_configuration['disk_performance_level']}) ##

                instance_temp_dict = {}
                instance_temp_dict.update({"region_id": MASTER_REGION})
                instance_temp_dict.update({"image_id": aliyun_configuration['instance_image_id']}) # TO CHANGE
                instance_temp_dict.update({"instance_type": aliyun_configuration['instance_type']}) # 4核8GB
                instance_temp_dict.update({"security_group_id": aliyun_configuration['instance_security_group_id']})
                # temp_instance_name = 'slam-hive_first_test_1_[' + created_esc_number + ",4]"
                temp_instance_name = 'slam-hive_first_test_' + task_signal +'_[' + str(start_node_index + now_create_esc_number) + ",4]"
                instance_temp_dict.update({"instance_name": temp_instance_name})
                instance_temp_dict.update({"description": 'slam-hive_first_test_1'})
                instance_temp_dict.update({"internet_max_bandwidth_in": 1})
                instance_temp_dict.update({"internet_max_bandwidth_out": 1})
                # temp_host_name = 'task-1-[' + created_esc_number + ",4]"
                temp_host_name = 'task-' + task_signal + '-[' + str(start_node_index + now_create_esc_number) + ",4]"
                instance_temp_dict.update({"host_name": temp_host_name})
                instance_temp_dict.update({"password": 'slam-hive1'})
                instance_temp_dict.update({"internet_charge_type": 'PayByTraffic'})
                # instance_temp_dict.update({"spot_price_limit": 5.0})
                instance_temp_dict.update({"instance_charge_type": 'PostPaid'})
                instance_temp_dict.update({"amount": now_need_to_buy_number})
                instance_temp_dict.update({"v_switch_id": ""})
                # pass a dict, containing the required paramter (4 + 13)
                # pass a dict, containing the required paramter (4 + 13)
                
                # 遍历每个可用区，购买服务器，直到购买的数量满足要求 || 库存用完
                
                instance_id_list = Esc_Create.create_esc(client, disk_temp_dict, instance_temp_dict)
                now_created_esc_number += len(instance_id_list)
                for i in range(len(instance_id_list)):
                    instance_id_list_total.append(instance_id_list[i])
                if now_created_esc_number == now_required_esc_number:
                    break
        # now instance_id_list_total contains all instance that have bought (number may less than required_number)
####
        # 等待实例创建成功
        # # 3.2 等待节点运行就绪
        # instance_id_list_total.append("i-8vbgm940ya8e50b7tksn")
        print(instance_id_list_total)
        time.sleep(5)
        while not Esc_Create.check_instance_status(Esc_Create.describe_instance_status(client, MASTER_REGION, instance_id_list_total)):
            time.sleep(2)
        
        print("all instance running") #
        print("all instance running time:",time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
        real_esc_number = len(instance_id_list_total)
        # 应该是等于node number的
##################################### 理论上后面a都一样了 double check一下
        # # 3.3 加入集群
        inner_IP_list = []
        end_instance = min(real_esc_number - 1, 99)
        instance_ids_str = '['
        for i in range(real_esc_number):
            if i == end_instance:
                instance_ids_str += "\"" + instance_id_list_total[i] + "\""
                instance_ids_str += ']'
                work_node_infos = Esc_Create.describe_instances_info(client, MASTER_REGION, instance_ids_str)
                #$ print(work_node0_infos[0].vpc_attributes)
                # work_node0_inner_IP = work_node0_infos[0].vpc_attributes.private_ip_address.ip_address[0]
                for work_node_info in work_node_infos:
                    inner_IP_list.append(work_node_info.vpc_attributes.private_ip_address.ip_address[0])
                end_instance = min(100 + end_instance, real_esc_number - 1)
                instance_ids_str = '['
                    
            else:
                instance_ids_str += "\"" + instance_id_list_total[i] + "\", "
            
        print(inner_IP_list)
####
        # inner_IP_list = ['172.17.248.32', '172.17.248.31'] ## TO DELETE
        # real_esc_number = 2 ## TO DELETE
        for i in range(real_esc_number):
            while True:
                try:
                    time.sleep(0.1)
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(hostname=inner_IP_list[i], port=10000, username='root', password='slam-hive1')
                    kubeadm_join_command = app.config['kubernetes_join_command']
                    # print(kubeadm_join_command)
                    # 加入集群
                    ssh.exec_command(kubeadm_join_command)
                    # cadvisor启动
                    # ssh.exec_command("docker-compose -f /home/docker-compose.yml up")
                    break
                except Exception as error:
                    pass

        print("command kubeadm join finish")
        time.sleep(5)
        config.load_kube_config()
        v1 = kube_client.CoreV1Api()
        
        ready_node_number = 0 
        # temp_host_name = 'task-' + task_signal + '-0000'
        # task-batch999-0000
        while True:
            ready_node_number = 0 
            nodes = v1.list_node().items
            for i in range(len(nodes)):
                # print(nodes[i].metadata.name)
                # print(nodes[i].status.conditions[len(nodes[i].status.conditions) - 1].type)
                if nodes[i].metadata.name.split('-')[1] == task_signal:
                    if nodes[i].status.conditions[len(nodes[i].status.conditions) - 1].type == 'Ready':
                        ready_node_number += 1
            if ready_node_number == real_esc_number: # include master node
                break
            time.sleep(5)
        print("all work nodes joined the kubernetes cluster!")
        print("all work nodes joined the kubernetes cluster time:",time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

        for i in range(real_esc_number):
            while True:
                try:
                    time.sleep(0.1)
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(hostname=inner_IP_list[i], port=10000, username='root', password='slam-hive1')
                    # cadvisor启动
                    ssh.exec_command("docker-compose -f /home/docker-compose.yml up")
                    break
                except Exception as error:
                    pass
        print("all work nodes have the cadvisor")
        time.sleep(5)

        for i in range(real_esc_number):
            while True:
                try:
                    time.sleep(0.1)

                    trans = paramiko.Transport(
                        sock=(inner_IP_list[i],10000)
                    )
                    trans.connect(
                        username="root",
                        password="slam-hive1"
                    )
                    sftp = paramiko.SFTPClient.from_transport(trans)
                    sftp.put("/root/.kube/config", "/etc/kubernetes/admin.conf")
                    break
                except Exception as error:
                    pass
            

            # 传输 admin.conf

        print("cluster finish time:",time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

        return inner_IP_list, real_esc_number, image_id, instance_id_list_total

        # # 3.4 开始task

        # #### 4. 将结果回传给master node





        # # 4.1 结束
    @staticmethod
    def transfer_assgin_file(
        inner_IP_list,
        src_path,
        dest_path
    ):
        for i in range(len(inner_IP_list)):
            while True:
                try:
                    time.sleep(0.1)

                    trans = paramiko.Transport(
                        sock=(inner_IP_list[i],10000)
                    )
                    trans.connect(
                        username="root",
                        password="slam-hive1"
                    )
                    sftp = paramiko.SFTPClient.from_transport(trans) #############3\
                    sftp.put(src_path, dest_path)
                    break
                except Exception as error:
                    pass
            