from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileSaveHistoryViewSet

router = DefaultRouter()
router.register(r'history', FileSaveHistoryViewSet, basename='history')

urlpatterns = [
    path('', include(router.urls)),
]
