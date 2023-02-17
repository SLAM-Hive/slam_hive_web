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

from flask import redirect, url_for, render_template
from slamhive import app, db, socketio
from slamhive.models import MappingTaskConfig, MappingTask
from slamhive.forms import DeleteMappingTaskForm
from concurrent.futures import ThreadPoolExecutor
from slamhive.task import mapping_cadvisor
from slamhive.blueprints.utils import *
from pathlib import Path
from datetime import datetime
from flask_apscheduler import APScheduler


executor = ThreadPoolExecutor(10)
scheduler = APScheduler()
scheduler.start()


def CheckTask(mappingtaskID):
    mappingtask = MappingTask.query.get(mappingtaskID)
    finished_path = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtaskID)+"/finished")
    if Path(finished_path).is_file():
        mappingtask.state = "Finished"
        db.session.commit()
        print('[MappingTask ID: '+str(mappingtaskID)+'] finished!')
        scheduler.remove_job(str(mappingtaskID))
        #push state to the frontend
        socketio.emit('update_state', {'data': 'Mapping task ' + str(mappingtaskID) +' is finished!'})
    else : 
        print('[MappingTask ID '+str(mappingtaskID)+'] is running...')
    

def RunMapping(configPath, mappingtaskID):
    mapping_cadvisor.mapping_task(configPath, mappingtaskID)
    print('The mapping task is done!')
 

@app.route('/mappingtask/create/<int:id>', methods=['GET', 'POST'])
def create_mappingtask(id):
    config = MappingTaskConfig.query.get(id)
    description = config.description
    state = 'Running'#To do: Check if the container is running
    time = datetime.now().replace(microsecond=0)
    
    mappingtask = MappingTask(description=description, state=state, time=time)
    db.session.add(mappingtask)
    config.mappingTasks.append(mappingtask)
    db.session.commit()

    config_filename = str(id) + "_" + str(config.name) + ".yaml"
    mappingtask_id = mappingtask.id
    mapping_result_dir = os.path.join(app.config['MAPPING_RESULTS_PATH'], str(mappingtask_id))
    if not os.path.exists(mapping_result_dir):
        os.mkdir(mapping_result_dir)
    config_save_path = os.path.join(mapping_result_dir, config_filename)
    config_dict = generate_config_dict(id)
    save_dict_to_yaml(config_dict, config_save_path)
    
    executor.submit(RunMapping, config_filename, str(mappingtask_id))
    scheduler.add_job(id=str(mappingtask_id), func=CheckTask, args=[mappingtask_id], trigger="interval", seconds=3)
    return redirect(url_for('index_mappingtask'))



@app.route('/mappingtask/index')
def index_mappingtask():
    form = DeleteMappingTaskForm()
    mappingtasks = MappingTask.query.order_by(MappingTask.id.desc()).all()
    return render_template('/mappingtask/index.html', mappingtasks=mappingtasks, form=form)


@app.route('/mappingtask/<int:id>/delete', methods=['POST'])
def delete_mappingtask(id):
    form = DeleteMappingTaskForm()
    if form.validate_on_submit():
        mappingtask = MappingTask.query.get(id)
        db.session.delete(mappingtask)
        db.session.commit()
    return redirect(url_for('index_mappingtask'))

