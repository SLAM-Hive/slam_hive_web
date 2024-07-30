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

from flask import flash, redirect, url_for, render_template, abort
from slamhive import app, db
from slamhive.models import AlgoParameter
from slamhive.forms import NewAlgoParameterForm, DeleteAlgoParameterForm


from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, HiddenField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Length, URL, Optional, ValidationError
from slamhive.models import AlgoParameter, Algorithm, MappingTaskConfig, ParameterValue, MappingTask, Dataset, Evaluation
from flask_wtf.file import FileField, FileRequired, FileAllowed





@app.route('/algoparam/create', methods=['GET', 'POST'])
def create_algoparam():

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    form = NewAlgoParameterForm()
    # form.printt(classType = 9)
    if form.validate_on_submit():
        name = form.name.data
        paramType = form.paramType.data
        description = form.description.data
        keyName = form.keyName.data
        value = form.value.data
        valueType = form.valueType.data
        classType = form.classType.data
        className = form.className.data
        algoParameter = AlgoParameter(name=name, 
                                      paramType=paramType, 
                                      description=description,
                                      keyName=keyName,
                                      value=value,
                                      valueType=valueType,
                                      classType=classType,
                                      className=className)
        db.session.add(algoParameter)
        db.session.commit()
       
        flash('Your creation is saved!')
        return redirect(url_for('index_algoparam'))
    return render_template('/parameters/create.html', form=form)

@app.route('/algoparam/<int:id>/copy', methods=['GET', 'POST'])
def copy_algoparam(id):

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    old_algoParameter = AlgoParameter.query.get(id)

    class CopyAlgoParameterForm(FlaskForm):
        pass
    

    setattr(CopyAlgoParameterForm, "name", StringField('Parameter Name', validators=[DataRequired(), Length(1, 128)], 
                                                       render_kw={'placeholder': 'For example: ORB2 parameter'},
                                                       default = old_algoParameter.name))
    setattr(CopyAlgoParameterForm, "classType", SelectField(label="Algorithm or Dataset Parameter Selection", # validators=[DataRequired()],
                                                            choices=[(0, 'Algorithm'), # 'Algorithm'), 
                                                            (1, 'Dataset')],
                                                            default = old_algoParameter.classType,
                                                            coerce = int))
    setattr(CopyAlgoParameterForm, "className", StringField('Algorithm/Dataset Name', validators=[DataRequired(), Length(1, 128)],
                                                            render_kw={'placeholder': 'For example: orb-slam2/euroc'},
                                                            default = old_algoParameter.className))
    setattr(CopyAlgoParameterForm, "paramType", SelectField(label='Parameter Type Selection', validators=[DataRequired()], 
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
                                                            coerce=str,
                                                            default = old_algoParameter.paramType))
    setattr(CopyAlgoParameterForm, "keyName", StringField('Parameter Key Name',  validators=[DataRequired(), Length(1, 128)],
                                                          render_kw={'placeholder': 'For example: nFeatures (orb2-slam)'},
                                                          default = old_algoParameter.keyName))
    setattr(CopyAlgoParameterForm, "value", StringField('Parameter Default Value',  validators=[DataRequired()],
                                                        render_kw={'placeholder': 'For example: 1200 (nFeatures default value)'},
                                                        default = old_algoParameter.value))
    setattr(CopyAlgoParameterForm, "valueType", SelectField('Parameter Value Type', validators=[DataRequired(), Length(1, 32)],
                                                            choices=[('int', 'int'),
                                                            ('float', 'float'),
                                                            ('double', 'double'),
                                                            ('string', 'string'),
                                                            ('matrix', 'matrix')],
                                                            coerce=str,
                                                            default = old_algoParameter.valueType)) 
    setattr(CopyAlgoParameterForm, "description", TextAreaField('Description', validators=[DataRequired()], 
                                                                render_kw={'rows':'5', 'placeholder': 'Please input parameter description. \nFor example: ORB Extractor is the number of features per image.'},
                                                                default = old_algoParameter.description))
    setattr(CopyAlgoParameterForm, "submit", SubmitField('Save'))                                                      

    form = CopyAlgoParameterForm()
    if form.validate_on_submit():
        name = form.name.data
        paramType = form.paramType.data
        description = form.description.data
        keyName = form.keyName.data
        value = form.value.data
        valueType = form.valueType.data
        classType = form.classType.data
        className = form.className.data
        algoParameter = AlgoParameter(name=name, 
                                      paramType=paramType, 
                                      description=description,
                                      keyName=keyName,
                                      value=value,
                                      valueType=valueType,
                                      classType=classType,
                                      className=className)
        db.session.add(algoParameter)
        db.session.commit()
       
        flash('Your creation is saved!')
        return redirect(url_for('index_algoparam'))
    return render_template('/parameters/copy.html', form=form)

@app.route('/algoparam/<int:id>/modify', methods=['GET', 'POST'])
def modify_algoparam(id):

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)

    algoParameter = AlgoParameter.query.get(id)

    class ModifyAlgoParameterForm(FlaskForm):
        pass
    

    setattr(ModifyAlgoParameterForm, "name", StringField('Parameter Name', validators=[DataRequired(), Length(1, 128)], 
                                                       render_kw={'placeholder': 'For example: ORB2 parameter'},
                                                       default = algoParameter.name))
    setattr(ModifyAlgoParameterForm, "classType", SelectField(label="Algorithm or Dataset Parameter Selection", # validators=[DataRequired()],
                                                            choices=[(0, 'Algorithm'), # 'Algorithm'), 
                                                            (1, 'Dataset')],
                                                            default = algoParameter.classType,
                                                            coerce = int))
    setattr(ModifyAlgoParameterForm, "className", StringField('Algorithm/Dataset Name', validators=[DataRequired(), Length(1, 128)],
                                                            render_kw={'placeholder': 'For example: orb-slam2/euroc'},
                                                            default = algoParameter.className))
    setattr(ModifyAlgoParameterForm, "paramType", SelectField(label='Parameter Type Selection', validators=[DataRequired()], 
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
                                                            coerce=str,
                                                            default = algoParameter.paramType))
    setattr(ModifyAlgoParameterForm, "keyName", StringField('Parameter Key Name',  validators=[DataRequired(), Length(1, 128)],
                                                          render_kw={'placeholder': 'For example: nFeatures (orb2-slam)'},
                                                          default = algoParameter.keyName))
    setattr(ModifyAlgoParameterForm, "value", StringField('Parameter Default Value',  validators=[DataRequired()],
                                                        render_kw={'placeholder': 'For example: 1200 (nFeatures default value)'},
                                                        default = algoParameter.value))
    setattr(ModifyAlgoParameterForm, "valueType", SelectField('Parameter Value Type', validators=[DataRequired(), Length(1, 32)],
                                                            choices=[('int', 'int'),
                                                            ('float', 'float'),
                                                            ('double', 'double'),
                                                            ('string', 'string'),
                                                            ('matrix', 'matrix')],
                                                            coerce=str,
                                                            default = algoParameter.valueType)) 
    setattr(ModifyAlgoParameterForm, "description", TextAreaField('Description', validators=[DataRequired()], 
                                                                render_kw={'rows':'5', 'placeholder': 'Please input parameter description. \nFor example: ORB Extractor is the number of features per image.'},
                                                                default = algoParameter.description))
    setattr(ModifyAlgoParameterForm, "submit", SubmitField('Save'))                                                      

    form = ModifyAlgoParameterForm()
    if form.validate_on_submit():
        algoParameter.name = form.name.data
        algoParameter.paramType = form.paramType.data
        algoParameter.description = form.description.data
        algoParameter.keyName = form.keyName.data
        algoParameter.value = form.value.data
        algoParameter.valueType = form.valueType.data
        algoParameter.classType = form.classType.data
        algoParameter.className = form.className.data
        db.session.commit()
       
        flash('Your modify is saved!')
        return redirect(url_for('index_algoparam'))
    return render_template('/parameters/copy.html', form=form)

@app.route('/algoparam/index')
def index_algoparam():
    form = DeleteAlgoParameterForm()
    params = AlgoParameter.query.order_by(AlgoParameter.id.desc()).all()
    db.session.commit()
    flash('Index')
    return render_template('/parameters/index.html', params=params, form=form, version=app.config['CURRENT_VERSION'])



@app.route('/algoparam/<int:id>/delete', methods=['POST'])
def delete_algoparam(id):

    version = app.config['CURRENT_VERSION']
    if version != 'workstation' and version != 'cluster' and version != 'aliyun':
        return abort(403)
        
    form = DeleteAlgoParameterForm()
    if form.validate_on_submit():
        algoParameter = AlgoParameter.query.get(id)
        db.session.delete(algoParameter)
        db.session.commit()
        flash('Deleted!')
    return redirect(url_for('index_algoparam'))