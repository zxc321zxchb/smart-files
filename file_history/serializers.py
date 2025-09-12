from rest_framework import serializers
from .models import FileSaveHistory


class FileSaveHistorySerializer(serializers.ModelSerializer):
    """文件保存历史序列化器"""
    file_size_mb = serializers.ReadOnlyField()
    is_recent = serializers.ReadOnlyField()
    path_category = serializers.ReadOnlyField()
    
    class Meta:
        model = FileSaveHistory
        fields = [
            'id', 'original_filename', 'original_path', 'final_path',
            'file_size', 'file_size_mb', 'file_extension', 'content_preview',
            'save_mode', 'is_recent', 'path_category', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_save_mode(self, value):
        """验证保存模式"""
        valid_modes = ['manual', 'auto', 'batch', 'import']
        if value not in valid_modes:
            raise serializers.ValidationError(f"保存模式必须是: {', '.join(valid_modes)}")
        return value


class FileSaveHistoryCreateSerializer(serializers.ModelSerializer):
    """文件保存历史创建序列化器"""
    
    class Meta:
        model = FileSaveHistory
        fields = [
            'original_filename', 'original_path', 'final_path',
            'file_size', 'file_extension', 'content_preview', 'save_mode'
        ]
    
    def create(self, validated_data):
        """创建历史记录"""
        # 自动设置文件扩展名
        if not validated_data.get('file_extension'):
            filename = validated_data.get('original_filename', '')
            if '.' in filename:
                validated_data['file_extension'] = filename.split('.')[-1].lower()
        
        return super().create(validated_data)


class FileSaveHistoryListSerializer(serializers.ModelSerializer):
    """文件保存历史列表序列化器（简化版）"""
    file_size_mb = serializers.ReadOnlyField()
    is_recent = serializers.ReadOnlyField()
    path_category = serializers.ReadOnlyField()
    
    class Meta:
        model = FileSaveHistory
        fields = [
            'id', 'original_filename', 'final_path', 'file_size_mb',
            'file_extension', 'save_mode', 'is_recent', 'path_category',
            'created_at'
        ]


class FileSaveHistorySearchSerializer(serializers.Serializer):
    """文件保存历史搜索序列化器"""
    query = serializers.CharField(max_length=255, required=False, help_text="搜索关键词")
    file_extension = serializers.CharField(max_length=20, required=False, help_text="文件扩展名")
    save_mode = serializers.CharField(max_length=50, required=False, help_text="保存模式")
    date_from = serializers.DateField(required=False, help_text="开始日期")
    date_to = serializers.DateField(required=False, help_text="结束日期")
    path_category = serializers.CharField(max_length=50, required=False, help_text="路径分类")
    
    def validate(self, data):
        """验证搜索参数"""
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError("开始日期不能晚于结束日期")
        
        return data


class FileSaveHistoryStatsSerializer(serializers.Serializer):
    """文件保存历史统计序列化器"""
    total_files = serializers.IntegerField()
    total_size_mb = serializers.FloatField()
    file_types = serializers.DictField()
    save_modes = serializers.DictField()
    path_categories = serializers.DictField()
    recent_files = serializers.IntegerField()
    avg_file_size_mb = serializers.FloatField()
