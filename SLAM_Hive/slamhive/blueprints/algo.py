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

from flask import flash, redirect, url_for, render_template, request, jsonify
from slamhive import app, db
from slamhive.models import Algorithm, AlgoParameter
from slamhive.forms import NewAlgoForm, DeleteAlgoForm, NewAlgoParameterForm, DeleteAlgoParameterForm


@app.route('/algo/create', methods=['GET', 'POST'])
def create_algo():
    form = NewAlgoForm()
    if form.validate_on_submit():
        imageTag = form.imageTag.data
        dockerUrl = form.dockerUrl.data
        description = form.description.data
        algo = Algorithm(imageTag=imageTag, dockerUrl=dockerUrl,description=description)
        db.session.add(algo)
        db.session.commit()        
        flash('Your creation is saved!')
        return redirect(url_for('index_algo'))
    return render_template('/algo/create.html', form=form)


@app.route('/algo/index')
def index_algo():
    form = DeleteAlgoForm()
    algos = Algorithm.query.order_by(Algorithm.id.desc()).all()
    db.session.commit()
    flash('Index')
    return render_template('/algo/index.html', algos=algos, form=form)


@app.route('/algo/<int:id>/delete', methods=['POST'])
def delete_algo(id):
    form = DeleteAlgoForm()
    if form.validate_on_submit():
        algo = Algorithm.query.get(id)
        db.session.delete(algo)
        db.session.commit()
        flash('Deleted!')
    return redirect(url_for('index_algo'))

