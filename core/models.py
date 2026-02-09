from django.db import models


class AuditLog(models.Model):
    """
    Track key actions for compliance and debugging.
    Logs critical operations like leave approvals, balance adjustments, etc.
    """

    ACTION_CHOICES = (
        ('LEAVE_APPROVED', 'Leave Approved'),
        ('LEAVE_REJECTED', 'Leave Rejected'),
        ('LEAVE_CANCELLED', 'Leave Cancelled'),
        ('BALANCE_ALLOCATED', 'Balance Allocated'),
        ('BALANCE_ADJUSTED', 'Balance Adjusted'),
        ('ATTENDANCE_MARKED', 'Attendance Marked'),
        ('ATTENDANCE_CORRECTED', 'Attendance Corrected'),
        ('EMPLOYEE_CREATED', 'Employee Created'),
        ('EMPLOYEE_UPDATED', 'Employee Updated'),
        ('EMPLOYEE_DEACTIVATED', 'Employee Deactivated'),
        ('EMPLOYEE_ACTIVATED', 'Employee Activated'),
        ('HOLIDAY_CREATED', 'Holiday Created'),
        ('HOLIDAY_UPDATED', 'Holiday Updated'),
        ('HOLIDAY_DELETED', 'Holiday Deleted'),
        ('OTHER', 'Other Action'),
    )

    user = models.ForeignKey(
        'employees.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        help_text='User who performed the action'
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text='Type of action performed'
    )
    model_name = models.CharField(
        max_length=50,
        help_text='Name of the model affected (e.g., LeaveRequest, Attendance)'
    )
    object_id = models.IntegerField(
        help_text='ID of the affected object'
    )
    description = models.TextField(
        help_text='Human-readable description of the action'
    )
    metadata = models.JSONField(
        blank=True,
        null=True,
        help_text='Additional data (old/new values, reasons, etc.)'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the user'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text='When the action was performed'
    )

    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        user_name = self.user.get_full_name() if self.user else 'System'
        return f"{user_name} - {self.get_action_display()} - {self.timestamp}"

    @classmethod
    def log_action(cls, user, action, model_name, object_id, description, metadata=None, ip_address=None):
        """
        Create an audit log entry.

        Args:
            user: User who performed the action
            action: Action type (from ACTION_CHOICES)
            model_name: Name of the model affected
            object_id: ID of the affected object
            description: Human-readable description
            metadata: Optional dict with additional data
            ip_address: Optional IP address

        Returns:
            AuditLog object
        """
        return cls.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            description=description,
            metadata=metadata or {},
            ip_address=ip_address
        )

    @classmethod
    def get_logs_for_object(cls, model_name, object_id):
        """
        Get all audit logs for a specific object.

        Args:
            model_name: Name of the model
            object_id: ID of the object

        Returns:
            QuerySet of AuditLog objects
        """
        return cls.objects.filter(
            model_name=model_name,
            object_id=object_id
        ).order_by('-timestamp')

    @classmethod
    def get_user_activity(cls, user, days=30):
        """
        Get recent activity for a user.

        Args:
            user: User object
            days: Number of days to look back

        Returns:
            QuerySet of AuditLog objects
        """
        from datetime import timedelta
        from django.utils import timezone

        cutoff_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(
            user=user,
            timestamp__gte=cutoff_date
        ).order_by('-timestamp')
