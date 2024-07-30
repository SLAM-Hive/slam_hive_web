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

from datetime import datetime
from slamhive import db

combmappingtaskconfig_mappingtaskconfig_table = db.Table(
    'combmappingtaskconfig_mappingtaskconfig',
    db.Column('combmappingtaskconfig_id', db.Integer, db.ForeignKey('combmappingtaskconfig.id')),
    db.Column('mappingtaskconfig_id', db.Integer, db.ForeignKey('mappingtaskconfig.id'))
)


groupmappingtaskconfig_mappingtaskconfig_table = db.Table(
    'groupmappingtaskconfig_mappingtaskconfig',
    db.Column('groupmappingtaskconfig_id', db.Integer, db.ForeignKey('groupmappingtaskconfig.id')),
    db.Column('mappingtaskconfig_id', db.Integer, db.ForeignKey('mappingtaskconfig.id'))
)

mappingtask_multievaluation_table = db.Table(
    'mappingtask_multievaluation',
    db.Column('mappingtask_id', db.Integer, db.ForeignKey('mappingtask.id')),
    db.Column('multievaluation_id', db.Integer, db.ForeignKey('multievaluation.id'))
)

mappingtaskconfig_parametervalue_table = db.Table(
    'mappingtaskconfig_parametervalue',
    db.Column('mappingtaskconfig_id', db.Integer, db.ForeignKey('mappingtaskconfig.id')),
    db.Column('parametervalue_id', db.Integer, db.ForeignKey('parametervalue.id'))
)

class Algorithm(db.Model):
    __tablename__ = 'algorithm'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), default="slam-hive-algorithm") 
    imageTag = db.Column(db.String(128), nullable=False, unique=True) 
    dockerUrl = db.Column(db.String(255), nullable=False) 
    description = db.Column(db.Text, nullable=True)
    className = db.Column(db.String(128), nullable=True)
    attribute = db.Column(db.Text, nullable=True)

    mappingTaskConfs = db.relationship('MappingTaskConfig', back_populates='algorithm', lazy=True)

# class FakeMappingTaskConfig(db.Model):
#     __tablename__ = 'fakemappingtaskconfig'
#     id = db.Column(db.Integer, primary_key=True)
#     mappingtaskconfig_id(db.Integer, db.ForeignKey('mappingtaskconfig.id'))
#     mappingtaskconfig = db.relationship('MappingTaskConfig', back_populates='fakemappingtaskconfigs', lazy=True)

#     name = db.Column(db.String(128), nullable=False)
#     description = db.Column(db.Text, nullable=True)
#     algorithm_id = db.Column(db.Integer, nullable=False)
#     dataset_id = db.Column(db.Integer, nullable=False)

class MappingTaskConfig(db.Model):
    __tablename__ = 'mappingtaskconfig'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    algorithm_id = db.Column(db.Integer, db.ForeignKey('algorithm.id'))
    algorithm = db.relationship('Algorithm', back_populates='mappingTaskConfs', lazy=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    dataset = db.relationship('Dataset', back_populates='mappingTaskConfs', lazy=True)
    
    # paramValues = db.relationship('ParameterValue', back_populates='mappingTaskConf', lazy=True)

    paramValues = db.relationship('ParameterValue', back_populates='mappingTaskConf', lazy=True, secondary = mappingtaskconfig_parametervalue_table)

    mappingTasks = db.relationship('MappingTask', back_populates='mappingTaskConf', lazy=True, cascade='save-update, merge, delete')
    combMappingTaskConf = db.relationship('CombMappingTaskConfig', back_populates='mappingTaskConf', secondary = combmappingtaskconfig_mappingtaskconfig_table, lazy=True)
    groupMappingTaskConf = db.relationship('GroupMappingTaskConfig', back_populates='mappingTaskConf', secondary = groupmappingtaskconfig_mappingtaskconfig_table, lazy=True)
    # fakemappingtaskconfigs = db.relationship('FakeMappingTaskConfig', back_populates='algorithm')

class CombMappingTaskConfig(db.Model):
    __tablename__ = 'combmappingtaskconfig'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128),nullable=False) 
    description = db.Column(db.Text, nullable=True)
    
    mappingTaskConf = db.relationship('MappingTaskConfig', back_populates='combMappingTaskConf', secondary = combmappingtaskconfig_mappingtaskconfig_table, lazy=True)

class GroupMappingTaskConfig(db.Model):
    __tablename__ = 'groupmappingtaskconfig'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128),nullable=False) 
    description = db.Column(db.Text, nullable=True)
    mappingTaskConf = db.relationship('MappingTaskConfig', back_populates='groupMappingTaskConf', secondary = groupmappingtaskconfig_mappingtaskconfig_table, lazy=True)

    multievaluation_id = db.Column(db.Integer,db.ForeignKey('multievaluation.id'))
    multiEvaluation = db.relationship('MultiEvaluation', uselist=False, back_populates="groupMappingTaskConf")

class ParameterValue(db.Model):
    __tablename__ = 'parametervalue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    keyName = db.Column(db.String(128), nullable=False)
    value = db.Column(db.Text, nullable=False) #store parameter value


    # new parameter for general parameter
    valueType = db.Column(db.String(128), nullable=False)
    className = db.Column(db.String(128), nullable=False)

    
    # mappingTaskConf_id = db.Column(db.Integer, db.ForeignKey('mappingtaskconfig.id'))
    mappingTaskConf_id = db.Column(db.Integer, nullable = True)
    mappingTaskConf = db.relationship('MappingTaskConfig', back_populates='paramValues', secondary = mappingtaskconfig_parametervalue_table, lazy=True) # , cascade='save-update, merge, delete')
    
    algoParam_id = db.Column(db.Integer, db.ForeignKey('algoparameter.id'))
    algoParam = db.relationship('AlgoParameter', back_populates='paramValues', lazy=True)


class AlgoParameter(db.Model):
    __tablename__ = 'algoparameter'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    keyName = db.Column(db.String(128), nullable=False) #Should describe the algorihtm default parameter value
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    valueType = db.Column(db.String(32), nullable=False)
    paramType = db.Column(db.String(32), nullable=False)
    classType = db.Column(db.Boolean, nullable=False)
    className = db.Column(db.String(128), nullable=False)
    
    paramValues = db.relationship('ParameterValue', back_populates='algoParam', lazy=True)

class BatchMappingTask(db.Model):
    __tablename__ = 'batchmappingtask'
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255), nullable=True)

class MappingTask(db.Model):
    __tablename__ = 'mappingtask'
    id = db.Column(db.Integer, primary_key=True) 
    state = db.Column(db.String(30), default="Idle") #Default：Idle, Running, Finished, etc
    time = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    description = db.Column(db.Text, nullable=True) 
    trajectory_state = db.Column(db.String(32), default="Running") # Success, Unsuccess 
    
    mappingTaskConf_id = db.Column(db.Integer, db.ForeignKey('mappingtaskconfig.id'))
    mappingTaskConf = db.relationship('MappingTaskConfig', back_populates='mappingTasks', lazy=True)
    
    evaluation = db.relationship('Evaluation', uselist=False, back_populates="mappingTask", cascade='save-update, merge, delete')
    performanceresults = db.relationship('PerformanceResults', uselist=False, back_populates="mappingTask", cascade='save-update, merge, delete')

    multiEvaluations = db.relationship('MultiEvaluation', back_populates='mappingtasks', secondary = mappingtask_multievaluation_table, lazy=True)


class MultiEvaluation(db.Model):
    __tablename__ = 'multievaluation'
    id = db.Column(db.Integer, primary_key = True)
    path = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    state = db.Column(db.String(32), default="Idle")

    mappingtasks = db.relationship('MappingTask', back_populates='multiEvaluations', secondary = mappingtask_multievaluation_table, lazy=True)

    groupMappingTaskConf = db.relationship('GroupMappingTaskConfig', uselist=False, back_populates="multiEvaluation")

class PerformanceResults(db.Model):
    __tablename__ = "performanceresults"
    id = db.Column(db.Integer, primary_key=True)

    mappingTask_id = db.Column(db.Integer, db.ForeignKey('mappingtask.id'))
    mappingTask = db.relationship('MappingTask', back_populates="performanceresults")

    max_cpu = db.Column(db.Float, nullable = False)
    mean_cpu = db.Column(db.Float, nullable = False)
    max_ram = db.Column(db.Float, nullable = False)

    

class Dataset(db.Model):
    __tablename__ = 'dataset'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    className = db.Column(db.String(128), nullable=True)
    attribute = db.Column(db.Text, nullable=True)

    mappingTaskConfs = db.relationship('MappingTaskConfig', back_populates='dataset', lazy=True)
   

class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(30), default="Idle")
    resultPath = db.Column(db.String(255), default="None")
    
    mappingTask_id = db.Column(db.Integer, db.ForeignKey('mappingtask.id'))
    mappingTask = db.relationship('MappingTask', back_populates="evaluation")

    # ate_rmse = db.Column(db.Float, nullable = True)
    evoResults = db.relationship('EvoResults', back_populates='evaluation',  uselist=False, lazy=True, cascade='save-update, merge, delete')

class EvoResults(db.Model):
    __tablename__ = 'evoresults'
    id = db.Column(db.Integer, primary_key=True)

    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'))
    evaluation = db.relationship('Evaluation', back_populates='evoResults', lazy=True, cascade='save-update, merge, delete')

    ate_rmse = db.Column(db.Float, nullable = False)
    ate_mean = db.Column(db.Float, nullable = False)
    ate_median = db.Column(db.Float, nullable = False)
    ate_std = db.Column(db.Float, nullable = False)
    ate_min = db.Column(db.Float, nullable = False)
    ate_max = db.Column(db.Float, nullable = False)
    ate_sse = db.Column(db.Float, nullable = False)
    rpe_rmse = db.Column(db.Float, nullable = False)
    rpe_mean = db.Column(db.Float, nullable = False)
    rpe_median = db.Column(db.Float, nullable = False)
    rpe_std = db.Column(db.Float, nullable = False)
    rpe_min = db.Column(db.Float, nullable = False)
    rpe_max = db.Column(db.Float, nullable = False)
    rpe_sse = db.Column(db.Float, nullable = False)



