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

import click
from slamhive import app, db

# flask initdb [--drop]
@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    """Initialize the database."""
    if drop:
        click.confirm('This operation will delete the database, do you want to continue?', abort=True)
        db.drop_all()
        click.echo('Drop tables.')
    db.create_all()
    click.echo('Initialized database.')


# flask migrate-algorithm-ros-version
@app.cli.command("migrate-algorithm-ros-version")
def migrate_algorithm_ros_version():
    """Add algorithm.rosVersion (ros1/ros2/other) and fill empty values from each image's ROS_DISTRO.

    Idempotent. The scheduler plays datasets according to this field; new
    algorithms set it on the registration page.
    """
    from sqlalchemy import inspect, text
    from slamhive.task.ros_interop import image_ros_version

    columns = {column["name"] for column in inspect(db.engine).get_columns("algorithm")}
    if "rosVersion" not in columns:
        db.session.execute(text("ALTER TABLE algorithm ADD COLUMN rosVersion VARCHAR(16) NULL"))
        db.session.commit()
        click.echo("Added column algorithm.rosVersion")
    rows = db.session.execute(text(
        "SELECT id, imageTag FROM algorithm WHERE rosVersion IS NULL OR rosVersion = ''")).fetchall()
    for algo_id, image_tag in rows:
        version = image_ros_version(image_tag)
        if version is None:
            click.echo("  {:<32} image slam-hive-algorithm:{} not found; set it on the Algorithm page".format(
                image_tag, image_tag))
            continue
        db.session.execute(text("UPDATE algorithm SET rosVersion = :v WHERE id = :i"), {"v": version, "i": algo_id})
        click.echo("  {:<32} {}".format(image_tag, version))
    db.session.commit()
