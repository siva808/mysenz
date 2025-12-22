from django.urls import path
from .views import *


urlpatterns = [
   path('vendor/', VendorAPIView.as_view()),
   path('product/', ProductAPIView.as_view()),
   path('medicine/', MedicineAPIView.as_view()),
   path('bulk-upload/', BulkUploadAPIView.as_view()),
   path("purchase-orders/", PurchaseOrderListCreateAPIView.as_view(), name="purchase-order-list-create"), 
   path("purchase-orders/", PurchaseOrderDetailAPIView.as_view(), name="purchase-order-detail"), 
   path("purchase-order-items/", PurchaseOrderItemListCreateAPIView.as_view(), name="purchase-order-item-list-create"),
]