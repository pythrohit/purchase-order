from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from common.permissions import get_request_tenant
from inventory.models import Item
from vendors.models import Vendor
from .models import PurchaseOrder, PurchaseOrderLine


class PurchaseOrderLineInputSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal("0.001"))
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.00"))


class PurchaseOrderLineReadSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    item_sku = serializers.CharField(source="item.sku", read_only=True)
    line_total = serializers.DecimalField(max_digits=24, decimal_places=5, read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = ["id", "item", "item_name", "item_sku", "quantity", "unit_price", "line_total"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    vendor = serializers.PrimaryKeyRelatedField(queryset=Vendor.objects.all())
    lines = PurchaseOrderLineInputSerializer(many=True, write_only=True, allow_empty=False)
    line_items = PurchaseOrderLineReadSerializer(source="lines", many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "po_number", "vendor", "order_date", "expected_date",
            "status", "notes", "lines", "line_items", "total_amount",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        if request is None:
            return attrs
        tenant = get_request_tenant(request)

        vendor = attrs.get("vendor")
        if vendor and (vendor.tenant_id != tenant.id or not vendor.is_active):
            raise serializers.ValidationError({"vendor": "Vendor must be active and belong to this tenant."})

        lines = attrs.get("lines")
        if lines is not None:
            item_ids = [line["item"].id for line in lines]
            if len(item_ids) != len(set(item_ids)):
                raise serializers.ValidationError({"lines": "Each item can appear only once; combine its quantity."})
            items = Item.objects.filter(
                tenant=tenant, is_active=True, id__in=item_ids
            ).values_list("id", flat=True)
            valid_ids = set(items)
            if valid_ids != set(item_ids):
                raise serializers.ValidationError({"lines": "Every item must be active and belong to this tenant."})

        order_date = attrs.get("order_date")
        expected_date = attrs.get("expected_date")
        if order_date and expected_date and expected_date < order_date:
            raise serializers.ValidationError({"expected_date": "Expected date cannot be before order date."})
        return attrs

    def get_total_amount(self, obj):
        # Prefetch lines in viewset to avoid an N+1 query pattern.
        total = sum(
            (line.quantity * line.unit_price for line in obj.lines.all()),
            Decimal("0.00"),
        )
        return str(total.quantize(Decimal("0.01")))

    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        request = self.context["request"]
        tenant = get_request_tenant(request)
        order = PurchaseOrder.objects.create(tenant=tenant, **validated_data)
        PurchaseOrderLine.objects.bulk_create([
            PurchaseOrderLine(
                tenant=tenant,
                purchase_order=order,
                item=line["item"],
                quantity=line["quantity"],
                unit_price=line["unit_price"],
            )
            for line in lines_data
        ])
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        # Submitted/approved orders are immutable through this endpoint.
        if instance.status != PurchaseOrder.Status.DRAFT:
            raise serializers.ValidationError("Only draft purchase orders can be edited.")

        lines_data = validated_data.pop("lines", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if lines_data is not None:
            request = self.context["request"]
            tenant = get_request_tenant(request)
            item_ids = [line["item"].id for line in lines_data]
            if len(item_ids) != len(set(item_ids)):
                raise serializers.ValidationError({"lines": "Each item can appear only once."})
            valid_ids = set(Item.objects.filter(
                tenant=tenant, is_active=True, id__in=item_ids
            ).values_list("id", flat=True))
            if valid_ids != set(item_ids):
                raise serializers.ValidationError({"lines": "Every item must be active and belong to this tenant."})

            instance.lines.all().delete()
            PurchaseOrderLine.objects.bulk_create([
                PurchaseOrderLine(
                    tenant=tenant, purchase_order=instance,
                    item=line["item"], quantity=line["quantity"],
                    unit_price=line["unit_price"],
                )
                for line in lines_data
            ])
        return instance
