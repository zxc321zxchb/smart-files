# Pandoc集成指南

## 问题描述

在Windows环境下，文件转换API返回500错误，而在Mac环境下正常工作。这是因为Windows环境缺少`pandoc`工具，而Mac环境已经安装了pandoc。

## 解决方案

我们实现了将pandoc打包到可执行文件中的方案，这样用户无需手动安装pandoc即可使用文件转换功能。

## 实现方案

### 1. 自动下载pandoc

创建了`download_pandoc.py`脚本，能够：
- 自动检测操作系统
- 从GitHub下载对应平台的pandoc二进制文件
- 支持代理下载（当直接下载失败时）
- 解压并准备pandoc可执行文件

### 2. 打包集成

修改了`file_save_system.spec`文件：
- 在打包时自动查找pandoc二进制文件
- 将pandoc打包到可执行文件中
- 支持Windows、macOS、Linux三个平台

### 3. 运行时检测

更新了`views.py`中的转换逻辑：
- 优先使用打包的pandoc
- 如果打包的pandoc不可用，回退到系统PATH中的pandoc
- 提供清晰的错误提示

## 使用方法

### 开发环境

1. 运行pandoc下载脚本：
```bash
python download_pandoc.py
```

2. 正常启动Django服务：
```bash
python start_server.py
```

### 生产环境

1. 运行构建脚本：
```bash
python build.py
```

构建脚本会自动：
- 下载pandoc
- 打包到可执行文件中
- 生成跨平台可执行文件

2. 运行生成的可执行文件：
```bash
# Windows
file_save_system.exe

# macOS/Linux
./file_save_system
```

## 文件结构

```
smart-files/
├── download_pandoc.py          # pandoc下载脚本
├── build.py                    # 构建脚本（已更新）
├── file_save_system.spec       # PyInstaller配置（已更新）
├── pandoc/                     # pandoc二进制文件目录
│   ├── pandoc.exe             # Windows版本
│   └── pandoc                 # macOS/Linux版本
└── file_save/views.py          # 转换逻辑（已更新）
```

## 技术细节

### 1. pandoc路径检测

```python
def get_pandoc_path(self):
    """获取pandoc可执行文件路径"""
    import sys
    import os
    
    # 如果是PyInstaller打包的环境
    if getattr(sys, 'frozen', False):
        # 获取可执行文件所在目录
        base_path = os.path.dirname(sys.executable)
        
        # 在Windows上查找pandoc.exe
        if sys.platform == 'win32':
            pandoc_path = os.path.join(base_path, 'pandoc.exe')
            if os.path.exists(pandoc_path):
                return pandoc_path
        else:
            # 在macOS/Linux上查找pandoc
            pandoc_path = os.path.join(base_path, 'pandoc')
            if os.path.exists(pandoc_path):
                return pandoc_path
    
    # 如果不是打包环境或找不到打包的pandoc，尝试系统PATH中的pandoc
    try:
        result = subprocess.run(['pandoc', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return 'pandoc'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
        
    return None
```

### 2. 代理下载机制

```python
def download_windows_pandoc(self, version):
    """下载Windows版本的pandoc"""
    # 构建下载URL
    url = f"https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-windows-x86_64.zip"
    proxy_url = f"https://fastgh.discoverlife.top/https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-windows-x86_64.zip"
    
    # 首先尝试直接下载
    try:
        print("尝试直接下载...")
        urllib.request.urlretrieve(url, zip_path)
        print(f"直接下载完成: {zip_path}")
    except Exception as e:
        print(f"直接下载失败: {e}")
        try:
            print("尝试使用代理下载...")
            urllib.request.urlretrieve(proxy_url, zip_path)
            print(f"代理下载完成: {zip_path}")
        except Exception as e2:
            print(f"代理下载也失败: {e2}")
            return None
```

### 3. 转换逻辑更新

```python
# 获取pandoc路径
pandoc_path = self.get_pandoc_path()
if not pandoc_path:
    raise Exception('Pandoc未安装，无法进行转换。请访问 https://pandoc.org/installing.html 下载并安装Pandoc，或使用包管理器安装：choco install pandoc')

# 使用pandoc进行转换
result = subprocess.run([
    pandoc_path, temp_md_path, '-o', output_path, 
    '--from', 'markdown+fenced_code_blocks+fenced_code_attributes+inline_code_attributes', 
    '--to', 'docx',
    '--highlight-style', 'pygments',
    '--standalone',
    '--wrap', 'preserve'
], capture_output=True, text=True, timeout=60)
```

### 4. 构建配置更新

```python
# 查找并添加pandoc二进制文件
pandoc_binaries = find_pandoc_binary()
if pandoc_binaries:
    # 使用第一个找到的pandoc
    pandoc_path = pandoc_binaries[0]
    print(f"找到pandoc: {pandoc_path}")
    
    # 添加到binaries列表
    binaries = [(pandoc_path, '.')]
else:
    print("警告: 未找到pandoc，文件转换功能将不可用")
    binaries = []
```

## 错误处理

### 1. pandoc未找到

如果系统未安装pandoc且下载失败，会显示友好的错误信息：

```
Pandoc未安装，无法进行转换。请访问 https://pandoc.org/installing.html 下载并安装Pandoc，或使用包管理器安装：choco install pandoc
```

### 2. 转换失败

如果pandoc转换失败，会显示具体的错误信息：

```
Pandoc转换失败: [具体错误信息]
```

### 3. 超时处理

转换操作设置了60秒超时，避免长时间等待。

## 测试验证

### 1. 开发环境测试

```bash
# 测试pandoc下载
python download_pandoc.py

# 测试转换功能
curl -X POST http://localhost:8000/api/files/1/convert/ \
  -H "Content-Type: application/json" \
  -d '{"target_format": "docx"}'
```

### 2. 生产环境测试

```bash
# 构建可执行文件
python build.py

# 运行可执行文件
./file_save_system

# 测试转换功能
curl -X POST http://localhost:8000/api/files/1/convert/ \
  -H "Content-Type: application/json" \
  -d '{"target_format": "docx"}'
```

## 注意事项

1. **文件大小**：打包pandoc会增加可执行文件大小（约50-100MB）
2. **平台兼容性**：需要为每个平台单独构建
3. **权限问题**：确保pandoc二进制文件有执行权限
4. **网络依赖**：首次构建需要网络连接下载pandoc
5. **代理下载**：当直接下载失败时，会自动使用代理 `https://fastgh.discoverlife.top/` 进行下载

## 故障排除

### 1. 构建失败

- 检查网络连接
- 确保有足够的磁盘空间
- 检查Python和PyInstaller版本
- 如果直接下载失败，脚本会自动尝试代理下载
- 如果代理下载也失败，请检查代理服务是否可用

### 2. 运行时错误

- 检查pandoc二进制文件是否存在
- 检查文件权限
- 查看详细错误日志

### 3. 转换失败

- 检查输入文件格式
- 检查输出目录权限
- 查看pandoc错误输出

## 更新日志

- **v1.0**: 初始实现，支持pandoc打包
- **v1.1**: 添加自动下载功能
- **v1.2**: 改进错误处理和路径检测
- **v1.3**: 添加代理下载支持，解决GitHub访问问题
