from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Post, Comment, Like
from .serializers import PostSerializer, CommentSerializer, LikeSerializer
from django.contrib.auth import get_user_model
import logging
from backend.authentication import IsNotBlocked
User = get_user_model()
logger = logging.getLogger(__name__)

class IsAuthorOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_staff

class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsNotBlocked]
    parser_classes = [MultiPartParser, FormParser]  

    def create(self, request, *args, **kwargs):
        logger.info(f"POST request data: {request.data}")
        logger.info(f"POST request files: {request.FILES}")
       
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        
        serializer = self.get_serializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
               
                post = serializer.save(author=request.user)
                logger.info(f"Post created successfully: {post.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error creating post: {str(e)}")
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error(f"Serializer validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        
        serializer.save(author=self.request.user)

class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrAdmin, IsNotBlocked]
    parser_classes = [MultiPartParser, FormParser]  

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        
        increment_view = request.query_params.get('increment_view', 'false').lower() == 'true'
        if increment_view:
            instance.read_count += 1
            instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.info(f"Updating post {instance.id} with data: {request.data}")
        logger.info(f"Update request files: {request.FILES}")
       
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
       
        if instance.author != request.user and not request.user.is_staff:
            raise PermissionDenied("You don't have permission to edit this post.")
        
       
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        
        if serializer.is_valid():
            try:
                updated_post = serializer.save()
                logger.info(f"Post updated successfully: {updated_post.id}")
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"Error updating post: {str(e)}")
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.error(f"Serializer validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        
        if instance.author != request.user and not request.user.is_staff:
            raise PermissionDenied("You don't have permission to delete this post.")
        
        
        logger.info(f"User {request.user.username} deleting post {instance.id}")
        
        return super().destroy(request, *args, **kwargs)

class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsNotBlocked]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthorOrAdmin,IsNotBlocked]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        
        if instance.author != request.user and not request.user.is_staff:
            raise PermissionDenied("You don't have permission to edit this comment.")
        
        
        logger.info(f"Updating comment {instance.id} with data: {request.data}")
        
        
        partial = kwargs.pop('partial', True)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        else:
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        
        if instance.author != request.user and not request.user.is_staff:
            raise PermissionDenied("You don't have permission to delete this comment.")
        
        return super().destroy(request, *args, **kwargs)

class CommentApprovalView(APIView):
    permission_classes = [permissions.IsAdminUser, IsNotBlocked]

    def post(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
            comment.is_approved = request.data.get('is_approved', False)
            comment.save()
            return Response({'message': 'Comment approval updated'}, status=status.HTTP_200_OK)
        except Comment.DoesNotExist:
            return Response({'error': 'Comment not found'}, status=status.HTTP_404_NOT_FOUND)

class LikeView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsNotBlocked]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            like, created = Like.objects.get_or_create(post=post, user=request.user)
            like.is_like = request.data.get('is_like', True)
            like.save()
            return Response({'message': 'Like updated'}, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)