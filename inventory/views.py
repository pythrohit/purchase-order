from rest_framework import filters
from common.views import TenantModelViewSet
from .models import Category, ItemGroup, Item
from .serializers import CategorySerializer, ItemGroupSerializer, ItemSerializer


class CategoryViewSet(TenantModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]


class ItemGroupViewSet(TenantModelViewSet):
    queryset = ItemGroup.objects.select_related("category").all()
    serializer_class = ItemGroupSerializer
    search_fields = ["name", "code"]
    filterset_fields = ["category"]
    ordering_fields = ["name", "created_at"]


class ItemViewSet(TenantModelViewSet):
    queryset = Item.objects.select_related("group", "group__category").all()
    serializer_class = ItemSerializer
    search_fields = ["name", "sku"]
    filterset_fields = ["group", "is_active"]
    ordering_fields = ["name", "created_at", "sku"]
