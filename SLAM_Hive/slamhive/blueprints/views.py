# This is part of SLAM Hive
# Copyright (C) 2024 Zinzhe Liu, Yuanyuan Yang, Bowen Xu, Sören Schwertfeger, ShanghaiTech University. 

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

from flask import render_template
from slamhive import app

from flask import request, jsonify


@app.before_request
def before():
    url = request.path  # 读取到当前接口的地址
    # print(url)
    # process url
    for i in range(len(url)):
        if url[len(url) - 1 - i].isdigit:
            continue
        else:
            url = url[0: len(url) - i]
            break
    print(url)
    for limitation_url in app.config['limitation_url']:
        # if url.find(limitation_url) != -1:
        if limitation_url == url:
            # 判断当前版本是否支持该url
            if limitation_url not in app.config[app.config['CURRENT_VERSION']]:
                print("This function is not allowed to use in this version!")
                return jsonify(result='version error')
            else:
                break
    # print(url)

@app.route('/')
def home():
    return render_template('/home.html')

