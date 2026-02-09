from django.contrib import admin
from .models import Attendance, Holiday


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status', 'is_self_marked', 'marked_by', 'marked_at')
    list_filter = ('status', 'is_self_marked', 'date')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    raw_id_fields = ('employee', 'marked_by')
    readonly_fields = ('marked_at', 'corrected_at')
    ordering = ('-date',)


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'is_optional', 'created_by')
    list_filter = ('is_optional', 'date')
    search_fields = ('name',)
    readonly_fields = ('created_by', 'created_at')
    ordering = ('date',)
