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
from django.db.models import Prefetch



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


@csrf_exempt
@api_view(["POST"])
def get_po_details(request):
    json_request = JSONParser().parse(request)
    po_number = json_request.get("po_number")
    status_filter = json_request.get("status")

    if status_filter:
        pos = (PurchaseOrder.objects.select_related("vendor").prefetch_related(
                Prefetch("items",queryset=PurchaseOrderItem.objects.select_related("product__category", "medicine__category"))).filter(status=status_filter))

        data = []
        for po in pos:
            cats = {item.product.category.name if item.product and item.product.category
                    else item.medicine.category.name if item.medicine and item.medicine.category
                    else "Uncategorized"
                    for item in po.items.all()}
            if not cats:
                category_name = None
            elif len(cats) == 1:
                category_name = next(iter(cats))
            else:
                category_name = "Mixed"

            data.append({
                "po_number": po.po_number,
                "vendor": getattr(po.vendor, "name", po.vendor_id),
                "created_at": po.order_date.strftime("%Y-%m-%d"),
                "status": po.status,
                "category_name": category_name
            })

        return JsonResponse({
            "success": True,
            "count": pos.count(), 
            "purchase_orders": data
        }, status=200)


    def item_category(item):
        if item.product:
            if hasattr(item.product, "category") and item.product.category:
                return item.product.category.name
            return getattr(item.product, "name", "Product")
        
        if item.medicine:
            if hasattr(item.medicine, "category") and item.medicine.category:
                return item.medicine.category.name
            return getattr(item.medicine, "name", "Medicine")
        return "Uncategorized"

    def po_category_summary(items_qs):
        cats = {item_category(i) for i in items_qs}
        if len(cats) == 0:
            return {"category_name": None, "categories": []}
        if len(cats) == 1:
            only = next(iter(cats))
            return {"category_name": only, "categories": [only]}
        return {"category_name": "Mixed", "categories": sorted(cats)}

    if not po_number:
        pos = (PurchaseOrder.objects
               .select_related("vendor")
               .prefetch_related(
                   Prefetch("items",
                            queryset=PurchaseOrderItem.objects.select_related(
                                "product__category", "medicine__category"
                            ))
               )
               .order_by("-id"))

        data = []
        for po in pos:
            summary = po_category_summary(po.items.all())
            data.append({
                "po_number": po.po_number,
                "vendor": getattr(po.vendor, "name", po.vendor_id),
                "created_at": po.order_date.strftime("%Y-%m-%d"),
                "status": po.status,
                "category_name": summary["category_name"],
              
            })
        return JsonResponse({"success": True, "purchase_orders": data}, status=200)

    # Case 2: One PO with item-level details + category summary
    try:
        po = (PurchaseOrder.objects.select_related("vendor").prefetch_related(Prefetch("items",queryset=PurchaseOrderItem.objects.select_related("product__category", "medicine__category"))).get(po_number=po_number))


    except PurchaseOrder.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": f"Purchase Order with number {po_number} does not exist"},
            status=404
        )

    items = []
    for item in po.items.all():
        obj = item.product or item.medicine  # whichever exists
        if not obj:
            continue

        item_data = {
            "id": obj.id,
            "product_id": getattr(obj, "product_id", None),
            "name": getattr(obj, "name", None),
            "description": getattr(obj, "description", None),
            "quantity": getattr(obj, "quantity", None),
            "brand_name": getattr(obj, "brand_name", None), 
            "molecule": getattr(obj, "molecule", None),
            "uom": getattr(obj, "uom", None),
            "shape": getattr(obj, "shape", None),
            "material": getattr(obj, "material", None),
            "color": getattr(obj, "color", None),
            "size": getattr(obj, "size", None),
            "stock": getattr(obj, "stock", None),
            "is_active": getattr(obj, "is_active", None),
            "category": getattr(obj, "category_id", None),
            "qty": item.qty,  # always include PO item qty
            "uom_po": item.uom,  # keep PO's UOM if different from product.uom
            "unit_price": str(item.unit_price) if item.unit_price else None,
            "subtotal": str(item.subtotal),
        }

        items.append(item_data)

#     items.append({
#     "id": item.id,
#     "qty": item.qty,          # top-level qty from PO item
#     "uom": item.uom,
#     "unit_price": str(item.unit_price) if item.unit_price else None,
#     "subtotal": str(item.subtotal),
#     "product": {
#         **product_data,       # unpack existing product fields
#         "qty": item.qty       # add qty here too
#     } if product_data else None,
#     "medicine": {
#         **medicine_data,      # unpack existing medicine fields
#         "qty": item.qty       # add qty here too
#     } if medicine_data else None,
# })


    summary = po_category_summary(po.items.all())
    po_data = {
        "po_number": po.po_number,
        "vendor": getattr(po.vendor, "name", po.vendor_id),
        "created_at": po.order_date.strftime("%Y-%m-%d"),
        "status": po.status,
        "category_name": summary["category_name"],
        "items": items,
    }

    return JsonResponse({"success": True, "purchase_order": po_data}, status=200)



@csrf_exempt
@api_view(["POST"])
def po_update_status(request):
    json_request = JSONParser().parse(request)
    po_number = json_request.get("po_number")
    new_status = json_request.get("status")

    if not po_number or not new_status:
        return JsonResponse({"success": False, "message": "po_number and status are required"}, status=400)

    try:
        po = PurchaseOrder.objects.get(po_number=po_number)
    except PurchaseOrder.DoesNotExist:
        return JsonResponse({"success": False, "message": f"Purchase Order with number {po_number} does not exist"}, status=404)

    po.status = new_status
    po.save()
    return JsonResponse({"success": True, "message": f"Purchase Order {po_number} status updated to {new_status}"}, status=200)



from django.db import transaction

@csrf_exempt
@api_view(["POST"])
def create_indent(request):
    json_request = JSONParser().parse(request)

    store_id = json_request.get("store_id")
    items_data = json_request.get("items", [])
    suggested_vendors = json_request.get("suggested_vendors", [])
    status = json_request.get("status")

    if not store_id or not items_data:
        return JsonResponse({"success": False, "message": "store_id and items are required"}, status=400)

    # Validate UUID
    try:
        store_uuid = uuid.UUID(store_id)
    except ValueError:
        return JsonResponse({"success": False, "message": "Invalid store_id format (must be UUID)"}, status=400)

    # Fetch store
    try:
        store = Store.objects.get(id=store_uuid)
    except Store.DoesNotExist:
        return JsonResponse({"success": False, "message": f"Store with id {store_id} does not exist"}, status=404)

    # ✅ Validate items first
    validated_items = []
    for item in items_data:
        prod_code = item.get("product_id")
        qty = int(item.get("quantity", 0))
        category_id = item.get("category_id")

        if not prod_code or qty <= 0:
            return JsonResponse({"success": False, "message": "Each item must include product_id and valid quantity"}, status=400)

        if category_id == 9:
            try:
                med_obj = Medicine.objects.get(product_id=prod_code)
            except Medicine.DoesNotExist:
                return JsonResponse({"success": False, "message": f"Medicine with product_id {prod_code} does not exist"}, status=400)
            validated_items.append(("medicine", med_obj, qty, category_id))
        else:
            try:
                prod_obj = Product.objects.get(product_id=prod_code)
            except Product.DoesNotExist:
                return JsonResponse({"success": False, "message": f"Product with product_id {prod_code} does not exist"}, status=400)
            validated_items.append(("product", prod_obj, qty, category_id))

    # ✅ Create indent + items atomically
    with transaction.atomic():
        indent = Indent.objects.create(store=store, status=status, suggested_vendors=suggested_vendors)

        created_items = []
        for item_type, obj, qty, category_id in validated_items:
            if item_type == "medicine":
                indent_item = IndentItem.objects.create(indent=indent, medicine=obj, quantity=qty)
            else:
                indent_item = IndentItem.objects.create(indent=indent, product=obj, quantity=qty)

            created_items.append({
                "id": indent_item.id,
                "product_id": obj.product_id,
                "name": obj.name,
                "quantity": indent_item.quantity,
                "category_id": category_id,
                "type": item_type,
            })

    return JsonResponse({
        "success": True,
        "message": "Indent created successfully",
        "indent_number": indent.indent_number,
        "items": created_items
    }, status=201)


@csrf_exempt 
@api_view(["GET"]) 
def get_intent_list(request): 
    statuses = IndentStatus.objects.values_list("status", flat=True)
    return Response({"success": True, "statuses": list(statuses)}, status=status.HTTP_200_OK)
    


@csrf_exempt
@api_view(["POST"])
def stoke_management(request):
    json_request = JSONParser().parse(request)
    Category_id = json_request.get("category_id")
   
    if Category_id ==9:

        product = Medicine.objects.get(product_id=Category_id)
    else:
        product = Product.objects.get(product_id=Category_id)

    return JsonResponse({"success": True, "message": "Product stock updated to "}, status=200)




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser

from .models import Indent, Vendor, Product, Medicine  # adjust imports to your app

@csrf_exempt
@api_view(["POST"])
def get_indent_details(request):
    json_request = JSONParser().parse(request)
    indent_number = json_request.get("indent_number")
    status_filter = json_request.get("status")
    store_id = json_request.get("store_id")


    # Filter by status
    if status_filter:
        indents = (
            Indent.objects
            .select_related("store")
            .prefetch_related("items__product__category", "items__medicine__category")
            .filter(status=status_filter)
        )

        data = []
        for indent in indents:
            vendor_names = []
            first_item = indent.items.first()
            category_id, category_name = None, None

            if indent.suggested_vendors:
                vendors = Vendor.objects.in_bulk(indent.suggested_vendors)
                vendor_names = [{"id": v.id, "name": v.name} for v in vendors.values()]

            if first_item:
                if first_item.product and first_item.product.category:
                    category_id = first_item.product.category_id
                    category_name = first_item.product.category.name
                elif first_item.medicine and first_item.medicine.category:
                    category_id = first_item.medicine.category_id
                    category_name = first_item.medicine.category.name

            data.append({
                "indent_number": indent.indent_number,
                "store": getattr(indent.store, "name", indent.store_id),
                "created_at": indent.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "status": indent.status,
                "category_id": category_id,
                "category_name": category_name,
                "suggested_vendors": vendor_names,
            })

        return JsonResponse({
            "success": True,
            "count": indents.count(),
            "indents": data
        }, status=200)

    # List all indents if no indent_number
    if not indent_number:
        indents = (
            Indent.objects
            .select_related("store")
            .prefetch_related("items__product__category", "items__medicine__category")
            .order_by("-id")
        )

        data = []
        for indent in indents:
            vendor_names = []
            first_item = indent.items.first()
            category_id, category_name = None, None

            if indent.suggested_vendors:
                vendors = Vendor.objects.in_bulk(indent.suggested_vendors)
                vendor_names = [{"id": v.id, "name": v.name} for v in vendors.values()]

            if first_item:
                if first_item.product and first_item.product.category:
                    category_id = first_item.product.category_id
                    category_name = first_item.product.category.name
                elif first_item.medicine and first_item.medicine.category:
                    category_id = first_item.medicine.category_id
                    category_name = first_item.medicine.category.name

            data.append({
                "indent_number": indent.indent_number,
                "store": getattr(indent.store, "name", indent.store_id),
                "created_at": indent.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "status": indent.status,
                "category_id": category_id,
                "category_name": category_name,
                "suggested_vendors": vendor_names,
            })

        return JsonResponse({"success": True, "indents": data}, status=200)

    # One indent with item-level details
    try:
        indent = (
            Indent.objects
            .select_related("store")
            .prefetch_related("items__product__category", "items__medicine__category")
            .get(indent_number=indent_number)
        )
    except Indent.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": f"Indent with number {indent_number} does not exist"},
        )

    # Resolve vendor names
    vendor_names = []
    if indent.suggested_vendors:
        vendors = Vendor.objects.in_bulk(indent.suggested_vendors)
        vendor_names = [v.name for v in vendors.values()]

    items = []
    category_id, category_name = None, None  # <-- initialize before loop

    for item in indent.items.all():
        obj = item.product or item.medicine
        if not obj:
            continue

        if hasattr(obj, "category") and obj.category:
            category_id = obj.category_id
            category_name = obj.category.name

        item_data = {
            "id": obj.id,
            "product_id": getattr(obj, "product_id", None),
            "name": getattr(obj, "name", None),
            "qty": item.quantity,
            "uom": getattr(obj, "uom", None),
            "brand_name": getattr(obj, "brand_name", None),
            "molecule": getattr(obj, "molecule", None),
            "type": "product" if item.product else "medicine",
            "category_name": category_name,
            "created_at": indent.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        items.append(item_data)

    indent_data = {
        "indent_number": indent.indent_number,
        "store": getattr(indent.store, "name", indent.store_id),
        "created_at": indent.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "status": indent.status,
        "suggested_vendors": vendor_names,
        "category_id": category_id,
        "category_name": category_name,
        "items": items,
    }

    return JsonResponse({"success": True, "indent": indent_data}, status=200)




@csrf_exempt
@api_view(["POST"])
def update_indent(request):
    json_request = JSONParser().parse(request)

    indent_number = json_request.get("indent_id")   
    status = json_request.get("status")
    items_data = json_request.get("items", [])
    suggested_vendors = json_request.get("suggested_vendors", [])

    if not indent_number or not items_data:
        return JsonResponse({"success": False, "message": "indent_id and items are required"})

    # Fetch indent
    try:
        indent = Indent.objects.get(indent_number=indent_number)
    except Indent.DoesNotExist:
        return JsonResponse({"success": False, "message": f"Indent {indent_number} does not exist"})

    #  Update indent status
    if status:
        indent.status = status
    if suggested_vendors:
        indent.suggested_vendors = suggested_vendors
        
    indent.save()

    created_or_updated_items = []

    with transaction.atomic():
        for item in items_data:
            prod_code = item.get("product_id")
            qty = int(item.get("qty", 0))
            category_id = item.get("category_id")

            if not prod_code or qty <= 0:
                return JsonResponse({"success": False, "message": "Each item must include product_id and valid quantity"})

            if category_id == 9:
                # Medicine
                try:
                    med_obj = Medicine.objects.get(product_id=prod_code)
                except Medicine.DoesNotExist:
                    return JsonResponse({"success": False, "message": f"Medicine with product_id {prod_code} does not exist"})

                indent_item, created = IndentItem.objects.update_or_create(
                    indent=indent,
                    medicine=med_obj,
                    defaults={"quantity": qty}
                )
                action = "created" if created else "updated"

                created_or_updated_items.append({
                    "id": indent_item.id,
                    "product_id": prod_code,
                    "name": med_obj.name,
                    "qty": indent_item.quantity,
                    "category_id": category_id,
                    "type": "medicine",
                    "action": action
                })
            else:
                # Product
                try:
                    prod_obj = Product.objects.get(product_id=prod_code)
                except Product.DoesNotExist:
                    return JsonResponse({"success": False, "message": f"Product with product_id {prod_code} does not exist"})

                indent_item, created = IndentItem.objects.update_or_create(
                    indent=indent,
                    product=prod_obj,
                    defaults={"quantity": qty}
                )
                action = "created" if created else "updated"

                created_or_updated_items.append({
                    "id": indent_item.id,
                    "product_id": prod_code,
                    "name": prod_obj.name,
                    "quantity": indent_item.quantity,
                    "category_id": category_id,
                    "type": "product",
                    "action": action
                })

    return JsonResponse({
        "success": True,
        "message": f"Indent {indent_number} updated successfully",
    }, status=200)
