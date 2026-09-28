"""Dataset playback: what a dataset plays (slamhive_dataset.yaml) and the player command.

A dataset folder describes its bags and how they are played in
``slamhive_dataset.yaml``; the task config (``dataset-parameters``,
``dataset-remap``) selects and adjusts. The platform then builds one
``rosbag play`` (ROS1 algorithm) or ``ros2 bag play`` (ROS2 algorithm) command.

    version: 1
    bags:                     # id -> path inside the dataset folder
      lidar: bpearl_front.bag #   (ROS1 .bag, rosbag2 directory or storage file)
      imu: mti.bag
    play:
      bags: [lidar]           # always played
      topics: []              # play only these topics (empty: all)
      rate: 1.0               # dataset-parameters bag_rate / bag_start /
      start: 0                #   bag_duration override these defaults
      duration: -1            # seconds, -1: to the end
    switches:                 # boolean dataset-parameters adding bags/topics
      play_mti: {default: false, bags: [imu], topics: []}
    choices:                  # dataset-parameters choosing one named value
      bag_profile: {default: full, values: {full: {bags: [lidar]}}}
    rules:                    # checks, with the message shown when they fail
      - {exactly_one: [play_a, play_b], message: "..."}
      - {at_least_one: [play_a, play_b], message: "..."}
      - {all_or_none: [play_a, play_b], message: "..."}
      - {must_be_true: [play_a], message: "..."}
      - {must_be_false: [play_b], message: "..."}

Every ``dataset-remap`` entry (algorithm topic: bag topic) becomes a remap;
remapping a topic that is not played has no effect.
"""

from pathlib import Path

import yaml

MANIFEST_NAME = "slamhive_dataset.yaml"
MANIFEST_VERSION = 1
# `rosbag play --clock` publishes 100 Hz; the ROS2 command asks for the same.
CLOCK_HZ = 100
# DDS discovery is asynchronous: wait before the first message is published.
ROS2_DELAY_S = 1.0


class PlaybackError(RuntimeError):
    pass


class Playback(object):
    """Resolved playback for one task."""

    def __init__(self, bags, topics, rate, start, duration, remaps):
        self.bags = bags            # [(id, relative path)]
        self.topics = topics        # [] = all topics
        self.rate = rate
        self.start = start
        self.duration = duration    # <= 0: to the end
        self.remaps = remaps        # [(bag topic, algorithm topic)]

    def as_dict(self):
        return {"bags": [{"id": i, "path": p} for i, p in self.bags], "topics": self.topics, "rate": self.rate,
                "start": self.start, "duration": self.duration,
                "remaps": ["{}:={}".format(a, b) for a, b in self.remaps]}


# --------------------------------------------------------------------------
# manifest
# --------------------------------------------------------------------------

def load_manifest(dataset_dir):
    path = Path(str(dataset_dir)) / MANIFEST_NAME
    if not path.is_file():
        raise PlaybackError("dataset has no {} (describe its bags and playback there)".format(MANIFEST_NAME))
    with path.open("r", encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle) or {}
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest):
    if manifest.get("version") != MANIFEST_VERSION:
        raise PlaybackError("{}: version must be {}".format(MANIFEST_NAME, MANIFEST_VERSION))
    bags = manifest.get("bags") or {}
    if not bags:
        raise PlaybackError("{}: no bags".format(MANIFEST_NAME))
    referenced = list((manifest.get("play") or {}).get("bags") or [])
    for switch in (manifest.get("switches") or {}).values():
        referenced += switch.get("bags") or []
    for choice in (manifest.get("choices") or {}).values():
        if choice.get("default") not in (choice.get("values") or {}):
            raise PlaybackError("{}: choice default {!r} is not one of its values".format(
                MANIFEST_NAME, choice.get("default")))
        for value in choice["values"].values():
            referenced += value.get("bags") or []
    unknown = sorted(set(referenced) - set(bags))
    if unknown:
        raise PlaybackError("{}: unknown bag ids {}".format(MANIFEST_NAME, unknown))


# --------------------------------------------------------------------------
# resolve with the task config
# --------------------------------------------------------------------------

def parse_bool(value, default):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in ("true", "1", "yes", "on"):
        return True
    if text in ("false", "0", "no", "off", ""):
        return False
    return default


def parse_float(value, default):
    if value is None or value == "":
        return float(default)
    return float(value)


def resolve(manifest, config):
    params = config.get("dataset-parameters") or {}
    play = manifest.get("play") or {}
    switches = manifest.get("switches") or {}

    def on(param):
        switch = switches.get(param) or {}
        return parse_bool(params.get(param), bool(switch.get("default", False)))

    checks = {
        "exactly_one": (lambda n, total: n == 1, "exactly one of {} must be true"),
        "at_least_one": (lambda n, total: n >= 1, "at least one of {} must be true"),
        "all_or_none": (lambda n, total: n in (0, total), "{} must be set together"),
        "must_be_true": (lambda n, total: n == total, "{} must be true"),
        "must_be_false": (lambda n, total: n == 0, "{} must be false"),
    }
    for rule in manifest.get("rules") or []:
        for kind, (ok, default_message) in checks.items():
            if kind in rule and not ok(sum(on(p) for p in rule[kind]), len(rule[kind])):
                raise PlaybackError(rule.get("message") or default_message.format(rule[kind]))

    bag_ids = list(play.get("bags") or [])
    topics = list(play.get("topics") or [])
    for param, switch in switches.items():
        if on(param):
            bag_ids += switch.get("bags") or []
            topics += switch.get("topics") or []
    for param, choice in (manifest.get("choices") or {}).items():
        value = params.get(param)
        value = choice["default"] if value in (None, "") else str(value).strip()
        if value not in choice["values"]:
            raise PlaybackError("{}={!r} is not one of {}".format(param, value, sorted(choice["values"])))
        bag_ids += choice["values"][value].get("bags") or []
        topics += choice["values"][value].get("topics") or []
    bag_ids = _unique(bag_ids)
    if not bag_ids:
        raise PlaybackError("no bag selected; set one of {} in dataset-parameters".format(sorted(switches)))

    remaps = []
    for algorithm_topic, bag_topic in (config.get("dataset-remap") or {}).items():
        if algorithm_topic and bag_topic:
            remaps.append((str(bag_topic).strip(), str(algorithm_topic).strip()))

    return Playback(
        bags=[(i, manifest["bags"][i]) for i in bag_ids],
        topics=_unique(topics),
        rate=parse_float(params.get("bag_rate"), play.get("rate", 1.0)),
        start=parse_float(params.get("bag_start"), play.get("start", 0)),
        duration=parse_float(params.get("bag_duration"), play.get("duration", -1)),
        remaps=remaps,
    )


def _unique(items):
    seen, result = set(), []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------

def _number(value):
    return "{:g}".format(float(value))


def ros1_command(files, playback):
    """rosbag play of ROS1 files; rosbag merges several bags by time itself."""
    cmd = ["rosbag", "play", "--clock", "--quiet"]
    if playback.rate != 1.0:
        cmd += ["-r", _number(playback.rate)]
    if playback.start > 0:
        cmd += ["-s", _number(playback.start)]
    if playback.duration > 0:
        cmd += ["-u", _number(playback.duration)]
    cmd += list(files)
    cmd += ["{}:={}".format(a, b) for a, b in playback.remaps]
    if playback.topics:
        cmd += ["--topics"] + list(playback.topics)  # last: --topics takes all remaining words
    return cmd, None


def ros2_command(bag, playback, window_applied):
    """ros2 bag play of one rosbag2 directory; returns (command, wall-clock timeout or None).

    ``window_applied``: the bag was cut to the selected topics and time window
    when it was converted, so only the rate is left to apply.
    """
    cmd = ["ros2", "bag", "play", str(bag), "--clock", str(CLOCK_HZ), "--disable-keyboard-controls",
           "--rate", _number(playback.rate), "--delay", _number(ROS2_DELAY_S)]
    timeout = None
    if not window_applied:
        if playback.start > 0:
            cmd += ["--start-offset", _number(playback.start)]
        if playback.duration > 0:  # Humble's ros2 bag play has no duration option
            timeout = playback.duration / playback.rate + ROS2_DELAY_S + 2.0
        if playback.topics:
            cmd += ["--topics"] + list(playback.topics)
    if playback.remaps:
        cmd += ["--remap"] + ["{}:={}".format(a, b) for a, b in playback.remaps]
    return cmd, timeout
