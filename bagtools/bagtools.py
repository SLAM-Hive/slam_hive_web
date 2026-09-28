#!/usr/bin/env python3
"""SLAM-Hive bag tools: probe and convert ROS1/ROS2 bags.

Runs inside the ``slam-hive-bagtools`` image (Python 3.12 + rosbags). The Web
container calls it through ``docker run``; every command prints one JSON
document on stdout so the caller can parse the result.

Commands:
  scan    DIR                     describe every bag in a dataset folder
  probe   PATH...                 describe bags (format, storage, version, topics)
  convert --src PATH... --dst OUT convert/merge bags to a ROS1 .bag or the
                                  platform ROS2 format (mcap, metadata v8)

What a bag *is* (ROS1/ROS2, storage, version, distro) is decided only by
bagformat.py, shared with the Web scheduler; this file adds rosbags-based reading.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import importlib.metadata
import json
import os
import shutil
import sys
import time
from pathlib import Path

import bagformat
from rosbags.convert.converter import LATCH, create_connections_converters
from rosbags.highlevel import AnyReader
from rosbags.interfaces import ConnectionExtRosbag1, ConnectionExtRosbag2, Nodetype
from rosbags.rosbag1 import Writer as Writer1
from rosbags.rosbag2 import StoragePlugin, Writer as Writer2
from rosbags.typesys import Stores, get_types_from_msg, get_typestore

# Platform ROS2 format: mcap + metadata v8, uncompressed. Every ROS2 algorithm
# image must have the mcap storage plugin (ros-<distro>-rosbag2-storage-mcap);
# Humble cannot parse metadata v9, so v8 is written.
ROS2_OUTPUT_VERSION = 8
ROS2_OUTPUT_STORAGE = StoragePlugin.MCAP
FRAME_FIELDS = ("frame_id", "child_frame_id")
TF_TYPES = {"tf2_msgs/msg/TFMessage", "tf/msg/tfMessage"}
LATCHED_TOPICS = {"/tf_static"}

DISTRO_STORES = {
    "foxy": Stores.ROS2_FOXY,
    "galactic": Stores.ROS2_GALACTIC,
    "humble": Stores.ROS2_HUMBLE,
    "iron": Stores.ROS2_IRON,
    "jazzy": Stores.ROS2_JAZZY,
    "kilted": Stores.ROS2_KILTED,
}


def rosbags_version():
    try:
        return importlib.metadata.version("rosbags")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


# --------------------------------------------------------------------------
# typestores
# --------------------------------------------------------------------------

def default_typestore_for(paths):
    """Typestore used when a ROS2 bag carries no message definitions."""
    for path in paths:
        distro = bagformat.describe(path)["ros_distro"].lower()
        if distro in DISTRO_STORES:
            return get_typestore(DISTRO_STORES[distro])
    return get_typestore(Stores.ROS2_HUMBLE)


def register_msg_dirs(typestore, msg_dirs):
    """Register custom ``<pkg>/msg/<Name>.msg`` definitions."""
    for msg_dir in msg_dirs or []:
        for msg_file in sorted(Path(msg_dir).rglob("*.msg")):
            pkg = msg_file.parent.parent.name
            name = "{}/msg/{}".format(pkg, msg_file.stem)
            typestore.register(get_types_from_msg(msg_file.read_text(encoding="utf-8"), name))


# --------------------------------------------------------------------------
# frame_id normalisation (tf2 in ROS2 rejects frame ids with a leading "/")
# --------------------------------------------------------------------------

def frame_field_types(typestore):
    """Return msgtypes that (transitively) contain a frame_id-like string."""
    memo = {}

    def visit(msgtype, stack):
        if msgtype in memo:
            return memo[msgtype]
        if msgtype in stack or msgtype not in typestore.fielddefs:
            return False
        stack = stack | {msgtype}
        found = False
        for name, typ in typestore.fielddefs[msgtype][1]:
            node = typ
            if node[0] in (Nodetype.SEQUENCE, Nodetype.ARRAY):
                node = node[1][0]
            if node[0] == Nodetype.BASE and node[1][0] == "string" and name in FRAME_FIELDS:
                found = True
            elif node[0] == Nodetype.NAME and visit(node[1], stack):
                found = True
        memo[msgtype] = found
        return found

    return {msgtype for msgtype in list(typestore.fielddefs) if visit(msgtype, frozenset())}


def strip_frames(msg):
    """Strip leading '/' from frame fields in place; return True if changed."""
    changed = False
    if not dataclasses.is_dataclass(msg):
        return False
    for field in dataclasses.fields(msg):
        value = getattr(msg, field.name)
        if field.name in FRAME_FIELDS and isinstance(value, str):
            if value.startswith("/"):
                object.__setattr__(msg, field.name, value.lstrip("/"))
                changed = True
        elif dataclasses.is_dataclass(value):
            changed |= strip_frames(value)
        elif isinstance(value, list):
            for item in value:
                if dataclasses.is_dataclass(item):
                    changed |= strip_frames(item)
    return changed


class FrameFixer:
    """Per-topic frame_id fixer for CDR payloads."""

    def __init__(self, typestore):
        self.typestore = typestore
        self.frame_types = frame_field_types(typestore)
        self.decision = {}
        self.fixed = {}

    def __call__(self, topic, msgtype, data):
        if msgtype not in self.frame_types:
            return data
        decision = self.decision.get(topic)
        if decision is False:
            return data
        msg = self.typestore.deserialize_cdr(data, msgtype)
        changed = strip_frames(msg)
        if decision is None and msgtype not in TF_TYPES:
            # Frame ids are constant per sensor topic: decide on the first message.
            self.decision[topic] = changed
        if not changed:
            return data
        self.fixed[topic] = self.fixed.get(topic, 0) + 1
        return self.typestore.serialize_cdr(msg, msgtype, little_endian=True)


# --------------------------------------------------------------------------
# probe
# --------------------------------------------------------------------------

def qos_durability(conn):
    ext = conn.ext
    if isinstance(ext, ConnectionExtRosbag1):
        return "transient_local" if ext.latching else "volatile"
    profiles = getattr(ext, "offered_qos_profiles", None) or []
    if any(getattr(profile.durability, "value", None) == 1 for profile in profiles):
        return "transient_local"
    return "volatile" if profiles else ""


def probe_one(path, info=None):
    """bagformat facts plus what rosbags reads (topics, duration)."""
    info = dict(info or bagformat.describe(path))
    if info["family"] == "unknown":
        return info
    try:
        with AnyReader([bagformat.bag_root(path)], default_typestore=default_typestore_for([path])) as reader:
            info["start_ns"] = reader.start_time
            info["end_ns"] = reader.end_time
            info["duration_s"] = (reader.end_time - reader.start_time) / 1e9
            info["message_count"] = reader.message_count
            topics = {}
            for conn in reader.connections:
                entry = topics.setdefault(
                    conn.topic,
                    {"name": conn.topic, "type": conn.msgtype, "count": 0, "durability": qos_durability(conn)},
                )
                entry["count"] += conn.msgcount
            info["topics"] = sorted(topics.values(), key=lambda item: item["name"])
            info["readable"] = True
    except Exception as exc:  # report, the caller decides what to do
        info["readable"] = False
        info["error"] = "{}: {}".format(type(exc).__name__, exc)
    return info


def cmd_scan(args):
    root = Path(args.dir)
    bags = [probe_one(root / info["path"], info) for info in bagformat.scan(root)]
    return {"rosbags": rosbags_version(), "dir": str(root), "family": bagformat.dataset_family(bags), "bags": bags}


def cmd_probe(args):
    return {"rosbags": rosbags_version(), "bags": [probe_one(p) for p in args.paths]}


# --------------------------------------------------------------------------
# convert
# --------------------------------------------------------------------------

def destination_typestore(reader, dst_is2):
    """Mirror rosbags' converter: keep source definitions, swap the Header."""
    if reader.is2 == dst_is2:
        return reader.typestore
    header = get_typestore(Stores.ROS2_FOXY if dst_is2 else Stores.ROS1_NOETIC).fielddefs["std_msgs/msg/Header"]
    typestore = get_typestore(Stores.EMPTY)
    typestore.register({**reader.typestore.fielddefs, "std_msgs/msg/Header": header})
    return typestore


def ros1_topic(topic):
    return topic if topic.startswith("/") else "/" + topic


def cmd_convert(args):
    srcs = [bagformat.bag_root(item) for item in args.src]
    dst = Path(args.dst)
    dst_is2 = args.dst_kind == "ros2"
    # Write under a temporary parent so rosbag2 file names match the final name.
    tmp_parent = dst.parent / ".tmp-{}-{}".format(dst.name, os.getpid())
    if tmp_parent.exists():
        shutil.rmtree(tmp_parent)
    tmp_parent.mkdir(parents=True)
    try:
        return _convert(args, srcs, dst, dst_is2, tmp_parent / dst.name)
    finally:
        shutil.rmtree(tmp_parent, ignore_errors=True)


def _convert(args, srcs, dst, dst_is2, tmp):
    started = time.time()
    default_typestore = default_typestore_for(srcs)
    register_msg_dirs(default_typestore, args.msg_dir)

    with AnyReader(srcs, default_typestore=default_typestore) as reader:
        register_msg_dirs(reader.typestore, args.msg_dir)
        include = {ros1_topic(t) for t in (args.include_topic or [])}
        connections = [c for c in reader.connections if not include or ros1_topic(c.topic) in include]
        if not connections:
            raise SystemExit("no matching topics in {}".format([str(s) for s in srcs]))

        start = reader.start_time
        if args.start_offset:
            start += int(round(float(args.start_offset) * 1e9))
        stop = None
        if args.duration and float(args.duration) > 0:
            stop = start + int(round(float(args.duration) * 1e9))

        if dst_is2:
            writer = Writer2(tmp, version=ROS2_OUTPUT_VERSION, storage_plugin=ROS2_OUTPUT_STORAGE)
        else:
            writer = Writer1(tmp)
            if args.compress:
                writer.set_compression(writer.CompressionFormat[args.compress.upper()])

        typestore = destination_typestore(reader, dst_is2)
        fixer = None
        counts = {}
        with writer:
            # ROS1 output needs absolute topic names; /tf_static is always latched.
            patched = []
            for conn in connections:
                ext = conn.ext
                if ros1_topic(conn.topic) in LATCHED_TOPICS:
                    if isinstance(ext, ConnectionExtRosbag1):
                        ext = ConnectionExtRosbag1(ext.callerid, 1)
                    else:
                        ext = ConnectionExtRosbag2(ext.serialization_format, LATCH)
                topic = conn.topic if dst_is2 else ros1_topic(conn.topic)
                patched.append(conn._replace(topic=topic, ext=ext))
            # rosbags creates the writer connections (QoS <-> latching mapping included).
            connmap, convmap = create_connections_converters(patched, typestore, reader, writer)
            if dst_is2 and args.strip_leading_slash:
                # Built after the converters: they register missing msgtypes (e.g. TFMessage).
                fixer = FrameFixer(typestore)
            patched_by_key = {(c.id, c.owner): p for c, p in zip(connections, patched)}
            # A bag without embedded definitions (e.g. Humble sqlite3) is decoded with
            # the distro's definitions; a topic serialized with another definition
            # cannot be converted. Skip such topics and report them.
            skipped = {}
            for rconn in connections:
                first = next(reader.messages(connections=[rconn]), None)
                try:
                    if first is not None:
                        convmap[rconn.msgtype](first[2])
                except Exception as exc:
                    topic = patched_by_key[(rconn.id, rconn.owner)].topic
                    skipped[topic] = "{} ({}): {}".format(rconn.msgtype, type(exc).__name__, exc)[:300]
                    print("[bagtools] skipping undecodable topic {}: {}".format(topic, skipped[topic]))
            active = [c for c in connections if patched_by_key[(c.id, c.owner)].topic not in skipped]
            if not active:
                raise SystemExit("no convertible topics: {}".format(skipped))
            dropped = {}
            for rconn, timestamp, data in reader.messages(connections=active, start=start, stop=stop):
                pconn = patched_by_key[(rconn.id, rconn.owner)]
                wconn = connmap[(pconn.id, pconn.owner)]
                try:
                    payload = convmap[rconn.msgtype](data)
                    if fixer is not None:
                        payload = fixer(wconn.topic, wconn.msgtype, payload)
                except Exception:
                    dropped[wconn.topic] = dropped.get(wconn.topic, 0) + 1
                    continue
                writer.write(wconn, timestamp, payload)
                counts[wconn.topic] = counts.get(wconn.topic, 0) + 1

    if dst.exists():
        shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
    tmp.rename(dst)
    return {
        "dst": str(dst),
        "dst_kind": args.dst_kind,
        "sources": [str(s) for s in srcs],
        "window_start_ns": start,
        "window_stop_ns": stop,
        "topic_counts": counts,
        "frame_ids_fixed": dict(fixer.fixed) if fixer else {},
        "skipped_topics": skipped,
        "dropped_messages": dropped,
        "seconds": round(time.time() - started, 1),
        "rosbags": rosbags_version(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan")
    scan.add_argument("dir")
    scan.set_defaults(func=cmd_scan)

    probe = sub.add_parser("probe")
    probe.add_argument("paths", nargs="+")
    probe.set_defaults(func=cmd_probe)

    convert = sub.add_parser("convert")
    convert.add_argument("--src", action="append", required=True)
    convert.add_argument("--dst", required=True)
    convert.add_argument("--dst-kind", choices=["ros1", "ros2"], required=True)
    convert.add_argument("--include-topic", action="append")
    convert.add_argument("--start-offset", type=float, default=0.0)
    convert.add_argument("--duration", type=float, default=0.0)
    convert.add_argument("--strip-leading-slash", action="store_true")
    convert.add_argument("--compress", choices=["bz2", "lz4"])
    convert.add_argument("--msg-dir", action="append")
    convert.set_defaults(func=cmd_convert)

    args = parser.parse_args(argv)
    # rosbags prints progress notes on stdout; keep stdout for the JSON result only.
    with contextlib.redirect_stdout(sys.stderr):
        result = args.func(args)
    json.dump(result, sys.stdout, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
