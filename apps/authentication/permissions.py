from rest_framework.permissions import BasePermission

class IsTenantUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'tenant_id') and
            request.user.tenant_id is not None
        )

class IsTenantAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'tenant_id') and
            request.user.tenant_id is not None and
            request.user.role in ['admin', 'super_admin']
        )

class HasTenantPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'tenant_id') or request.user.tenant_id is None:
            return False
        
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True
        
        from .models import UserPermission
        return UserPermission.objects.filter(
            user=request.user,
            resource=required_permission.get('resource'),
            action=required_permission.get('action'),
            tenant_id=request.user.tenant_id
        ).exists()