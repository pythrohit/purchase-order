from decimal import Decimal
from django.db import models
from django.db.models import Q
from common.models import TenantOwnedModel


class PurchaseOrder(TenantOwnedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        CANCELLED = "CANCELLED", "Cancelled"

    po_number = models.CharField(max_length=40)
    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.PROTECT, related_name="purchase_orders")
    order_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "po_number"], name="uniq_po_number_per_tenant"),
            models.CheckConstraint(
                condition=Q(expected_date__isnull=True) | Q(expected_date__gte=models.F("order_date")),
                name="po_expected_date_not_before_order_date",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant", "status", "order_date"]),
            models.Index(fields=["tenant", "vendor", "order_date"]),
        ]

    @property
    def total_amount(self):
        return sum(
            (line.quantity * line.unit_price for line in self.lines.all()),
            Decimal("0.00"),
        )

    def __str__(self):
        return self.po_number


class PurchaseOrderLine(TenantOwnedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey("inventory.Item", on_delete=models.PROTECT, related_name="purchase_order_lines")
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["purchase_order", "item"], name="uniq_item_per_purchase_order"),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="po_line_quantity_positive"),
            models.CheckConstraint(condition=Q(unit_price__gte=0), name="po_line_price_nonnegative"),
        ]
        indexes = [
            models.Index(fields=["tenant", "purchase_order"]),
            models.Index(fields=["tenant", "item"]),
        ]

    @property
    def line_total(self):
        return self.quantity * self.unit_price
