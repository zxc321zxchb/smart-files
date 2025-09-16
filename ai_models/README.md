# AI模型管理模块

本模块包含所有与AI模型相关的管理功能，包括模型下载、安装、配置等。

## 目录结构

```
ai_models/
├── __init__.py                    # 模块入口，导出所有公共接口
├── managers/                      # 管理器实现
│   ├── __init__.py               # 管理器模块入口
│   ├── model_manager.py          # 核心模型管理器
│   ├── ai_download_manager.py    # AI下载管理器
│   ├── s3_download_manager.py    # S3/R2下载管理器
│   └── precompiled_package_manager.py  # 预编译包管理器
└── config/                       # 配置文件
    └── precompiled_package_config.json  # 预编译包配置
```

## 模块功能

### 核心管理器 (managers/)

- **model_manager.py**: 处理AI模型的下载、检查和加载
- **ai_download_manager.py**: 管理AI模型的下载、安装和状态监控
- **s3_download_manager.py**: 通过S3协议下载预编译包，支持Cloudflare R2和AWS S3
- **precompiled_package_manager.py**: 处理预编译AI依赖包的下载、验证和安装

### 配置文件 (config/)

- **precompiled_package_config.json**: 预编译包的配置信息，包括下载地址、版本、校验和等

## 使用方法

```python
# 导入所有管理器
from ai_models import (
    get_model_manager,
    get_download_manager,
    get_s3_download_manager,
    get_precompiled_package_manager
)

# 使用模型管理器
model_manager = get_model_manager()
status = model_manager.get_model_status()

# 使用下载管理器
download_manager = get_download_manager()
download_manager.download_ai_environment()
```

## 文件重组说明

本次重组将原本分散在根目录的AI模型相关文件统一整理到 `ai_models` 模块中：

- 提高了代码的组织性和可维护性
- 明确了模块职责和边界
- 便于后续功能扩展和维护
- 保持了与现有代码的兼容性

## 注意事项

- 所有导入路径已更新为新的模块结构
- PyInstaller构建配置已相应调整
- 配置文件路径已更新到新的位置
- 保持了所有原有功能的完整性
