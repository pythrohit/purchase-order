from rest_framework.exceptions import PermissionDenied, ValidationError
from common.models import Tenant, TenantMembership


def get_request_tenant(request):
    if not request.user or not request.user.is_authenticated:
        raise PermissionDenied("Authentication is required.")

    raw_tenant_id = request.headers.get("X-Tenant-ID")
    if not raw_tenant_id:
        raise ValidationError({"X-Tenant-ID": "This header is required."})

    try:
        tenant_id = int(raw_tenant_id)
    except (TypeError, ValueError):
        raise ValidationError({"X-Tenant-ID": "Must be a valid tenant ID."})

    membership_exists = TenantMembership.objects.filter(
        user=request.user, tenant_id=tenant_id, is_active=True, tenant__is_active=True
    ).exists()
    if not membership_exists:
        raise PermissionDenied("You do not have access to this tenant.")

    return Tenant.objects.get(pk=tenant_id, is_active=True)

