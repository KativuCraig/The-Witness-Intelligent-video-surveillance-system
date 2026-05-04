from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'


class IsSecurity(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'SECURITY'


class IsViewer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'VIEWER'


class IsAdminOrSecurity(BasePermission):
    """Allow access to users with role ADMIN or SECURITY."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['ADMIN', 'SECURITY']
