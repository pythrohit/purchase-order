from rest_framework import permissions, viewsets
from common.permissions import get_request_tenant


class TenantModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    tenant_field = "tenant"

    def get_tenant(self):
        if not hasattr(self, "_request_tenant"):
            self._request_tenant = get_request_tenant(self.request)
        return self._request_tenant

    def get_queryset(self):
        return super().get_queryset().filter(tenant=self.get_tenant())

    def perform_create(self, serializer):
        serializer.save(tenant=self.get_tenant())
