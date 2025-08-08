from rest_framework import serializers
from django.db import transaction
from .models import Post, SubPost

class SubPostSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = SubPost
        fields = ['id', 'title', 'body']
        extra_kwargs = {'id': {'read_only': False}}

class PostSerializer(serializers.ModelSerializer):
    subposts = SubPostSerializer(many=True, required=False)
    author = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = Post
        fields = ['id', 'title', 'body', 'author', 'created_at', 'updated_at', 'views_count', 'likes', 'subposts']
        read_only_fields = ['created_at', 'updated_at', 'views_count', 'likes']

    @transaction.atomic
    def create(self, validated_data):
        subs_data = validated_data.pop('subposts', [])
        post = Post.objects.create(**validated_data)
        for sub_data in subs_data:
            SubPost.objects.create(post=post, **sub_data)
        return post

    @transaction.atomic
    def update(self, instance, validated_data):
        subs_data = validated_data.pop('subposts', [])

        # Обновляем поля родительского объекта Post
        instance.title = validated_data.get('title', instance.title)
        instance.body = validated_data.get('body', instance.body)
        instance.save()

        # Получаем id существующих под-постов
        existing_subpost_ids = {sub.id for sub in instance.subposts.all()}
        sent_subpost_ids = {sub.get('id') for sub in subs_data if sub.get('id')}

        # Удаляем под-посты, которые не были отправлены в запросе
        for sub_id in (existing_subpost_ids - sent_subpost_ids):
            SubPost.objects.get(id=sub_id).delete()

        # Обновляем или создаем под-посты
        for sub_data in subs_data:
            sub_id = sub_data.get('id', None)
            if sub_id:
                subpost = SubPost.objects.get(id=sub_id, post=instance)
                subpost.title = sub_data.get('title', subpost.title)
                subpost.body = sub_data.get('body', subpost.body)
                subpost.save()
            else:
                SubPost.objects.create(post=instance, **sub_data)

        return instance
