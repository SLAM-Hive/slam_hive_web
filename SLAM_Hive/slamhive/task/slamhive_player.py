#!/usr/bin/env python3
"""SLAM-Hive dataset player, installed as /slamhive/dataset/rosbag_play.py for every task.

Runs the command the scheduler planned in /slamhive/dataset/playback.json
(`rosbag play ...` for ROS1 algorithms, `ros2 bag play ...` for ROS2 ones).
Algorithms keep calling `python3 /slamhive/dataset/rosbag_play.py` as before.

Compatible with Python 3.5 (ROS Kinetic images); standard library only.
"""

import json
import os
import shutil
import signal
import subprocess
import sys

PLAYBACK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playback.json")


def main():
    with open(PLAYBACK, "r") as handle:
        plan = json.load(handle)
    command = [str(part) for part in plan["command"]]
    timeout = plan.get("timeout_s")
    print("[slamhive-player] {}".format(plan.get("summary", "")), flush=True)
    print("[slamhive-player] command: {}".format(" ".join(command)), flush=True)
    if shutil.which(command[0]) is None:
        # Caller did not source ROS; do it for the player.
        command = ["bash", "-c", 'source /opt/ros/"$ROS_DISTRO"/setup.bash >/dev/null 2>&1; exec "$@"',
                   "bash"] + command
    process = subprocess.Popen(command)
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        print("[slamhive-player] bag_duration reached, stopping playback", flush=True)
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        return 0


if __name__ == "__main__":
    sys.exit(main())
