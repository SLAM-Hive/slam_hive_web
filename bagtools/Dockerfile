# SLAM-Hive bag tools: probe/convert ROS1 and ROS2 bags outside the Web runtime.
# Build: docker build -t slam-hive-bagtools:1 slam_hive_web/bagtools
FROM python:3.12-slim
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple rosbags==0.11.5 pyyaml==6.0.2
COPY bagformat.py bagtools.py /opt/bagtools/
WORKDIR /work
ENTRYPOINT ["python", "/opt/bagtools/bagtools.py"]
