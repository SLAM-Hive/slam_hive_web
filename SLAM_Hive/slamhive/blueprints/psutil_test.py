import psutil
import os

def handware_info():
    # ============================== CPU parameters =========================================
    print("============================== CPU parameters =========================================")
    cpu_parameters = []
    # CPU psutil
    cpu_parameters.append(("physical cores", str(psutil.cpu_count(logical = False))))
    cpu_parameters.append(("logical cores", str(psutil.cpu_count())))

    # os.system("lscpu | grep 型号名称：")

    result = os.popen("lscpu") # | grep 型号名称：")

    context = result.read()

    for line in context.splitlines():
        # print(line)
        # line by line parsing
        flag = 0
        initial_list = line.split(":")
        if len(initial_list) == 2:
            # cpu_parameters.append((initial_list[0], initial_list[1]))
            flag = 1
        else :
            initial_list = line.split("：")
            if len(initial_list) == 2:
                # cpu_parameters.append((initial_list[0], initial_list[1]))  
                flag = 1
        
        if flag == 1:
            # English or Chinese or other ???
            # now temporary surport English and Chinese (need to check English)

            first_str = initial_list[0]
            real_first_index = 0
            for s in initial_list[1]:
                if s == " ":
                    real_first_index = real_first_index + 1
                else :
                    break
            last_str = initial_list[1][real_first_index:]
            # print(first_str+":"+last_str+":")

            
            real_first_str = ''
            real_last_str = ''
            if first_str == "架构":
                real_first_str = "architecture"
            elif first_str == "型号名称":
                real_first_str = "model"
            # elif first_str == "CPU MHz":
            #     real_first_str = "reference frequency (MHz)"
            elif first_str == "CPU 最大 MHz":
                real_first_str = "maximum overlocking frequency (MHz)"
            elif first_str == "CPU 最小 MHz":
                real_first_str = "minimum frequency (MHz)"
            elif first_str == "BogoMIPS":
                real_first_str = "MIPS"
            elif first_str == "L1d 缓存":
                real_first_str = "L1 data cache"
            elif first_str == "L1i 缓存":
                real_first_str = "L1 instruct cache"
            elif first_str == "L2 缓存":
                real_first_str = "L2 cache"
            elif first_str == "L3 缓存":
                real_first_str = "L3 cache"
            else :
                continue

            real_last_str = last_str
            cpu_parameters.append((real_first_str, real_last_str))



    result.close()
    # print("===================")
    for i in range(len(cpu_parameters)):
        print(cpu_parameters[i][0]+":   "+cpu_parameters[i][1])

    print("============================== Memory parameters =========================================")

    memory_parameters = []
    memorys = psutil.virtual_memory()
    # print(round(memorys.total/1024/1024/1024,2))
    memory_parameters.append(("total memory (GB)", str(round(memorys.total/1024/1024/1024,2))))

    for i in range(len(memory_parameters)):
        print(memory_parameters[i][0]+":   "+memory_parameters[i][1])


    print("============================== Disk parameters =========================================")

    print(psutil.disk_usage("/").total/1024/1024/1024)

    disk_parameters = []

    disk_parameters.append(("hard drive capacity", str(round(psutil.disk_usage("/").total/1024/1024/1024))))

    # disk_io = psutil.disk_io_counters()
    # print("read time",disk_io.read_time,"write time",disk_io.write_time)

    # get device name which "/" is mounted
    root_divice_name = ""
    disk_partitionses = psutil.disk_partitions()
    for di in disk_partitionses:
        # print(di.mountpoint)
        if di.mountpoint == "/":
            root_divice_name = di.device
    # print(root_divice_name)

    # exec h

    # str = os.system("echo %s | sudo -S %s" % (" ","hdparm -t /dev/sda5"))

    #bu zhidao weisha zhege mingling buhaoshile
    # result = os.popen("echo %s | sudo -S %s" % (" ","hdparm -t /dev/sda5")) # | grep 型号名称：")

    #but will run this process in root permission, so can just run the command
    # result = os.popen("sudo -S %s" % ("hdparm -t /dev/sda5")) # | grep 型号名称：")
    result = os.popen("hdparm -t /dev/sda5")

    context = result.read()

    for line in context.splitlines():
        print(line)

handware_info()