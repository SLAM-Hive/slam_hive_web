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

from datetime import datetime
from slamhive import db

class Algorithm(db.Model):
    __tablename__ = 'algorithm'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), default="slam-hive-algorithm") 
    imageTag = db.Column(db.String(128), nullable=False, unique=True) 
    dockerUrl = db.Column(db.String(255), nullable=False) 
    description = db.Column(db.Text, nullable=True)
    mappingTaskConfs = db.relationship('MappingTaskConfig', back_populates='algorithm', lazy=True)


class MappingTaskConfig(db.Model):
    __tablename__ = 'mappingtaskconfig'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    algorithm_id = db.Column(db.Integer, db.ForeignKey('algorithm.id'))
    algorithm = db.relationship('Algorithm', back_populates='mappingTaskConfs', lazy=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    dataset = db.relationship('Dataset', back_populates='mappingTaskConfs', lazy=True)
    paramValues = db.relationship('ParameterValue', back_populates='mappingTaskConf', lazy=True)
    mappingTasks = db.relationship('MappingTask', back_populates='mappingTaskConf', lazy=True, cascade='save-update, merge, delete')


class ParameterValue(db.Model):
    __tablename__ = 'parametervalue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    value = db.Column(db.Text, nullable=False) #store parameter value
    mappingTaskConf_id = db.Column(db.Integer, db.ForeignKey('mappingtaskconfig.id'))
    mappingTaskConf = db.relationship('MappingTaskConfig', back_populates='paramValues', lazy=True)
    algoParam_id = db.Column(db.Integer, db.ForeignKey('algoparameter.id'))
    algoParam = db.relationship('AlgoParameter', back_populates='paramValues', lazy=True)


class AlgoParameter(db.Model):
    __tablename__ = 'algoparameter'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True) #Should describe the algorihtm default parameter value
    paramType = db.Column(db.String(30), nullable=False)
    paramValues = db.relationship('ParameterValue', back_populates='algoParam', lazy=True)


class MappingTask(db.Model):
    __tablename__ = 'mappingtask'
    id = db.Column(db.Integer, primary_key=True) 
    state = db.Column(db.String(30), default="Idle") #Default：Idle, Running, Finished, etc
    time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    description = db.Column(db.Text, nullable=True) 
    mappingTaskConf_id = db.Column(db.Integer, db.ForeignKey('mappingtaskconfig.id'))
    mappingTaskConf = db.relationship('MappingTaskConfig', back_populates='mappingTasks', lazy=True)
    evaluation = db.relationship('Evaluation', uselist=False, back_populates="mappingTask", cascade='save-update, merge, delete')


class Dataset(db.Model):
    __tablename__ = 'dataset'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    mappingTaskConfs = db.relationship('MappingTaskConfig', back_populates='dataset', lazy=True)
   

class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(30), default="Idle")
    resultPath = db.Column(db.String(255), default="None")
    mappingTask_id = db.Column(db.Integer, db.ForeignKey('mappingtask.id'))
    mappingTask = db.relationship('MappingTask', back_populates="evaluation")

