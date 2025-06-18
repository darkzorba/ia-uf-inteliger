from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UFViewSet

router = DefaultRouter()
router.register(r'ufs', UFViewSet, basename='uf') # 'ufs' é o prefixo da URL

urlpatterns = [
    path('', include(router.urls)),
]