"""
Serializers for Core functionality.
Handles AuditLog and other core models.
"""

from rest_framework import serializers
from .models import AuditLog
from employees.serializers import UserBasicSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model."""
    user_details = UserBasicSerializer(source='user', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_details',
            'action', 'action_display',
            'model_name', 'object_id',
            'description', 'metadata',
            'ip_address', 'timestamp'
        ]
        read_only_fields = ['user', 'timestamp']


class DashboardSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    user = serializers.DictField()
    leave_balance_summary = serializers.ListField(child=serializers.DictField())
    pending_leave_requests = serializers.IntegerField()
    upcoming_leaves = serializers.ListField(child=serializers.DictField())
    attendance_this_month = serializers.DictField()
    upcoming_holidays = serializers.ListField(child=serializers.DictField())


class ManagerDashboardSerializer(serializers.Serializer):
    """Serializer for manager dashboard statistics."""
    team_size = serializers.IntegerField()
    pending_approvals = serializers.IntegerField()
    team_on_leave_today = serializers.IntegerField()
    team_attendance_today = serializers.DictField()
    upcoming_team_leaves = serializers.ListField(child=serializers.DictField())


class AdminDashboardSerializer(serializers.Serializer):
    """Serializer for admin dashboard statistics."""
    total_employees = serializers.IntegerField()
    active_employees = serializers.IntegerField()
    total_departments = serializers.IntegerField()
    stats = serializers.DictField()
    leave_utilization = serializers.DictField()
