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

from flask import Flask
from flask_bootstrap import Bootstrap4
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
import os

app = Flask('slamhive')
# app = Flask(__name__)
app.config.from_pyfile('settings.py')
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

db = SQLAlchemy(app)
bootstrap = Bootstrap4(app)
moment = Moment(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)

app.config['MAPPING_RESULTS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_results/mapping_results')
app.config['EVALUATION_RESULTS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_results/evaluation_results')
app.config['PARAMETERS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_parameters')
app.config['CONFIGURATIONS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_configurations')
app.config['DATASETS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_datasets')
app.config['ALGORITHMS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_algos')
# app.config['EVALUATION_COMPARE_RESULTS_PATH'] = os.path.join(os.path.abspath('../..'), 'slam_hive_results/evaluation_compare_results')

from slamhive.blueprints import views, params, algo, mappingtaskconf, mappingtask, dataset, evaluate
from slamhive import commands