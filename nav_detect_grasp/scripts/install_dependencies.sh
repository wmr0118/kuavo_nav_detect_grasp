#!/bin/bash

# 安装依赖脚本
# 使用方法: ./install_dependencies.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info "开始安装nav_detect_grasp demo的依赖包..."
echo ""

# 检查是否为Ubuntu系统
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_error "此脚本仅支持Ubuntu/Linux系统"
    exit 1
fi

# 检查ROS版本
if [ -z "$ROS_DISTRO" ]; then
    print_error "ROS环境未设置！请先安装ROS Noetic"
    print_info "安装命令: sudo apt-get install ros-noetic-desktop-full"
    exit 1
fi

print_info "检测到ROS版本: $ROS_DISTRO"

# 更新包列表
print_info "更新包列表..."
sudo apt-get update

# 安装ROS依赖包
print_info "安装ROS依赖包..."
sudo apt-get install -y \
    ros-$ROS_DISTRO-apriltag-ros \
    ros-$ROS_DISTRO-cv-bridge \
    ros-$ROS_DISTRO-image-transport \
    ros-$ROS_DISTRO-tf2-ros \
    ros-$ROS_DISTRO-tf2-geometry-msgs \
    ros-$ROS_DISTRO-realsense2-camera \
    ros-$ROS_DISTRO-robot-localization \
    ros-$ROS_DISTRO-navigation \
    ros-$ROS_DISTRO-gmapping \
    ros-$ROS_DISTRO-amcl

# 安装Python依赖
print_info "安装Python依赖..."
sudo apt-get install -y \
    python3-pip \
    python3-opencv \
    python3-numpy \
    python3-scipy

# 安装Ultralytics YOLO
print_info "安装Ultralytics YOLO..."
pip3 install ultralytics

# 安装其他Python包
print_info "安装其他Python包..."
pip3 install \
    opencv-python \
    numpy \
    scipy \
    matplotlib \
    pillow

# 检查安装结果
print_info "检查安装结果..."
echo ""

# 检查ROS包
ros_packages=(
    "apriltag_ros"
    "cv_bridge"
    "image_transport"
    "tf2_ros"
    "tf2_geometry_msgs"
    "realsense2_camera"
)

for pkg in "${ros_packages[@]}"; do
    if rospack find "$pkg" > /dev/null 2>&1; then
        print_success "$pkg: 已安装"
    else
        print_error "$pkg: 安装失败"
    fi
done

# 检查Python包
python_packages=(
    "ultralytics"
    "opencv"
    "numpy"
    "scipy"
)

for pkg in "${python_packages[@]}"; do
    if python3 -c "import $pkg" 2>/dev/null; then
        print_success "$pkg: 已安装"
    else
        print_error "$pkg: 安装失败"
    fi
done

echo ""
print_success "依赖安装完成！"
print_info "现在可以运行demo了："
print_info "1. 编译工作空间: catkin_make"
print_info "2. 下载YOLO模型: ./models/download_models.sh"
print_info "3. 启动demo: ./scripts/start_demo.sh"
echo ""
print_info "如果遇到问题，请运行测试脚本: ./scripts/test_components.py" 