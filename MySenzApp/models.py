import uuid,random,string 
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.contrib.auth import get_user_model

class AdminUserManager(BaseUserManager):
    def create_user(self, email, password=None, role="customer", **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "superadmin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)
    class Meta:
        db_table="adminusermanager"

class AdminUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # 🔑 UUID instead of int
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, default="customer")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = AdminUserManager()

    def __str__(self):
        return self.email
    class Meta:
        db_table="adminusers"    

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(AdminUser, on_delete=models.CASCADE, related_name="customer")
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    class Meta:
        db_table = "customer"
    

class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.start_time}-{self.end_time} (Day {self.day_of_week})"
    class Meta:
        db_table="timeslot"



class Store(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store_name = models.CharField(max_length=150)
    store_contact = models.CharField(max_length=20)
    store_address = models.TextField()

    def __str__(self):
        return self.store_name
    
    class Meta:
        db_table="store"
            
class Category(models.Model):
    name = models.CharField(max_length=100,unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table="categorys"

class Service(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255,unique=True)
    description = models.TextField(blank=True)
    price = models.IntegerField()
    show_in_ecom = models.BooleanField(default=True)
    home_care_enabled = models.BooleanField(default=True)
    instore_enabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    class Meta:
        db_table="services"


class Booking(models.Model):
    APPOINTMENT_TYPES = (
        ('home', 'Home Care'),
        ('instore', 'In-Store'),
    )
    STATUS_CHOICES = (
        ('new booking', 'New Booking'),
        ('contacted', 'Contacted'),
        ('follow-up', 'Follow-Up'),
        ('intersted', 'Intersted'),
        ('not intersted','Not Intersted'),
        ('converted','Converted'),
        ('lost','LOst'),

    )
    booking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user=models.ForeignKey(Customer,on_delete=models.CASCADE)
    store=models.ForeignKey(Store,on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES)
    date = models.DateField()
    slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    booking_address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new booking')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    alert_type =models.CharField(max_length=150)#alerte message
     
    def __str__(self):
        return f"Appointment {self.id} - {self.service.name}"
    
    class Meta:
        db_table="booking"
        
ser = get_user_model()
def generate_passcode(length=6):
    return ''.join(random.choices(string.digits, k=length)) 
  
class StoreManager(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="managers")
    user = models.OneToOneField(AdminUser, on_delete=models.CASCADE, related_name="store_manager")
    is_active = models.BooleanField(default=True)
    category= models.ForeignKey(Category,on_delete=models.CASCADE)
    service= models.ForeignKey(Service,on_delete=models.CASCADE)
    manager_name = models.CharField(max_length=150)
    manager_contact = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    passcode = models.CharField(max_length=10, default=generate_passcode) 
    def __str__(self):
        return f"{self.manager_name} ({self.user.email})"
    class Meta:
        db_table="storemanager"


class AppointmentStatusLog(models.Model):
    appointment = models.ForeignKey(Booking, on_delete=models.CASCADE)
    status = models.CharField(max_length=30)
    updated_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True)
    remarks = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table="appoinmentstatuslog"



class MedicineRequest(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('closed', 'Closed'),
    )

    customer_name = models.CharField(max_length=200)
    customer_mobile = models.CharField(max_length=20)
    area = models.CharField(max_length=200)
    pincode = models.CharField(max_length=10, blank=True)
    requirement_text = models.TextField()
    prescription_file = models.FileField(upload_to='prescriptions/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    converted_to_order = models.BooleanField(default=False)
    bill_number = models.CharField(max_length=100, blank=True)
    updated_by = models.ForeignKey(AdminUser, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# class GlobalSettings(models.Model):
#     alert_mobile_numbers = models.JSONField(default=list)
#     alert_type = models.CharField(max_length=20, default="sms")  # sms/whatsapp/both
#     medicine_customer_care_numbers = models.JSONField(default=list)
#     billing_api_url = models.CharField(max_length=500, blank=True)
#     billing_api_key = models.CharField(max_length=200, blank=True)
#     branch_id = models.CharField(max_length=100, blank=True)

#     def __str__(self):
#         return "Global Settings"


