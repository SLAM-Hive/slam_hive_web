"""Give an algorithm its dataset in the ROS version it runs with.

The scheduler calls :func:`prepare_dataset_for_mapping` before it starts an
algorithm container. Two facts decide everything:

* the algorithm's ROS version, a field set when it is registered
  (``algorithm.rosVersion``, written into the task config as
  ``algorithm-ros-version``): ros1 / ros2 / other;
* what each selected bag is, from ``bagformat`` (file contents).

What is played comes from the dataset's ``slamhive_dataset.yaml`` and the task
config (see ``playback.py``). Then one table:

    algorithm \\ bag   ROS1 bag            ROS2 bag
    ros1 / other      as is               converted to a ROS1 bag
    ros2              converted to mcap   as is if every ROS2 image plays it
                                          (sqlite3/mcap, metadata <= v8),
                                          else converted to mcap

A ROS2 algorithm plays one bag: several selected bags (or a non-playable one)
are converted together into one mcap bag (metadata v8) cut to the selected
topics and time window. Conversions run in the ``slam-hive-bagtools`` image
and are cached in ``slam_hive_datasets/.converted``.

The algorithm container sees a per-task dataset view at /slamhive/dataset:
links to every file of the dataset (/slamhive/dataset_src), converted bags
(/slamhive/.bagcache), and the player ``rosbag_play.py`` that runs the planned
command from ``playback.json``.
"""

import hashlib
import json
import os
import shlex
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from slamhive.task import playback

# What a bag is (ROS1/ROS2, storage, version, distro) is decided only by
# bagformat.py, shared with the bagtools image (slam_hive_web/bagtools).
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "bagtools"))
import bagformat  # noqa: E402


HOST_DATASETS_ROOT = Path("/SLAM-Hive/slam_hive_datasets")
CONTAINER_DATASETS_ROOT = Path("/slam_hive_datasets")
HOST_RESULTS_ROOT = Path("/SLAM-Hive/slam_hive_results")
CONTAINER_RESULTS_ROOT = Path("/slam_hive_results")
HOST_ALGOS_ROOT = Path("/SLAM-Hive/slam_hive_algos")
CONTAINER_ALGOS_ROOT = Path("/slam_hive_algos")
HOST_WEB_ROOT = Path("/SLAM-Hive/slam_hive_web")
CONTAINER_WEB_ROOT = Path("/home/slam_hive_web")

CACHE_DIR_NAME = ".converted"
BAGTOOLS_IMAGE = os.environ.get("SLAMHIVE_BAGTOOLS_IMAGE", "slam-hive-bagtools:1")
PLAYER_PATH = Path(__file__).with_name("slamhive_player.py")
LOCK_TIMEOUT_S = 4 * 3600

# Container-side layout.
IN_DATASET = "/slamhive/dataset"          # per-task view
IN_DATASET_SRC = "/slamhive/dataset_src"  # the registered dataset folder
IN_CACHE = "/slamhive/.bagcache"          # converted bags

ROS_VERSIONS = ("ros1", "ros2", "other")
ROS1_DISTROS = {"indigo", "jade", "kinetic", "lunar", "melodic", "noetic"}
ROS2_DISTROS = {
    "ardent", "bouncy", "crystal", "dashing", "eloquent", "foxy", "galactic",
    "humble", "iron", "jazzy", "kilted", "lyrical", "rolling",
}


class InteropError(RuntimeError):
    pass


@dataclass
class PreparedDataset:
    dataset_path: str                     # host path mounted at /slamhive/dataset
    algorithm_ros: str
    dataset_ros: str
    status: str                           # summary, e.g. "ros2 <- x.bag (converted to mcap v8 ...)"
    cache_key: str = ""
    manifest_path: str = ""
    extra_volumes: list = field(default_factory=list)  # "host:container:mode"
    environment: dict = field(default_factory=dict)


# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------

_PATH_PAIRS = (
    (HOST_DATASETS_ROOT, CONTAINER_DATASETS_ROOT),
    (HOST_RESULTS_ROOT, CONTAINER_RESULTS_ROOT),
    (HOST_ALGOS_ROOT, CONTAINER_ALGOS_ROOT),
    (HOST_WEB_ROOT, CONTAINER_WEB_ROOT),
)


def host_to_local_path(path):
    """Host path -> path visible to this (Web) process."""
    path = Path(str(path))
    for host, local in _PATH_PAIRS:
        if local.exists() and _is_under(path, host):
            return local / path.relative_to(host)
    return path


def local_to_host_path(path):
    """Path visible to this process -> host path (for docker bind mounts)."""
    path = Path(str(path))
    for host, local in _PATH_PAIRS:
        if local.exists() and _is_under(path, local):
            return host / path.relative_to(local)
    return path


def _is_under(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _log(logger, message, level="info"):
    if logger is not None:
        getattr(logger, level)(message)
    else:
        print(message)


def _write_json(path, data):
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _sha(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()


def _safe_name(value):
    text = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value)).strip("._")
    return text or "dataset"


def _docker_client():
    import docker

    return docker.DockerClient(base_url="unix:///var/run/docker.sock")


# --------------------------------------------------------------------------
# algorithm ROS version (registration helpers)
# --------------------------------------------------------------------------

def classify_distro(distro):
    distro = str(distro or "").strip().lower()
    if distro in ROS1_DISTROS:
        return "ros1"
    if distro in ROS2_DISTROS:
        return "ros2"
    return "none"


def image_env(image):
    env = {}
    for item in image.attrs.get("Config", {}).get("Env") or []:
        key, _, value = item.partition("=")
        env[key] = value
    return env


def image_ros_version(algo_tag, client=None):
    """ros1 / ros2 / other from ROS_DISTRO in slam-hive-algorithm:<tag>; None if the image is missing.

    Only used to pre-fill and sanity-check the algorithm's rosVersion field; the
    scheduler itself reads the field.
    """
    import docker

    client = client or _docker_client()
    try:
        image = client.images.get("slam-hive-algorithm:{}".format(algo_tag))
    except docker.errors.ImageNotFound:
        return None
    version = classify_distro(image_env(image).get("ROS_DISTRO", ""))
    return "other" if version == "none" else version


# --------------------------------------------------------------------------
# conversion cache (runs slam-hive-bagtools)
# --------------------------------------------------------------------------

def fingerprint(path):
    """Size/mtime fingerprint of a bag file or rosbag2 directory."""
    path = Path(path)
    files = sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
    root = path if path.is_dir() else path.parent
    return [
        {"path": str(p.relative_to(root)), "size": p.stat().st_size, "mtime_ns": p.stat().st_mtime_ns}
        for p in files
    ]


def run_bagtools(client, args, log_path, host_source_root):
    """Run slam-hive-bagtools; the dataset folder is mounted at /src, the cache at /out.

    Mounting the dataset folder itself (not the datasets root) lets docker resolve a
    dataset that is a symlink to another location, as it does for the algorithm container.
    """
    container = client.containers.run(
        BAGTOOLS_IMAGE,
        command=[str(a) for a in args],
        volumes=["{}:/src:ro".format(host_source_root),
                 "{}:/out:rw".format(HOST_DATASETS_ROOT / CACHE_DIR_NAME)],
        network_mode="none",
        detach=True,
    )
    try:
        status = container.wait()
        exit_code = status.get("StatusCode") if isinstance(status, dict) else status  # docker SDK < 3: int
        stdout = container.logs(stdout=True, stderr=False).decode("utf-8", "replace")
        stderr = container.logs(stdout=False, stderr=True).decode("utf-8", "replace")
    finally:
        container.remove(force=True)
    with Path(log_path).open("a", encoding="utf-8") as handle:
        handle.write("$ bagtools {}\n{}\n".format(" ".join(shlex.quote(str(a)) for a in args), stderr))
    if exit_code != 0:
        raise InteropError("bagtools {} failed (exit {}): {}".format(
            args[0], exit_code, stderr.strip().splitlines()[-1:] or ""))
    return json.loads(stdout.strip().splitlines()[-1])


class Converter(object):
    """Materialises conversion jobs in the shared cache (slam_hive_datasets/.converted)."""

    def __init__(self, client, local_dataset, work_dir, logger=None):
        self.client = client
        self.local_dataset = Path(local_dataset)
        self.work_dir = Path(work_dir)
        self.logger = logger
        self._image_id = None

    def __call__(self, job):
        """job: kind, dst_kind (ros1|ros2), sources (local paths), topics, start, duration.

        Returns (container path of the converted bag, cache entry name).
        """
        if self._image_id is None:
            self._image_id = self.client.images.get(BAGTOOLS_IMAGE).id
        sources = [Path(s) for s in job["sources"]]
        key = _sha({
            "job": {k: v for k, v in job.items() if k != "sources"},
            "sources": [{"rel": str(s.relative_to(self.local_dataset)), "fp": fingerprint(s)} for s in sources],
            "bagtools": self._image_id,
        })
        name = "{}__{}__{}".format(_safe_name(self.local_dataset.name), job["kind"], key[:16])
        bag_name = "bag.bag" if job["dst_kind"] == "ros1" else "bag"
        cache_root = CONTAINER_DATASETS_ROOT / CACHE_DIR_NAME
        target = cache_root / name
        done = target / "conversion.json"
        in_cache = "{}/{}/{}".format(IN_CACHE, name, bag_name)
        if done.is_file():
            _log(self.logger, "[ros_interop] cache hit {}".format(name))
            return in_cache, name

        lock = cache_root / (name + ".lock")
        cache_root.mkdir(parents=True, exist_ok=True)
        started = time.time()
        while True:
            try:
                lock.mkdir()
                break
            except FileExistsError:
                if done.is_file():
                    return in_cache, name
                if time.time() - started > LOCK_TIMEOUT_S:
                    raise InteropError("timed out waiting for conversion lock {}".format(lock))
                time.sleep(5)
        try:
            if done.is_file():
                return in_cache, name
            if target.exists():
                shutil.rmtree(str(target))
            target.mkdir(parents=True)
            args = ["convert", "--dst", "/out/{}/{}".format(name, bag_name), "--dst-kind", job["dst_kind"]]
            for src in sources:
                args += ["--src", "/src/" + str(src.relative_to(self.local_dataset))]
            for topic in job.get("topics") or []:
                args += ["--include-topic", topic]
            if job.get("start"):
                args += ["--start-offset", str(job["start"])]
            if job.get("duration"):
                args += ["--duration", str(job["duration"])]
            if job["dst_kind"] == "ros2":
                args.append("--strip-leading-slash")  # tf2 in ROS2 rejects frame ids starting with '/'
            _log(self.logger, "[ros_interop] converting -> {}".format(name))
            result = run_bagtools(self.client, args, self.work_dir / "conversion.log",
                                  local_to_host_path(self.local_dataset))
            result.update({"job": dict(job, sources=[str(local_to_host_path(s)) for s in sources]),
                           "key": key, "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
            result["sources"] = [str(local_to_host_path(s)) for s in sources]
            _write_json(done, result)
            return in_cache, name
        except Exception:
            shutil.rmtree(str(target), ignore_errors=True)
            raise
        finally:
            shutil.rmtree(str(lock), ignore_errors=True)


def conversion_warnings(cache_name):
    """Topics the converter could not decode (e.g. definitions missing from the bag)."""
    result = _read_json(CONTAINER_DATASETS_ROOT / CACHE_DIR_NAME / cache_name / "conversion.json")
    return {k: result[k] for k in ("skipped_topics", "dropped_messages") if result.get(k)}


# --------------------------------------------------------------------------
# the decision
# --------------------------------------------------------------------------

def plan_playback(ros_version, pb, infos, convert, all_bags=()):
    """Decide per the table; returns (command, timeout, links, conversions, summary).

    ``infos``: bagformat info (with "local" path) per selected bag, same order as
    ``pb.bags``; ``convert(job) -> (container path, cache name)``; ``all_bags``:
    (relative path, info) of every bag in the dataset: ROS2 bags are also offered
    as ROS1 files to ros1/other algorithms that open ``*.bag`` themselves.
    ``links``: dataset-view name -> container path.
    """
    if ros_version not in ROS_VERSIONS:
        raise InteropError("algorithm ROS version must be one of {}, got {!r}; set it on the Algorithm page".format(
            ROS_VERSIONS, ros_version))
    for (bag_id, rel), info in zip(pb.bags, infos):
        if info["family"] not in ("ros1", "ros2") or info["issues"]:
            raise InteropError("bag {} ({}): {}".format(bag_id, rel, info["label"]))

    links, conversions = {}, []
    if ros_version in ("ros1", "other"):
        ros1_path = {}
        for rel, info in all_bags:
            if info["family"] == "ros2" and not info["issues"]:
                path, name = convert({"kind": "ros2_to_ros1", "dst_kind": "ros1", "sources": [info["local"]]})
                link = _unique_link(links, Path(rel).name.split(".")[0] + ".bag")
                links[link] = path
                ros1_path[str(Path(rel))] = "{}/{}".format(IN_DATASET, link)
                conversions.append(name)
        files = []
        for (_, rel), info in zip(pb.bags, infos):
            files.append("{}/{}".format(IN_DATASET, rel) if info["family"] == "ros1" else ros1_path[str(Path(rel))])
        command, timeout = playback.ros1_command(files, pb)
        summary = "{} <- {}".format(ros_version, ", ".join(
            "{} ({})".format(rel, "as is" if i["family"] == "ros1" else "converted to ROS1")
            for (_, rel), i in zip(pb.bags, infos)))
        return command, timeout, links, conversions, summary

    # ros2: exactly one bag that every ROS2 image plays, or one converted mcap bag
    if len(pb.bags) == 1 and bagformat.plays_on_any_ros2(infos[0]):
        rel = pb.bags[0][1]
        command, timeout = playback.ros2_command("{}/{}".format(IN_DATASET, rel), pb, window_applied=False)
        return command, timeout, links, conversions, "ros2 <- {} (as is: {})".format(rel, infos[0]["label"])
    path, name = convert({
        "kind": "to_ros2", "dst_kind": "ros2", "sources": [i["local"] for i in infos],
        "topics": list(pb.topics), "start": pb.start or None,
        "duration": pb.duration if pb.duration > 0 else None,
    })
    links["_ros2_playback"] = path
    conversions.append(name)
    command, timeout = playback.ros2_command("{}/_ros2_playback".format(IN_DATASET), pb, window_applied=True)
    summary = "ros2 <- {} (converted to mcap v8 from: {})".format(
        ", ".join(rel for _, rel in pb.bags), "; ".join(i["label"] for i in infos))
    return command, timeout, links, conversions, summary


def _unique_link(links, name):
    candidate, n = name, 2
    while candidate in links:
        candidate = "{}_{}.bag".format(name[:-4], n)
        n += 1
    return candidate


# --------------------------------------------------------------------------
# dataset view
# --------------------------------------------------------------------------

def build_view(view, local_dataset, links, plan):
    """Per-task /slamhive/dataset: links to the dataset, converted bags, the player."""
    if view.exists():
        shutil.rmtree(str(view))
    view.mkdir(parents=True)
    for entry in sorted(os.listdir(str(local_dataset))):
        if entry in ("rosbag_play.py", "__pycache__") or entry in links:
            continue
        os.symlink("{}/{}".format(IN_DATASET_SRC, entry), str(view / entry))
    for name, target in links.items():
        os.symlink(target, str(view / name))
    if plan is not None:
        shutil.copy2(str(PLAYER_PATH), str(view / "rosbag_play.py"))
        _write_json(view / "playback.json", plan)


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------

def prepare_dataset_for_mapping(config_dict, dataset_path, result_path, config_path=None, logger=None,
                                client=None, convert=None):
    """Resolve playback, convert what the algorithm's ROS version needs, build the dataset view."""
    host_dataset = Path(str(dataset_path))
    local_dataset = host_to_local_path(host_dataset)
    local_result = host_to_local_path(result_path)
    work = local_result / "interop"
    work.mkdir(parents=True, exist_ok=True)
    ros_version = str(config_dict.get("algorithm-ros-version") or "").strip().lower()
    decision = {"algorithm": config_dict.get("slam-hive-algorithm"), "algorithm_ros_version": ros_version,
                "dataset": str(host_dataset)}
    if ros_version == "other" and not (local_dataset / playback.MANIFEST_NAME).is_file():
        # Non-ROS algorithms read the dataset files themselves; nothing to play.
        summary = "other <- dataset files as they are (no {})".format(playback.MANIFEST_NAME)
        view = local_result / "dataset_view"
        build_view(view, local_dataset, {}, None)
        decision.update(summary=summary)
        _write_json(work / "decision.json", decision)
        _log(logger, "[ros_interop] {}".format(summary))
        return PreparedDataset(dataset_path=str(local_to_host_path(view)), algorithm_ros=ros_version,
                               dataset_ros="", status=summary,
                               manifest_path=str(local_to_host_path(work / "decision.json")),
                               extra_volumes=["{}:{}:ro".format(host_dataset, IN_DATASET_SRC)])
    try:
        manifest = playback.load_manifest(local_dataset)
        pb = playback.resolve(manifest, config_dict)
        scanned = {}
        for info in bagformat.scan(local_dataset):
            info["local"] = str(local_dataset / info["path"])
            scanned[str(Path(info["path"]))] = info
        infos = []
        for bag_id, rel in pb.bags:
            if not (local_dataset / rel).exists():
                raise InteropError("bag {} listed in {} does not exist: {}".format(
                    bag_id, playback.MANIFEST_NAME, rel))
            info = scanned.get(str(Path(rel))) or dict(bagformat.describe(local_dataset / rel))
            info.setdefault("local", str(local_dataset / rel))
            infos.append(info)
        decision["playback"] = pb.as_dict()
        decision["bags"] = [dict(info, id=bag_id) for (bag_id, _), info in zip(pb.bags, infos)]
        if convert is None:
            convert = Converter(client or _docker_client(), local_dataset, work, logger)
        command, timeout, links, conversions, summary = plan_playback(
            ros_version, pb, infos, convert, all_bags=sorted(scanned.items()))
    except (playback.PlaybackError, InteropError) as exc:
        decision["error"] = str(exc)
        _write_json(work / "decision.json", decision)
        (local_result / "conversion_failed.txt").write_text(decision["error"] + "\n", encoding="utf-8")
        raise InteropError(str(exc))

    warnings = {}
    for name in conversions:
        found = conversion_warnings(name)
        if found:
            warnings[name] = found
    plan = {"summary": summary, "command": command, "timeout_s": timeout, "conversions": conversions,
            "warnings": warnings}
    decision.update(plan)
    view = local_result / "dataset_view"
    build_view(view, local_dataset, links, plan)
    _write_json(work / "decision.json", decision)
    _log(logger, "[ros_interop] {}".format(summary))
    _log(logger, "[ros_interop] play: {}".format(" ".join(command)))
    for name, warning in warnings.items():
        _log(logger, "[ros_interop] warning {}: {}".format(name, warning), "warning")

    return PreparedDataset(
        dataset_path=str(local_to_host_path(view)),
        algorithm_ros=ros_version,
        dataset_ros="/".join(sorted({info["family"] for info in infos})),
        status=summary,
        cache_key=",".join(conversions),
        manifest_path=str(local_to_host_path(work / "decision.json")),
        extra_volumes=[
            "{}:{}:ro".format(host_dataset, IN_DATASET_SRC),
            "{}:{}:ro".format(HOST_DATASETS_ROOT / CACHE_DIR_NAME, IN_CACHE),
        ],
    )
