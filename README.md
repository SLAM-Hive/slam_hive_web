## 1. Install Docker
Install Docker and docker-compose: <https://www.docker.com>


## 2. Build SLAM algorithm images
We provide some SLAM algorithms Dockerfile and running scripts, here is an example to build an image:
```
$ git clone https://github.com/STAR-Center/SLAM-Hive.git SLAM_Hive
$ cd SLAM_Hive/slam_hive_algos/orb-slam2-ros-mono
$ sudo chmod +x install.sh
$ ./install.sh
```
You can check whether the image is successfully built as follows:
```
$ docker images
```
you can see:
```
slam-hive-algorithm     orb-slam2-ros-mono      [IMAGE ID]      [CREATED]       [SIZE]
```
Go go to other directory in `/SLAM_Hive/slam_hive_algos/<> `and execute the above command to build remaining images. After that you will see the following images:
```
REPOSITORY             TAG                              IMAGE ID       CREATED         SIZE
slam-hive-evaluation   evo                              0254b6ded2cb   5 weeks ago     1.79GB
slam-hive-algorithm    vins-mono                        de2b13e0fc07   5 weeks ago     2.96GB
slam-hive-algorithm    vins-fusion-mono-imu             9078af9ba64a   7 days ago      3.1GB
slam-hive-algorithm    vins-fusion-stereo               9078af9ba64a   7 days ago      3.1GB
slam-hive-algorithm    vins-fusion-stereo-imu           9078af9ba64a   7 days ago      3.1GB
slam-hive-algorithm    orb-slam2-ros-mono               2f8241d1df9a   6 weeks ago     3.39GB
slam-hive-algorithm    orb-slam2-ros-rgbd               2f8241d1df9a   6 weeks ago     3.39GB
slam-hive-algorithm    orb-slam2-ros-stereo             2f8241d1df9a   6 weeks ago     3.39GB
slam-hive-algorithm    orb-slam3-ros-mono               28c13955a331   9 days ago      4.17GB
slam-hive-algorithm    orb-slam3-ros-mono-inertial      28c13955a331   9 days ago      4.17GB
slam-hive-algorithm    orb-slam3-ros-stereo             28c13955a331   9 days ago      4.17GB
slam-hive-algorithm    orb-slam3-ros-stereo-inertial    28c13955a331   9 days ago      4.17GB
slam-hive-algorithm    orb-slam3-ros-rgbd               28c13955a331   9 days ago      4.17GB
slam-hive-algorithm    lio-sam                          99b1395a3b41   9 days ago      3.15GB
```
If the image construction speed is very slow, it is recommended to find the Dockerfile in the corresponding folder and change the source list: `/etc/apt/sources.list`

## 3. Download datasets
If there is not enough space on your computer, run the following command to download two datasets: `MH_01_easy.bag` (2.7G), `rgbd_dataset_freiburg2_desk.bag` (2.2 GB).
```
$ cd SLAM_Hive/slam_hive_datatsets
$ python3 download.py
```
We also provide download script for other datasets: `SLAM_Hive/slam_hive_datasets/download_all.py`. Please modify the script to download the dataset according to your needs.

## 4. Build web

```
$ cd SLAM_Hive/slam_hive_web
$ sudo chmod -R 777 db/data
$ docker-compose up
```
Then,open your browser and visit: <http://127.0.0.1:5000>

## 5. Create tasks
Ensure you have installed correspoding images and downloaded the dataset before creating tasks.
### 5.1 Create mapping tasks
Take orb-slam2-ros-mono and MH_01_easy as an example: (please make sure the above steps are successful)

Step1: Click the "Copy" button of the first config in the MappingTaskConfig list. 

Step2: Give this config a name and fill in the description.

Step3: Change some parameter values according to the actual situation, then click the "Save" button and return to the MappingTaskConfig list, click the "Create MappingTask" button, then a mapping task will be generated in the background, and when the task is completed, the status of this mapping task will change to " Finished” on MappingTask list.

You can also create a mapping task from scratch by clicking "Create Config". 

<!-- Click "Create Config" button on MappingTaskConfig page, select the algorithm and dataset you have installed and downloaded.  -->
### 5.2 Create evaluation tasks
When the mapping task is completed, the "Evaluate" button will appear in the MappingTask list. Click it to start the evaluation. After the evaluation is completed, the status of the Evaluation list will become "Finished". Click "Show" to see the evaluation results.

### 5.3 Extending Algorithms, Datasets, parameters
We provide some algorithms, datasets, and parameters supported by SLAM Hive on the web. For new additions, refer to the following tutorials.
### 5.3.1 Create your own algorithm
Step1: Write execution scripts

Algorithm execution scripts include three file. You can create them refer to scripts in `/SLAM_Hive/slam_hive_algos/<>/slamhive/`. The functions of each script are as described below.
| Script      | Description |
| ----------- | ----------- |
|`Docker image`| Build your algorithm Docker image, the image name must be: `slam-hive-algorithm:[tag]`. The name of your algorithm scripts folder must be the same as the image tag name.|
|`template.yaml`| This is the parameters template. Each mapping will generate a `mappingtask.yaml `parameter file based on template and the parameters input on the web. The template format is like `cx: $cx` . (Don't  ignore the space in between)    |
|`mapping.py`| The script first extracts the value of the configuration file generated by the web, generates `mappingtask.yaml` and remap command strings, then executes the corresponding algorithm running command, and finally saves the estimated trajectory to the specified directory.         |
|(optional) `launch file`| The launch file is optional, used to start the ROS node, set the configuration file path, and be responsible for the remap of the algorithm topic. |

##
Step2: Add algorithm to web

Click the "New" button on the Algorithm page, input the algorithm name, the name must be the same as the tag name of the image. Input your algorithm scripts url and description.
### 5.3.2 Create new dataset
Step1: Provide your dataset and a script

| File      | Description |
| ----------- | ----------- |
|`ROS bag`| Provide dataset in the form of ROS bag. |
|`groundtruth.txt`| The groundtruth format must be: `tx ty tz qx qy qz qw`|
|`rosbag_play.py`| This script generates the command of playing and remapping topics of the ROS bag. For details, please refer to `SLAM_Hive/slam_hive_datasets/<>/rosbag_play.py`|

##
Step2: Add dataset to web

Input dataset folder name, which must be the same as the name of dataset folder. Input dataset download url and description.
### 5.3.3 Create parameters
1.Format type declaration

(Don't omit space in between)
| Type      | Format |
| ----------- | ----------- |
|Dataset|This is the parameter type related to dataset, the format should follow: <br>`name1: value1`<br>`name2: value2`<br>...|
|Dataset matrix|If the dataset parameter is a matrix, choose this type, the format should follow:<br>`name: [value1, value2, ...]`|
|Dataset remap|If there is a need for ROS bag topic remap, please choose this type:<br>`name1: topic1`<br>`name2: topic2`<br>...|
|Algorithm| This is the parameter type related to algorithm, the format should follow:<br>`name1: value1`<br>`name2: value2`<br>...|
|Algorithm remap|If there is a need for algorithm remap,please choose this type:<br>`name1: topic1`<br>`name2: topic2`<br>...|
##
2.Add parameters to web

Fristly, add parameters on Parameter page, click "New", input parameter name, select the type according to the table above and fill in the description. Then, when you create MappingTaskConfig, choose the parameter you added in the previous step and input the value according to the format corresponding to the type.

## 6. Licence
The source code is released under [GPLv3](http://www.gnu.org/licenses/) license.

We are still working on improving the code reliability. For any technical issues, you can make an issue.

