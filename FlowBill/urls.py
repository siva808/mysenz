from django.urls import path
from .views import *


urlpatterns = [
   path('vendor/', VendorAPIView.as_view()),
   path('product/', ProductAPIView.as_view()),
   path('bulk-upload/', BulkUploadAPIView.as_view()),
   #path("purchase-orders/", PurchaseOrderListCreateAPIView.as_view(), name="purchase-order-list-create"), 
   #path("purchase-orders/", PurchaseOrderDetailAPIView.as_view(), name="purchase-order-detail"), 
   #path("purchase-order-items/", PurchaseOrderItemListCreateAPIView.as_view(), name="purchase-order-item-list-create"),
   path("get_vendor/",get_vendor, name="get_vendor"),
   path("create_indent/",create_indent,name="create_indent"),
   path("create_po/",create_purchase_order,name="create_purchase_order"),
   path("get_products/",get_products,name="get_products"),
   path("get_po_details/",get_po_details,name="get_po_details"),
   path("update_po_status/",po_update_status,name="update_po_status"),

   
]