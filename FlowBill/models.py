from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid
from MySenzApp.models import Category


class Vendor(models.Model):
    
    vendor_id = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    mobile = models.CharField(max_length=15)
    email = models.EmailField()
    gst = models.CharField(max_length=15)
    categories = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    payment = models.CharField(max_length=50,default="CREDIT")
    credit_days = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs): 
        if not self.vendor_id:
            unique_code = uuid.uuid4().hex[:8].upper()
            self.vendor_id = f"VND-{unique_code}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    class Meta:
        db_table = "vendor"
    
#vendor_id,name,address,mobile,email,gst,categories,payment,credit_days,is_active

class Product(models.Model):

    product_id = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1) 

    # Medicine-specific fields 
    brand_name = models.CharField(max_length=100, blank=True, null=True) 
    molecule = models.CharField(max_length=100, blank=True, null=True) 
    uom = models.CharField(max_length=20, blank=True, null=True) # strip, box, tablet 

    # optical fields
    shape = models.CharField(max_length=50, blank=True, null=True) 
    material = models.CharField(max_length=50, blank=True, null=True) 
    color = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)

    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):

        if not self.id:  
            super().save(*args, **kwargs)
        if not self.product_id:
            self.product_id = f"PRD-WH-{self.id:06d}"
            super().save(update_fields=["product_id"])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "product"

    
 #product_id,name,description,brand_name,molecule,uom,shape,material,color,size,stock,is_active,category

class Medicine(models.Model):
    
    product_id = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1) 
    brand_name = models.CharField(max_length=100, blank=True, null=True) 
    molecule = models.CharField(max_length=100, blank=True, null=True) 
    uom = models.CharField(max_length=20, blank=True, null=True) # strip, box, tablet 
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):

        if not self.id:  
            super().save(*args, **kwargs)
        if not self.product_id:
            self.product_id = f"PRD-WH-{self.id:06d}"
            super().save(update_fields=["product_id"])
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "medicine"




class PurchaseOrder(models.Model):

    po_number = models.CharField(max_length=20, unique=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="purchase_orders")
    order_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20,default="created")  # created, received, cancelled
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.po_number:
            super().save(*args, **kwargs)
            self.po_number = f"PO-WH-{self.id:06d}"
            super().save(update_fields=["po_number"])
        else:
            super().save(*args, **kwargs)

    def recalc_total(self):
        self.total_amount = sum(item.subtotal for item in self.items.all())
        self.save(update_fields=["total_amount"])

    def __str__(self):
        return self.po_number


class PurchaseOrderItem(models.Model):
    
    purchase_order = models.ForeignKey(PurchaseOrder, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    uom = models.CharField(max_length=20)  # Nos, ml, strip, etc.
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        self.purchase_order.recalc_total()

    def __str__(self):
        if self.product:
            return f"{self.product.name} x {self.quantity} {self.uom}"
        elif self.medicine:
            return f"{self.medicine.name} x {self.quantity} {self.uom}"
        return f"Item {self.id}"
