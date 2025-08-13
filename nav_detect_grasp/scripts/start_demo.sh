#!/bin/bash

# Navigation, Detection and Grasp Demo启动脚本
# 使用方法: ./start_demo.sh [simulation|real] [camera_type]

set -e  # 遇到错误时退出

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

# 检查ROS环境
check_ros_environment() {
    print_info "检查ROS环境..."
    
    if [ -z "$ROS_DISTRO" ]; then
        print_error "ROS环境未设置！请先运行 source /opt/ros/noetic/setup.bash"
        exit 1
    fi
    
    if [ "$ROS_DISTRO" != "noetic" ]; then
        print_warning "当前ROS版本: $ROS_DISTRO，推荐使用ROS Noetic"
    fi
    
    print_success "ROS环境检查通过: $ROS_DISTRO"
}

# 检查工作空间
check_workspace() {
    print_info "检查工作空间..."
    
    if [ -z "$ROS_PACKAGE_PATH" ]; then
        print_error "ROS工作空间未设置！请先运行 source devel/setup.bash"
        exit 1
    fi
    
    # 检查包是否存在
    if ! rospack find nav_detect_grasp > /dev/null 2>&1; then
        print_error "nav_detect_grasp包未找到！请先编译工作空间"
        exit 1
    fi
    
    print_success "工作空间检查通过"
}

# 检查依赖包
check_dependencies() {
    print_info "检查依赖包..."
    
    local missing_packages=()
    
    # 检查必要的ROS包
    local required_packages=(
        "apriltag_ros"
        "kuavo_msgs"
        "cv_bridge"
        "image_transport"
        "tf2_ros"
        "tf2_geometry_msgs"
    )
    
    for pkg in "${required_packages[@]}"; do
        if ! rospack find "$pkg" > /dev/null 2>&1; then
            missing_packages+=("$pkg")
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        print_error "缺少以下依赖包: ${missing_packages[*]}"
        print_info "请安装缺失的包: sudo apt-get install ros-noetic-${missing_packages[*]}"
        exit 1
    fi
    
    print_success "依赖包检查通过"
}

# 检查相机驱动
check_camera_driver() {
    local camera_type=$1
    
    print_info "检查相机驱动: $camera_type"
    
    case $camera_type in
        "realsense")
            if ! rospack find realsense2_camera > /dev/null 2>&1; then
                print_warning "RealSense相机驱动未安装"
                print_info "安装命令: sudo apt-get install ros-noetic-realsense2-camera"
            else
                print_success "RealSense相机驱动已安装"
            fi
            ;;
        "zed")
            if ! rospack find zed_ros > /dev/null 2>&1; then
                print_warning "ZED相机驱动未安装"
                print_info "请从ZED官网下载并安装ZED ROS包"
            else
                print_success "ZED相机驱动已安装"
            fi
            ;;
        *)
            print_warning "未知相机类型: $camera_type"
            ;;
    esac
}

# 检查YOLO模型
check_yolo_model() {
    print_info "检查YOLO模型..."
    
    local model_path="$(rospack find nav_detect_grasp)/models/yolov8n.pt"
    
    if [ ! -f "$model_path" ]; then
        print_warning "YOLO模型文件不存在: $model_path"
        print_info "请下载YOLOv8模型文件到models目录"
        print_info "下载命令: wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O $model_path"
    else
        print_success "YOLO模型文件存在"
    fi
}

# 启动相机节点
start_camera() {
    local camera_type=$1
    
    print_info "启动相机节点: $camera_type"
    
    case $camera_type in
        "realsense")
            if rospack find realsense2_camera > /dev/null 2>&1; then
                print_info "启动RealSense相机..."
                roslaunch realsense2_camera rs_camera.launch &
                sleep 3
            else
                print_warning "RealSense相机驱动未安装，跳过相机启动"
            fi
            ;;
        "zed")
            if rospack find zed_ros > /dev/null 2>&1; then
                print_info "启动ZED相机..."
                roslaunch zed_wrapper zed_camera.launch &
                sleep 3
            else
                print_warning "ZED相机驱动未安装，跳过相机启动"
            fi
            ;;
        "gemini")
            print_info "启动Gemini-335L相机..."
            # 使用官方推荐的启动方式
            roslaunch dynamic_biped load_robot_head.launch use_orbbec:=true &
            sleep 3
            ;;
        *)
            print_warning "未知相机类型，跳过相机启动"
            ;;
    esac
}

# 启动AprilTag检测
start_apriltag_detection() {
    print_info "启动AprilTag检测节点..."
    
    # 启动AprilTag检测
    roslaunch apriltag_ros continuous_detection.launch camera_name:=/camera image_topic:=image_raw &
    sleep 2
    
    print_success "AprilTag检测节点已启动"
}

# 启动主demo
start_main_demo() {
    local simulation_mode=$1
    
    print_info "启动主demo节点..."
    
    if [ "$simulation_mode" = "simulation" ]; then
        print_info "仿真模式启动..."
        roslaunch nav_detect_grasp nav_detect_grasp.launch use_simulation:=true &
    else
        print_info "实物模式启动..."
        roslaunch nav_detect_grasp nav_detect_grasp.launch use_simulation:=false &
    fi
    
    sleep 2
    print_success "主demo节点已启动"
}

# 启动RViz可视化
start_visualization() {
    print_info "启动RViz可视化..."
    
    rviz -d "$(rospack find nav_detect_grasp)/rviz/nav_detect_grasp.rviz" &
    
    print_success "RViz可视化已启动"
}

# 显示使用说明
show_usage() {
    echo "使用方法: $0 [simulation|real] [camera_type]"
    echo ""
    echo "参数说明:"
    echo "  simulation|real  运行模式 (默认: real)"
    echo "  camera_type      相机类型 (默认: realsense)"
    echo ""
    echo "示例:"
    echo "  $0                    # 实物模式 + RealSense相机"
    echo "  $0 simulation         # 仿真模式 + RealSense相机"
    echo "  $0 real zed          # 实物模式 + ZED相机"
    echo "  $0 simulation zed    # 仿真模式 + ZED相机"
    echo "  $0 real gemini       # 实物模式 + Gemini-335L相机"
    echo "  $0 simulation gemini # 仿真模式 + Gemini-335L相机"
    echo ""
    echo "注意事项:"
    echo "  1. 确保ROS环境已设置"
    echo "  2. 确保工作空间已编译"
    echo "  3. 确保相机已连接并驱动已安装"
    echo "  4. 确保AprilTag标记已放置在目标位置"
    echo "  5. 确保目标物体在相机视野内"
}

# 主函数
main() {
    echo "=========================================="
    echo "  Navigation, Detection and Grasp Demo"
    echo "=========================================="
    echo ""
    
    # 解析参数
    local simulation_mode=${1:-"real"}
    local camera_type=${2:-"realsense"}
    
    # 验证参数
    if [ "$simulation_mode" != "simulation" ] && [ "$simulation_mode" != "real" ]; then
        print_error "无效的运行模式: $simulation_mode"
        show_usage
        exit 1
    fi
    
    if [ "$camera_type" != "realsense" ] && [ "$camera_type" != "zed" ] && [ "$camera_type" != "gemini" ]; then
        print_error "无效的相机类型: $camera_type"
        show_usage
        exit 1
    fi
    
    print_info "运行模式: $simulation_mode"
    print_info "相机类型: $camera_type"
    echo ""
    
    # 执行检查
    check_ros_environment
    check_workspace
    check_dependencies
    check_camera_driver "$camera_type"
    check_yolo_model
    echo ""
    
    # 启动节点
    print_info "开始启动demo节点..."
    echo ""
    
    start_camera "$camera_type"
    start_apriltag_detection
    start_main_demo "$simulation_mode"
    start_visualization
    
    echo ""
    print_success "所有节点启动完成！"
    echo ""
    print_info "Demo已启动，请查看RViz窗口进行可视化"
    print_info "按Ctrl+C停止所有节点"
    echo ""
    
    # 等待用户中断
    wait
}

# 清理函数
cleanup() {
    print_info "正在停止所有节点..."
    
    # 停止所有后台进程
    jobs -p | xargs -r kill
    
    print_success "所有节点已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 检查是否请求帮助
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage
    exit 0
fi

# 运行主函数
main "$@" 