from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileSaveViewSet, FilePathViewSet
from .ai_views import AIStatusViewSet

router = DefaultRouter()
router.register(r'files', FileSaveViewSet, basename='files')
router.register(r'file_paths', FilePathViewSet, basename='file_paths')
router.register(r'ai', AIStatusViewSet, basename='ai')

urlpatterns = [
    path('', include(router.urls)),
]
