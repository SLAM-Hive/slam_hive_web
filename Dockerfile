# This is part of SLAM Hive
# Copyright (C) 2024 Xinzhe Liu, Yuanyuan Yang, Bowen Xu, Sören Schwertfeger, ShanghaiTech University. 

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

FROM ubuntu:20.04
WORKDIR /home/slam_hive_web
ENV FLASK_APP SLAM_Hive/slamhive
ENV FLASK_RUN_HOST 0.0.0.0

RUN sed -i s/archive.ubuntu.com/mirrors.aliyun.com/g /etc/apt/sources.list && \
    sed -i s/security.ubuntu.com/mirrors.aliyun.com/g /etc/apt/sources.list && \
    apt-get update && apt-get upgrade -y 

#RUN apk add --no-cache gcc musl-dev linux-headers

COPY SLAM_Hive/requirements.txt requirements.txt

RUN apt update && apt install -y pip

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pip -U && \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

RUN pip install -r requirements.txt
RUN pip install cryptography
RUN apt install -y curl


ENV TZ=Asia/Shanghai

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo '$TZ' > /etc/timezone

RUN apt-get update &&  apt -y install texlive-xetex

RUN apt-get install -y apt-transport-https \
    ca-certificates curl gnupg-agent software-properties-common 

# Use Tsinghua mirror for Docker to avoid connection issues
# Add retry logic and --fix-missing flag to handle network issues
RUN curl -fsSL https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/ubuntu $(lsb_release -cs) stable"

# Update package list with retry
RUN apt-get update || (sleep 5 && apt-get update)

# Install Docker components separately to handle partial failures
RUN apt-get install -y --fix-missing containerd.io || \
    (apt-get update && apt-get install -y --fix-missing containerd.io)

RUN apt-get install -y --fix-missing docker-ce-cli docker-ce docker-compose-plugin

# 配置Docker镜像加速
# RUN mkdir -p /etc/docker && \
#     echo '{"registry-mirrors": ["https://docker.m.daocloud.io"]}' > /etc/docker/daemon.json

COPY . .

#### add
RUN ln  -s  /slam_hive_results/mapping_results/ /home/slam_hive_web/SLAM_Hive/slamhive/static/

# 启动Flask应用，支持调试模式
ENV FLASK_DEBUG 1
CMD ["flask", "run", "--debugger"]