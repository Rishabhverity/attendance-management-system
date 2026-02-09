"""
Serializers for Leave Management.
Handles LeaveType, LeaveBalance, and LeaveRequest models.
"""

from rest_framework import serializers
from django.utils import timezone
from .models import LeaveType, LeaveBalance, LeaveRequest
from employees.serializers import UserBasicSerializer


class LeaveTypeSerializer(serializers.ModelSerializer):
    """Serializer for LeaveType model."""

    class Meta:
        model = LeaveType
        fields = [
            'id', 'code', 'name', 'is_paid',
            'requires_documentation', 'max_consecutive_days',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class LeaveBalanceSerializer(serializers.ModelSerializer):
    """Serializer for LeaveBalance model."""
    employee_details = UserBasicSerializer(source='employee', read_only=True)
    leave_type_details = LeaveTypeSerializer(source='leave_type', read_only=True)
    available = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)

    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'employee', 'employee_details',
            'leave_type', 'leave_type_details',
            'year', 'allocated', 'used', 'adjusted', 'available',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'used']

    def validate(self, attrs):
        """Validate leave balance."""
        # Check if balance already exists for this employee, leave type, and year
        employee = attrs.get('employee')
        leave_type = attrs.get('leave_type')
        year = attrs.get('year')

        if self.instance is None:  # Creating new balance
            if LeaveBalance.objects.filter(employee=employee, leave_type=leave_type, year=year).exists():
                raise serializers.ValidationError(
                    f"Leave balance already exists for {employee.get_full_name()} - {leave_type.code} - {year}"
                )

        return attrs


class LeaveBalanceSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for leave balance (for dashboard/summary views)."""
    leave_type_code = serializers.CharField(source='leave_type.code', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    available = serializers.DecimalField(max_digits=5, decimal_places=1, read_only=True)

    class Meta:
        model = LeaveBalance
        fields = ['id', 'leave_type_code', 'leave_type_name', 'year', 'allocated', 'used', 'adjusted', 'available']


class LeaveRequestSerializer(serializers.ModelSerializer):
    """Serializer for LeaveRequest model."""
    employee_details = UserBasicSerializer(source='employee', read_only=True)
    leave_type_details = LeaveTypeSerializer(source='leave_type', read_only=True)
    approved_by_details = UserBasicSerializer(source='approved_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_details',
            'leave_type', 'leave_type_details',
            'start_date', 'end_date', 'total_days', 'reason', 'attachment',
            'status', 'status_display',
            'applied_at', 'approved_by', 'approved_by_details',
            'decision_at', 'manager_comments',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'employee', 'status', 'applied_at',
            'approved_by', 'decision_at', 'manager_comments',
            'created_at', 'updated_at'
        ]

    def validate(self, attrs):
        """Validate leave request."""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        leave_type = attrs.get('leave_type')
        total_days = attrs.get('total_days')

        # Validate dates
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})

        # Get employee from context (will be set in view)
        employee = self.context.get('employee') or self.context['request'].user

        # Check for overlapping leaves (only when creating)
        if self.instance is None:
            overlapping = LeaveRequest.objects.filter(
                employee=employee,
                status__in=['PENDING', 'APPROVED'],
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            if overlapping.exists():
                raise serializers.ValidationError(
                    "Leave request overlaps with existing pending/approved leave."
                )

        # Check leave balance for paid leaves
        if leave_type and leave_type.is_paid and total_days:
            try:
                balance = LeaveBalance.objects.get(
                    employee=employee,
                    leave_type=leave_type,
                    year=start_date.year
                )
                if balance.available < total_days:
                    raise serializers.ValidationError(
                        f"Insufficient leave balance. Available: {balance.available}, Requested: {total_days}"
                    )
            except LeaveBalance.DoesNotExist:
                raise serializers.ValidationError(
                    f"No leave balance found for {leave_type.code} in {start_date.year}"
                )

        return attrs

    def create(self, validated_data):
        """Create leave request with employee from context."""
        validated_data['employee'] = self.context['request'].user
        validated_data['status'] = 'PENDING'
        return super().create(validated_data)


class LeaveRequestListSerializer(serializers.ModelSerializer):
    """Simplified serializer for leave request list views."""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    leave_type_code = serializers.CharField(source='leave_type.code', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee_name', 'employee_id',
            'leave_type_code', 'leave_type_name',
            'start_date', 'end_date', 'total_days',
            'status', 'status_display', 'applied_at'
        ]


class LeaveApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting leave requests."""
    comments = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Validate that leave request can be approved/rejected."""
        leave_request = self.context['leave_request']

        if leave_request.status != 'PENDING':
            raise serializers.ValidationError("Only pending leave requests can be approved or rejected.")

        return attrs

    def save(self, **kwargs):
        """This will be called from the view after validation."""
        pass


class LeaveCancellationSerializer(serializers.Serializer):
    """Serializer for cancelling leave requests."""

    def validate(self, attrs):
        """Validate that leave request can be cancelled."""
        leave_request = self.context['leave_request']
        user = self.context['request'].user

        # Only the employee who created the request can cancel it
        if leave_request.employee != user:
            raise serializers.ValidationError("You can only cancel your own leave requests.")

        # Can only cancel pending or approved requests
        if leave_request.status not in ['PENDING', 'APPROVED']:
            raise serializers.ValidationError("Only pending or approved leave requests can be cancelled.")

        return attrs


class TeamLeaveCalendarSerializer(serializers.Serializer):
    """Serializer for team leave calendar view."""
    employee_id = serializers.CharField()
    employee_name = serializers.CharField()
    leave_type_code = serializers.CharField()
    leave_type_name = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_days = serializers.DecimalField(max_digits=4, decimal_places=1)
    status = serializers.CharField()
