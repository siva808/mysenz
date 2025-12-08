from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from rest_framework import status, permissions
from django.conf import settings

User = get_user_model()

from rest_framework_simplejwt.tokens import RefreshToken

class CustomerSignupView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = CustomerSignupSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                subject= "Welcome to our PY OLLIVE"
                message=f"Hi {user.email},\n\nthank you for Signing"
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [user.email]
                send_mail(subject,message,from_email,recipient_list,fail_silently=False)
                return Response(serializer.to_representation(user), status=status.HTTP_201_CREATED)
            except Exception:
                return Response({"success":False,"message":"Email already Exists"},status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": False, "message": " signup failed", "errors": serializer.errors},status=status.HTTP_400_BAD_REQUEST)

class CustomerLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CustomerLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"success": True, "message": "Logged out successfully"})
        except Exception:
            return Response({"success": False, "message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        
class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            import random, string
            reset_code = ''.join(random.choices(string.digits, k=6))
            # TODO: store reset_code securely
            send_mail(
                "Password Reset Code",
                f"Your reset code is {reset_code}",
                "noreply@yourapp.com",
                [email],
                fail_silently=True,
            )
            return Response({"success": True, "message": "Reset code sent to email"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

