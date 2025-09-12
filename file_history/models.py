from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class FileSaveHistory(models.Model):
    """文件保存历史记录模型"""
    original_filename = models.CharField(max_length=255, verbose_name="原始文件名")
    original_path = models.TextField(blank=True, null=True, verbose_name="原始路径")
    final_path = models.TextField(verbose_name="最终保存路径")
    file_size = models.BigIntegerField(blank=True, null=True, verbose_name="文件大小(字节)")
    file_extension = models.CharField(max_length=20, blank=True, verbose_name="文件扩展名")
    content_preview = models.TextField(blank=True, verbose_name="内容预览")
    save_mode = models.CharField(max_length=50, default="manual", verbose_name="保存模式")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'save_history'
        ordering = ['-created_at']
        verbose_name = "文件保存历史"
        verbose_name_plural = "文件保存历史"
    
    def __str__(self):
        return f"{self.original_filename} -> {self.final_path}"
    
    @property
    def file_size_mb(self):
        """返回文件大小(MB)"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    @property
    def is_recent(self):
        """判断是否为最近保存的文件(24小时内)"""
        from django.utils import timezone
        from datetime import timedelta
        return self.created_at > timezone.now() - timedelta(hours=24)
    
    @property
    def path_category(self):
        """根据路径返回分类"""
        if 'documents' in self.final_path.lower():
            return 'documents'
        elif 'images' in self.final_path.lower():
            return 'images'
        elif 'downloads' in self.final_path.lower():
            return 'downloads'
        elif 'desktop' in self.final_path.lower():
            return 'desktop'
        else:
            return 'other'