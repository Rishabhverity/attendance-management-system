from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta


class LeaveType(models.Model):
    """
    Master data for leave types (CL, SL, EL, LWP).
    """
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text='Leave type code (e.g., CL, SL, EL, LWP)'
    )
    name = models.CharField(
        max_length=50,
        help_text='Full name of leave type'
    )
    is_paid = models.BooleanField(
        default=True,
        help_text='Whether this leave type is paid'
    )
    requires_documentation = models.BooleanField(
        default=False,
        help_text='Whether attachment/documentation is required'
    )
    max_consecutive_days = models.IntegerField(
        null=True,
        blank=True,
        help_text='Maximum consecutive days allowed in one request'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of leave type'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_types'
        verbose_name = 'Leave Type'
        verbose_name_plural = 'Leave Types'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class LeaveBalance(models.Model):
    """
    Track leave balances per employee per leave type per year.
    """
    employee = models.ForeignKey(
        'employees.User',
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='balances'
    )
    year = models.IntegerField(
        help_text='Fiscal year (e.g., 2026)'
    )
    allocated = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text='Total allocated leave days'
    )
    used = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text='Leave days used'
    )
    adjusted = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text='Manual adjustments by admin'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_balances'
        verbose_name = 'Leave Balance'
        verbose_name_plural = 'Leave Balances'
        unique_together = ('employee', 'leave_type', 'year')
        ordering = ['employee', 'leave_type', '-year']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.code} - {self.year}"

    @property
    def available(self):
        """Calculate available balance."""
        return self.allocated + self.adjusted - self.used

    def deduct(self, days):
        """
        Deduct days from balance.
        Used when leave is approved.
        """
        days = Decimal(str(days))
        if self.leave_type.is_paid and (self.used + days) > (self.allocated + self.adjusted):
            raise ValidationError(f"Insufficient balance. Available: {self.available}, Requested: {days}")
        self.used += days
        self.save()

    def restore(self, days):
        """
        Restore days to balance.
        Used when leave is cancelled.
        """
        days = Decimal(str(days))
        self.used = max(Decimal('0'), self.used - days)
        self.save()

    def clean(self):
        """Validate that available balance is not negative for paid leaves."""
        if self.leave_type.is_paid and self.available < 0:
            raise ValidationError("Available balance cannot be negative for paid leaves.")


class LeaveRequest(models.Model):
    """
    Track leave applications and approval workflow.
    """

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )

    employee = models.ForeignKey(
        'employees.User',
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name='requests'
    )
    start_date = models.DateField(
        help_text='Leave start date'
    )
    end_date = models.DateField(
        help_text='Leave end date'
    )
    total_days = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        help_text='Total leave days (e.g., 1.5 for half-day)'
    )
    reason = models.TextField(
        help_text='Reason for leave'
    )
    attachment = models.FileField(
        upload_to='leave_attachments/',
        blank=True,
        null=True,
        help_text='Optional supporting document'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text='Current status of leave request'
    )
    applied_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the request was submitted'
    )
    approved_by = models.ForeignKey(
        'employees.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leave_approvals',
        help_text='Manager who approved/rejected'
    )
    decision_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the decision was made'
    )
    manager_comments = models.TextField(
        blank=True,
        help_text='Manager comments on approval/rejection'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_requests'
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.code} - {self.start_date} to {self.end_date}"

    def clean(self):
        """Validate leave request."""
        # Validate date range
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("Start date must be before or equal to end date.")

        # Check for overlapping leaves
        if self.employee_id:
            overlapping = LeaveRequest.objects.filter(
                employee=self.employee,
                status__in=['PENDING', 'APPROVED']
            ).exclude(pk=self.pk)

            if self.start_date and self.end_date:
                overlapping = overlapping.filter(
                    start_date__lte=self.end_date,
                    end_date__gte=self.start_date
                )

                if overlapping.exists():
                    raise ValidationError("Leave request overlaps with existing pending/approved leave.")

    def calculate_total_days(self):
        """
        Calculate working days between start and end date.
        Excludes holidays and weekends (configurable).
        For MVP, simple calculation based on date range.
        """
        if not self.start_date or not self.end_date:
            return Decimal('0')

        # Simple calculation: end_date - start_date + 1
        # In production, you'd exclude holidays and weekends
        delta = (self.end_date - self.start_date).days + 1
        return Decimal(str(delta))

    def can_cancel(self):
        """Check if leave request can be cancelled."""
        return self.status == 'PENDING'

    def approve(self, manager, comments=''):
        """
        Approve the leave request and update balance.
        """
        if self.status != 'PENDING':
            raise ValidationError("Only pending requests can be approved.")

        # Deduct from balance
        try:
            balance = LeaveBalance.objects.get(
                employee=self.employee,
                leave_type=self.leave_type,
                year=self.start_date.year
            )
            balance.deduct(self.total_days)
        except LeaveBalance.DoesNotExist:
            if self.leave_type.is_paid:
                raise ValidationError(f"No leave balance found for {self.leave_type.code} in {self.start_date.year}")

        self.status = 'APPROVED'
        self.approved_by = manager
        self.decision_at = timezone.now()
        self.manager_comments = comments
        self.save()

    def reject(self, manager, comments=''):
        """
        Reject the leave request (no balance change).
        """
        if self.status != 'PENDING':
            raise ValidationError("Only pending requests can be rejected.")

        self.status = 'REJECTED'
        self.approved_by = manager
        self.decision_at = timezone.now()
        self.manager_comments = comments
        self.save()

    def cancel(self):
        """
        Cancel the leave request.
        If already approved, restore balance.
        """
        if self.status == 'APPROVED':
            # Restore balance
            try:
                balance = LeaveBalance.objects.get(
                    employee=self.employee,
                    leave_type=self.leave_type,
                    year=self.start_date.year
                )
                balance.restore(self.total_days)
            except LeaveBalance.DoesNotExist:
                pass

        if self.status in ['PENDING', 'APPROVED']:
            self.status = 'CANCELLED'
            self.save()
        else:
            raise ValidationError("Only pending or approved requests can be cancelled.")
