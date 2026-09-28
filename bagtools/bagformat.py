"""The one place that decides what a ROS bag is (ROS1 or ROS2, storage, version, distro).

Detection reads file contents (magic bytes, bag/mcap headers, sqlite schema,
metadata.yaml), never file or folder names. Used by the Web scheduler
(``slamhive/task/ros_interop.py``) and by ``bagtools.py``; standard library plus
PyYAML only, Python >= 3.6.

    scan(dataset_dir)  -> [BagInfo]           every bag in a dataset folder
    describe(path)     -> BagInfo             one bag (file or rosbag2 directory)
    dataset_family(infos) -> ros1|ros2|mixed|none
    bag_root(path)     -> rosbag2 directory for a storage file inside one
    plays_on_any_ros2(info) -> True if every supported ROS2 image plays it as is

A BagInfo is a JSON-serialisable dict:

    path                 as given (relative to the scanned folder for scan())
    family               ros1 | ros2 | unknown
    container            ros1_bag | rosbag2_dir | sqlite3_file | mcap_file
    storage              rosbag | sqlite3 | mcap
    format_version       "2.0"/"1.2" (ROS1) | metadata.yaml version (ROS2 dir) | None
    ros_distro           distro that wrote it, "" if unknown ("rosbags" = written by rosbags)
    compression          none | bz2 | lz4 | zstd
    compression_mode     chunk (ROS1) | file | message (ROS2) | ""
    embedded_definitions True/False/None: message definitions stored in the bag
    files                storage files of the bag
    issues               problems that stop players/converters from reading it as is
    notes                facts worth knowing that do not stop reading (e.g. bare storage file)
    label                one-line summary for logs and the UI
"""

import os
import sqlite3
import struct
from pathlib import Path
from urllib.parse import quote

import yaml

ROS1_MAGIC = b"#ROSBAG V"
SQLITE_MAGIC = b"SQLite format 3\x00"
MCAP_MAGIC = b"\x89MCAP0\r\n"
ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"

# Only files with these endings are opened while scanning (datasets can hold
# thousands of images); the content still decides what they are.
CANDIDATE_SUFFIXES = (".bag", ".bag.active", ".db3", ".mcap", ".db3.zstd", ".mcap.zstd")
SKIP_DIRS = {"__pycache__"}


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

def scan(root):
    """Describe every bag inside a dataset folder (rosbag2 directories count as one bag)."""
    root = Path(str(root))
    infos = []
    for dirpath, dirnames, filenames in os.walk(str(root), followlinks=True):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS)
        current = Path(dirpath)
        if "metadata.yaml" in filenames:
            infos.append(_relative(describe(current), root))
            dirnames[:] = []
            continue
        for name in sorted(filenames):
            if name.endswith(CANDIDATE_SUFFIXES):
                info = describe(current / name)
                if info["family"] != "unknown":
                    infos.append(_relative(info, root))
    return infos


def describe(path):
    """Describe one bag: a ROS1 bag file, a rosbag2 directory or a bare rosbag2 storage file."""
    path = Path(str(path))
    if path.is_dir():
        if (path / "metadata.yaml").is_file():
            return _describe_rosbag2_dir(path)
        return _info(path, "unknown", issues=["directory without metadata.yaml"])
    kind = sniff(path)
    if kind == "ros1_bag":
        return _describe_ros1(path)
    if kind in ("sqlite3", "mcap"):
        if (path.parent / "metadata.yaml").is_file():
            return _describe_rosbag2_dir(path.parent)
        info = _describe_storage_file(path, kind)
        info["format_version"] = info.get("embedded_metadata_version")
        info["notes"].append("no metadata.yaml next to it (bare {} file)".format(kind))
        return _finish(info)
    if kind == "zstd" and (path.parent / "metadata.yaml").is_file():
        return _describe_rosbag2_dir(path.parent)
    return _info(path, "unknown", issues=["not a ROS1 bag, rosbag2 directory or rosbag2 storage file"])


def dataset_family(infos):
    families = {info["family"] for info in infos if info["family"] != "unknown"}
    if families == {"ros1"}:
        return "ros1"
    if families == {"ros2"}:
        return "ros2"
    if families:
        return "mixed"
    return "none"


# What every supported ROS2 algorithm image can play without conversion. Images
# must ship the mcap storage plugin; Humble cannot parse metadata.yaml v9.
ROS2_PLAYABLE_STORAGE = ("sqlite3", "mcap")
ROS2_PLAYABLE_MAX_VERSION = 8
ROS2_PLAYABLE_COMPRESSION = ("none", "", "zstd")


def plays_on_any_ros2(info):
    return (
        info["family"] == "ros2"
        and info["container"] == "rosbag2_dir"
        and info["storage"] in ROS2_PLAYABLE_STORAGE
        and isinstance(info["format_version"], int)
        and info["format_version"] <= ROS2_PLAYABLE_MAX_VERSION
        and info["compression"] in ROS2_PLAYABLE_COMPRESSION
        and not info["issues"]
    )


def bag_root(path):
    """A storage file inside a rosbag2 directory stands for the directory."""
    path = Path(str(path))
    if path.is_file() and (path.parent / "metadata.yaml").is_file():
        return path.parent
    return path


def sniff(path):
    """Content type of a file: ros1_bag | sqlite3 | mcap | zstd | None."""
    try:
        with open(str(path), "rb") as handle:
            head = handle.read(16)
    except OSError:
        return None
    if head.startswith(ROS1_MAGIC):
        return "ros1_bag"
    if head.startswith(SQLITE_MAGIC):
        return "sqlite3"
    if head.startswith(MCAP_MAGIC):
        return "mcap"
    if head.startswith(ZSTD_MAGIC):
        return "zstd"
    return None


# --------------------------------------------------------------------------
# ROS1
# --------------------------------------------------------------------------

def _describe_ros1(path):
    info = _info(path, "ros1", container="ros1_bag", storage="rosbag", files=[path.name],
                 embedded_definitions=True, compression_mode="chunk")
    try:
        with open(str(path), "rb") as handle:
            line = handle.readline(64)
            info["format_version"] = line[len(ROS1_MAGIC):].strip().decode("ascii", "replace")
            if info["format_version"] != "2.0":
                info["issues"].append("ROS1 bag format {} (only 2.0 is readable; migrate with a ROS1 "
                                      "`rosbag` tool)".format(info["format_version"]))
                return _finish(info)
            header = _ros1_record_header(handle)
            if header.get("op") != b"\x03":
                info["issues"].append("missing bag header record")
                return _finish(info)
            index_pos = struct.unpack("<Q", header["index_pos"])[0]
            info["chunk_count"] = struct.unpack("<I", header["chunk_count"])[0]
            info["connection_count"] = struct.unpack("<I", header["conn_count"])[0]
            if index_pos == 0:
                info["issues"].append("not indexed (recording was not closed; run `rosbag reindex`)")
            _skip_ros1_data(handle)
            first = _ros1_record_header(handle)
            if first.get("op") == b"\x05":
                info["compression"] = first.get("compression", b"none").decode("ascii", "replace")
    except (OSError, struct.error, ValueError, KeyError) as exc:
        info["issues"].append("unreadable ROS1 header: {}".format(exc))
    return _finish(info)


def _ros1_record_header(handle):
    (length,) = struct.unpack("<I", _read_exact(handle, 4))
    if length > (1 << 20):
        raise ValueError("record header too large ({} bytes)".format(length))
    data = _read_exact(handle, length)
    fields, pos = {}, 0
    while pos + 4 <= len(data):
        (flen,) = struct.unpack("<I", data[pos:pos + 4])
        name, _, value = data[pos + 4:pos + 4 + flen].partition(b"=")
        fields[name.decode("ascii", "replace")] = value
        pos += 4 + flen
    return fields


def _skip_ros1_data(handle):
    (length,) = struct.unpack("<I", _read_exact(handle, 4))
    handle.seek(length, os.SEEK_CUR)


# --------------------------------------------------------------------------
# ROS2
# --------------------------------------------------------------------------

def _describe_rosbag2_dir(path):
    try:
        with (path / "metadata.yaml").open("r", encoding="utf-8") as handle:
            meta = (yaml.safe_load(handle) or {}).get("rosbag2_bagfile_information") or {}
    except (OSError, yaml.YAMLError) as exc:
        return _info(path, "ros2", container="rosbag2_dir", issues=["unreadable metadata.yaml: {}".format(exc)])
    files = [str(f) for f in meta.get("relative_file_paths") or []]
    info = _info(
        path, "ros2", container="rosbag2_dir",
        storage=meta.get("storage_identifier") or "",
        format_version=meta.get("version"),
        ros_distro=str(meta.get("ros_distro") or ""),
        compression=meta.get("compression_format") or "none",
        compression_mode=(meta.get("compression_mode") or "").lower(),
        files=files,
    )
    missing = [f for f in files if not (path / f).is_file()]
    if missing:
        info["issues"].append("metadata.yaml lists missing file(s): {}".format(", ".join(missing)))
    readable = [path / f for f in files if (path / f).is_file() and sniff(path / f) in ("sqlite3", "mcap")]
    if readable:
        # Storage files know more than old metadata.yaml versions (distro, definitions).
        inner = _describe_storage_file(readable[0], sniff(readable[0]))
        info["embedded_definitions"] = inner["embedded_definitions"]
        if not info["ros_distro"]:
            info["ros_distro"] = inner["ros_distro"]
        if inner["storage"] != info["storage"]:
            info["issues"].append("metadata.yaml says storage {} but files are {}".format(
                info["storage"], inner["storage"]))
    elif info["storage"] == "mcap":
        info["embedded_definitions"] = True
    return _finish(info)


def _describe_storage_file(path, kind):
    info = _info(path, "ros2", container=kind + "_file", storage=kind, files=[path.name])
    if kind == "sqlite3":
        _read_sqlite(path, info)
    else:
        _read_mcap(path, info)
    return info


def _read_sqlite(path, info):
    uri = "file:{}?mode=ro&immutable=1".format(quote(str(path)))
    try:
        conn = sqlite3.connect(uri, uri=True)
        try:
            tables = {row[0] for row in conn.execute("select name from sqlite_master where type='table'")}
            if "schema" in tables:
                row = conn.execute("select schema_version, ros_distro from schema").fetchone()
                if row:
                    info["sqlite_schema_version"] = row[0]
                    info["ros_distro"] = str(row[1] or "")
            if "metadata" in tables:  # Iron+ and rosbags keep a copy of metadata.yaml here
                row = conn.execute("select metadata from metadata order by id desc limit 1").fetchone()
                if row:
                    _apply_embedded_metadata(info, row[0])
            info["embedded_definitions"] = "message_definitions" in tables and bool(
                conn.execute("select count(*) from message_definitions").fetchone()[0])
        finally:
            conn.close()
    except sqlite3.Error as exc:
        info["issues"].append("unreadable sqlite3 file: {}".format(exc))


def _read_mcap(path, info):
    info["embedded_definitions"] = True
    try:
        with open(str(path), "rb") as handle:
            handle.seek(len(MCAP_MAGIC))
            opcode, content = _mcap_record(handle)
            if opcode == 0x01:
                profile, pos = _mcap_string(content, 0)
                library, _ = _mcap_string(content, pos)
                info["mcap_profile"] = profile
                info["mcap_library"] = library
                if profile == "ros1":
                    info["family"] = "ros1"
            metadata = _mcap_metadata(handle, "rosbag2")
            if metadata.get("serialized_metadata"):  # rosbag2 keeps a copy of metadata.yaml here
                _apply_embedded_metadata(info, metadata["serialized_metadata"])
    except (OSError, struct.error, ValueError) as exc:
        info["issues"].append("unreadable mcap header: {}".format(exc))


def _mcap_record(handle):
    opcode = _read_exact(handle, 1)[0]
    (length,) = struct.unpack("<Q", _read_exact(handle, 8))
    if length > (1 << 26):
        raise ValueError("mcap record too large")
    return opcode, _read_exact(handle, length)


def _mcap_string(data, pos):
    (length,) = struct.unpack("<I", data[pos:pos + 4])
    return data[pos + 4:pos + 4 + length].decode("utf-8", "replace"), pos + 4 + length


def _mcap_metadata(handle, name):
    """Read the last Metadata record called ``name`` via the summary's MetadataIndex ({} if absent)."""
    handle.seek(0, os.SEEK_END)
    size = handle.tell()
    footer_start = size - len(MCAP_MAGIC) - (1 + 8 + 20)
    if footer_start <= 0:
        return {}
    handle.seek(footer_start)
    opcode, content = _mcap_record(handle)
    if opcode != 0x02:
        return {}
    summary_start = struct.unpack("<Q", content[0:8])[0]
    if not summary_start:
        return {}
    handle.seek(summary_start)
    offset = None
    while handle.tell() < footer_start:
        opcode, content = _mcap_record(handle)
        if opcode == 0x0D and _mcap_string(content, 16)[0] == name:  # MetadataIndex: offset, length, name
            offset = struct.unpack("<Q", content[0:8])[0]
    if offset is None:
        return {}
    handle.seek(offset)
    opcode, record = _mcap_record(handle)
    if opcode != 0x0C:
        return {}
    _, pos = _mcap_string(record, 0)
    (map_len,) = struct.unpack("<I", record[pos:pos + 4])
    pos, end, result = pos + 4, pos + 4 + map_len, {}
    while pos < end:
        key, pos = _mcap_string(record, pos)
        value, pos = _mcap_string(record, pos)
        result[key] = value
    return result


def _apply_embedded_metadata(info, text):
    """Version/distro from the metadata.yaml copy stored inside a sqlite3 or mcap file."""
    try:
        meta = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return
    meta = meta.get("rosbag2_bagfile_information", meta)
    if meta.get("version") is not None:
        info["embedded_metadata_version"] = meta["version"]
    if meta.get("ros_distro"):
        info["ros_distro"] = str(meta["ros_distro"])


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _read_exact(handle, size):
    data = handle.read(size)
    if len(data) != size:
        raise ValueError("unexpected end of file")
    return data


def _info(path, family, container="", storage="", format_version=None, ros_distro="", compression="none",
          compression_mode="", embedded_definitions=None, files=None, issues=None):
    return {
        "path": str(path),
        "family": family,
        "container": container,
        "storage": storage,
        "format_version": format_version,
        "ros_distro": ros_distro,
        "compression": compression,
        "compression_mode": compression_mode,
        "embedded_definitions": embedded_definitions,
        "files": list(files or []),
        "issues": list(issues or []),
        "notes": [],
    }


def _finish(info):
    info["label"] = label(info)
    return info


def _relative(info, root):
    try:
        info["path"] = str(Path(info["path"]).relative_to(root)) or "."
    except ValueError:
        pass
    return info


def label(info):
    """e.g. 'ROS2 sqlite3 v5 humble, zstd file compression, 3 files'."""
    if info["family"] == "unknown":
        return "not a bag"
    parts = [info["family"].upper()]
    if info["container"] == "ros1_bag":
        parts.append("bag v{}".format(info["format_version"]))
    else:
        parts.append(info["storage"] or "?")
        if info["format_version"] is not None:
            parts.append("v{}".format(info["format_version"]))
        elif info["container"].endswith("_file"):
            parts.append("file")
    if info["ros_distro"]:
        parts.append(info["ros_distro"])
    text = " ".join(parts)
    if info["compression"] not in ("", "none"):
        text += ", {} {} compression".format(info["compression"], info["compression_mode"] or "")
    if len(info["files"]) > 1:
        text += ", {} files".format(len(info["files"]))
    if info["notes"]:
        text += " ({})".format("; ".join(info["notes"]))
    if info["issues"]:
        text += " [{}]".format("; ".join(info["issues"]))
    return text.replace("  ", " ")
