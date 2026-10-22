from django.db import models
from common.models import TenantOwnedModel


class Category(TenantOwnedModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=40)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code"], name="uniq_category_code_per_tenant")
        ]
        indexes = [models.Index(fields=["tenant", "name"])]

    def __str__(self):
        return self.name


class ItemGroup(TenantOwnedModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="groups")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=40)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code"], name="uniq_item_group_code_per_tenant")
        ]
        indexes = [models.Index(fields=["tenant", "category"])]

    def __str__(self):
        return self.name


class Item(TenantOwnedModel):
    group = models.ForeignKey(ItemGroup, on_delete=models.PROTECT, related_name="items")
    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=64)
    unit = models.CharField(max_length=20, default="pcs")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "sku"], name="uniq_item_sku_per_tenant")
        ]
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["tenant", "group"]),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"
