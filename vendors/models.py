from django.db import models
from common.models import TenantOwnedModel


class Vendor(TenantOwnedModel):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=25, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code"], name="uniq_vendor_code_per_tenant")
        ]
        indexes = [models.Index(fields=["tenant", "is_active"])]

    def __str__(self):
        return self.name
