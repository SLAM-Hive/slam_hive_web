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

# mappingtaskconfig_parametervalue_table = db.Table(
#     'mappingtaskconfig_parametervalue',
#     db.Column('mappingtaskconfig_id', db.Integer, db.ForeignKey('mappingtaskconfig.id')),
#     db.Column('parametervalue_id', db.Integer, db.ForeignKey('parametervalue.id'))
# )

# parametervalue_metavalue_table = db.Table(
#     'parametervalue_metavalue',
#     db.Column('parametervalue_id', db.Integer, db.ForeignKey('parametervalue.id')),
#     db.Column('metavalue_id', db.Integer, db.ForeignKey('metavalue.id'))
# )

combmappingtaskconfig_mappingtaskconfig_table = db.Table(
    'combmappingtaskconfig_mappingtaskconfig',
    db.Column('combmappingtaskconfig_id', db.Integer, db.ForeignKey('combmappingtaskconfig.id')),
    db.Column('mappingtaskconfig_id', db.Integer, db.ForeignKey('mappingtaskconfig.id'))
)

class Algorithm(db.Model):
    __tablename__ = 'algorithm'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), default="slam-hive-algorithm") 
    imageTag = db.Column(db.String(128), nullable=False, unique=True) 
    dockerUrl = db.Column(db.String(255), nullable=False) 
    description = db.Column(db.Text, nullable=True)
    mappingTaskConfs = db.relationship('MappingTaskConfig', back_populates='algorithm', lazy=True)

class CombMappingTaskConfig(db.Model):
    __tablename__ = 'combmappingtaskconfig'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128),nullable=False) 
    description = db.Column(db.Text, nullable=True)
    
    mappingTaskConf = db.relationship('MappingTaskConfig', back_populates='combMappingTaskConf', secondary = combmappingtaskconfig_mappingtaskconfig_table, lazy=True)


class MappingTaskConfig(db.Model):
    __tablename__ = 'mappingtaskconfig'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)

    algorithm_id = db.Column(db.Integer, db.ForeignKey('algorithm.id'))
    algorithm = db.relationship('Algorithm', back_populates='mappingTaskConfs', lazy=True)

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    dataset = db.relationship('Dataset', back_populates='mappingTaskConfs', lazy=True)

    # now n-n
    paramValues = db.relationship('ParameterValue', back_populates='mappingTaskConf', lazy=True)
    # mappingTasks = db.relationship('MappingTask', back_populates='mappingTaskConf', lazy=True, cascade='save-update, merge, delete')
    # paramValues = db.relationship('ParameterValue', back_populates='mappingTaskConf', secondary = mappingtaskconfig_parametervalue_table, lazy=True)
    
    # now still 1-n, do not change
    mappingTasks = db.relationship('MappingTask', back_populates='mappingTaskConf', lazy=True, cascade='save-update, merge, delete')

    # now relationship with combmappingtaskconfig
    combMappingTaskConf = db.relationship('CombMappingTaskConfig', back_populates='mappingTaskConf', secondary = combmappingtaskconfig_mappingtaskconfig_table, lazy=True)


class MetaValue(db.Model):
    __tablename__ = 'metavalue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    value = db.Column(db.String(256), nullable=False)
    value_type = db.Column(db.String(32), nullable=False)

    parameterValue_id = db.Column(db.Integer, db.ForeignKey("parametervalue.id"), nullable=False)
    paramValues = db.relationship('ParameterValue', back_populates='metaValues', lazy=True)

class ParameterValue(db.Model):
    __tablename__ = 'parametervalue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    value = db.Column(db.Text, nullable=False) #store parameter value

    mappingTaskConf_id = db.Column(db.Integer, db.ForeignKey('mappingtaskconfig.id'))
    mappingTaskConf = db.relationship('MappingTaskConfig', back_populates='paramValues', lazy=True)
    # mappingTaskConf = db.relationship('MappingTaskConfig', back_populates='paramValues', secondary = mappingtaskconfig_parametervalue_table ,lazy=True)


    algoParam_id = db.Column(db.Integer, db.ForeignKey('algoparameter.id'))
    algoParam = db.relationship('AlgoParameter', back_populates='paramValues', lazy=True)

    #new
    metaValues = db.relationship('MetaValue', back_populates='paramValues',lazy=True)


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
    performanceresults = db.relationship('PerformanceResults', uselist=True, back_populates="mappingTask", cascade='save-update, merge, delete')

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
    mappingTaskConfs = db.relationship('MappingTaskConfig', back_populates='dataset', lazy=True)
   

class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(30), default="Idle")
    resultPath = db.Column(db.String(255), default="None")
    mappingTask_id = db.Column(db.Integer, db.ForeignKey('mappingtask.id'))
    mappingTask = db.relationship('MappingTask', back_populates="evaluation")

    # ate_rmse = db.Column(db.Float, nullable = True)
    evoResults = db.relationship('EvoResults', back_populates='evaluation', lazy=True, cascade='save-update, merge, delete')

class EvoResults(db.Model):
    __tablename__ = 'evoresults'
    id = db.Column(db.Integer, primary_key=True)

    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'))
    evaluation = db.relationship('Evaluation', back_populates='evoResults', lazy=True)

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



