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

from flask import flash, redirect, url_for, render_template
from slamhive import app, db
from slamhive.models import AlgoParameter
from slamhive.forms import NewAlgoParameterForm, DeleteAlgoParameterForm


@app.route('/algoparam/create', methods=['GET', 'POST'])
def create_algoparam():
    form = NewAlgoParameterForm()
    if form.validate_on_submit():
        name = form.name.data
        paramType = form.paramType.data
        description = form.description.data
        algoParameter = AlgoParameter(name=name, paramType=paramType, description=description)
        db.session.add(algoParameter)
        db.session.commit()
       
        flash('Your creation is saved!')
        return redirect(url_for('index_algoparam'))
    return render_template('/parameters/create.html', form=form)


@app.route('/algoparam/index')
def index_algoparam():
    form = DeleteAlgoParameterForm()
    params = AlgoParameter.query.order_by(AlgoParameter.id.desc()).all()
    db.session.commit()
    flash('Index')
    return render_template('/parameters/index.html', params=params, form=form)


@app.route('/algoparam/<int:id>/delete', methods=['POST'])
def delete_algoparam(id):
    form = DeleteAlgoParameterForm()
    if form.validate_on_submit():
        algoParameter = AlgoParameter.query.get(id)
        db.session.delete(algoParameter)
        db.session.commit()
        flash('Deleted!')
    return redirect(url_for('index_algoparam'))