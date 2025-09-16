# 文件保存系统 (Django DRF)

一个基于Django REST Framework的文件保存和历史记录管理系统，专注于文件保存、历史记录管理和数据查询功能。

## 功能特性

### 核心功能
- **文件保存**: 支持base64编码的文件内容保存
- **文件转换**: 支持文件格式转换
- **历史记录**: 完整的文件保存历史记录管理
- **性能监控**: 系统操作性能统计和分析
- **数据查询**: 多维度数据查询和统计分析
- **数据导出**: 支持CSV和JSON格式导出
- **智能保存**: 基于AI的相似文件检测和智能保存功能

### 技术特性
- **RESTful API**: 完整的REST API设计
- **自动文档**: Swagger/ReDoc API文档
- **数据过滤**: 支持搜索、过滤、排序、分页
- **性能统计**: 实时性能监控和趋势分析
- **管理后台**: Django Admin管理界面

## 项目结构

```
file_save_system/
├── file_save/              # 文件保存应用
│   ├── models.py          # 文件保存模型
│   ├── serializers.py     # 序列化器
│   ├── views.py           # 视图集
│   ├── services.py        # 业务服务
│   ├── urls.py            # URL路由
│   └── admin.py           # 管理后台
├── file_history/          # 历史记录应用
│   ├── models.py          # 历史记录模型
│   ├── serializers.py     # 序列化器
│   ├── views.py           # 视图集
│   ├── services.py        # 业务服务
│   ├── urls.py            # URL路由
│   └── admin.py           # 管理后台
├── performance/           # 性能监控应用
│   ├── models.py          # 性能统计模型
│   ├── serializers.py     # 序列化器
│   ├── views.py           # 视图集
│   ├── services.py        # 业务服务
│   ├── urls.py            # URL路由
│   └── admin.py           # 管理后台
├── file_save_system/      # 项目配置
│   ├── settings.py        # 开发环境设置
│   ├── settings_prod.py   # 生产环境设置
│   └── urls.py            # 主URL配置
├── data/                  # 数据目录
├── logs/                  # 日志目录
├── requirements.txt       # 依赖包
├── migrate_data.py        # 数据迁移脚本
├── start_server.py        # 服务器启动脚本
├── deploy.sh             # 部署脚本
└── README.md             # 项目说明
```

## 智能保存功能

### 功能概述
智能保存功能基于AI技术，能够：
- **相似文件检测**: 使用SentenceTransformer模型分析文件内容相似度
- **智能推荐**: 自动推荐最相似的文件进行内容追加
- **语义理解**: 理解文件内容的语义，不仅仅是文本匹配
- **索引管理**: 使用FAISS向量数据库进行高效的相似度搜索

### 技术架构
- **文本嵌入**: SentenceTransformer (all-MiniLM-L6-v2)
- **向量搜索**: FAISS (Facebook AI Similarity Search)
- **相似度算法**: 余弦相似度
- **索引存储**: 本地FAISS索引文件

### API端点
- `POST /api/files/find_similar/` - 查找相似文件
- `POST /api/files/save_to_similar/` - 保存到相似文件
- `GET /api/files/similarity_debug/` - 相似度服务调试
- `POST /api/files/rebuild_similarity_index/` - 重建相似度索引

## 快速开始

### 1. 环境要求
- Python 3.9+
- Django 4.2+
- SQLite (开发环境)

### 2. 安装部署

#### 自动部署
```bash
# 运行部署脚本
./deploy.sh
```

#### 手动部署
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装智能保存功能依赖（可选）
python install_smart_save_deps.py

# 创建必要目录
mkdir -p logs data static media

# 运行数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 运行数据迁移
python migrate_data.py
```

### 3. 启动服务器

#### 开发环境
```bash
python start_server.py
```

#### 生产环境
```bash
python start_server.py prod
```

### 4. 访问系统

- **API文档**: http://localhost:8000/swagger/
- **管理后台**: http://localhost:8000/admin/
- **API端点**: http://localhost:8000/api/

## API 端点

### 文件保存 API
- `GET /api/files/` - 获取文件列表
- `POST /api/files/` - 保存文件
- `GET /api/files/{id}/` - 获取文件详情
- `PUT /api/files/{id}/` - 更新文件
- `DELETE /api/files/{id}/` - 删除文件
- `GET /api/files/statistics/` - 获取统计信息
- `GET /api/files/search/` - 搜索文件
- `POST /api/files/convert/` - 转换文件格式
- `POST /api/files/batch_upload/` - 批量上传

### 历史记录 API
- `GET /api/history/` - 获取历史记录列表
- `POST /api/history/` - 创建历史记录
- `GET /api/history/{id}/` - 获取历史记录详情
- `PUT /api/history/{id}/` - 更新历史记录
- `DELETE /api/history/{id}/` - 删除历史记录
- `GET /api/history/statistics/` - 获取统计信息
- `GET /api/history/search/` - 高级搜索
- `GET /api/history/trends/` - 获取趋势数据
- `GET /api/history/popular_paths/` - 获取热门路径
- `POST /api/history/export/` - 导出历史记录

### 性能监控 API
- `GET /api/performance/` - 获取性能统计列表
- `POST /api/performance/` - 记录性能数据
- `GET /api/performance/summary/` - 获取性能摘要
- `GET /api/performance/trends/` - 获取性能趋势
- `GET /api/performance/slow_operations/` - 获取慢操作
- `GET /api/performance/error_operations/` - 获取错误操作
- `POST /api/performance/record/` - 记录性能数据

## 数据模型

### FileSave (文件保存)
- `filename`: 文件名
- `file_path`: 文件路径
- `file_size`: 文件大小
- `file_extension`: 文件扩展名
- `content_type`: 内容类型
- `content_data`: 文件内容(base64编码)
- `created_at`: 创建时间
- `updated_at`: 更新时间

### FileSaveHistory (历史记录)
- `original_filename`: 原始文件名
- `original_path`: 原始路径
- `final_path`: 最终保存路径
- `file_size`: 文件大小
- `file_extension`: 文件扩展名
- `content_preview`: 内容预览
- `save_mode`: 保存模式
- `created_at`: 创建时间
- `updated_at`: 更新时间

### PerformanceStats (性能统计)
- `operation_type`: 操作类型
- `response_time_ms`: 响应时间(毫秒)
- `success`: 是否成功
- `error_message`: 错误信息
- `file_size`: 文件大小
- `user_agent`: 用户代理
- `ip_address`: IP地址
- `created_at`: 创建时间

## 配置说明

### 开发环境配置
- 数据库: SQLite
- 调试模式: 开启
- 日志级别: INFO
- CORS: 允许所有来源

### 生产环境配置
- 数据库: SQLite (可配置PostgreSQL)
- 调试模式: 关闭
- 日志级别: INFO/ERROR
- CORS: 限制来源
- 静态文件: 收集到staticfiles目录

## 数据迁移

### 从旧系统迁移
```bash
# 运行数据迁移脚本
python migrate_data.py [旧数据库路径]
```

### 创建示例数据
数据迁移脚本会自动创建示例数据，包括：
- 示例文件保存记录
- 示例历史记录
- 示例性能统计数据

## 测试

### 运行API测试
```bash
python test_api.py
```

### 运行Django测试
```bash
python manage.py test
```

## 部署

### 开发环境
```bash
python start_server.py
```

### 生产环境
```bash
python start_server.py prod
```

### Docker部署 (可选)
```bash
# 构建镜像
docker build -t file-save-system .

# 运行容器
docker run -p 8000:8000 file-save-system
```

## 监控和日志

### 日志文件
- `logs/django.log`: 应用日志
- `logs/django_error.log`: 错误日志

### 性能监控
- 响应时间统计
- 成功率统计
- 慢操作识别
- 错误操作追踪

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库文件权限
   - 确保data目录存在

2. **静态文件404**
   - 运行 `python manage.py collectstatic`
   - 检查STATIC_ROOT配置

3. **API文档无法访问**
   - 检查drf-yasg是否正确安装
   - 确认URL配置正确

4. **CORS错误**
   - 检查CORS_ALLOWED_ORIGINS配置
   - 确认前端域名已添加

### 日志查看
```bash
# 查看应用日志
tail -f logs/django.log

# 查看错误日志
tail -f logs/django_error.log
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

- 项目地址: [GitHub Repository]
- 问题反馈: [Issues]
- 文档: [Documentation]
