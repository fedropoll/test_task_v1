from rest_framework import viewsets
from .models import Post, SubPost
from .serializers import PostSerializer, SubPostSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer


class SubPostViewSet(viewsets.ModelViewSet):
    queryset = SubPost.objects.all()
    serializer_class = SubPostSerializer
