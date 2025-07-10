from django.urls import path
from .views import CustomTokenObtainPairView, RegisterView, LogoutView, UserListView, UserDetailView,get_current_user

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    
path('me/', get_current_user, name='current_user')
]