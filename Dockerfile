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
RUN curl -sSL https://get.daocloud.io/docker | sh

COPY . .
CMD ["flask", "run"]