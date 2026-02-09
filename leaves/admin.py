from django.contrib import admin
from .models import LeaveType, LeaveBalance, LeaveRequest


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_paid', 'requires_documentation')
    list_filter = ('is_paid', 'requires_documentation')
    search_fields = ('code', 'name')


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'allocated', 'used', 'available')
    list_filter = ('year', 'leave_type')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    raw_id_fields = ('employee',)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'total_days', 'status', 'applied_at')
    list_filter = ('status', 'leave_type', 'applied_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'reason')
    raw_id_fields = ('employee', 'approved_by')
    readonly_fields = ('applied_at', 'decision_at')
    ordering = ('-applied_at',)
