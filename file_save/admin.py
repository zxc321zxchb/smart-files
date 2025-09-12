from django.contrib import admin
from .models import FileSave


@admin.register(FileSave)
class FileSaveAdmin(admin.ModelAdmin):
    list_display = ['filename', 'file_extension', 'file_size_mb', 'content_type', 'created_at']
    list_filter = ['file_extension', 'content_type', 'created_at']
    search_fields = ['filename', 'file_path']
    readonly_fields = ['created_at', 'updated_at', 'file_size_mb', 'is_image', 'is_document']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('filename', 'file_path', 'file_extension', 'content_type')
        }),
        ('文件内容', {
            'fields': ('file_size', 'file_size_mb', 'content_data')
        }),
        ('文件属性', {
            'fields': ('is_image', 'is_document')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )