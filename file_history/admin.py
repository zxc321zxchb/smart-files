from django.contrib import admin
from .models import FileSaveHistory


@admin.register(FileSaveHistory)
class FileSaveHistoryAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'file_extension', 'save_mode', 'path_category', 'file_size_mb', 'is_recent', 'created_at']
    list_filter = ['file_extension', 'save_mode', 'created_at']
    search_fields = ['original_filename', 'final_path', 'content_preview']
    readonly_fields = ['created_at', 'updated_at', 'file_size_mb', 'is_recent', 'path_category']
    ordering = ['-created_at']
    
    fieldsets = (
        ('文件信息', {
            'fields': ('original_filename', 'original_path', 'final_path', 'file_extension')
        }),
        ('文件属性', {
            'fields': ('file_size', 'file_size_mb', 'content_preview')
        }),
        ('保存信息', {
            'fields': ('save_mode', 'path_category', 'is_recent')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )