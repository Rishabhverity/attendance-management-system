"""
Custom permission classes for role-based access control (RBAC).
Implements permissions for Employee, Manager, and Admin roles.
"""

from rest_framework import permissions


class IsEmployee(permissions.BasePermission):
    """
    Permission class for Employee role.
    Allows access to own records only.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated and has Employee role."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'EMPLOYEE'
        )

    def has_object_permission(self, request, view, obj):
        """Check if user can access the specific object (own data only)."""
        # Check if object has an employee field
        if hasattr(obj, 'employee'):
            return obj.employee == request.user
        # Check if object is the user themselves
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # For User objects
        return obj == request.user


class IsManager(permissions.BasePermission):
    """
    Permission class for Manager role.
    Allows access to own data and direct reports' data.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated and has Manager role."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'MANAGER'
        )

    def has_object_permission(self, request, view, obj):
        """Check if user can access the specific object (own or team member's data)."""
        # Manager can access their own data
        if hasattr(obj, 'employee'):
            if obj.employee == request.user:
                return True
            # Check if employee reports to this manager
            if hasattr(obj.employee, 'profile') and obj.employee.profile.reporting_manager == request.user:
                return True

        if hasattr(obj, 'user'):
            if obj.user == request.user:
                return True
            # Check if user reports to this manager
            if hasattr(obj.user, 'profile') and obj.user.profile.reporting_manager == request.user:
                return True

        # For User objects
        if obj == request.user:
            return True
        if hasattr(obj, 'profile') and obj.profile.reporting_manager == request.user:
            return True

        return False


class IsAdmin(permissions.BasePermission):
    """
    Permission class for Admin/HR role.
    Allows full access to all resources.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated and has Admin role."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )

    def has_object_permission(self, request, view, obj):
        """Admin has access to all objects."""
        return True


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows:
    - Read access to all authenticated users
    - Write access only to Admin users
    """

    def has_permission(self, request, view):
        """Check permissions based on request method."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Read permissions (GET, HEAD, OPTIONS) for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for Admin
        return request.user.role == 'ADMIN'


class IsOwnerOrManager(permissions.BasePermission):
    """
    Permission class that allows:
    - User to access their own records
    - Manager to access direct reports' records
    - Admin to access all records
    """

    def has_permission(self, request, view):
        """All authenticated users can make requests."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user can access the specific object."""
        user = request.user

        # Admin has full access
        if user.role == 'ADMIN':
            return True

        # Check if accessing own data
        if hasattr(obj, 'employee') and obj.employee == user:
            return True
        if hasattr(obj, 'user') and obj.user == user:
            return True
        if obj == user:
            return True

        # Check if manager accessing team member's data
        if user.role == 'MANAGER':
            if hasattr(obj, 'employee'):
                employee_profile = getattr(obj.employee, 'profile', None)
                if employee_profile and employee_profile.reporting_manager == user:
                    return True

            if hasattr(obj, 'user'):
                user_profile = getattr(obj.user, 'profile', None)
                if user_profile and user_profile.reporting_manager == user:
                    return True

            if hasattr(obj, 'profile'):
                if obj.profile.reporting_manager == user:
                    return True

        return False


class CanApproveLeave(permissions.BasePermission):
    """
    Permission class for leave approval.
    Only managers can approve leaves of their direct reports.
    Admins can approve any leave.
    """

    def has_permission(self, request, view):
        """Check if user can approve leaves."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['MANAGER', 'ADMIN']
        )

    def has_object_permission(self, request, view, obj):
        """Check if user can approve this specific leave request."""
        user = request.user

        # Admin can approve any leave
        if user.role == 'ADMIN':
            return True

        # Manager can approve only if they are the reporting manager
        if user.role == 'MANAGER':
            employee_profile = getattr(obj.employee, 'profile', None)
            if employee_profile and employee_profile.reporting_manager == user:
                return True

        return False


class CanCorrectAttendance(permissions.BasePermission):
    """
    Permission class for attendance correction.
    Only Admin can correct attendance.
    """

    def has_permission(self, request, view):
        """Check if user can correct attendance."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )
