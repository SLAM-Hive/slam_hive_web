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

from flask import flash, redirect, url_for, render_template, request, jsonify, send_from_directory
from slamhive import app, db
from slamhive.models import Algorithm, MappingTaskConfig, ParameterValue, AlgoParameter, Dataset
from slamhive.forms import DeleteMappingTaskConfigForm
from slamhive.blueprints.utils import *
from werkzeug.utils import secure_filename
import json, yaml, os, uuid


@app.route('/config/<int:id>/create_task', methods=['POST','GET'])
def export_config(id):
    config = MappingTaskConfig.query.get(id)
    config_dict = generate_config_dict(id)
    filename = str(id) + "_" + config.name + ".yaml"
    save_path = os.path.join(app.config['CONFIGURATIONS_PATH'], filename)
    save_dict_to_yaml(config_dict, save_path)
    directory = save_path.replace(filename, '')
    return send_from_directory(directory, filename, as_attachment=True)


@app.route('/config/create')
def create_config():
    algos = Algorithm.query.order_by(Algorithm.name).all()
    datasets = Dataset.query.order_by(Dataset.name).all()
    parameters = AlgoParameter.query.order_by(AlgoParameter.id.asc()).all()
    return render_template('/config/create.html', algos=algos, datasets=datasets, parameters=parameters)


@app.route('/config/create/submit', methods=['POST'])
def submit_config(): 
    print("------submit_config()------")
    data = json.loads(request.get_data())
    # get last element: mappingtaskconfID, then delete
    MappingTaskConfig_Name = data[str(len(data)-2)]['MappingTaskConfig_Name']
    MappingTaskConfig_Description = data[str(len(data)-2)]['MappingTaskConfig_Description']
    Algorithm_Id = data[str(len(data)-1)]['Algorithm_Id']
    Dataset_Id = data[str(len(data)-1)]['Dataset_Id']
    del data[str(len(data)-1)]
    del data[str(len(data)-1)]
    # print("after delete:\n"+str(data))
    # store mappingtaskconfig
    config = MappingTaskConfig(name=MappingTaskConfig_Name, description=MappingTaskConfig_Description)
    algorithm = Algorithm.query.get(Algorithm_Id)   
    dataset = Dataset.query.get(Dataset_Id)     
    db.session.add(config)
    algorithm.mappingTaskConfs.append(config)
    dataset.mappingTaskConfs.append(config)
    db.session.commit()
    # print(data)
    for value1 in data.values():
        print('------')
        parameter = []
        for value2 in value1.values():
            # print(value2)
            parameter.append(value2)
        print(parameter[0])#Parameter id
        print(parameter[1])#ParameterValue value
        param = AlgoParameter.query.get(parameter[0])
        paramValue = ParameterValue(name=param.name, value=parameter[1])
        db.session.add(paramValue)
        config.paramValues.append(paramValue)
        param.paramValues.append(paramValue)
        db.session.commit()       
    return jsonify(result='success')


@app.route('/config/index', methods=['POST','GET'])
def index_config():
    form = DeleteMappingTaskConfigForm()
    configs = MappingTaskConfig.query.order_by(MappingTaskConfig.id.desc()).all()
    db.session.commit()
    return render_template('/config/index.html', configs=configs, form=form)


@app.route('/config/<int:id>/delete', methods=['POST'])
def delete_config(id):
    form = DeleteMappingTaskConfigForm()
    if form.validate_on_submit():
        config = MappingTaskConfig.query.get(id)
        db.session.delete(config)
        db.session.commit()
    return redirect(url_for('index_config'))


@app.route('/config/<int:id>/copy', methods=['GET', 'POST'])
def copy_config(id):
    config = MappingTaskConfig.query.get(id)
    algos = Algorithm.query.order_by(Algorithm.name).all()
    datasets = Dataset.query.order_by(Dataset.name).all()
    parameters = AlgoParameter.query.order_by(AlgoParameter.id.asc()).all()
    return render_template('/config/copy.html', algos=algos, datasets=datasets, parameters=parameters, config=config)




##############To do################
#         upload config yaml
###################################
# app.config['MAX_CONTENT_LENGTH'] = 3*1024*1024
# app.config['UPLOAD_PATH'] = os.path.join(app.root_path, 'uploads')

# def random_filename(filename):
#     ext = os.path.splitext(filename)[1]
#     new_filename = uuid.uuid4().hex + ext
#     return new_filename

# @app.route('/config/upload', methods=['POST','GET'])
# def upload_config():
#     form = UploadForm()
#     print("success: form = UploadForm()")
#     if form.validate_on_submit():
#         f = form.config.data
#         filename = random_filename(f.filename)
#         f.save(os.path.join(app.config['UPLOAD_PATH'], filename))
#         flash('Upload success.')
#         print("Upload success"+'\n')
#         return redirect(url_for('show_config', filename=filename))
#     return render_template('/config/upload.html', form=form)

# app.jinja_env.globals.update(isinstance=isinstance)
# @app.route('/config/uploaded/show/<path:filename>')
# def show_config(filename):
#     yaml_file = os.path.join(app.config['UPLOAD_PATH'], filename)
#     with open(yaml_file, encoding='utf-8') as file:
#         content = file.read()
#         print(content)
#         data = yaml.load(content, Loader=yaml.FullLoader)
#         print(data)
#         # print(type(data))
#         ##############To do################
#         #store to database
#         ###################################
#     return render_template('/config/uploaded.html', filename=filename, data=data)

# @app.route('/config/uploaded/<path:filename>')
# def get_file(filename):
#     return send_from_directory(app.config['UPLOAD_PATH'], filename)

