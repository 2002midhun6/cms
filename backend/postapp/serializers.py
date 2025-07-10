from rest_framework import serializers
from .models import Post, Comment, Like
from django.contrib.auth import get_user_model
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff']

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'is_approved']
        read_only_fields = ['author', 'created_at']

class PostSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'image', 'created_at', 
                  'updated_at', 'read_count', 'comments', 'comments_count', 'likes_count']
        read_only_fields = ['author', 'created_at', 'updated_at', 'read_count']

    def get_comments_count(self, obj):
        return obj.comments.filter(is_approved=True).count()

    def get_likes_count(self, obj):
        return obj.likes.filter(is_like=True).count()

    def get_image(self, obj):
        if obj.image:
            # Generate full Cloudinary URL
            url, _ = cloudinary_url(obj.image.public_id, resource_type='image')
            return url
        return None

class LikeSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'post', 'user', 'is_like', 'created_at']