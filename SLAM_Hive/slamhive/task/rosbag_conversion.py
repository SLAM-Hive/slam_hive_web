import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import yaml


HOST_DATASETS_ROOT = Path("/SLAM-Hive/slam_hive_datasets")
CONTAINER_DATASETS_ROOT = Path("/slam_hive_datasets")
HOST_RESULTS_ROOT = Path("/SLAM-Hive/slam_hive_results")
CONTAINER_RESULTS_ROOT = Path("/slam_hive_results")
CONVERSION_DIR_NAME = ".converted"
CONVERSION_SCHEMA_VERSION = 1
PLAY_SCRIPT_VERSION = 2
ROS1_PLAY_SCRIPT_VERSION = 2


@dataclass
class PreparedDataset:
    dataset_path: str
    algorithm_ros: str
    dataset_ros: str
    status: str
    cache_key: str = ""
    manifest_path: str = ""


def _logger_info(logger, message):
    if logger is not None:
        logger.info(message)
    else:
        print(message)


def _logger_error(logger, message):
    if logger is not None:
        logger.error(message)
    else:
        print(message, file=sys.stderr)


def _as_path(path):
    return Path(str(path))


def host_to_local_path(path):
    path = _as_path(path)
    text = str(path)
    if CONTAINER_DATASETS_ROOT.exists() and text.startswith(str(HOST_DATASETS_ROOT)):
        return CONTAINER_DATASETS_ROOT / path.relative_to(HOST_DATASETS_ROOT)
    if CONTAINER_RESULTS_ROOT.exists() and text.startswith(str(HOST_RESULTS_ROOT)):
        return CONTAINER_RESULTS_ROOT / path.relative_to(HOST_RESULTS_ROOT)
    return path


def local_to_host_path(path):
    path = _as_path(path)
    text = str(path)
    if text.startswith(str(CONTAINER_DATASETS_ROOT)):
        return HOST_DATASETS_ROOT / path.relative_to(CONTAINER_DATASETS_ROOT)
    if text.startswith(str(CONTAINER_RESULTS_ROOT)):
        return HOST_RESULTS_ROOT / path.relative_to(CONTAINER_RESULTS_ROOT)
    return path


def normalize_ros_version(value):
    text = str(value or "").strip().lower().replace("_", "").replace("-", "").replace(" ", "")
    if text in {"ros2", "2"}:
        return "ros2"
    if text in {"ros1", "1"}:
        return "ros1"
    return ""


def detect_algorithm_ros(config_dict):
    fields = [
        config_dict.get("algorithm-attribute"),
        config_dict.get("slam-hive-algorithm"),
    ]
    for field in fields:
        text = str(field or "").lower()
        compact = text.replace("_", "").replace("-", "").replace(" ", "")
        if "ros2" in compact:
            return "ros2"
        if "ros1" in compact:
            return "ros1"
    return "ros1"


def _read_yaml(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except Exception:
        return {}


def detect_dataset_ros(dataset_path):
    local_path = host_to_local_path(dataset_path)
    manifest = local_path / "dataset_manifest.yaml"
    if manifest.exists():
        data = _read_yaml(manifest)
        for key in ("ros_version", "bag_format", "native_ros"):
            version = normalize_ros_version(data.get(key))
            if version:
                return version

    conversion_manifest = local_path / "conversion_manifest.yaml"
    if conversion_manifest.exists():
        data = _read_yaml(conversion_manifest)
        version = normalize_ros_version(data.get("target_ros_version"))
        if version:
            return version

    if (local_path / "metadata.yaml").exists():
        return "ros2"
    for metadata in local_path.rglob("metadata.yaml"):
        if CONVERSION_DIR_NAME not in metadata.parts:
            return "ros2"
    for bag in local_path.rglob("*.bag"):
        if CONVERSION_DIR_NAME not in bag.parts:
            return "ros1"
    return "ros1"


def _dataset_name(dataset_path):
    return host_to_local_path(dataset_path).name


def _safe_name(value):
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("._")
    return text or "dataset"


def _rosbags_version():
    try:
        return importlib.metadata.version("rosbags")
    except Exception:
        return "unknown"


def _source_bags_from_manifest(dataset_path):
    local_path = host_to_local_path(dataset_path)
    manifest = local_path / "dataset_manifest.yaml"
    if not manifest.exists():
        return []
    data = _read_yaml(manifest)
    bag_values = data.get("bags") or data.get("source_bags") or []
    if isinstance(bag_values, str):
        bag_values = [bag_values]
    bags = []
    for item in bag_values:
        if isinstance(item, dict):
            value = item.get("path") or item.get("bag") or item.get("name")
        else:
            value = item
        if not value:
            continue
        bag_path = Path(str(value))
        if not bag_path.is_absolute():
            bag_path = local_path / bag_path
        if bag_path.exists() and bag_path.suffix == ".bag":
            bags.append(bag_path)
    return bags


def find_source_bags(dataset_path):
    local_path = host_to_local_path(dataset_path)
    bags = _source_bags_from_manifest(dataset_path)
    if not bags:
        bags = [
            path
            for path in local_path.rglob("*.bag")
            if CONVERSION_DIR_NAME not in path.parts
        ]
    bags = sorted(set(bags), key=lambda path: str(path.relative_to(local_path)))
    if not bags:
        raise RuntimeError("No ROS1 .bag files found in dataset: {}".format(local_path))
    return bags


def find_source_ros2_bags(dataset_path):
    """Find rosbag2 directories, using an explicit dataset manifest when present."""
    local_root = host_to_local_path(dataset_path)
    manifest = _read_yaml(local_root / "dataset_manifest.yaml")
    bag_values = manifest.get("bags") or manifest.get("source_bags")
    if bag_values:
        if isinstance(bag_values, (str, dict)):
            bag_values = [bag_values]
        bags = []
        for item in bag_values:
            value = (
                item.get("path") or item.get("bag") or item.get("name")
            ) if isinstance(item, dict) else item
            if not value:
                raise RuntimeError("ROS2 dataset manifest contains a bag without a path")
            bag = Path(str(value))
            if not bag.is_absolute():
                bag = local_root / bag
            try:
                bag = bag.resolve()
                bag.relative_to(local_root.resolve())
            except ValueError as exc:
                raise RuntimeError("ROS2 bag must be inside its dataset: {}".format(bag)) from exc
            if not (bag / "metadata.yaml").is_file():
                raise RuntimeError("ROS2 bag metadata.yaml not found: {}".format(bag))
            bags.append(bag)
    elif (local_root / "metadata.yaml").is_file():
        bags = [local_root.resolve()]
    else:
        bags = [
            metadata.parent.resolve()
            for metadata in local_root.rglob("metadata.yaml")
            if CONVERSION_DIR_NAME not in metadata.parts
        ]
    bags = sorted(set(bags), key=lambda bag: str(bag.relative_to(local_root.resolve())))
    if not bags:
        raise RuntimeError("No ROS2 bag metadata.yaml found in dataset: {}".format(local_root))
    return bags


def _file_fingerprint(path, dataset_root):
    stat = path.stat()
    return {
        "path": str(path.relative_to(dataset_root)),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def build_cache_key(dataset_path, source_bags):
    local_root = host_to_local_path(dataset_path)
    payload = {
        "schema": CONVERSION_SCHEMA_VERSION,
        "play_script": PLAY_SCRIPT_VERSION,
        "source_dataset": _dataset_name(dataset_path),
        "source_ros_version": "ros1",
        "target_ros_version": "ros2",
        "converter": "rosbags",
        "converter_version": _rosbags_version(),
        "source_bags": [
            _file_fingerprint(path, local_root)
            for path in source_bags
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), payload


def build_ros1_cache_key(dataset_path, source_bags):
    local_root = host_to_local_path(dataset_path).resolve()
    payload = {
        "schema": CONVERSION_SCHEMA_VERSION,
        "play_script": ROS1_PLAY_SCRIPT_VERSION,
        "source_dataset": _dataset_name(dataset_path),
        "source_ros_version": "ros2",
        "target_ros_version": "ros1",
        "converter": "rosbags",
        "converter_version": _rosbags_version(),
        "source_bags": [
            {
                "path": str(bag.relative_to(local_root)),
                "files": [
                    _file_fingerprint(path, local_root)
                    for path in sorted(bag.rglob("*")) if path.is_file()
                ],
            }
            for bag in source_bags
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), payload


def _converted_host_path(dataset_path, cache_key):
    name = "{}__ros1_to_ros2__{}".format(_safe_name(_dataset_name(dataset_path)), cache_key[:16])
    return HOST_DATASETS_ROOT / CONVERSION_DIR_NAME / name


def _converted_ros1_host_path(dataset_path, cache_key):
    name = "{}__ros2_to_ros1__{}".format(_safe_name(_dataset_name(dataset_path)), cache_key[:16])
    return HOST_DATASETS_ROOT / CONVERSION_DIR_NAME / name


def _write_yaml(path, data):
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, default_flow_style=False, sort_keys=False)


def _copy_common_files(source_root, target_root):
    for name in ("groundtruth.txt", "groundtruth.tum"):
        source = source_root / name
        if source.exists() and source.is_file():
            shutil.copy2(str(source), str(target_root / name))


def _bag_output_name(source_bag, used_names):
    base = _safe_name(source_bag.stem)
    name = base
    suffix = 2
    while name in used_names:
        name = "{}_{}".format(base, suffix)
        suffix += 1
    used_names.add(name)
    return name


def _run_convert(source_bag, output_dir, log_file):
    converter = shutil.which("rosbags-convert")
    if not converter:
        raise RuntimeError("rosbags-convert not found. Install the Python package 'rosbags' in the Web runtime.")
    cmd = [converter, str(source_bag), "--dst", str(output_dir)]
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write("[rosbags-convert] {}\n".format(" ".join(cmd)))
        handle.flush()
        subprocess.run(cmd, stdout=handle, stderr=subprocess.STDOUT, check=True)


def _generate_ros2_play_script(path):
    script = r'''#!/usr/bin/env python3
import shlex
import subprocess
from pathlib import Path

import yaml


CONFIG_PATH = Path("/slamhive/config.yaml")
DATASET_ROOT = Path("/slamhive/dataset")
ROS2_BAGS_ROOT = DATASET_ROOT / "ros2_bags"


def load_config():
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def parse_float(value, default):
    if value in (None, ""):
        return default
    return float(value)


def shell_join(parts):
    if hasattr(shlex, "join"):
        return shlex.join(parts)
    return " ".join(shlex.quote(str(part)) for part in parts)


def available_bag_dirs():
    if not ROS2_BAGS_ROOT.exists():
        return []
    return sorted(path for path in ROS2_BAGS_ROOT.iterdir() if (path / "metadata.yaml").exists())


def resolve_bag_dir(dataset_params):
    bag_value = (
        dataset_params.get("ros2_bag")
        or dataset_params.get("bag_name")
        or dataset_params.get("bag_dir")
        or dataset_params.get("bag_path")
    )
    bag_dirs = available_bag_dirs()
    if bag_value:
        candidate = Path(str(bag_value))
        if not candidate.is_absolute():
            direct = DATASET_ROOT / candidate
            by_name = ROS2_BAGS_ROOT / candidate
            candidate = direct if direct.exists() else by_name
        if not candidate.exists():
            raise FileNotFoundError("Selected ROS2 bag does not exist: {}".format(candidate))
        return candidate
    if len(bag_dirs) == 1:
        return bag_dirs[0]
    if not bag_dirs:
        raise FileNotFoundError("No ROS2 bag metadata found under {}".format(ROS2_BAGS_ROOT))
    names = ", ".join(path.name for path in bag_dirs)
    raise RuntimeError("Multiple converted ROS2 bags are available; set dataset parameter ros2_bag to one of: {}".format(names))


def metadata_topics(bag_dir):
    metadata_path = bag_dir / "metadata.yaml"
    if not metadata_path.exists():
        return set()
    with metadata_path.open("r", encoding="utf-8") as handle:
        metadata = yaml.safe_load(handle) or {}
    topics = set()
    for item in metadata.get("rosbag2_bagfile_information", {}).get("topics_with_message_count", []):
        name = item.get("topic_metadata", {}).get("name")
        if name:
            topics.add(name)
            topics.add("/" + name.lstrip("/"))
    return topics


def build_remaps(config, bag_dir):
    remaps = []
    known_topics = metadata_topics(bag_dir)
    for expected_topic, original_topic in (config.get("dataset-remap") or {}).items():
        original = str(original_topic).strip()
        expected = str(expected_topic).strip()
        if known_topics and original not in known_topics:
            raise RuntimeError("dataset-remap source topic does not exist in converted bag: {}".format(original))
        remaps.append("{}:={}".format(original, expected))
    return remaps


def main():
    config = load_config()
    dataset_params = config.get("dataset-parameters") or {}
    bag_dir = resolve_bag_dir(dataset_params)
    rate = parse_float(dataset_params.get("bag_rate"), 1.0)
    start_offset = parse_float(dataset_params.get("bag_start"), 0.0)
    duration = parse_float(dataset_params.get("bag_duration"), -1.0)
    remaps = build_remaps(config, bag_dir)

    cmd = [
        "ros2",
        "bag",
        "play",
        str(bag_dir),
        "--clock",
        "--disable-keyboard-controls",
        "--rate",
        str(rate),
    ]
    if start_offset > 0:
        cmd.extend(["--start-offset", str(start_offset)])
    if remaps:
        cmd.append("--remap")
        cmd.extend(remaps)
    if duration > 0:
        cmd = ["timeout", "--kill-after", "15", str(duration)] + cmd

    print("[rosbag_play.py] selected converted ROS2 bag: {}".format(bag_dir), flush=True)
    print("[rosbag_play.py] command: {}".format(shell_join(cmd)), flush=True)
    result = subprocess.run(cmd, check=False)
    if result.returncode in {124, 137} and duration > 0:
        print("[rosbag_play.py] timeout reached after {}s; treating bounded playback as complete".format(duration), flush=True)
        return
    result.check_returncode()


if __name__ == "__main__":
    main()
'''
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)


def _generate_ros1_play_script(path):
    shutil.copy2(str(Path(__file__).with_name("rosbag_play_ros1.py")), str(path))
    path.chmod(0o755)


def _ros1_bag_topics(path):
    from rosbags.rosbag1 import Reader

    reader = Reader(str(path))
    reader.open()
    try:
        return sorted({connection.topic for connection in reader.connections})
    finally:
        reader.close()


def _ros1_cache_ready(target_local):
    manifest = _read_yaml(target_local / "conversion_manifest.yaml")
    converted_bags = manifest.get("converted_bags") or []
    return (
        (target_local / "rosbag_play.py").is_file()
        and bool(converted_bags)
        and all(
            isinstance(item, dict)
            and bool(item.get("topics"))
            and isinstance(item.get("output"), str)
            and (target_local / item["output"]).is_file()
            and (target_local / item["output"]).stat().st_size > 0
            for item in converted_bags
        )
    )


def _cache_ready(target_local):
    return (
        (target_local / "conversion_manifest.yaml").exists()
        and (target_local / "rosbag_play.py").exists()
        and any((path / "metadata.yaml").exists() for path in (target_local / "ros2_bags").glob("*"))
    )


def _write_conversion_failure(result_path, message):
    local_result = host_to_local_path(result_path)
    try:
        local_result.mkdir(parents=True, exist_ok=True)
        (local_result / "conversion_failed.txt").write_text(message + "\n", encoding="utf-8")
    except Exception:
        pass


def materialize_ros2_dataset(dataset_path, result_path, logger=None):
    source_root = host_to_local_path(dataset_path)
    source_bags = find_source_bags(dataset_path)
    cache_key, payload = build_cache_key(dataset_path, source_bags)
    target_host = _converted_host_path(dataset_path, cache_key)
    target_local = host_to_local_path(target_host)
    manifest_path = target_local / "conversion_manifest.yaml"
    log_path = host_to_local_path(result_path) / "rosbag_conversion.log"

    if _cache_ready(target_local):
        _logger_info(logger, "[rosbag_conversion] cache hit: {}".format(target_host))
        return str(target_host), cache_key, str(local_to_host_path(manifest_path)), "cache-hit"

    lock_dir = target_local.with_name(target_local.name + ".lock")
    start_time = time.time()
    while True:
        try:
            lock_dir.parent.mkdir(parents=True, exist_ok=True)
            lock_dir.mkdir()
            break
        except FileExistsError:
            if _cache_ready(target_local):
                _logger_info(logger, "[rosbag_conversion] cache became ready while waiting: {}".format(target_host))
                return str(target_host), cache_key, str(local_to_host_path(manifest_path)), "cache-hit"
            if time.time() - start_time > 1800:
                raise RuntimeError("Timed out waiting for ROS bag conversion lock: {}".format(lock_dir))
            time.sleep(5)

    tmp_local = target_local.with_name(target_local.name + ".tmp.{}".format(os.getpid()))
    try:
        if _cache_ready(target_local):
            return str(target_host), cache_key, str(local_to_host_path(manifest_path)), "cache-hit"
        if tmp_local.exists():
            shutil.rmtree(str(tmp_local))
        tmp_local.mkdir(parents=True)
        (tmp_local / "ros2_bags").mkdir()
        host_to_local_path(result_path).mkdir(parents=True, exist_ok=True)

        used_names = set()
        converted_bags = []
        for source_bag in source_bags:
            output_name = _bag_output_name(source_bag, used_names)
            output_dir = tmp_local / "ros2_bags" / output_name
            _logger_info(logger, "[rosbag_conversion] converting {} -> {}".format(source_bag, output_dir))
            _run_convert(source_bag, output_dir, log_path)
            if not (output_dir / "metadata.yaml").exists():
                raise RuntimeError("rosbags-convert did not create metadata.yaml at {}".format(output_dir))
            converted_bags.append(
                {
                    "source": str(source_bag.relative_to(source_root)),
                    "output": "ros2_bags/{}".format(output_name),
                }
            )

        _copy_common_files(source_root, tmp_local)
        _generate_ros2_play_script(tmp_local / "rosbag_play.py")
        manifest = dict(payload)
        manifest.update(
            {
                "source_dataset_path": str(local_to_host_path(source_root)),
                "target_dataset_path": str(target_host),
                "cache_key": cache_key,
                "converted_bags": converted_bags,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        _write_yaml(tmp_local / "conversion_manifest.yaml", manifest)
        _write_yaml(
            tmp_local / "dataset_manifest.yaml",
            {
                "dataset_name": target_host.name,
                "ros_version": "ros2",
                "bag_format": "ros2",
                "source_dataset": _dataset_name(dataset_path),
                "source_ros_version": "ros1",
            },
        )

        if target_local.exists():
            shutil.rmtree(str(target_local))
        tmp_local.rename(target_local)
        _logger_info(logger, "[rosbag_conversion] conversion ready: {}".format(target_host))
        return str(target_host), cache_key, str(local_to_host_path(manifest_path)), "converted"
    except Exception as exc:
        _write_conversion_failure(result_path, str(exc))
        _logger_error(logger, "[rosbag_conversion] conversion failed: {}".format(exc))
        if tmp_local.exists():
            shutil.rmtree(str(tmp_local), ignore_errors=True)
        raise
    finally:
        shutil.rmtree(str(lock_dir), ignore_errors=True)


def materialize_ros1_dataset(dataset_path, result_path, logger=None):
    source_root = host_to_local_path(dataset_path).resolve()
    source_bags = find_source_ros2_bags(dataset_path)
    cache_key, payload = build_ros1_cache_key(dataset_path, source_bags)
    target_host = _converted_ros1_host_path(dataset_path, cache_key)
    target_local = host_to_local_path(target_host)
    manifest_path = target_local / "conversion_manifest.yaml"
    log_path = host_to_local_path(result_path) / "rosbag_conversion.log"

    if _ros1_cache_ready(target_local):
        _logger_info(logger, "[rosbag_conversion] cache hit: {}".format(target_host))
        return str(target_host), cache_key, str(local_to_host_path(manifest_path)), "cache-hit"

    lock_dir = target_local.with_name(target_local.name + ".lock")
    start_time = time.time()
    while True:
        try:
            lock_dir.parent.mkdir(parents=True, exist_ok=True)
            lock_dir.mkdir()
            break
        except FileExistsError:
            if _ros1_cache_ready(target_local):
                _logger_info(logger, "[rosbag_conversion] cache became ready while waiting: {}".format(target_host))
                return str(target_host), cache_key, str(local_to_host_path(manifest_path)), "cache-hit"
            if time.time() - start_time > 1800:
                raise RuntimeError("Timed out waiting for ROS bag conversion lock: {}".format(lock_dir))
            time.sleep(5)

    tmp_local = target_local.with_name(target_local.name + ".tmp.{}".format(os.getpid()))
    try:
        if _ros1_cache_ready(target_local):
            return str(target_host), cache_key, str(local_to_host_path(manifest_path)), "cache-hit"
        if tmp_local.exists():
            shutil.rmtree(str(tmp_local))
        tmp_local.mkdir(parents=True)
        (tmp_local / "ros1_bags").mkdir()
        host_to_local_path(result_path).mkdir(parents=True, exist_ok=True)

        used_names = set()
        converted_bags = []
        for source_bag in source_bags:
            output_name = _bag_output_name(source_bag, used_names) + ".bag"
            output_bag = tmp_local / "ros1_bags" / output_name
            _logger_info(logger, "[rosbag_conversion] converting {} -> {}".format(source_bag, output_bag))
            _run_convert(source_bag, output_bag, log_path)
            if not output_bag.is_file() or output_bag.stat().st_size == 0:
                raise RuntimeError("rosbags-convert did not create ROS1 bag: {}".format(output_bag))
            topics = _ros1_bag_topics(output_bag)
            if not topics:
                raise RuntimeError("Converted ROS1 bag has no topics: {}".format(output_bag))
            converted_bags.append(
                {
                    "source": str(source_bag.relative_to(source_root)),
                    "output": "ros1_bags/{}".format(output_name),
                    "topics": topics,
                }
            )

        _copy_common_files(source_root, tmp_local)
        _generate_ros1_play_script(tmp_local / "rosbag_play.py")
        manifest = dict(payload)
        manifest.update(
            {
                "source_dataset_path": str(local_to_host_path(source_root)),
                "target_dataset_path": str(target_host),
                "cache_key": cache_key,
                "converted_bags": converted_bags,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        _write_yaml(tmp_local / "conversion_manifest.yaml", manifest)
        _write_yaml(
            tmp_local / "dataset_manifest.yaml",
            {
                "dataset_name": target_host.name,
                "ros_version": "ros1",
                "bag_format": "ros1",
                "source_dataset": _dataset_name(dataset_path),
                "source_ros_version": "ros2",
            },
        )

        if target_local.exists():
            shutil.rmtree(str(target_local))
        tmp_local.rename(target_local)
        _logger_info(logger, "[rosbag_conversion] conversion ready: {}".format(target_host))
        return str(target_host), cache_key, str(local_to_host_path(manifest_path)), "converted"
    except Exception as exc:
        _write_conversion_failure(result_path, str(exc))
        _logger_error(logger, "[rosbag_conversion] conversion failed: {}".format(exc))
        if tmp_local.exists():
            shutil.rmtree(str(tmp_local), ignore_errors=True)
        raise
    finally:
        shutil.rmtree(str(lock_dir), ignore_errors=True)


def prepare_dataset_for_mapping(config_dict, dataset_path, result_path, logger=None):
    algorithm_ros = detect_algorithm_ros(config_dict or {})
    dataset_ros = detect_dataset_ros(dataset_path)
    _logger_info(
        logger,
        "[rosbag_conversion] algorithm_ros={}, dataset_ros={}, dataset_path={}".format(
            algorithm_ros,
            dataset_ros,
            dataset_path,
        ),
    )
    if algorithm_ros == "ros2" and dataset_ros == "ros1":
        converted_path, cache_key, manifest_path, status = materialize_ros2_dataset(
            dataset_path,
            result_path,
            logger=logger,
        )
        return PreparedDataset(
            dataset_path=converted_path,
            algorithm_ros=algorithm_ros,
            dataset_ros=dataset_ros,
            status=status,
            cache_key=cache_key,
            manifest_path=manifest_path,
        )
    if algorithm_ros == "ros1" and dataset_ros == "ros2":
        converted_path, cache_key, manifest_path, status = materialize_ros1_dataset(
            dataset_path,
            result_path,
            logger=logger,
        )
        return PreparedDataset(
            dataset_path=converted_path,
            algorithm_ros=algorithm_ros,
            dataset_ros=dataset_ros,
            status=status,
            cache_key=cache_key,
            manifest_path=manifest_path,
        )
    return PreparedDataset(
        dataset_path=str(dataset_path),
        algorithm_ros=algorithm_ros,
        dataset_ros=dataset_ros,
        status="skipped",
    )
