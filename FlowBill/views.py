from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAdminUser
import csv
from django.db import transaction

class VendorAPIView(APIView):
    permission_classes = [IsAdminUser] 

    def post(self, request):
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            vendor = serializer.save()
            return Response(
                {"success":True,"message": "Vendor created", "vendor_id": vendor.vendor_id},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    def put(self, request): 
        vendor_id = request.data.get("vendor_id") 
        vendor = get_object_or_404(Vendor, vendor_id=vendor_id) 
        serializer = VendorSerializer(vendor, data=request.data, partial=True) 
        if serializer.is_valid(): 
            serializer.save() 
            return Response( {"success": True, "message": "Vendor updated", "data": serializer.data}, status=status.HTTP_200_OK ) 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        vendors = Vendor.objects.all()
        serializer = VendorSerializer(vendors, many=True)
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_200_OK
        )

    def delete(self, request):
        json_request = JSONParser().parse(request)
        vendor_id = json_request.get("vendor_id")

        vendor = get_object_or_404(Vendor, pk=vendor_id)
        vendor.delete()
        return Response(
            {"success": True, "message": "Vendor deleted"},
            status=status.HTTP_204_NO_CONTENT
        )
    
class ProductAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        queryset = Product.objects.all()

        # Extract filters from query params
        category_id = request.query_params.get("category_id")
        brand_name = request.query_params.get("brand_name")
        molecule = request.query_params.get("molecule")
        uom = request.query_params.get("uom")
        color = request.query_params.get("color")
        is_active = request.query_params.get("is_active")

        # Apply filters if present
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if brand_name:
            queryset = queryset.filter(brand_name__icontains=brand_name)
        if molecule:
            queryset = queryset.filter(molecule__icontains=molecule)
        if uom:
            queryset = queryset.filter(uom__iexact=uom)
        if color:
            queryset = queryset.filter(color__iexact=color)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        serializer = ProductSerializer(queryset, many=True)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Product created successfuly "}, status=status.HTTP_201_CREATED)
        return Response({"success": False, "error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, ):
        product_id = request.data.get("product_id") 
        try:
            product = Product.objects.get(product_id=product_id)

        except Product.DoesNotExist:
            return Response({"success": False, "error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True,"message":"product updated", "data": serializer.data})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        pk = request.data.get("product_id")

        try:
            product = Product.objects.get(product_id=pk)
        except Product.DoesNotExist:
            return Response({"success": False, "error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True, "message": "Product updated", "data": serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        pk = request.data.get("product_id")
        try:
            product = Product.objects.get(product_id=pk)
            product.delete()
            return Response({"success": "Product deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            return Response({"success": False, "error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
 

class MedicineAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):

        categories = Medicine.objects.all()

        if 'category_id' in request.query_params:
            categories = categories.filter(category_id=request.query_params['category_id'])

        serializer = MedicineSerializer(categories, many=True)
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_200_OK
        )
    
    def post(self, request):
        serializer = MedicineSerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            return Response(
                {"success":True,"message": "Category created", "category_id": category.category_id},
                status=status.HTTP_201_CREATED
            )
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)  
        
    def put(self, request): 
        product_id = request.data.get("product_id")
        category = get_object_or_404(Medicine, product_id=product_id) 
        serializer = MedicineSerializer(category, data=request.data, partial=True) 
        if serializer.is_valid():  
            serializer.save() 
            return Response( {"success": True, "message": "Category updated", "data": serializer.data}, status=status.HTTP_200_OK ) 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


    def delete(self, request):
        json_request = JSONParser().parse(request)
        product_id = json_request.get("product_id")

        category = get_object_or_404(Medicine, product_id=product_id)
        category.delete()
        return Response(
            {"success": True, "message": "Category deleted"},
            status=status.HTTP_204_NO_CONTENT
        )
    



class BulkUploadAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        products, medicines, errors = [], [], []

        
        if isinstance(request.data, list):
            rows = request.data
        else:
           
            file_csv = request.FILES.get("file")
            if not file_csv:
                return Response(
                    {"success": False, "error": "Provide JSON array or CSV file"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            rows = csv.DictReader(file_csv.read().decode("utf-8").splitlines())

        
        for idx, row in enumerate(rows, start=1):
            
            category_name = row.get("category", "").strip().lower()

            
            category_obj = Category.objects.filter(name__iexact=category_name).first()
            if not category_obj:
                errors.append({
                    "row": idx,
                    "errors": {"success": False, "category": [f"Category '{category_name}' does not exist"]}
                })
                continue

            
            serializer_class = MedicineSerializer if category_name == "medicine" else ProductSerializer
            serializer = serializer_class(data={k: v for k, v in row.items() if k != "category"})

            if serializer.is_valid():
                obj = serializer_class.Meta.model(**serializer.validated_data)
                obj.category = category_obj   
                if category_name == "medicine":
                    medicines.append(obj)
                else:
                    products.append(obj)
            else:
                errors.append({"success": False, "row": idx, "errors": serializer.errors})

       
        if errors:
            return Response(
                {"success": False, "message": "Validation failed", "errors": errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        with transaction.atomic():
            for product in products:
                product.save()
            for medicine in medicines:
                medicine.save()

        return Response(
            {
                "success": True,
                "message": "Bulk upload complete",
                "products_uploaded": len(products),
                "medicines_uploaded": len(medicines)
            },
            status=status.HTTP_201_CREATED
        )



class PurchaseOrderListCreateAPIView(APIView):

    def get(self, request):

        pos = PurchaseOrder.objects.all()
        serializer = PurchaseOrderSerializer(pos, many=True)

        return Response(serializer.data)

    def post(self, request):

        serializer = PurchaseOrderSerializer(data=request.data)
        if serializer.is_valid():
            po = serializer.save()
            return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderDetailAPIView(APIView):

    def get(self, request, pk):
        po_number = request.data.get("po_number")

        try:
            po = PurchaseOrder.objects.get(po_number=po_number)

        except PurchaseOrder.DoesNotExist:
            return Response({"success": False, "error": "PO not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PurchaseOrderSerializer(po)

        return Response({"success": True, "message": "Purchase order retrieved successfully"})

    def patch(self, request, pk):
        po_number = request.data.get("po_number")
        try:
            po = PurchaseOrder.objects.get(po_number=po_number)

        except PurchaseOrder.DoesNotExist:
            return Response({"success": False, "error": "PO not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PurchaseOrderSerializer(po, data=request.data, partial=True)
        if serializer.is_valid():
            po = serializer.save()
            return Response({"success": True, "message": "Purchase order updated successfully"})
        
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PurchaseOrderItemListCreateAPIView(APIView):

    def get(self, request):

        items = PurchaseOrderItem.objects.all()
        serializer = PurchaseOrderItemSerializer(items, many=True)
        return Response({"success": True,"message": "Purchase order items retrieved successfully"})

    def post(self, request):
        
        serializer = PurchaseOrderItemSerializer(data=request.data)
        if serializer.is_valid():
            item = serializer.save()
            return Response(PurchaseOrderItemSerializer(item).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
