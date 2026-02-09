from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmployeeProfile, Department, Designation


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'employee_id', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'employee_id')
    ordering = ('employee_id',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('employee_id', 'role')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('employee_id', 'role')}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_at')
    search_fields = ('title',)


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'designation', 'reporting_manager', 'is_active')
    list_filter = ('is_active', 'department', 'designation')
    search_fields = ('user__first_name', 'user__last_name', 'user__employee_id')
    raw_id_fields = ('user', 'reporting_manager')
