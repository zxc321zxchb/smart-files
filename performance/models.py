from django.db import models
from django.core.validators import MinValueValidator


class PerformanceStats(models.Model):
    """性能统计模型"""
    OPERATION_TYPES = [
        ('file_save', '文件保存'),
        ('file_convert', '文件转换'),
        ('file_upload', '文件上传'),
        ('file_download', '文件下载'),
        ('history_query', '历史查询'),
        ('statistics', '统计分析'),
        ('data_export', '数据导出'),
    ]
    
    operation_type = models.CharField(
        max_length=100, 
        choices=OPERATION_TYPES,
        verbose_name="操作类型"
    )
    response_time_ms = models.FloatField(
        validators=[MinValueValidator(0.0)],
        verbose_name="响应时间(毫秒)"
    )
    success = models.BooleanField(verbose_name="是否成功")
    error_message = models.TextField(blank=True, null=True, verbose_name="错误信息")
    file_size = models.BigIntegerField(blank=True, null=True, verbose_name="文件大小(字节)")
    user_agent = models.TextField(blank=True, null=True, verbose_name="用户代理")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP地址")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'performance_stats'
        ordering = ['-created_at']
        verbose_name = "性能统计"
        verbose_name_plural = "性能统计"
        indexes = [
            models.Index(fields=['operation_type', 'created_at']),
            models.Index(fields=['success', 'created_at']),
            models.Index(fields=['response_time_ms']),
        ]
    
    def __str__(self):
        status = "成功" if self.success else "失败"
        return f"{self.get_operation_type_display()} - {status} ({self.response_time_ms}ms)"
    
    @property
    def is_slow_operation(self):
        """判断是否为慢操作(超过1秒)"""
        return self.response_time_ms > 1000
    
    @property
    def performance_level(self):
        """返回性能等级"""
        if self.response_time_ms < 100:
            return "excellent"
        elif self.response_time_ms < 500:
            return "good"
        elif self.response_time_ms < 1000:
            return "average"
        else:
            return "poor"
    
    @classmethod
    def get_average_response_time(cls, operation_type=None, days=7):
        """获取平均响应时间"""
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = cls.objects.filter(
            success=True,
            created_at__gte=timezone.now() - timedelta(days=days)
        )
        
        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
        
        from django.db.models import Avg
        result = queryset.aggregate(avg_time=Avg('response_time_ms'))
        return result['avg_time'] or 0