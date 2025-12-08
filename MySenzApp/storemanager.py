from .serializers import *
from .models import *
from .notification import NotificationService
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework import status,generics,permissions
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from asgiref.sync import sync_to_async
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

#return Response({"success": False, "error": "Invalid credentials"})
@api_view(["GET"])
@permission_classes([IsAuthenticated])   
def get_store_manager_profile(request):
    try:
        store_manager = StoreManager.objects.get(user=request.user)
        serializer = StoreManagerSerializer(store_manager)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except StoreManager.DoesNotExist:
        return Response({"success": False, "message":"No StoreManager profile found for this user"})
    

class StoreManagerListView(generics.ListAPIView):
    serializer_class = StoreManagerDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StoreManager.objects.all()

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "success": True,
                "message": "Store managers fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False,"message": "Failed to fetch store managers","errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoryListView(generics.ListAPIView):
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.all()

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({"success": True,"message": "Catogery fetched successfully","data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False,"message": "Failed to fetch store managers","errors": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(["POST"])
def create_store_manager(request):
    serializer = StoreConfigSerializer(data=request.data.get("details"))
    if not serializer.is_valid():
        return Response({ "success": False,"message": "Validation failed","errors": serializer.errors})
    data = serializer.validated_data
    try:
        store = Store.objects.create(
            store_name=data["storeName"],
            store_contact=data["storeContact"],
            store_address=data["storeAddress"]
        )
    # Create AdminUser for manager
        manager_user = AdminUser.objects.create_user(
            email=data["managerEmail"],
            password=data["managerPassword"],
            role="manager"
        )

        # Create StoreManager
        store_manager = StoreManager.objects.create(
            store=store,
            user=manager_user,
            manager_name=data["managerName"],
            manager_contact=data["managerContact"]
        )

        return Response({"succes":True,"message": "StoreManager created successfully","store": StoreSerializer(store).data,
            "manager": StoreManagerSerializer(store_manager).data
        })

    except Exception as e:
        return Response({"succes": False,"message": "Unexpected error occurred",
            "details": str(e)
        }) 
        
class StoreManagerDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            uuid = request.query_params.get("uuid")
            if not uuid:
                return Response({"success": False,"message": "UUID query parameter is required"})

            manager = get_object_or_404(StoreManager, id=uuid)
            serializer = StoreManagerDetailSerializer(manager)

            return Response({"success":True,"message": "success","data": serializer.data
            })

        except StoreManager.DoesNotExist:
            return Response({"success": False,"message": "Manager not found"})

        except Exception as e:
            return Response({"success": False,"message": str(e)
            })
        
class UpdateStoreManagerActiveView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        manager_id = request.data.get("managerId")
        active_type = request.data.get("activeType") 

        if manager_id is None or active_type is None:
            return Response({"success": False, "message": "managerId and activeType are required"})

        manager = get_object_or_404(StoreManager, id=manager_id)
        manager.is_active = bool(active_type)
        manager.save()

        serializer = StoreManagerDetailSerializer(manager)
        return Response({
            "success": True,
            "message": f"Manager {'activated' if manager.is_active else 'deactivated'} successfully",
            "data": serializer.data
        })
    

class CategoryAPIView(APIView):
    def get(self, request):
        category_id = request.query_params.get("id")
        try:
            if category_id:
                category = get_object_or_404(Category, pk=category_id)
                serializer = ServiceCategorySerializer(category)
                return Response({"success": True,"message": "Category retrieved successfully","data": serializer.data
                }, status=status.HTTP_200_OK)

            categories = Category.objects.all().order_by("id")

            serializer = ServiceCategorySerializer(categories, many=True)
            return Response({"success": True,"message": "Categories retrieved successfully","data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False,"message": f"Error retrieving category: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        serializer = ServiceCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,"message": "Category created successfully","data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False,"message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        category_id = request.query_params.get("id")
        if not category_id:
            return Response({"success": False,"message": "id query parameter required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            category = get_object_or_404(Category, pk=category_id)
            serializer = ServiceCategorySerializer(category, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({"success": True,"message": "Category updated successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            return Response({"success": False,"message": "Validation failed","errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"success": False,"message": f"Error updating category: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        category_id = request.query_params.get("id")
        if not category_id:
            return Response({"success": False,"message": "id query parameter required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            category = get_object_or_404(Category, pk=category_id)
            category.delete()
            return Response({"success": True,"message": "Category deleted successfully"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False,"message": f"Error deleting category: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ServiceAPIView(APIView):
    def get(self, request):
        category_name = request.query_params.get("name")
        if category_name:
            category = get_object_or_404(Service, name__iexact=category_name)
            serializer = ServiceDetailsSerializer(category)
            return Response({"success": True,"message": "Services retrieved successfully","data": serializer.data
            }, status=status.HTTP_200_OK)

        categories = Service.objects.all().order_by("id")
        serializer = ServiceDetailsSerializer(categories, many=True)
        return Response({"success": True,"message": "All Services retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ServiceCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True,"message": "Services created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False,"message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        service_id = request.query_params.get("id")
        if not service_id:
            return Response({"success": False,"message": "id query parameter required"}, status=status.HTTP_400_BAD_REQUEST)

        service = get_object_or_404(Service, pk=service_id)
        serializer = ServiceSerializer(service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True,"message": "Service updated successfully","data": serializer.data
        }, status=status.HTTP_200_OK)

        return Response({"success": False,"message": "Validation failed","errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        category_name = request.query_params.get("name")
        if not category_name:
            return Response({"success": False,"message": "name query parameter required"}, status=status.HTTP_400_BAD_REQUEST)

        category = get_object_or_404(Service, name__iexact=category_name)
        category.delete()
        return Response({"success": True,"message": "Services deleted successfully"}, status=status.HTTP_200_OK)
    
class ManagerServiceAPIView(APIView):
    def get(self, request):
        manager_id = request.query_params.get("id")
        if manager_id:
            manager = get_object_or_404(
                StoreManager.objects.select_related("store", "category", "service", "user"),
                pk=manager_id
            )
            serializer = StoreManagerserviceSerializer(manager)
            return Response({"success": True,"message": "Manager details retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        managers = StoreManager.objects.select_related("store", "category", "service", "user")
        serializer = StoreManagerserviceSerializer(managers, many=True)
        return Response({"success": True,"message": "All managers retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request):
        #PUT: Update manager category/service using query param ?id=<uuid>.
        manager_id = request.query_params.get("id")
        if not manager_id:
            return Response({"success": False, "message": "Manager ID is required"},
                            status=status.HTTP_400_BAD_REQUEST)

        manager = get_object_or_404(StoreManager, pk=manager_id)
        serializer = StoreManagerServiceUpdateSerializer(manager, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True,"message": "StoreManager updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
class BookingAPIView(APIView):
    def post(self,request):
        serializer= BokkingCreateSerializer(data=request.data)
        if serializer.is_valid():
            booking=serializer.save()
            NotificationService.notify_booking_update(booking)
            return Response({"success":True,"message":"booking created" ,"data":serializer.data},status=status.HTTP_201_CREATED)
        return Response({"success":False,"message":"fille the all field!.."},status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        booking_id = request.query_params.get("id")
        if booking_id:
            booking = get_object_or_404(Booking, pk=booking_id)  
            serializer = BookingGetSerilaizer(booking)
            return Response({"success": True,"message": "Booking retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        bookings = Booking.objects.all().order_by("booking_id") 
        serializer = BookingGetSerilaizer(bookings, many=True)
        return Response({
            "success": True,
            "message": "All bookings retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    def put(self, request):
        booking_id=request.query_params.get("id")
        if not booking_id:
            return Response({"success":False,"message":"Data required!."},status=status.HTTP_404_NOT_FOUND)
        booking =get_object_or_404(Booking, pk=booking_id)
        serializer =Bookingupdateserializer(booking,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success":True,"message":"success","data":serializer.data},status=status.HTTP_200_OK)
        return Response({"success":True,"message":"success","errors":serializer.errors},status=status.HTTP_200_OK)



class BookingSearchView(APIView):
    pagination_class = PageNumberPagination
    
    def get(self, request):
        search = request.GET.get("search")
        status_filter = request.GET.get("status")
        service_filter = request.GET.get("service")

        # ✅ Start with empty Q object
        query = Q()

        if search:
            query &= Q(user__name__icontains=search) | Q(store__store_name__icontains=search)
        if status_filter:
            query &= Q(status=status_filter)
        if service_filter:
            query &= Q(service__name__icontains=service_filter)

        # ✅ Apply query to queryset
        qs = Booking.objects.filter(query)

        try:
            if not qs.exists():
                return Response({"message": "No data found"}, status=status.HTTP_404_NOT_FOUND)

            paginator = self.pagination_class()
            page = paginator.paginate_queryset(qs, request, view=self)
            if page is not None:
                serializer = BookingSearchSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = BookingSearchSerializer(qs, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
