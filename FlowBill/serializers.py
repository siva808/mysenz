from rest_framework import serializers
from .models import *

class VendorSerializer(serializers.ModelSerializer): 
    
    class Meta: 
        model = Vendor 
        fields = "__all__" 
        read_only_fields = ["vendor_id"]


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["product_id"]


class MedicineSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Medicine
        fields = "__all__"
        read_only_fields = ["category_id"]


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    brand_name = serializers.CharField(source="product.brand_name", read_only=True)
    molecule = serializers.CharField(source="product.molecule", read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            "id", "purchase_order", "product", "medicine",
            "product_name", "brand_name", "molecule",
            "quantity", "uom", "unit_price", "subtotal"
        ]
        read_only_fields = ["subtotal"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, required=False)

    class Meta:
        model = PurchaseOrder
        fields = ["id", "po_number", "vendor", "order_date", "status", "total_amount", "items"]
        read_only_fields = ["po_number", "order_date", "total_amount"]
        

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        po = PurchaseOrder.objects.create(**validated_data)
        for item_data in items_data:
            PurchaseOrderItem.objects.create(purchase_order=po, **item_data)
        po.recalc_total()
        return po
