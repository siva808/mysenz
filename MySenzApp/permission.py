from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    """
    Custom permission to only allow users with role 'admin' or 'SUPERADMIN'.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check role
        return request.user.role in ["admin", "SUPERADMIN"]
