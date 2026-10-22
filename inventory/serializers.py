from rest_framework import serializers
from .models import Category, ItemGroup, Item


class TenantScopedRelatedFieldMixin:
    def validate_related_tenant(self, obj):
        request = self.context.get("request")
        if request is None:
            return obj
        from common.tenancy import get_request_tenant
        if obj.tenant_id != get_request_tenant(request).id:
            raise serializers.ValidationError("Related object belongs to another tenant.")
        return obj


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "code", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ItemGroupSerializer(serializers.ModelSerializer, TenantScopedRelatedFieldMixin):
    class Meta:
        model = ItemGroup
        fields = ["id", "category", "name", "code", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_category(self, value):
        return self.validate_related_tenant(value)


class ItemSerializer(serializers.ModelSerializer, TenantScopedRelatedFieldMixin):
    class Meta:
        model = Item
        fields = ["id", "group", "name", "sku", "unit", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_group(self, value):
        return self.validate_related_tenant(value)
