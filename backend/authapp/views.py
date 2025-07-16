from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    user = request.user
    
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
       
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        
    })
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        print('Login request data:', request.data)
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            print('Authenticated user:', user)
            tokens = serializer.validated_data
            response = Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                },
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
            response.set_cookie(
                key='access_token',
                value=tokens['access'],
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax'
            )
            response.set_cookie(
                key='refresh_token',
                value=tokens['refresh'],
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax'
            )
            return response
        except serializers.ValidationError as e:
            return Response(
                {'error': e.detail.get('error', 'Invalid credentials')},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            print('Authentication error:', str(e))
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CustomTokenRefreshView(TokenRefreshView):
    """Custom token refresh view that handles cookies"""
    
    def post(self, request, *args, **kwargs):
        # Get refresh token from cookies
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': 'No refresh token found in cookies'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Add refresh token to request data
        request.data['refresh'] = refresh_token
        
        try:
            response = super().post(request, *args, **kwargs)
            
            # If successful, set the new access token in cookies
            if response.status_code == 200:
                new_access_token = response.data.get('access')
                if new_access_token:
                    response.set_cookie(
                        key='access_token',
                        value=new_access_token,
                        httponly=True,
                        secure=False,
                        samesite='Lax'
                    )
                
                # Handle refresh token rotation
                new_refresh_token = response.data.get('refresh')
                if new_refresh_token:
                    response.set_cookie(
                        key='refresh_token',
                        value=new_refresh_token,
                        httponly=True,
                        secure=False,
                        samesite='Lax'
                    )
            
            return response
            
        except Exception as e:
            print('Token refresh error:', str(e))
            return Response({
                'error': 'Token refresh failed'
            }, status=status.HTTP_401_UNAUTHORIZED)

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            print('Logout refresh token:', refresh_token)
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            response = Response({'message': 'Logout successful'}, status=status.HTTP_205_RESET_CONTENT)
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]