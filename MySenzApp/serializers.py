from rest_framework import serializers
from .models import *
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework.response import Response


class TimestampMixin(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True, required=False)

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = ["id", "username", "email", "role", "is_active"]
        
class StoreConfigSerializer(serializers.Serializer):
    storeName = serializers.CharField(max_length=150)
    storeContact = serializers.CharField(max_length=20)
    storeAddress = serializers.CharField()
    managerName = serializers.CharField(max_length=150)
    managerContact = serializers.CharField(max_length=20)
    managerEmail = serializers.EmailField()
    managerPassword = serializers.CharField(write_only=True)

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ["id", "store_name", "store_contact", "store_address"]

class StoreManagerSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    manager_email = serializers.EmailField(source="user.email", read_only=True)
    class Meta:
        model = StoreManager
        fields = ["id", "manager_name", "manager_contact", "manager_email", "store","is_active"]
        read_only_fields = ["created_at", "passcode"]

class StoreManagerDetailSerializer(serializers.ModelSerializer):
    store = StoreSerializer(read_only=True)
    manager_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = StoreManager
        fields = ["id", "manager_name", "manager_contact", "manager_email", "store","is_active"]


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id","name","is_active"]


class ServiceDetailsSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), write_only=True)

    class Meta:
        model = Service
        fields = ["id","name","price","description","is_active","category","category_id"]


class ServiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["name", "description", "price", "category"]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id","name", "description","price","category","show_in_ecom",
                  "home_care_enabled","instore_enabled","is_active"]

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ["id","start_time","end_time","is_active",]


class BokkingCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Booking
        fields =["user","store","category","service","appointment_type","booking_address"]

class BookingGetSerilaizer(serializers.ModelSerializer):
    class Meta:
        model= Booking
        field ='__all__'

class Bookingupdateserializer(serializers.ModelSerializer):
    class Meta:
        model =Booking
        fields=["category","service","appoinment_type","status","update_at"]
    
class CustomerSerilaizer(serializers.ModelSerializer):
    class meta:
        model=Customer
        fields=["id","name","contact","address","create_at"]

class BookingDetailsSerializer(serializers.ModelSerializer):
    customer=CustomerSerilaizer(read_only=True)
    class Meta:
        model = Booking 
        fields = ["booking_id","service","category",""]
        read_only_field=["customer_name","customer_email"]
class BookingcreateSerializer(serializers.ModelSerializer):
     class meta:
         model=Booking
         field='__all__'
class CustomerSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "email", "name", "contact", "address", "created_at"]


class MedicineRequestListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineRequest
        fields = ["id","request_uuid","customer_name","mobile","area","pincode","requirement_text","prescription_file","status","notes","created_at"]

class MedicineRequestStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineRequest
        fields = ["status", "notes"]

class StoreManagerserviceSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = StoreManager
        fields = ["id","manager_name","manager_contact","user_email","store_name","category_name","service_name",
            "is_active","created_at","updated_at"]

class StoreManagerServiceUpdateSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = StoreManager
        fields = ["id","manager_name","manager_contact","store","category","service","store_name","category_name","service_name",
            "is_active","updated_at"]
        

User = get_user_model()

class CustomerSignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = AdminUser
        fields = ["email", "password"]

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        user = AdminUser.objects.create_user(email=email,password=password,role="customer")
        Customer.objects.create(user=user)
        return user


class CustomerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_active:
            raise serializers.ValidationError("User is inactive")
        data["user"] = user
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No account with this email")
        return value
    
class BookingSearchSerializer(serializers.ModelSerializer):
    customer_name=serializers.CharField(source="user.name",read_only=True)
    store_name = serializers.CharField(source="stor.store_name",read_only=True)
    servic_name= serializers.CharField(source="service.name",read_only=True)
    class Meta:
        model = Booking
        field= '__all__'