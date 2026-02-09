from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model."""

    list_display = ('user', 'action', 'model_name', 'object_id', 'timestamp', 'ip_address')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'description', 'object_id')
    raw_id_fields = ('user',)
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'description', 'metadata', 'ip_address', 'timestamp')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Action Details', {
            'fields': ('user', 'action', 'timestamp', 'ip_address')
        }),
        ('Affected Object', {
            'fields': ('model_name', 'object_id', 'description')
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation of audit logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs."""
        return False
