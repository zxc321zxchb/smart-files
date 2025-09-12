#!/bin/bash
# 多平台构建脚本

echo "🚀 开始多平台构建..."

# 创建构建目录
mkdir -p builds

# 构建Linux版本
echo "📦 构建Linux版本..."
docker build -f Dockerfile.build -t file-save-system-linux .
docker run --rm -v $(pwd)/builds/linux:/app/dist file-save-system-linux

# 构建Windows版本（需要Windows容器）
echo "📦 构建Windows版本..."
# 注意：这需要在Windows容器环境中运行
# docker build -f Dockerfile.build.windows -t file-save-system-windows .
# docker run --rm -v $(pwd)/builds/windows:/app/dist file-save-system-windows

echo "✅ 构建完成！"
echo "Linux版本: builds/linux/"
echo "Windows版本: 需要在Windows系统上构建"
