"""
Serializers for Attendance Management.
Handles Attendance and Holiday models.
"""

from rest_framework import serializers
from datetime import date
from django.utils import timezone
from .models import Attendance, Holiday
from employees.serializers import UserBasicSerializer


class HolidaySerializer(serializers.ModelSerializer):
    """Serializer for Holiday model."""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Holiday
        fields = [
            'id', 'name', 'date', 'description', 'is_optional',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create holiday with created_by from request user."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance model."""
    employee_details = UserBasicSerializer(source='employee', read_only=True)
    marked_by_details = UserBasicSerializer(source='marked_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'employee', 'employee_details',
            'date', 'status', 'status_display',
            'marked_by', 'marked_by_details',
            'is_self_marked', 'correction_reason',
            'marked_at', 'corrected_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'employee', 'marked_by', 'is_self_marked',
            'marked_at', 'corrected_at',
            'created_at', 'updated_at'
        ]

    def validate_date(self, value):
        """Validate attendance date based on user role."""
        user = self.context['request'].user

        # Employees can only mark today's attendance
        if user.role == 'EMPLOYEE' and value != date.today():
            raise serializers.ValidationError("Employees can only mark attendance for today.")

        # Check if it's a holiday
        if Holiday.objects.filter(date=value).exists():
            holiday = Holiday.objects.get(date=value)
            raise serializers.ValidationError(f"Cannot mark attendance on holiday: {holiday.name}")

        return value

    def validate(self, attrs):
        """Validate attendance record."""
        date_value = attrs.get('date')
        employee = self.context.get('employee') or self.context['request'].user

        # Check for duplicate attendance (only when creating)
        if self.instance is None:
            if Attendance.objects.filter(employee=employee, date=date_value).exists():
                raise serializers.ValidationError(
                    f"Attendance already marked for {date_value}"
                )

        return attrs

    def create(self, validated_data):
        """Create attendance record."""
        user = self.context['request'].user
        validated_data['employee'] = self.context.get('employee') or user
        validated_data['marked_by'] = user
        validated_data['is_self_marked'] = (validated_data['employee'] == user)
        return super().create(validated_data)


class AttendanceMarkSerializer(serializers.Serializer):
    """Serializer for marking own attendance (simplified for employees)."""
    status = serializers.ChoiceField(choices=['PRESENT', 'WFH', 'HALF_DAY', 'ABSENT'])

    def validate(self, attrs):
        """Validate attendance marking."""
        user = self.context['request'].user
        today = date.today()

        # Check if already marked today
        if Attendance.objects.filter(employee=user, date=today).exists():
            raise serializers.ValidationError("Attendance already marked for today.")

        # Check if it's a holiday
        if Holiday.objects.filter(date=today).exists():
            holiday = Holiday.objects.get(date=today)
            raise serializers.ValidationError(f"Cannot mark attendance on holiday: {holiday.name}")

        return attrs


class AttendanceCorrectionSerializer(serializers.Serializer):
    """Serializer for admin attendance correction."""
    status = serializers.ChoiceField(choices=['PRESENT', 'WFH', 'HALF_DAY', 'ABSENT'])
    correction_reason = serializers.CharField(required=True)

    def validate_correction_reason(self, value):
        """Ensure correction reason is provided."""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("Correction reason must be at least 5 characters long.")
        return value


class AttendanceListSerializer(serializers.ModelSerializer):
    """Simplified serializer for attendance list views."""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    employee_id = serializers.CharField(source='employee.employee_id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'employee_name', 'employee_id',
            'date', 'status', 'status_display',
            'is_self_marked', 'marked_at'
        ]


class MonthlyAttendanceSerializer(serializers.Serializer):
    """Serializer for monthly attendance view."""
    date = serializers.DateField()
    status = serializers.CharField()
    is_holiday = serializers.BooleanField(default=False)
    holiday_name = serializers.CharField(required=False, allow_null=True)
    is_self_marked = serializers.BooleanField(required=False)
    correction_reason = serializers.CharField(required=False, allow_blank=True)


class AttendanceSummarySerializer(serializers.Serializer):
    """Serializer for attendance summary reports."""
    employee_id = serializers.CharField()
    employee_name = serializers.CharField()
    department = serializers.CharField()
    present_days = serializers.IntegerField()
    wfh_days = serializers.IntegerField()
    half_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    on_leave = serializers.IntegerField()
    holidays = serializers.IntegerField()
    total_working_days = serializers.IntegerField()
    attendance_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
