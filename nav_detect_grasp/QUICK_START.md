# Navigation, Detection and Grasp Demo - 快速开始

## 🚀 一键启动

### 方法1: 使用启动脚本（推荐）
```bash
# 进入demo目录
cd src/demo/trace_path/nav_detect_grasp

# 一键启动（实物模式 + RealSense相机）
./scripts/start_demo.sh

# 仿真模式启动
./scripts/start_demo.sh simulation

# 使用ZED相机
./scripts/start_demo.sh real zed
```

### 方法2: 手动启动
```bash
# 1. 启动相机
roslaunch realsense2_camera rs_camera.launch

# 2. 启动AprilTag检测
roslaunch apriltag_ros continuous_detection.launch camera_name:=/camera image_topic:=image_raw

# 3. 启动主demo
roslaunch nav_detect_grasp nav_detect_grasp.launch

# 4. 启动可视化（可选）
rviz -d rviz/nav_detect_grasp.rviz
```

## 📋 前置要求

### 系统要求
- Ubuntu 20.04 + ROS Noetic
- Python 3.8+
- 相机：RealSense D435i 或 ZED

### 硬件要求
- Kuavo人形机器人
- 相机（已连接并驱动已安装）
- AprilTag标记（放置在目标位置）
- 目标物体（水杯、瓶子等）

## 🔧 安装步骤

### 1. 安装依赖
```bash
# 自动安装所有依赖
./scripts/install_dependencies.sh

# 或手动安装
sudo apt-get install ros-noetic-apriltag-ros ros-noetic-realsense2-camera
pip3 install ultralytics opencv-python numpy
```

### 2. 编译工作空间
```bash
# 在workspace根目录
catkin_make
source devel/setup.bash
```

### 3. 下载YOLO模型
```bash
# 自动下载YOLO模型
./models/download_models.sh

# 或手动下载
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt
```

## 🧪 测试系统

### 运行组件测试
```bash
# 测试所有组件是否正常工作
./scripts/test_components.py
```

### 检查话题
```bash
# 查看所有活跃话题
rostopic list

# 检查关键话题
rostopic echo /camera/color/image_raw
rostopic echo /robot_tag_info
rostopic echo /yolo_detections
```

## ⚙️ 配置参数

### 修改检测参数
编辑 `config/detection_params.yaml`:
```yaml
apriltag:
  marker_id: 0              # 目标AprilTag ID
  marker_size: 0.05         # 标记尺寸(m)

yolo:
  confidence_threshold: 0.5  # 检测置信度阈值
  target_classes: ["cup", "bottle"]  # 目标类别
```

### 修改导航参数
编辑 `config/navigation_params.yaml`:
```yaml
target_area_pose:
  x: 1.0      # 目标区域位置
  y: 0.0
  z: 0.74
  yaw: 0.0
```

### 修改抓取参数
编辑 `config/grasp_params.yaml`:
```yaml
grasp:
  approach_distance: 0.2    # 接近距离
  hand_separation: 0.15     # 手部间距
```

## 🎯 使用流程

### 1. 准备工作
- 确保机器人处于安全状态
- 放置AprilTag标记在目标位置
- 放置目标物体在相机视野内

### 2. 启动系统
```bash
./scripts/start_demo.sh
```

### 3. 执行任务
系统将自动执行以下步骤：
1. **导航**到目标区域
2. **检测**AprilTag和YOLO目标
3. **接近**目标物体
4. **抓取**目标物体
5. **导航**到放置区域
6. **放置**物体
7. **返回**起始位置

### 4. 监控状态
- 查看RViz可视化界面
- 监控终端输出日志
- 检查话题数据

## 🚨 故障排除

### 常见问题

#### 1. 相机不工作
```bash
# 检查相机连接
lsusb | grep RealSense

# 重启相机驱动
rosnode kill /camera/realsense2_camera_node
roslaunch realsense2_camera rs_camera.launch
```

#### 2. AprilTag检测失败
```bash
# 检查相机话题
rostopic echo /camera/color/image_raw

# 检查AprilTag节点
rosnode list | grep apriltag
```

#### 3. YOLO检测失败
```bash
# 检查模型文件
ls -la models/

# 检查Python包
python3 -c "import ultralytics; print('OK')"
```

#### 4. 机器人控制失败
```bash
# 检查控制服务
rosservice list | grep arm

# 检查机器人状态
rostopic echo /robot_status
```

### 获取帮助
```bash
# 查看详细日志
roslaunch nav_detect_grasp nav_detect_grasp.launch --screen

# 运行测试脚本
./scripts/test_components.py

# 查看启动脚本帮助
./scripts/start_demo.sh --help
```

## 📚 更多信息

- **完整文档**: 查看 `README.md`
- **代码结构**: 查看 `scripts/` 目录
- **配置文件**: 查看 `config/` 目录
- **启动文件**: 查看 `launch/` 目录

## 🤝 技术支持

如果遇到问题，请：
1. 运行测试脚本检查组件状态
2. 查看终端日志输出
3. 检查配置文件参数
4. 参考故障排除部分

---

**祝您使用愉快！** 🎉 