from common.views import TenantModelViewSet
from .models import Vendor
from .serializers import VendorSerializer


class VendorViewSet(TenantModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    search_fields = ["name", "code", "email"]
    filterset_fields = ["is_active"]
    ordering_fields = ["name", "created_at"]
