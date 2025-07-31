from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_superuser','bio', 'profile_picture', 'password','is_blocked']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            bio=validated_data.get('bio', ''),
            profile_picture=validated_data.get('profile_picture', ''),
            is_blocked=validated_data.get('is_blocked', False)  
        )
        return user

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.bio = validated_data.get('bio', instance.bio)
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
        instance.is_blocked = validated_data.get('is_blocked', instance.is_blocked)  
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        instance.save()
        return instance

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Get the user first to check is_blocked
        username = attrs.get('username')
        try:
            user = User.objects.get(username=username)
            if user.is_blocked:
                print(f"Blocked user {user.username} attempted login")
                raise serializers.ValidationError({'error': 'This account is blocked'})
        except User.DoesNotExist:
            pass  # Let super().validate handle invalid username

        # Proceed with default validation
        try:
            data = super().validate(attrs)
            print(f"User {self.user.username} authenticated successfully")
            return data
        except AuthenticationFailed:
            print("Authentication failed: Invalid username or password")
            raise serializers.ValidationError({'error': 'Invalid username or password'})

    @classmethod
    def get_token(cls, user):
        if user.is_blocked:
            print(f"Blocked user {user.username} attempted token generation")
            raise serializers.ValidationError({'error': 'This account is blocked'})
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        token['is_blocked'] = user.is_blocked
        return token