# This is part of SLAM Hive
# Copyright (C) 2024 Xinzhe Liu, Yuanyuan Yang, Bowen Xu, Sören Schwertfeger, ShanghaiTech University. 

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

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, HiddenField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Length, URL, Optional, ValidationError
from slamhive.models import AlgoParameter, Algorithm, MappingTaskConfig, ParameterValue, MappingTask, Dataset, Evaluation
from flask_wtf.file import FileField, FileRequired, FileAllowed


class NewAlgoForm(FlaskForm):
    # name = StringField('Name (default name is "slam-hive-algorithm")', default='slam-hive-algorithm')
    imageTag = StringField('Image tag', validators=[Length(1, 128)], 
                # render_kw={'placeholder': 'For exmaple: vins-mono'})   
                render_kw={'placeholder': 'For exmaple: orb-slam2-ros-mono'})    
    dockerUrl = StringField('Dockerfile and mapping script address link', validators=[DataRequired(), URL(), Length(1, 255)])
    className = StringField('Algorithm Class Name', validators=[DataRequired(), Length(1, 128)],
                render_kw={'placeholder': 'For example: orb-slam2'})
    description = TextAreaField('Description', validators=[DataRequired()], render_kw={'rows':'5'})
    attribute = TextAreaField('Attribute', validators=[DataRequired()], render_kw={'rows':'5'})
    submit = SubmitField('Save')
    #slam-hive-algorithm:[imageTag], can't be repeated
    def validate_imageTag(self, field):
        if Algorithm.query.filter_by(imageTag=field.data).first():
            print("imageTag can't be repeated\n")
            raise ValidationError('Image tag already in use!')


class DeleteAlgoForm(FlaskForm):
    submit = SubmitField('Delete')


class NewDatasetForm(FlaskForm):
    name = StringField('Dataset folder name', validators=[Length(1, 128)],
            render_kw={'placeholder': 'For exmaple: MH_01_easy'})
    url = StringField('Dataset address link', validators=[DataRequired(), URL(), Length(1, 255)])
    description = TextAreaField('Description', validators=[DataRequired()], render_kw={'rows':'5'})
    className = StringField('Dataset name', validators=[DataRequired(), Length(1, 128)],
                render_kw={'placeholder': 'For example: euroc'})
    attribute = TextAreaField('Attribute', validators=[DataRequired()], render_kw={'rows':'5'})
    submit = SubmitField('Save')
    def validate_name(self, field):
        if Dataset.query.filter_by(name=field.data).first():
            print("Dataset name can't be repeated\n")
            raise ValidationError('Dataset name already in use!')


class DeleteDatasetForm(FlaskForm):
    submit = SubmitField('Delete')


class NewParamterValueForm(FlaskForm):
    name = StringField('name', validators=[DataRequired(), Length(1, 128)],
                    render_kw={'placeholder': 'Input name please.'})
    value = StringField('value', validators=[DataRequired(), Length(1, 30)],
                    render_kw={'placeholder': 'Input value please.'})

class DeleteMappingTaskForm(FlaskForm):
    submit = SubmitField('Delete')


# class NewMappingTaskConfigForm(FlaskForm):
#     algorithm = SelectField('Algorithm Selection', coerce=int, default=1)
#     dataset = SelectField('Dataset Selection', coerce=int, default=1)
#     name = StringField('Mapping Task Configuration Name', validators=[DataRequired(), Length(1, 128)], 
#                         render_kw={'placeholder': 'For example, orb2_config_A'})
#     description = TextAreaField('Description', validators=[DataRequired()], render_kw={'rows':'5'})
#     submit = SubmitField('confirm')

#     def __init__(self, *args, **kwargs):
#         super(NewMappingTaskConfigForm, self).__init__(*args, **kwargs)
#         self.algorithm.choices = [(algorithm.id, algorithm.imageTag)
#                                  for algorithm in Algorithm.query.order_by(Algorithm.name).all()]


class DeleteMappingTaskConfigForm(FlaskForm):
    submit = SubmitField('Delete')

class DeleteGroupMappingTaskConfigForm(FlaskForm):
    submit = SubmitField('Delete')

class DeleteGroupMappingTaskConfigForm1(FlaskForm):
    submit = SubmitField('Delete')

class DeleteCustomAnalysisGroup(FlaskForm):
    submit = SubmitField('Delete')

#The field attribute value should be consistent with the attribute name of the Model!!!
class NewAlgoParameterForm(FlaskForm):

    # test_id = 1

    # def __init__(self, test_id):
    #     super(NewAlgoParameterForm, self).__init__()
    #     test_id = test_id
    
    # def printt(self, classType):
    #     self.classType.choices = [(0, classType),(1, 'Dataset')]
    #     # print("ttttttt ", cls.test_id)

    name = StringField('Parameter Name', validators=[DataRequired(), Length(1, 128)], 
                        render_kw={'placeholder': 'For example: ORB2 parameter'})
    classType = SelectField(label="Algorithm or Dataset Parameter Selection", # validators=[DataRequired()],
                            choices=[(0, "Algorithm"), # 'Algorithm'), 
                            (1, 'Dataset')],
                            coerce=int)
    className = StringField('Example Algorithm/Dataset Name', validators=[DataRequired(), Length(1, 128)],
                            render_kw={'placeholder': 'For example: orb-slam2/euroc'})
    paramType = SelectField(label='Parameter Type Selection', validators=[DataRequired()], 
                            choices=[('Dataset', 'Dataset'), 
                            ('Dataset matrix', 'Dataset matrix'), 
                            ('Dataset remap', 'Dataset remap'),
                            ('Algorithm', 'Algorithm'), 
                            ('Algorithm remap', 'Algorithm remap'),
                            ('Dataset frequency', 'Dataset frequency'),
                            ('Dataset frequency remap', 'Dataset frequency remap'),
                            ('Dataset resolution', 'Dataset resolution'),
                            ('Dataset resolution size', 'Dataset resolution size'),
                            ('Dataset resolution intrinsic', 'Dataset resolution intrinsic'),
                            ('General parameter', 'General parameter')],
                            coerce=str)
    keyName = StringField('Example Parameter Key Name',  validators=[DataRequired(), Length(1, 128)],
                          render_kw={'placeholder': 'For example: nFeatures (orb2-slam)'})
    value = StringField('Example Parameter Value',  validators=[DataRequired()],
                        render_kw={'placeholder': 'For example: 1200 (nFeatures default value)'})
    valueType = SelectField('Example Parameter Value Type', validators=[DataRequired(), Length(1, 32)],
                            choices=[('int', 'int'),
                            ('float', 'float'),
                            ('double', 'double'),
                            ('string', 'string'),
                            ('matrix', 'matrix')],
                            coerce=str)
    description = TextAreaField('Description', validators=[DataRequired()], 
                    render_kw={'rows':'5', 'placeholder': 'Please input parameter description. \nFor example: ORB Extractor is the number of features per image.'})
    submit = SubmitField('Save')




class DeleteAlgoParameterForm(FlaskForm):
    submit = SubmitField('Delete')


class DeleteEvaluationForm(FlaskForm):
    submit = SubmitField('Delete')


# class NewMappingTaskForm(FlaskForm):
#     # time = DateTimeField(default=datetime.utcnow)
#     mappingTaskConf = SelectField('MappingTaskConfig Selection', coerce=int, default=1)
#     name = StringField('Mapping Task Name', validators=[DataRequired(), Length(1, 30)],
#                     render_kw={'placeholder': 'Input MappingTask name please.'})
#     state = StringField('State of the MappingTask (default state is "Idle")', default='Idle')
#     description = TextAreaField('Description', validators=[DataRequired()], render_kw={'rows':'5'})
#     submit = SubmitField('Create')

#     def __init__(self, *args, **kwargs):
#         super(NewMappingTaskForm, self).__init__(*args, **kwargs)
#         self.mappingTaskConf.choices = [(mappingTaskConf.id, mappingTaskConf.name)
#                                  for mappingTaskConf in MappingTaskConfig.query.order_by(MappingTaskConfig.name).all()]

# class UploadForm(FlaskForm):
#     config = FileField('Upload Configuration YAML File', validators=[FileRequired(), FileAllowed(['yaml'])])
#     submit = SubmitField('Upload')