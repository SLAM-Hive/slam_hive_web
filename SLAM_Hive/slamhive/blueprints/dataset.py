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
from slamhive.models import Dataset
from slamhive.forms import NewDatasetForm, DeleteDatasetForm

@app.route('/dataset/create', methods=['GET', 'POST'])
def create_dataset():
    form = NewDatasetForm()
    if form.validate_on_submit():
        name = form.name.data
        url = form.url.data
        description = form.description.data
        dataset = Dataset(name=name, url=url, description=description)
        db.session.add(dataset)
        db.session.commit()        
        flash('Your creation is saved!')
        return redirect(url_for('index_dataset'))
    return render_template('/dataset/create.html', form=form)


@app.route('/dataset/index')
def index_dataset():
    form =  DeleteDatasetForm()
    datasets = Dataset.query.order_by(Dataset.id.desc()).all()
    db.session.commit()
    flash('Index')
    return render_template('/dataset/index.html', datasets=datasets, form=form)


@app.route('/dataset/<int:id>/delete', methods=['POST'])
def delete_dataset(id):
    form = DeleteDatasetForm()
    if form.validate_on_submit():
        dataset = Dataset.query.get(id)
        db.session.delete(dataset)
        db.session.commit()
        flash('Deleted!')
    return redirect(url_for('index_dataset'))

