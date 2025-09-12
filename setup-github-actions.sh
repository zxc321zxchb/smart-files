#!/bin/bash
# GitHub Actions 快速设置脚本

echo "🚀 设置GitHub Actions多平台构建..."

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    echo "📦 初始化Git仓库..."
    git init
fi

# 检查是否有远程仓库
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "⚠️  请先添加GitHub远程仓库："
    echo "   git remote add origin https://github.com/zxc321zxchb/smart-files.git"
    echo ""
fi

# 添加所有文件
echo "📁 添加文件到Git..."
git add .

# 检查是否有未提交的更改
if git diff --staged --quiet; then
    echo "✅ 没有新的更改需要提交"
else
    echo "💾 提交更改..."
    git commit -m "Add GitHub Actions multi-platform build support

- Add PyInstaller configuration
- Add multi-platform build workflow
- Add build scripts and documentation
- Support Windows, macOS, and Linux builds"
fi

# 显示下一步操作
echo ""
echo "🎉 GitHub Actions配置完成！"
echo ""
echo "📋 下一步操作："
echo "1. 添加GitHub远程仓库（如果还没有）："
echo "   git remote add origin https://github.com/zxc321zxchb/smart-files.git"
echo ""
echo "2. 推送到GitHub："
echo "   git push -u origin main"
echo ""
echo "3. 在GitHub上查看Actions："
echo "   https://github.com/yourusername/your-repo/actions"
echo ""
echo "4. 创建发布版本（可选）："
echo "   git tag v1.0.0"
echo "   git push origin v1.0.0"
echo ""
echo "🔗 相关文件："
echo "   - .github/workflows/build.yml (构建工作流)"
echo "   - build.py (本地构建脚本)"
echo "   - build-ci.py (CI构建脚本)"
echo "   - GITHUB_ACTIONS_GUIDE.md (详细说明)"
echo ""
echo "✨ 配置完成！推送代码后会自动构建多平台版本。"
