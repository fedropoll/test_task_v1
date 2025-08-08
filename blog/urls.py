from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, SubPostViewSet, BulkPostCreateView
from drf_spectacular.views import SpectacularSwaggerView

router = DefaultRouter()
router.register('posts', PostViewSet)
router.register('subposts', SubPostViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('posts/bulk_create/', BulkPostCreateView.as_view(), name='bulk_create'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
