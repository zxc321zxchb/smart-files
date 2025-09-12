from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileSaveViewSet, FilePathViewSet

router = DefaultRouter()
router.register(r'files', FileSaveViewSet, basename='files')
router.register(r'file_paths', FilePathViewSet, basename='file_paths')

urlpatterns = [
    path('', include(router.urls)),
]
