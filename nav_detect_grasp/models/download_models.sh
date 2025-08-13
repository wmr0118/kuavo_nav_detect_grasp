#!/bin/bash

# 下载YOLO模型脚本
# 使用方法: ./download_models.sh

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

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_DIR="$SCRIPT_DIR"

print_info "开始下载YOLO模型文件..."
print_info "模型将下载到: $MODELS_DIR"
echo ""

# 创建models目录（如果不存在）
mkdir -p "$MODELS_DIR"

# 下载YOLOv8n模型（轻量级，适合实时检测）
print_info "下载YOLOv8n模型..."
if [ ! -f "$MODELS_DIR/yolov8n.pt" ]; then
    wget -O "$MODELS_DIR/yolov8n.pt" \
         "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
    print_success "YOLOv8n模型下载完成"
else
    print_info "YOLOv8n模型已存在，跳过下载"
fi

# 下载YOLOv8s模型（中等大小，平衡速度和精度）
print_info "下载YOLOv8s模型..."
if [ ! -f "$MODELS_DIR/yolov8s.pt" ]; then
    wget -O "$MODELS_DIR/yolov8s.pt" \
         "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt"
    print_success "YOLOv8s模型下载完成"
else
    print_info "YOLOv8s模型已存在，跳过下载"
fi

# 下载YOLOv8m模型（较大，更高精度）
print_info "下载YOLOv8m模型..."
if [ ! -f "$MODELS_DIR/yolov8m.pt" ]; then
    wget -O "$MODELS_DIR/yolov8m.pt" \
         "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt"
    print_success "YOLOv8m模型下载完成"
else
    print_info "YOLOv8m模型已存在，跳过下载"
fi

echo ""
print_info "检查下载的模型文件..."

# 检查文件大小
for model in yolov8n.pt yolov8s.pt yolov8m.pt; do
    if [ -f "$MODELS_DIR/$model" ]; then
        size=$(du -h "$MODELS_DIR/$model" | cut -f1)
        print_success "$model: $size"
    else
        print_error "$model: 下载失败"
    fi
done

echo ""
print_success "所有YOLO模型下载完成！"
print_info "默认使用YOLOv8n模型（最快速度）"
print_info "如需更高精度，可在配置文件中修改model_path参数"
echo ""
print_info "模型文件位置: $MODELS_DIR" 