from rest_framework import serializers
from .models import FileSave, FilePath


class FilePathSerializer(serializers.ModelSerializer):
    """文件路径序列化器"""
    is_frequent = serializers.ReadOnlyField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = FilePath
        fields = [
            'id', 'path_pattern', 'description', 'category', 'category_display',
            'is_active', 'usage_count', 'last_used_at', 'is_frequent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'last_used_at', 'created_at', 'updated_at']
    
    def validate_path_pattern(self, value):
        """验证路径模式"""
        if not value or not value.strip():
            raise serializers.ValidationError("路径不能为空")
        
        # 检查路径是否已存在
        if self.instance is None:  # 创建时
            if FilePath.objects.filter(path_pattern=value.strip()).exists():
                raise serializers.ValidationError("该路径已存在")
        
        return value.strip()


class FilePathCreateSerializer(serializers.ModelSerializer):
    """文件路径创建序列化器"""
    
    class Meta:
        model = FilePath
        fields = ['path_pattern', 'description', 'category', 'is_active']
    
    def validate_path_pattern(self, value):
        """验证路径模式"""
        if not value or not value.strip():
            raise serializers.ValidationError("路径不能为空")
        
        if FilePath.objects.filter(path_pattern=value.strip()).exists():
            raise serializers.ValidationError("该路径已存在")
        
        return value.strip()


class FilePathListSerializer(serializers.ModelSerializer):
    """文件路径列表序列化器（简化版）"""
    is_frequent = serializers.ReadOnlyField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = FilePath
        fields = [
            'id', 'path_pattern', 'description', 'category', 'category_display',
            'is_active', 'usage_count', 'last_used_at', 'is_frequent', 'created_at'
        ]


class FileSaveSerializer(serializers.ModelSerializer):
    """文件保存序列化器"""
    file_size_mb = serializers.ReadOnlyField()
    is_image = serializers.ReadOnlyField()
    is_document = serializers.ReadOnlyField()
    
    class Meta:
        model = FileSave
        fields = [
            'id', 'filename', 'file_path', 'file_size', 'file_size_mb',
            'file_extension', 'content_type', 'content_data',
            'is_image', 'is_document', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_file_size(self, value):
        """验证文件大小"""
        if value > 100 * 1024 * 1024:  # 100MB
            raise serializers.ValidationError("文件大小不能超过100MB")
        return value
    
    def validate_content_data(self, value):
        """验证base64内容"""
        if not value:
            raise serializers.ValidationError("文件内容不能为空")
        
        # 简单的base64验证
        import base64
        try:
            base64.b64decode(value)
        except Exception:
            raise serializers.ValidationError("无效的base64编码")
        
        return value


class FileSaveCreateSerializer(serializers.ModelSerializer):
    """文件保存创建序列化器"""
    
    class Meta:
        model = FileSave
        fields = [
            'id', 'filename', 'file_path', 'file_size', 'file_extension',
            'content_type', 'content_data'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """创建文件保存记录并实际保存文件到本地"""
        import os
        import base64
        
        # 自动设置文件扩展名
        if not validated_data.get('file_extension'):
            filename = validated_data.get('filename', '')
            if '.' in filename:
                validated_data['file_extension'] = filename.split('.')[-1].lower()
        
        # 获取文件路径和内容
        file_path = validated_data.get('file_path', '')
        content_data = validated_data.get('content_data', '')
        
        try:
            # 创建目录（如果不存在）
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"创建目录: {directory}")
            
            # 解码base64内容并写入文件
            if content_data:
                file_content = base64.b64decode(content_data)
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                print(f"文件保存成功: {file_path}")
            else:
                print(f"警告: 文件内容为空，跳过文件创建: {file_path}")
                
        except Exception as e:
            print(f"保存文件到本地失败: {e}")
            # 即使本地保存失败，也继续保存数据库记录
            # 这样至少可以在数据库中记录文件信息
        
        return super().create(validated_data)


class FileSaveListSerializer(serializers.ModelSerializer):
    """文件保存列表序列化器（简化版）"""
    file_size_mb = serializers.ReadOnlyField()
    is_image = serializers.ReadOnlyField()
    is_document = serializers.ReadOnlyField()
    
    class Meta:
        model = FileSave
        fields = [
            'id', 'filename', 'file_path', 'file_size_mb',
            'file_extension', 'content_type', 'is_image', 'is_document',
            'created_at'
        ]
