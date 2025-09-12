# GitHub Actions 多平台构建指南

## 🎯 功能概述

GitHub Actions将自动为您的Django项目构建Windows、macOS和Linux三个平台的可执行文件。

## 🚀 使用方法

### 1. 推送代码到GitHub

```bash
# 初始化Git仓库（如果还没有）
git init

# 添加所有文件
git add .

# 提交更改
git commit -m "Add PyInstaller multi-platform build support"

# 添加远程仓库
git remote add origin https://github.com/yourusername/your-repo.git

# 推送到GitHub
git push -u origin main
```

### 2. 自动构建

推送代码后，GitHub Actions会自动：
- ✅ 在Windows上构建 `.exe` 文件
- ✅ 在macOS上构建可执行文件
- ✅ 在Linux上构建可执行文件
- ✅ 测试每个构建产物
- ✅ 上传构建产物到Artifacts

### 3. 手动触发构建

在GitHub仓库页面：
1. 点击 "Actions" 标签
2. 选择 "多平台构建" 工作流
3. 点击 "Run workflow" 按钮
4. 选择分支并点击 "Run workflow"

### 4. 创建发布版本

创建标签来触发发布：

```bash
# 创建标签
git tag v1.0.0

# 推送标签
git push origin v1.0.0
```

这将自动：
- 🏷️ 创建GitHub Release
- 📦 打包所有平台的文件
- 📝 生成使用说明
- 🚀 提供下载链接

## 📁 构建产物

### Artifacts（每次构建）
- `file-save-system-windows/` - Windows版本
- `file-save-system-macos/` - macOS版本  
- `file-save-system-linux/` - Linux版本

### Release（标签触发）
- `file_save_system_windows.exe` - Windows可执行文件
- `file_save_system_macos` - macOS可执行文件
- `file_save_system_linux` - Linux可执行文件
- `start_windows.bat` - Windows启动脚本
- `start_macos.sh` - macOS启动脚本
- `start_linux.sh` - Linux启动脚本
- `README.md` - 使用说明

## 🔧 工作流配置

### 触发条件
- 推送到 `main` 或 `master` 分支
- 创建标签（格式：`v*`）
- 手动触发（workflow_dispatch）
- Pull Request

### 构建环境
- **Windows**: `windows-latest`
- **macOS**: `macos-latest`  
- **Linux**: `ubuntu-latest`
- **Python**: 3.12

### 构建步骤
1. 检出代码
2. 设置Python环境
3. 安装依赖
4. 运行构建脚本
5. 测试可执行文件
6. 上传构建产物

## 📊 构建状态

在GitHub仓库页面可以看到：
- 🟢 绿色：构建成功
- 🔴 红色：构建失败
- 🟡 黄色：构建中

## 🐛 故障排除

### 常见问题

1. **构建失败**
   - 检查 `requirements.txt` 中的依赖
   - 查看构建日志中的错误信息
   - 确保所有Python包都支持目标平台

2. **可执行文件无法运行**
   - 检查目标系统是否支持
   - 确认文件权限设置正确
   - 查看系统依赖是否满足

3. **文件过大**
   - 检查 `excludes` 列表
   - 移除不必要的依赖
   - 使用 `--exclude-module` 排除模块

### 调试方法

1. **查看构建日志**
   - 在Actions页面点击失败的构建
   - 查看详细的错误信息

2. **本地测试**
   - 在本地运行 `python build.py`
   - 测试生成的可执行文件

3. **检查依赖**
   - 运行 `pip list` 查看已安装的包
   - 检查版本兼容性

## 🔄 更新和维护

### 更新依赖
```bash
# 更新requirements.txt
pip freeze > requirements.txt

# 提交更改
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### 修改构建配置
1. 编辑 `file_save_system.spec`
2. 提交更改
3. 推送触发自动构建

### 添加新平台
1. 在 `.github/workflows/build.yml` 中添加新的job
2. 配置对应的运行环境
3. 测试构建流程

## 📈 性能优化

### 构建速度优化
- 使用缓存减少依赖安装时间
- 并行构建多个平台
- 优化构建脚本

### 文件大小优化
- 排除不必要的模块
- 使用 `--exclude-module` 参数
- 压缩静态资源

## 🎉 最佳实践

1. **版本管理**
   - 使用语义化版本号
   - 为每个发布创建标签

2. **测试**
   - 在多个平台上测试
   - 自动化测试流程

3. **文档**
   - 保持README更新
   - 提供详细的使用说明

4. **安全**
   - 定期更新依赖
   - 扫描安全漏洞

---

**配置完成！** 🎊

现在您的项目支持自动多平台构建，每次推送代码都会自动生成Windows、macOS和Linux版本的可执行文件！
