from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from rest_framework import status, permissions
from django.conf import settings
from .notification import NotificationService
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser

User = get_user_model()
from rest_framework_simplejwt.tokens import RefreshToken

class CustomerSignupView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = CustomerSignupSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                subject= "Welcome to our PY OLLIVE"
                message=f"Hi {user.email},\n\nthank you for Signing"
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [user.email]
                send_mail(subject,message,from_email,recipient_list,fail_silently=False)
                return Response({
                    "success": True,
                    "message": "Signup successful",
                    "access": access_token,
                    "refresh": refresh_token,
                    "user": serializer.to_representation(user)
                }, status=status.HTTP_201_CREATED)
            except Exception:
                return Response({"success":False,"message":"Email already Exists"},status=status.HTTP_400_BAD_REQUEST)
        return Response({"success": False, "message": " signup failed", "errors": serializer.errors},status=status.HTTP_400_BAD_REQUEST)

class CustomerLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = CustomerLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            return Response({"sucess":True,"message":"Login Sucessfully","access": str(access),
                            "refresh": str(refresh),
                             "user": {"id": user.id,"email": user.email,"role": user.role,}},
                            status=status.HTTP_200_OK)
        return Response({"sucess":False,"message":" Validation error"}, status=status.HTTP_400_BAD_REQUEST)


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

#booking api for customer 

class BookingAPIView(APIView):

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            booking = serializer.save()
            return Response(
                {"message": "Booking created", "booking_id": booking.booking_id},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, booking_id=None):
        if booking_id:
            booking = get_object_or_404(Booking, pk=booking_id)
            serializer = BookingSerializer(booking)
            return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)
        bookings = Booking.objects.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)

    def delete(self, request, booking_id):
        booking = get_object_or_404(Booking, pk=booking_id)
        booking.delete()
        return Response({"success": True, "message": "Booking deleted"},status=status.HTTP_204_NO_CONECTED)
    


@api_view(["POST"])
def create_booking(request):
    data = JSONParser().parse(request)

    # ✅ Required fields
    required_fields = [
        "user_id",
        "customer_mobile",
        "store_id",
        "category_id",
        "appointment_type",
        "appointment_date",
        "appointment_time",
        "services",
    ]

    # ✅ Validate required fields
    missing = [f for f in required_fields if f not in data]
    if missing:
        return Response(
            {"success": False, "message": f"Missing fields: {', '.join(missing)}"},
            status=400
        )

    try:
        # ✅ Fetch foreign keys
        user = Customer.objects.get(id=data["user_id"])
        store = Store.objects.get(id=data["store_id"])
        category = Category.objects.get(id=data["category_id"])

        # ✅ Create booking (without services first)
        booking = Booking.objects.create(
            user=user,
            customer_mobile=data["customer_mobile"],
            store=store,
            category=category,
            appointment_type=data["appointment_type"],
            appointment_date=data["appointment_date"],
            appointment_time=data["appointment_time"],  # ArrayField
            booking_address=data.get("booking_address", ""),
            status="new booking",
            payment_status="pending",
        )

        # ✅ Add services (ManyToMany)
        service_ids = data["services"]  # list of service IDs
        services = Service.objects.filter(id__in=service_ids)
        booking.services.add(*services)

        return Response(
            {"success": True, "message": "Booking created", "booking_id": str(booking.booking_id)},
            status=201
        )

    except Customer.DoesNotExist:
        return Response({"success": False, "message": "Invalid user_id"})

    except Store.DoesNotExist:
        return Response({"success": False, "message": "Invalid store_id"})

    except Category.DoesNotExist:
        return Response({"success": False, "message": "Invalid category_id"})

    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=500)