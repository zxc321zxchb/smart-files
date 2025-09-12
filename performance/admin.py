from django.contrib import admin
from .models import PerformanceStats


@admin.register(PerformanceStats)
class PerformanceStatsAdmin(admin.ModelAdmin):
    list_display = ['operation_type', 'response_time_ms', 'success', 'performance_level', 'is_slow_operation', 'created_at']
    list_filter = ['operation_type', 'success', 'created_at']
    search_fields = ['error_message', 'user_agent', 'ip_address']
    readonly_fields = ['created_at', 'performance_level', 'is_slow_operation']
    ordering = ['-created_at']
    
    fieldsets = (
        ('操作信息', {
            'fields': ('operation_type', 'response_time_ms', 'success')
        }),
        ('性能指标', {
            'fields': ('performance_level', 'is_slow_operation')
        }),
        ('错误信息', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('文件信息', {
            'fields': ('file_size',),
            'classes': ('collapse',)
        }),
        ('请求信息', {
            'fields': ('user_agent', 'ip_address'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )