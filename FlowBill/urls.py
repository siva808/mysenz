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
   path("indents/", IndentListCreateAPIView.as_view(), name="indent-list-create"),
   path("create_po/",create_purchase_order,name="create_purchase_order"),
   path("get_products/",get_products,name="get_products"),

   
]