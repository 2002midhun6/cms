# authentication.py (create this file in your authentication app)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from rest_framework import exceptions

User = get_user_model()

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # First try the standard header authentication
        header_auth = super().authenticate(request)
        if header_auth is not None:
            return header_auth
        
        # If no header authentication, try cookie authentication
        access_token = request.COOKIES.get('access_token')
        if access_token is None:
            return None
        
        try:
            # Validate the token
            validated_token = self.get_validated_token(access_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except TokenError:
            return None
        except Exception:
            return None