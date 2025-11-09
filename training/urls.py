from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TrainingModuleViewSet

router = DefaultRouter()
router.register(r'modules', TrainingModuleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
