#!/usr/bin/env python3
"""Playback entrypoint copied into an automatically converted ROS1 dataset."""

import shlex
import subprocess
from pathlib import Path

import yaml


CONFIG_PATH = Path("/slamhive/config.yaml")
DATASET_ROOT = Path("/slamhive/dataset")


def load_yaml(path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def parse_float(value, default):
    return default if value in (None, "") else float(value)


def shell_join(parts):
    if hasattr(shlex, "join"):
        return shlex.join(parts)
    return " ".join(shlex.quote(str(part)) for part in parts)


def select_bags(params, manifest):
    entries = manifest.get("converted_bags") or []
    if not entries:
        raise RuntimeError("Converted dataset has no ROS1 bags")

    selection = (
        params.get("ros2_bag")
        or params.get("bag_name")
        or params.get("bag_dir")
        or params.get("bag_path")
    )
    if selection:
        selected_name = Path(str(selection).rstrip("/")).name
        entries = [
            entry for entry in entries
            if selected_name in {
                Path(entry["source"]).name,
                Path(entry["output"]).name,
                Path(entry["output"]).stem,
            }
        ]
        if len(entries) != 1:
            raise RuntimeError("ROS2 bag selection did not identify exactly one converted bag: {}".format(selection))

    selected = []
    root = DATASET_ROOT.resolve()
    for entry in entries:
        bag_path = (root / entry["output"]).resolve()
        try:
            bag_path.relative_to(root)
        except ValueError as exc:
            raise RuntimeError("Converted bag path is outside the dataset: {}".format(bag_path)) from exc
        if not bag_path.is_file():
            raise FileNotFoundError("Converted ROS1 bag not found: {}".format(bag_path))
        selected.append((bag_path, entry))
    return selected


def build_remaps(config, selected):
    known_topics = {topic for _, entry in selected for topic in entry.get("topics", [])}
    remaps = []
    for expected_topic, original_topic in (config.get("dataset-remap") or {}).items():
        original = str(original_topic).strip()
        expected = str(expected_topic).strip()
        if original not in known_topics:
            raise RuntimeError("dataset-remap source topic does not exist in converted ROS1 bag: {}".format(original))
        remaps.append("{}:={}".format(original, expected))
    return remaps


def main():
    config = load_yaml(CONFIG_PATH)
    manifest = load_yaml(DATASET_ROOT / "conversion_manifest.yaml")
    params = config.get("dataset-parameters") or {}
    selected = select_bags(params, manifest)

    rate = parse_float(params.get("bag_rate"), 1.0)
    start = parse_float(params.get("bag_start"), 0.0)
    duration = parse_float(params.get("bag_duration"), -1.0)
    if rate <= 0 or start < 0:
        raise ValueError("bag_rate must be positive and bag_start must be nonnegative")

    command = ["rosbag", "play"] + [str(path) for path, _ in selected]
    command.extend(["--clock", "-r", str(rate)])
    if start > 0:
        command.extend(["-s", str(start)])
    if duration > 0:
        command.extend(["-u", str(duration)])
    command.extend(build_remaps(config, selected))

    print("[rosbag_play.py] selected_bags={}".format([entry["source"] for _, entry in selected]), flush=True)
    print("[rosbag_play.py] command={}".format(shell_join(command)), flush=True)
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
