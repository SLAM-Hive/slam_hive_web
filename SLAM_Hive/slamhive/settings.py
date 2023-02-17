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

import os
import sys
from slamhive import app
#=====================================SQLite==========================================
# SQLite URI compatible
# WIN = sys.platform.startswith('win')
# if WIN:
#     prefix = 'sqlite:///'
# else:
#     prefix = 'sqlite:////'

# dev_db = prefix + os.path.join(os.path.dirname(app.root_path), 'data.db')

# SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')
# SQLALCHEMY_TRACK_MODIFICATIONS = False
# SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', dev_db)


#=====================================MySQL==========================================
DIALECT = 'mysql'
DRIVER = 'pymysql'
USERNAME = 'root'
PASSWORD = 'SLAMHive1#'
# HOST = 'localhost'
HOST = '172.40.0.3'
PORT = '3306'
DATABASE = 'slamhiveDB'

SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')
SQLALCHEMY_TRACK_MODIFICATIONS = False
# SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT,DRIVER,USERNAME,PASSWORD,HOST,PORT,DATABASE)
dev_db = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT,DRIVER,USERNAME,PASSWORD,HOST,PORT,DATABASE)
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', dev_db)



