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

import docker

def get_pkg_path():
    flask_client = docker.APIClient(base_url='unix://var/run/docker.sock')
    path_list = flask_client.inspect_container("slam_hive_web")['HostConfig']['Binds']
    SLAM_HIVE_PATH = ''
    for path in path_list:
        if 'slam_hive_results' in path:
            SLAM_HIVE_PATH = path
            break
    SLAM_HIVE_PATH = SLAM_HIVE_PATH.split("/slam_hive_results:")[0] #/home/yyy/SLAM_Hive 
    return SLAM_HIVE_PATH