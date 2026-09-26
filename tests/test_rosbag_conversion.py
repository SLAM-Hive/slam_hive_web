"""Contract tests for automatic ROS2-to-ROS1 dataset preparation."""

import ast
import importlib.util
import sys
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import yaml


TASK_DIR = Path(__file__).resolve().parents[1] / "SLAM_Hive" / "slamhive" / "task"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


conversion = load_module("tested_rosbag_conversion", TASK_DIR / "rosbag_conversion.py")
player = load_module("tested_rosbag_play_ros1", TASK_DIR / "rosbag_play_ros1.py")


class RosbagConversionTests(unittest.TestCase):
    def test_conversion_failure_marks_task_failed_and_stops_polling(self):
        # Import only these callbacks: the legacy blueprint starts a scheduler at import time.
        blueprint = TASK_DIR.parent / "blueprints" / "mappingtask.py"
        tree = ast.parse(blueprint.read_text(encoding="utf-8"))
        callbacks = [
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in {"RunMapping", "CheckTask"}
        ]
        namespace = {}
        exec(compile(ast.Module(body=callbacks, type_ignores=[]), str(blueprint), "exec"), namespace)

        task = SimpleNamespace(state="Running", trajectory_state="Running")
        namespace.update(
            app=SimpleNamespace(logger=mock.Mock(), app_context=nullcontext),
            db=SimpleNamespace(session=mock.Mock()),
            MappingTask=SimpleNamespace(query=SimpleNamespace(get=lambda _task_id: task)),
            mapping_cadvisor=SimpleNamespace(mapping_task=mock.Mock(side_effect=RuntimeError("conversion failed"))),
            scheduler=mock.Mock(),
        )
        namespace["scheduler"].get_job.return_value = object()

        with self.assertRaisesRegex(RuntimeError, "conversion failed"):
            namespace["RunMapping"]("config.yaml", "123")
        self.assertEqual((task.state, task.trajectory_state), ("Failed", "Unsuccess"))
        namespace["db"].session.commit.assert_called_once()

        namespace["CheckTask"](123)
        namespace["scheduler"].remove_job.assert_called_once_with("123")

    def test_ros1_algorithm_gets_converted_ros2_dataset(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset = Path(directory)
            (dataset / "metadata.yaml").write_text("rosbag2_bagfile_information: {}\n")
            config = {"slam-hive-algorithm": "example-ros1", "slam-hive-dataset": "source"}
            with mock.patch.object(
                conversion,
                "materialize_ros1_dataset",
                return_value=("/converted", "key", "/manifest", "converted"),
            ) as materialize:
                prepared = conversion.prepare_dataset_for_mapping(config, str(dataset), "/result")

            materialize.assert_called_once_with(str(dataset), "/result", logger=None)
            self.assertEqual(prepared.dataset_path, "/converted")
            self.assertEqual((prepared.algorithm_ros, prepared.dataset_ros), ("ros1", "ros2"))

    def test_existing_ros1_to_ros2_direction_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset = Path(directory)
            (dataset / "sample.bag").write_bytes(b"bag")
            config = {"slam-hive-algorithm": "example-ros2", "slam-hive-dataset": "source"}
            with mock.patch.object(
                conversion,
                "materialize_ros2_dataset",
                return_value=("/converted", "key", "/manifest", "converted"),
            ) as materialize:
                prepared = conversion.prepare_dataset_for_mapping(config, str(dataset), "/result")

            materialize.assert_called_once_with(str(dataset), "/result", logger=None)
            self.assertEqual((prepared.algorithm_ros, prepared.dataset_ros), ("ros2", "ros1"))

    def test_manifest_selection_and_data_change_invalidate_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first"
            second = root / "second"
            for bag in (first, second):
                bag.mkdir()
                (bag / "metadata.yaml").write_text("rosbag2_bagfile_information: {}\n")
                (bag / "data.db3").write_bytes(b"a")
            (root / "dataset_manifest.yaml").write_text(yaml.safe_dump({"bags": ["first"]}))

            self.assertEqual(conversion.find_source_ros2_bags(root), [first.resolve()])
            with mock.patch.object(conversion, "_rosbags_version", return_value="test"):
                before, _ = conversion.build_ros1_cache_key(root, [first.resolve()])
                (first / "data.db3").write_bytes(b"changed")
                after, _ = conversion.build_ros1_cache_key(root, [first.resolve()])
            self.assertNotEqual(before, after)

    def test_generated_ros1_player_uses_one_clock_and_reversed_remap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ros1_bags").mkdir()
            for name in ("camera.bag", "imu.bag"):
                (root / "ros1_bags" / name).write_bytes(b"bag")
            manifest = {
                "converted_bags": [
                    {"source": "camera", "output": "ros1_bags/camera.bag", "topics": ["/camera/raw"]},
                    {"source": "imu", "output": "ros1_bags/imu.bag", "topics": ["/mti/imu"]},
                ]
            }
            config = {
                "dataset-parameters": {"bag_rate": 0.5, "bag_start": 2, "bag_duration": 8},
                "dataset-remap": {"/imu/data": "/mti/imu"},
            }
            manifest_path = root / "conversion_manifest.yaml"
            config_path = root / "config.yaml"
            manifest_path.write_text(yaml.safe_dump(manifest))
            config_path.write_text(yaml.safe_dump(config))

            with mock.patch.object(player, "DATASET_ROOT", root), mock.patch.object(player, "CONFIG_PATH", config_path), mock.patch.object(player.subprocess, "run") as run:
                player.main()

            run.assert_called_once()
            command = run.call_args.args[0]
            self.assertEqual(command[:2], ["rosbag", "play"])
            self.assertEqual(command.count("--clock"), 1)
            self.assertEqual(len([part for part in command if part.endswith(".bag")]), 2)
            self.assertIn("/mti/imu:=/imu/data", command)
            self.assertEqual(command[command.index("-r") + 1], "0.5")
            self.assertEqual(command[command.index("-s") + 1], "2.0")
            self.assertEqual(command[command.index("-u") + 1], "8.0")

    def test_existing_bag_path_selects_one_source_bag(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ros1_bags").mkdir()
            for name in ("camera.bag", "imu.bag"):
                (root / "ros1_bags" / name).write_bytes(b"bag")
            manifest = {
                "converted_bags": [
                    {"source": "camera", "output": "ros1_bags/camera.bag", "topics": []},
                    {"source": "imu", "output": "ros1_bags/imu.bag", "topics": []},
                ]
            }
            with mock.patch.object(player, "DATASET_ROOT", root):
                selected = player.select_bags({"bag_path": "/slamhive/dataset/imu"}, manifest)
            self.assertEqual([entry["source"] for _, entry in selected], ["imu"])


if __name__ == "__main__":
    unittest.main()
