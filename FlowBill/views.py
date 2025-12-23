from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status, permissions
from MySenzApp.crud import DocumentManager
import csv
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

class VendorAPIView(APIView):
    permission_classes = [IsAdminUser] 

    def post(self, request):
        serializer = VendorSerializer(data=request.data)
        if serializer.is_valid():
            vendor = serializer.save()
            return Response(
                {"success":True,"message": "Vendor created", "vendor_id": vendor.vendor_id},)
        return Response({"success": False, "error": serializer.errors})

    
    def put(self, request): 
        vendor_id = request.data.get("vendor_id") 
        vendor = get_object_or_404(Vendor, vendor_id=vendor_id) 
        serializer = VendorSerializer(vendor, data=request.data, partial=True) 
        if serializer.is_valid(): 
            serializer.save() 
            return Response( {"success": True, "message": "Vendor updated", "data": serializer.data}) 
        return Response({"success": False, "error": serializer.errors})
    
    def get(self, request):
        vendors = Vendor.objects.all()
        serializer = VendorSerializer(vendors, many=True)

        return Response(
            {"success": True, "data": serializer.data})

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
        medicine = Medicine.objects.all()
        queryset = Product.objects.all()

        # Extract filters from query params
        category_id = request.query_params.get("category_id")
        brand_name = request.query_params.get("brand_name")
        molecule = request.query_params.get("molecule")
        uom = request.query_params.get("uom")
        color = request.query_params.get("color")
        is_active = request.query_params.get("is_active")

        # Apply filters if present
        if category_id == 9:
            medicine = medicine.filter(category_id=category_id)
        else:   
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
        category_id = request.data.get("category")

        if category_id == 9:
            medicine_serializer = MedicineSerializer(data=request.data)
            if medicine_serializer.is_valid():
                medicine_serializer.save()
                return Response(
                    {"success": True, "message": "Medicine created successfully"},
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {"success": False, "error": medicine_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        product_serializer = ProductSerializer(data=request.data)
        if product_serializer.is_valid():
            product_serializer.save()
            return Response(
                {"success": True, "message": "Product created successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"success": False, "error": product_serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


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



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_vendor(request):
    category_name = request.data.get("category_name")

    if not category_name:
        return Response(
            {"success": False, "error": "category_name is required"})

    # category_name is already a string, so use it directly
    vendors = Vendor.objects.filter(categories__contains=[category_name],is_active=True).values("id", "name")

    return Response(
        {"success": True, "data": list(vendors)},
        status=status.HTTP_200_OK
    )





class IndentListCreateAPIView(APIView):
    
    def post(self, request):

        serializer = IndentSerializer(data=request.data)
        if serializer.is_valid():
            indent = serializer.save()
            return Response(IndentSerializer(indent).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def update(self, request):
        indent_number = request.data.get("indent_number")
        indent = Indent.objects.filter(indent_number=indent_number)

        serializer = IndentSerializer(indent, data=request.data, partial=True)
        if serializer.is_valid():
            indent = serializer.save()
            return Response(IndentSerializer(indent).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


class IndentListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        indents = Indent.objects.select_related("store").prefetch_related("items__product")
        serializer = IndentSerializer(indents, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = IndentSerializer(data=request.data)
        if serializer.is_valid():
            indent = serializer.save()
            return Response(IndentSerializer(indent).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IndentDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return Indent.objects.select_related("store").prefetch_related("items__product").get(pk=pk)
        except Indent.DoesNotExist:
            return None

    def get(self, request, pk):
        indent = self.get_object(pk)
        if not indent:
            return Response({"error": "Indent not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(IndentSerializer(indent).data)

    def patch(self, request, pk):
        indent = self.get_object(pk)
        if not indent:
            return Response({"error": "Indent not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = IndentSerializer(indent, data=request.data, partial=True)
        if serializer.is_valid():
            indent = serializer.save()
            return Response(IndentSerializer(indent).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IndentListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        pk = request.data.get("id")
        indents = DocumentManager.fetch_all_rows(
            Indent,
            filters={"id":pk},
            field_list=["id", "indent_number", "store", "status"],
            sort_list=["-created_at"]
        )
        serializer = IndentSerializer(indents, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = IndentSerializer(data=request.data)
        if serializer.is_valid():
            indent = serializer.save()
            return Response(IndentSerializer(indent).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IndentDetailAPIView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        pk = request.data.get("id")

        indent = DocumentManager.fetch_row(Indent,filters={"id": pk},field_list=["id", "indent_number", "store", "status"])

        if not indent:
            return Response({"error": "Indent not found"})
        
        serializer = IndentSerializer(indent)
        return Response(serializer.data)

    def patch(self, request, pk):
        indent = DocumentManager.fetch_row(Indent, filters={"id": pk})
        if not indent:
            return Response({"error": "Indent not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = IndentSerializer(indent, data=request.data, partial=True)
        if serializer.is_valid():
            indent = serializer.save()
            return Response(IndentSerializer(indent).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        deleted = DocumentManager.remove_rows(Indent, filters={"id": pk})
        if deleted:
            return Response({"success": True}, status=status.HTTP_200_OK)
        return Response({"error": "Indent not found"}, status=status.HTTP_404_NOT_FOUND)




@csrf_exempt
@api_view(["POST"])
def create_purchase_order(request):
    json_request = JSONParser().parse(request)
    vendor_id = json_request.get("vendor") # <-- match your payload key
    items_data = json_request.get("items", [])

    try: 
        vendor = Vendor.objects.get(id=vendor_id) 
    except Vendor.DoesNotExist: 
        return JsonResponse({"error": f"Vendor with id {vendor_id} does not exist"}, status=400) 
    # Create PurchaseOrder
    po = PurchaseOrder.objects.create(vendor=vendor)

    created_items = []
    for item in items_data:
        prod_code = item.get("product_id")
        qty = int(item.get("qty", 0))
        uom = item.get("uom")
        category_id = item.get("category_id")

        if not prod_code:
            return JsonResponse({"success": False, "message": "Each item must include a valid 'product_id'"}, status=400)

        if category_id == 9:
            # Medicine lookup
            try:
                med_obj = Medicine.objects.get(product_id=prod_code)
            except Medicine.DoesNotExist:
                return JsonResponse({"success": False, "message": f"Medicine with product_id {prod_code} does not exist"}, status=400)

            po_item = PurchaseOrderItem.objects.create(
                purchase_order=po,
                medicine=med_obj,
                qty=qty,
                uom=uom
            )
        else:
            # Product lookup
            try:
                prod_obj = Product.objects.get(product_id=prod_code)
            except Product.DoesNotExist:
                return JsonResponse({"success": False, "message": f"Product with product_id {prod_code} does not exist"}, status=400)

            po_item = PurchaseOrderItem.objects.create(
                purchase_order=po,
                product=prod_obj,
                qty=qty,
                uom=uom
            )

        created_items.append({
            "id": po_item.id,
            "product_id": prod_code,
            "qty": qty,
            "uom": uom
        })

    # Build response manually


    return JsonResponse({"success":True,"message":"Purchase Order created successfully"}, status=201)

@csrf_exempt
@api_view(["POST"])
def get_products(request):
    category_id = request.data.get("category_id")
    if not category_id:
        return JsonResponse({"success":False,"message": "category_id is required"}, status=400)

    try:
        category_id = int(category_id)
        
    except ValueError:
        return JsonResponse({"success":False,"message": "category_id must be an integer"}, status=400)
    if category_id == 9:
        products = Medicine.objects.filter(category_id=category_id).values()
    else:
        products = Product.objects.filter(category_id=category_id).values()

    return JsonResponse({"success": True, "data": list(products)}, status=200)

