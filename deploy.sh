#!/bin/bash

# Django DRF 项目部署脚本

echo "开始部署Django DRF项目..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 创建必要的目录
echo "创建必要目录..."
mkdir -p logs
mkdir -p data
mkdir -p static
mkdir -p media

# 设置权限
chmod 755 logs
chmod 755 data
chmod 755 static
chmod 755 media

# 运行数据库迁移
echo "运行数据库迁移..."
python manage.py makemigrations
python manage.py migrate

# 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput

# 创建超级用户（如果不存在）
echo "检查超级用户..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('超级用户已创建')
else:
    print('超级用户已存在')
"

# 运行数据迁移
echo "运行数据迁移..."
python migrate_data.py

echo "部署完成！"
echo ""
echo "启动服务器:"
echo "  开发环境: python start_server.py"
echo "  生产环境: python start_server.py prod"
echo ""
echo "访问地址:"
echo "  API文档: http://localhost:8000/swagger/"
echo "  管理后台: http://localhost:8000/admin/"
echo "  用户名: admin"
echo "  密码: admin123"
