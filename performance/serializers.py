from rest_framework import serializers
from .models import PerformanceStats


class PerformanceStatsSerializer(serializers.ModelSerializer):
    """性能统计序列化器"""
    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)
    is_slow_operation = serializers.ReadOnlyField()
    performance_level = serializers.ReadOnlyField()
    
    class Meta:
        model = PerformanceStats
        fields = [
            'id', 'operation_type', 'operation_type_display', 'response_time_ms',
            'success', 'error_message', 'file_size', 'user_agent', 'ip_address',
            'is_slow_operation', 'performance_level', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_response_time_ms(self, value):
        """验证响应时间"""
        if value < 0:
            raise serializers.ValidationError("响应时间不能为负数")
        if value > 300000:  # 5分钟
            raise serializers.ValidationError("响应时间不能超过5分钟")
        return value


class PerformanceStatsCreateSerializer(serializers.ModelSerializer):
    """性能统计创建序列化器"""
    
    class Meta:
        model = PerformanceStats
        fields = [
            'operation_type', 'response_time_ms', 'success', 'error_message',
            'file_size', 'user_agent', 'ip_address'
        ]
    
    def validate_operation_type(self, value):
        """验证操作类型"""
        valid_types = [choice[0] for choice in PerformanceStats.OPERATION_TYPES]
        if value not in valid_types:
            raise serializers.ValidationError(f"操作类型必须是: {', '.join(valid_types)}")
        return value


class PerformanceStatsListSerializer(serializers.ModelSerializer):
    """性能统计列表序列化器（简化版）"""
    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)
    is_slow_operation = serializers.ReadOnlyField()
    performance_level = serializers.ReadOnlyField()
    
    class Meta:
        model = PerformanceStats
        fields = [
            'id', 'operation_type', 'operation_type_display', 'response_time_ms',
            'success', 'is_slow_operation', 'performance_level', 'created_at'
        ]


class PerformanceStatsTrendSerializer(serializers.Serializer):
    """性能统计趋势序列化器"""
    date = serializers.DateField()
    operation_type = serializers.CharField()
    avg_response_time = serializers.FloatField()
    total_operations = serializers.IntegerField()
    success_rate = serializers.FloatField()
    slow_operations = serializers.IntegerField()


class PerformanceStatsSummarySerializer(serializers.Serializer):
    """性能统计摘要序列化器"""
    total_operations = serializers.IntegerField()
    success_rate = serializers.FloatField()
    avg_response_time = serializers.FloatField()
    slow_operations = serializers.IntegerField()
    error_operations = serializers.IntegerField()
    operation_types = serializers.DictField()
    performance_levels = serializers.DictField()
    recent_trend = serializers.ListField(child=PerformanceStatsTrendSerializer())
