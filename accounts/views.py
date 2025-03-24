"""

from django.shortcuts import render
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.hashers import make_password
from .models import User
from .serializers import RegisterSerializer, UserSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
# Create your views here.
"""
"""
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = get_object_or_404(User, email=email)
        token = get_random_string(40)
        user.profile.reset_password_token = token
        user.profile.reset_password_expire = datetime.now() + timedelta(minutes=30)
        user.profile.save()

        reset_link = f"http://127.0.0.1:8000/reset-password/{token}/"
        send_mail('Password Reset', f'Reset your password here: {reset_link}', "no-reply@example.com", [email])

        return Response({'message': 'Password reset link sent.'})

class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request, token):
        user = get_object_or_404(User, profile__reset_password_token=token)
        if user.profile.reset_password_expire.replace(tzinfo=None) < datetime.now():
            return Response({'error': 'Reset link expired.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data['password'] != serializer.validated_data['confirm_password']:
            return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['password'])
        user.profile.reset_password_token = ""
        user.profile.reset_password_expire = None
        user.save()
        user.profile.save()

        return Response({'message': 'Password reset successful.'})
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import logout
from .models import User
from .serializers import UserSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None):
        if user_id:  # If user_id is provided, check access
            if request.user.is_staff or request.user.id == user_id:
                user = generics.get_object_or_404(User, id=user_id)
            else:
                return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        else:
            user = request.user

        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request, user_id=None):
        if user_id and (request.user.is_staff or request.user.id == user_id):
            user = generics.get_object_or_404(User, id=user_id)
        else:
            user = request.user

        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
