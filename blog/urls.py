from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, SubPostViewSet

router = DefaultRouter()
router.register(r'posts', PostViewSet)
router.register(r'subposts', SubPostViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
