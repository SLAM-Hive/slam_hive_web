# Automatic ROS bag format adaptation

In workstation mode, users select an algorithm and a dataset through the usual Web workflow. At mapping task startup, the scheduler checks their ROS versions. When the bag format differs from the algorithm, the Web container converts the dataset, caches the result under `slam_hive_datasets/.converted/`, and mounts that cached dataset at `/slamhive/dataset`. The task's original config and dataset registration stay the same.

| Algorithm | Source dataset | Scheduler action |
| --- | --- | --- |
| ROS1 | ROS1 bag | Use original dataset |
| ROS2 | ROS2 bag | Use original dataset |
| ROS2 | ROS1 bag | Convert to ROS2 bag and generate `ros2 bag play` script |
| ROS1 | ROS2 bag | Convert to ROS1 `.bag` and generate `rosbag play` script |

The Web runtime needs the pinned `rosbags` package from `SLAM_Hive/requirements.txt`. The algorithm image still needs its own ROS playback command (`rosbag` for ROS1 or `ros2 bag` for ROS2). Conversion is a file operation before the algorithm container starts; no live ROS bridge is involved.

ROS version detection checks `algorithm-attribute` and the algorithm image tag for `ros2` or `ros1` (otherwise it defaults to ROS1). A dataset may declare `ros_version: ros2` or `bag_format: ros2` in `dataset_manifest.yaml`; otherwise the scheduler looks for a rosbag2 `metadata.yaml` or a ROS1 `.bag`. A ROS2 dataset can place `metadata.yaml` at its root or in one or more bag subdirectories. If several bag directories exist, list the intended ones in the dataset manifest:

```yaml
ros_version: ros2
bags:
  - camera_bag
  - imu_bag
```

For ROS2-to-ROS1 conversion, the generated `rosbag_play.py` plays all selected converted bags in one `rosbag play ... --clock` process. An existing `dataset-parameters.ros2_bag`, `bag_name`, `bag_dir`, or `bag_path` value can select one source bag when a config needs only that bag. `bag_rate`, `bag_start`, and `bag_duration` map to ROS1 `-r`, `-s`, and `-u`. A `dataset-remap` entry maps an algorithm input topic to a source bag topic; for example `/scan: /laser/raw` becomes `/laser/raw:=/scan` in the playback command. Topic names are checked against the converted bag before playback.

The cache key includes source file sizes and modification times, converter version, and playback script version. Conversion logs are written to the mapping result directory as `rosbag_conversion.log`; a failed conversion also writes `conversion_failed.txt` and marks the mapping task failed. `conversion_manifest.yaml` in the cache records source bags, output bags, and topics.

Conversion changes the bag format, not the semantics of its messages. The ROS1 algorithm must still support the resulting message types and topics. The pinned converter may reject ROS2 bags containing unsupported custom message types or storage layouts; those require a dataset-specific conversion path. Check the conversion log before changing algorithm code.
