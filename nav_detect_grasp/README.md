# Navigation, Detection and Grasp Demo

## 概述

`nav_detect_grasp` 是一个完整的导航、检测和抓取演示程序，展示了Kuavo人形机器人如何：

1. **自主导航**到目标区域
2. **检测和识别**目标物体（使用AprilTag和YOLO）
3. **精确接近**并抓取物体
4. **导航到放置区域**
5. **安全放置**物体
6. **返回起始位置**

该演示结合了机器人的运动控制、视觉感知和机械臂操作能力。

## 功能特性

- **多模态检测**: 支持AprilTag二维码检测和YOLO通用物体检测
- **自主导航**: 使用步态控制实现精确的机器人导航
- **智能抓取**: 基于IK/FK计算的精确机械臂控制
- **安全保护**: 碰撞检测和运动限制
- **可视化**: 实时路径和状态可视化
- **配置灵活**: 支持仿真和实物模式

## 系统要求

### 硬件要求
- Kuavo人形机器人
- Gemini-335L相机（推荐，官方标配）、RealSense或ZED相机（支持深度信息）
- AprilTag标记（可选，用于精确定位）
- 目标物体（水杯、瓶子、书本等）

### 软件依赖
- ROS Noetic
- Kuavo Humanoid SDK
- AprilTag ROS包 (`aruco_ros`)
- YOLOv8 (`ultralytics`)
- Gemini-335L相机驱动（`dynamic_biped`，官方推荐）
- RealSense2或ZED相机驱动（可选）
- OpenCV (`cv_bridge`)

## 安装和编译

### 1. 安装依赖包

```bash
# 安装AprilTag ROS包
sudo apt-get install ros-noetic-aruco-ros

# 安装相机驱动（选择其一）
sudo apt-get install ros-noetic-realsense2-camera
# 或
sudo apt-get install ros-noetic-zed-ros-wrapper

# 安装Python依赖
pip3 install ultralytics opencv-python numpy
```

### 2. 编译包

```bash
cd ~/kuavo_ros_control
catkin build nav_detect_grasp
source devel/setup.bash
```

### 3. 下载YOLO模型

```bash
# 创建模型目录
mkdir -p ~/kuavo_ros_control/src/demo/trace_path/nav_detect_grasp/models

# 下载预训练模型（首次运行会自动下载）
cd ~/kuavo_ros_control/src/demo/trace_path/nav_detect_grasp/models
# 或者手动下载：wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

## 使用方法

### 1. 准备环境

#### 设置机器人版本
```bash
export ROBOT_VERSION=45  # 根据实际机器人版本设置
```

#### 准备AprilTag标记（可选）
- 打印ID为0的AprilTag标记
- 标记尺寸：5cm × 5cm
- 将标记固定在目标物体上

#### 设置工作环境
- 确保机器人周围有足够的空间（至少3m×3m）
- 放置目标物体在机器人前方1-1.5米处
- 确保放置区域无障碍
- 准备一个放置平台或区域

### 2. 启动演示

#### 仿真模式
```bash
# 启动仿真环境
roslaunch nav_detect_grasp nav_detect_grasp.launch use_simulation:=true
```

#### 实物模式
```bash
# 启动实物控制
roslaunch nav_detect_grasp nav_detect_grasp.launch use_simulation:=false
```

#### 自定义参数启动
```bash
# 禁用YOLO检测，仅使用AprilTag
roslaunch nav_detect_grasp nav_detect_grasp.launch use_yolo_detection:=false

# 禁用AprilTag检测，仅使用YOLO
roslaunch nav_detect_grasp nav_detect_grasp.launch use_apriltag_detection:=false

# 禁用可视化
roslaunch nav_detect_grasp nav_detect_grasp.launch use_visualization:=false
```

### 3. 运行演示

1. 等待机器人启动并进入stance模式
2. 在终端中按Enter键开始演示
3. 观察机器人执行完整的导航+检测+抓取流程

## 配置参数

### 导航参数 (`config/navigation_params.yaml`)

```yaml
# 目标区域位置
target_area_pose:
  x: 1.0      # 前方1米
  y: 0.0      # 正前方
  z: 0.74     # COM高度
  yaw: 0.0    # 朝向

# 放置区域位置
place_area_pose:
  x: 2.0      # 前方2米
  y: 0.5      # 左侧0.5米
  z: 0.74     # COM高度
  yaw: 45.0   # 45度朝向
```

### 检测参数 (`config/detection_params.yaml`)

```yaml
# AprilTag检测参数
apriltag:
  marker_id: 0                   # 目标AprilTag ID
  marker_size: 0.05              # 标记尺寸
  detection_timeout: 10.0        # 检测超时

# YOLO检测参数
yolo:
  model_path: "yolov8n.pt"       # YOLO模型文件
  confidence_threshold: 0.5      # 检测置信度阈值
  target_classes: ["cup", "bottle", "book", "box"]  # 目标物体类别
```

### 抓取参数 (`config/grasp_params.yaml`)

```yaml
# 抓取参数
grasp:
  approach_distance: 0.2            # 接近距离
  hand_separation: 0.15             # 手部间距
  gripper_open_position: 90         # 夹爪开启位置
  gripper_close_position: 10        # 夹爪关闭位置
```

## 工作流程

### 1. 初始化阶段
- 机器人启动并进入stance模式
- 加载配置参数
- 初始化SDK和控制器
- 启动相机和检测节点

### 2. 导航阶段
- 使用`/cmd_pose`控制导航到目标区域
- 实时路径规划和碰撞检测
- 精确到达目标位置

### 3. 检测阶段
- 启动AprilTag标记检测（如果启用）
- 启动YOLO物体检测（如果启用）
- 计算目标物体的3D位置
- 验证目标在可操作范围内

### 4. 接近阶段
- 计算接近姿态
- 精确导航到抓取位置
- 调整机器人朝向

### 5. 抓取阶段
- 设置机械臂为外部控制模式
- 计算IK解算抓取姿态
- 执行抓取动作
- 关闭夹爪

### 6. 放置阶段
- 导航到放置区域
- 计算放置姿态
- 执行放置动作
- 打开夹爪

### 7. 返回阶段
- 导航回起始位置
- 恢复初始姿态

## 故障排除

### 常见问题

#### 1. 机器人无法启动
- 检查机器人版本设置：`echo $ROBOT_VERSION`
- 确认机器人硬件连接正常
- 检查急停开关状态

#### 2. 检测失败
- **AprilTag检测失败**:
  - 检查标记是否清晰可见
  - 确认标记ID正确
  - 调整相机参数和光照条件
- **YOLO检测失败**:
  - 检查模型文件是否存在
  - 确认目标物体在相机视野内
  - 调整置信度阈值

#### 3. 导航失败
- 检查目标位置是否可达
- 确认路径无障碍
- 调整导航参数

#### 4. 抓取失败
- 检查IK解算是否成功
- 确认机械臂在安全范围内
- 验证夹爪状态

### 调试技巧

#### 1. 启用可视化
```bash
roslaunch nav_detect_grasp nav_detect_grasp.launch use_visualization:=true
```

#### 2. 查看TF变换
```bash
rosrun tf tf_echo base_link head_camera_color_optical_frame
```

#### 3. 监控话题
```bash
# 查看机器人状态
rostopic echo /humanoid_mpc_observation

# 查看AprilTag检测结果
rostopic echo /robot_tag_info

# 查看YOLO检测结果
rostopic echo /yolo_detections

# 查看目标位姿
rostopic echo /target_pose

# 查看机器人位姿
rostopic echo /odom
```

#### 4. 检查服务状态
```bash
# 检查IK服务
rosservice call /ik/two_arm_hand_pose_cmd_srv

# 检查手臂控制模式
rosservice call /arm_traj_change_mode
```

## 扩展开发

### 添加新的导航目标

1. 修改`navigation_params.yaml`中的目标位置
2. 在代码中添加新的导航逻辑
3. 测试导航精度和安全性

### 支持新的物体类型

1. 添加新的AprilTag标记ID
2. 在YOLO配置中添加新的目标类别
3. 修改抓取策略和参数

### 集成SLAM功能

1. 添加SLAM节点（如cartographer、gmapping）
2. 实现动态路径规划
3. 集成障碍物避障

### 改进抓取策略

1. 实现基于视觉的抓取点选择
2. 添加力反馈控制
3. 实现多指协调抓取

## 性能优化

### 检测性能
- 调整YOLO模型大小（yolov8n.pt → yolov8s.pt → yolov8m.pt）
- 优化图像分辨率
- 使用GPU加速（如果可用）

### 导航性能
- 调整步态参数
- 优化路径规划算法
- 实现预测性控制

### 抓取性能
- 优化IK求解参数
- 实现轨迹平滑
- 添加碰撞检测

## 贡献指南

欢迎提交Issue和Pull Request来改进这个演示程序。

### 开发规范
- 遵循PEP 8 Python代码规范
- 添加适当的注释和文档
- 进行充分的测试

### 测试要求
- 在仿真环境中测试所有功能
- 在实物机器人上验证关键功能
- 提供测试用例和示例

## 许可证

本项目采用BSD许可证。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至：[your_email@example.com]

## 更新日志

### v0.0.1 (2024-01-XX)
- 初始版本发布
- 支持AprilTag和YOLO检测
- 实现基本的导航和抓取功能
- 提供完整的配置和启动文件 