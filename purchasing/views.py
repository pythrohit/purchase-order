from django.db.models import Prefetch
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from common.views import TenantModelViewSet
from .models import PurchaseOrder, PurchaseOrderLine
from .serializers import PurchaseOrderSerializer


class PurchaseOrderViewSet(TenantModelViewSet):
    queryset = PurchaseOrder.objects.select_related("vendor").prefetch_related(
        Prefetch(
            "lines",
            queryset=PurchaseOrderLine.objects.select_related("item").order_by("id"),
        )
    )
    serializer_class = PurchaseOrderSerializer
    search_fields = ["po_number", "vendor__name"]
    filterset_fields = ["status", "vendor"]
    ordering_fields = ["order_date", "created_at", "po_number"]

    def perform_destroy(self, instance):
        if instance.status != PurchaseOrder.Status.DRAFT:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Only draft purchase orders can be deleted.")
        instance.delete()

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        order = self.get_object()
        if order.status != PurchaseOrder.Status.DRAFT:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Only draft purchase orders can be submitted.")
        if not order.lines.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("A purchase order must contain at least one line.")
        order.status = PurchaseOrder.Status.SUBMITTED
        order.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(order).data, status=status.HTTP_200_OK)
