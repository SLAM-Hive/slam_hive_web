# Dataset playback and ROS1 / ROS2

An algorithm runs with one ROS version; a dataset holds ROS1 or ROS2 bags in any
of their formats. The platform plays the dataset to the algorithm in the
algorithm's ROS version. Algorithms only receive topics.

Code: `SLAM_Hive/slamhive/task/playback.py` (what is played),
`SLAM_Hive/slamhive/task/ros_interop.py` (the table, conversions, dataset view),
`SLAM_Hive/slamhive/task/slamhive_player.py` (player in the container),
`bagtools/bagformat.py` (what a bag is), `bagtools/` (converter image).

## 1. The algorithm's ROS version

Set when the algorithm is registered (Algorithm page, field *ROS version*:
`ros1`, `ros2` or `other`), stored in `algorithm.rosVersion` and written into
every task config as `algorithm-ros-version`. The registration page only warns
when the image's `ROS_DISTRO` says otherwise. Existing algorithms were filled
from their images with `flask migrate-algorithm-ros-version` (idempotent; run
it in `SLAM_Hive/` with `FLASK_APP=slamhive` after a fresh database import).

## 2. What a bag is

`bagtools/bagformat.py` is the only code that decides it, from file contents:

| Bag | Recognised by | Version / distro from |
| --- | --- | --- |
| ROS1 bag | file starts with `#ROSBAG V` | magic line (`2.0`); bag header (indexed or not); first chunk (`none`/`bz2`/`lz4`) |
| rosbag2 directory | `metadata.yaml` | `version`, `storage_identifier`, `compression_*`, `ros_distro`; else the `.db3` `schema` table |
| bare `.db3` | SQLite magic | `schema` table, `metadata` table (copy of metadata.yaml), `message_definitions` |
| bare `.mcap` | mcap magic | header profile (`ros2`/`ros1`), `rosbag2` metadata record |

Each bag gets a record (`family`, `storage`, `format_version`, `ros_distro`,
`compression`, `issues`, `notes`, `label`, e.g. `ROS2 sqlite3 v5 humble, zstd
file compression, 3 files`). `issues` (not indexed, ROS1 format 1.2, files
missing) stop a task that plays the bag. Build the image once, then inspect any
dataset:

```bash
docker build -t slam-hive-bagtools:1 /SLAM-Hive/slam_hive_web/bagtools
docker run --rm -v /SLAM-Hive/slam_hive_datasets/<dataset>:/src:ro slam-hive-bagtools:1 scan /src
```

## 3. What a dataset plays: `slamhive_dataset.yaml`

Every dataset folder describes its bags and playback; the task config
(`dataset-parameters`, `dataset-remap`) selects and adjusts. `rosbag_play.py`
files in dataset folders are no longer run.

```yaml
version: 1
bags:                       # id -> path in the dataset folder (ROS1 .bag, rosbag2 dir or file)
  lidar: bpearl_front.bag
  imu: mti.bag
play:
  bags: [lidar]             # always played
  topics: []                # play only these topics (empty: all)
  rate: 1.0                 # dataset-parameters bag_rate / bag_start / bag_duration override
  start: 0
  duration: -1              # seconds, -1: to the end
switches:                   # boolean dataset-parameters adding bags/topics
  play_mti: {default: false, bags: [imu]}
choices:                    # dataset-parameters choosing one named value
  bag_profile: {default: full, values: {full: {bags: [lidar]}}}
rules:                      # checks with the message shown when they fail
  - {exactly_one: [play_a, play_b], message: "..."}   # also at_least_one, all_or_none,
                                                      # must_be_true, must_be_false
```

`bag_rate`, `bag_start`, `bag_duration` work for every dataset. Every
`dataset-remap` entry (`algorithm topic: bag topic`) becomes a remap; remapping
a topic that is not played has no effect.

A new dataset needs this file; copy one from a similar dataset. The existing
datasets got theirs generated from their old `rosbag_play.py`; the old script
was run, unchanged, under all historical task configs and every switch
combination to check that both play the same bags, topics, rate and window:
133 datasets verified over 1277 configs, 6 without a legacy script generated
from their bags.

## 4. The table

| algorithm \ bag | ROS1 bag | ROS2 bag |
| --- | --- | --- |
| `ros1`, `other` | as is | converted to a ROS1 bag |
| `ros2` | converted to mcap | as is when every ROS2 image plays it (rosbag2 directory, sqlite3 or mcap, metadata ≤ v8, no compression or zstd); else converted to mcap |

* **Platform ROS2 format: mcap, metadata v8.** Every ROS2 algorithm image must
  install `ros-<distro>-rosbag2-storage-mcap` (Humble ships only sqlite3) —
  see `slam_hive_algos/rtabmap-ros2/Dockerfile`. Metadata v9 (Jazzy) is not
  parsed by Humble, so v9 bags are converted.
* Converted bags are **not compressed**, on purpose: the player runs inside the
  algorithm container, so decompression would compete with real-time
  algorithms and be counted in their measured CPU/RAM. The cache can grow
  large; it is regenerable, so delete entries instead of compressing them.
* A ROS2 algorithm plays one bag: several selected bags, ROS1 bags or a v9 bag
  are converted together into one mcap bag cut to the selected topics and
  window. A ROS1 algorithm gets each ROS2 bag as a whole ROS1 bag and
  `rosbag play` does the rest (several bags, `--topics`, `-s`, `-u`).
* Conversions (`slam-hive-bagtools:1`: Python 3.12, rosbags 0.11.5) read every
  ROS1/ROS2 version directly. Converting to ROS2 strips a leading `/` from frame
  ids (tf2 rejects them) and keeps `/tf_static` latched (transient local).
  Topics a bag cannot decode (a Humble sqlite3 bag stores no message
  definitions; a topic written with another definition) are skipped and listed
  as `skipped_topics`.
* Cache: `slam_hive_datasets/.converted/<dataset>__<kind>__<hash>/` with
  `conversion.json`; the hash covers source files (size, mtime), topics,
  window and the bagtools image id. Delete entries to free disk.

## 5. What the algorithm container sees

| Path | Content |
| --- | --- |
| `/slamhive/dataset` | per-task view (`mapping_results/<task>/dataset_view`): links to every file of the dataset, converted bags (`<name>.bag` for ROS1, `_ros2_playback` for ROS2), `rosbag_play.py` = the platform player, `playback.json` |
| `/slamhive/dataset_src` | the registered dataset folder (read-only) |
| `/slamhive/.bagcache` | converted bags (read-only) |

Algorithms keep calling `python3 /slamhive/dataset/rosbag_play.py`; it runs the
planned `rosbag play ...` / `ros2 bag play ... --clock 100 --delay 1` (the delay
lets DDS discovery finish; for ROS2 `bag_duration` is a timeout). Algorithms that
open `*.bag` themselves find ROS1 bags in the view. Each task writes its
decision to `mapping_results/<task>/interop/decision.json` (playback, bag
records, command, conversions, warnings).

## 6. Task isolation

Algorithm containers run on the Docker bridge network (`ALGO_CONTAINER_NETWORK`
in `configuration.py`; `"host"` restores the old behaviour) with
`ROS_DOMAIN_ID = 1 + task_id % 100`, so ROS1 tasks (roscore on 11311) and ROS2
tasks (DDS) can run at the same time. Real-time algorithms are still sensitive
to machine load: compare accuracy on runs that did not share the machine.

## 7. Limits

* Conversion changes the container format, not the meaning of the data: topics,
  frames, calibration and time sync still come from the config
  (`dataset-remap`, algorithm parameters). Example: a dataset whose `/tf`
  contains mocap `world→camera` must remap `/tf` away for an algorithm that
  publishes that transform.
* `dataset-frequency` / `dataset-resolution` preprocessing (module_b) only
  handles a ROS1 `<dataset>/<dataset>.bag`; other datasets fail at once.

## 8. Verification (2026-09-28)

Through the Web API, same parameters as the reference run; ROS2 datasets were
written by the real `ros2 bag convert`.

| algorithm (ROS) | dataset | table cell | ATE [m] | reference |
| --- | --- | --- | --- | --- |
| vins-mono (ros1) | EuRoC MH_01, ROS1 | as is | 0.1037 | 0.099–0.100 earlier runs |
| orb-slam2-rgbd (ros1) | TUM fr2_desk, Jazzy mcap v9 | ROS2 → ROS1 | 0.0061 | 0.0062 native |
| gmapping (ros1) | TUM pioneer, Humble sqlite3 v5 | ROS2 → ROS1 | 0.197 | 0.189 native |
| HectorSLAM (ros1) | rtabmap_demo, sqlite3 v8 | ROS2 → ROS1 | success (no GT) | |
| fast-lio2 (ros1) | bpearl + MTI, 2 ROS1 bags by switches | as is | 13.2277 | 13.2277 |
| fast-lio2 (ros1) | bpearl + MTI merged, Jazzy mcap | ROS2 → ROS1 | 13.2277 | 13.2277 |
| rtabmap (ros2) | rtabmap_demo, sqlite3 v8 | as is | success | |
| rtabmap (ros2) | rtabmap_demo ROS1 source | ROS1 → mcap v8 | 0.98 cm from the as-is run | two as-is runs differ by 1.8 cm |
| rtabmap (ros2) | TUM fr1_xyz ROS1 (bz2, `/frame` ids) | ROS1 → mcap v8 | 0.058 | 0.033–0.065 over 5 earlier runs |
| rtabmap (ros2) | TUM fr1_xyz, Jazzy mcap v9 | v9 → mcap v8 | 0.058 | same |
| droid-slam (other) | TUM fr1_xyz ROS1 | as is | 0.113107 | 0.113107 |
| droid-slam (other) | TUM fr1_xyz, Jazzy mcap v9 | ROS2 → ROS1 | 0.113107 | 0.113107 |

A fast-lio2 run that shared the machine with a 4 GB conversion gave 13.42; run
alone it gave 13.2277 again.
