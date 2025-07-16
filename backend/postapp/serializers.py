from rest_framework import serializers
from .models import Post, Comment, Like
from django.contrib.auth import get_user_model
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
import logging

User = get_user_model()

# Add logging for debugging
logger = logging.getLogger(__name__)

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

    def update(self, instance, validated_data):
        # Handle partial update - only update content if provided
        if 'content' in validated_data:
            instance.content = validated_data['content']
        instance.save()
        return instance

    def validate_content(self, value):
        # Add validation for content
        if not value or not value.strip():
            raise serializers.ValidationError("Content cannot be empty")
        if len(value) > 500:
            raise serializers.ValidationError("Content must be 500 characters or less")
        return value.strip()

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

    def create(self, validated_data):
        """Override create method to handle image upload"""
        logger.info(f"Creating post with data: {validated_data}")
        
        # Get the image from the request if it exists
        request = self.context.get('request')
        image_file = None
        
        if request and hasattr(request, 'FILES') and 'image' in request.FILES:
            image_file = request.FILES['image']
            logger.info(f"Image file found: {image_file.name}")
        
        # Create the post instance
        post = Post.objects.create(**validated_data)
        
        # Handle image upload if present
        if image_file:
            try:
                # Save the image to the CloudinaryField
                post.image = image_file
                post.save()
                logger.info(f"Image uploaded successfully for post {post.id}")
            except Exception as e:
                logger.error(f"Error uploading image: {str(e)}")
                # You might want to handle this differently based on your requirements
                raise serializers.ValidationError(f"Error uploading image: {str(e)}")
        
        return post

    def update(self, instance, validated_data):
        """Override update method to handle image updates"""
        logger.info(f"Updating post {instance.id} with data: {validated_data}")
        
        # Get the image from the request if it exists
        request = self.context.get('request')
        image_file = None
        
        if request and hasattr(request, 'FILES') and 'image' in request.FILES:
            image_file = request.FILES['image']
            logger.info(f"New image file found: {image_file.name}")
        
        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Handle image update if present
        if image_file:
            try:
                # Update the image
                instance.image = image_file
                logger.info(f"Image updated successfully for post {instance.id}")
            except Exception as e:
                logger.error(f"Error updating image: {str(e)}")
                raise serializers.ValidationError(f"Error updating image: {str(e)}")
        
        instance.save()
        return instance

    def get_comments_count(self, obj):
        return obj.comments.filter(is_approved=True).count()

    def get_likes_count(self, obj):
        return obj.likes.filter(is_like=True).count()

    def get_image(self, obj):
        if obj.image:
            try:
                # Generate full Cloudinary URL
                url, _ = cloudinary_url(obj.image.public_id, resource_type='image')
                return url
            except Exception as e:
                logger.error(f"Error getting image URL: {str(e)}")
                # Fallback to the direct URL if cloudinary_url fails
                return str(obj.image.url) if hasattr(obj.image, 'url') else None
        return None

class LikeSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'post', 'user', 'is_like', 'created_at']