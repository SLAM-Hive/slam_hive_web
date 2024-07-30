from aliyun_tools import Esc_Create
import os, time, paramiko


if __name__ == '__main__':
    ####################
    # 假设：
    # batch task0 选择了1个config，并为此创建1个work node，将config-0对应的task-0分配给work node 0
    
    # 创建batch task 0的流程：
        # 在db.batchmappingtask插入新数据；同时在/SLAM-Hive/slam-hive-results/batch_mappingtask/0
        # 循环创建每个task；
        # 创建完成后，将task的id写入到 ..../0/subTask.txt中
        # controller通过自己的pod名字，ssh连接到主服务器，拷贝.../0，拿到自己所要运行的task的id
        # 然后传输自己所需要的/slam-hive-results/xxx，获取到yaml配置文件
        # 然后根据yaml配置文件拿到dataset和algo
    # 改动流程：
        # 前三步不变
        # 创建一个work node0，主服务器主动将所需要的文件传输过去（将所以得subTask冗余的传输到node0，其他不变）
        # 据此e生成image
        # 创建其他work node
