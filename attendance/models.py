from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date


class Attendance(models.Model):
    """
    Track daily employee attendance (manual marking).
    Supports self-marking and admin corrections.
    """

    STATUS_CHOICES = (
        ('PRESENT', 'Present'),
        ('WFH', 'Work From Home'),
        ('HALF_DAY', 'Half Day'),
        ('ABSENT', 'Absent'),
    )

    employee = models.ForeignKey(
        'employees.User',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField(
        help_text='Attendance date'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PRESENT',
        help_text='Attendance status'
    )
    marked_by = models.ForeignKey(
        'employees.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='attendance_marked_by',
        help_text='User who marked attendance (self or admin)'
    )
    is_self_marked = models.BooleanField(
        default=True,
        help_text='True if employee marked, False if admin marked/corrected'
    )
    correction_reason = models.TextField(
        blank=True,
        help_text='Reason for admin correction'
    )
    marked_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When attendance was initially marked'
    )
    corrected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When admin corrected the attendance'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance'
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        unique_together = ('employee', 'date')
        ordering = ['-date', 'employee']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['employee', 'date']),
        ]

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date} - {self.status}"

    def clean(self):
        """Validate attendance record."""
        # Employees can only mark current date (business logic enforced in views)
        # Admin can mark any date (past or current)

        # Check if marking a holiday
        if Holiday.objects.filter(date=self.date).exists():
            raise ValidationError(f"Cannot mark attendance on a holiday: {self.date}")

    def mark_correction(self, admin_user, new_status, reason):
        """
        Admin correction of attendance.

        Args:
            admin_user: User making the correction (must be admin)
            new_status: New attendance status
            reason: Reason for correction
        """
        if not admin_user.is_admin_role():
            raise ValidationError("Only admins can correct attendance.")

        self.status = new_status
        self.marked_by = admin_user
        self.is_self_marked = False
        self.correction_reason = reason
        self.corrected_at = timezone.now()
        self.save()

    @classmethod
    def mark_for_employee(cls, employee, date_to_mark, status, marked_by):
        """
        Mark attendance for an employee.

        Args:
            employee: User object
            date_to_mark: Date to mark attendance
            status: Attendance status
            marked_by: User marking the attendance

        Returns:
            Attendance object
        """
        # Check if employee can mark this date
        if marked_by == employee and date_to_mark != date.today():
            raise ValidationError("Employees can only mark attendance for today.")

        is_self = (marked_by == employee)

        attendance, created = cls.objects.update_or_create(
            employee=employee,
            date=date_to_mark,
            defaults={
                'status': status,
                'marked_by': marked_by,
                'is_self_marked': is_self,
            }
        )
        return attendance


class Holiday(models.Model):
    """
    Organization-wide holiday calendar.
    Managed by admin/HR.
    """
    name = models.CharField(
        max_length=200,
        help_text='Holiday name (e.g., Independence Day)'
    )
    date = models.DateField(
        unique=True,
        help_text='Holiday date'
    )
    description = models.TextField(
        blank=True,
        help_text='Additional details about the holiday'
    )
    is_optional = models.BooleanField(
        default=False,
        help_text='Whether this is an optional holiday'
    )
    created_by = models.ForeignKey(
        'employees.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='holidays_created',
        help_text='Admin who created this holiday'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'holidays'
        verbose_name = 'Holiday'
        verbose_name_plural = 'Holidays'
        ordering = ['date']

    def __str__(self):
        return f"{self.name} - {self.date}"

    @classmethod
    def get_holidays_for_year(cls, year):
        """
        Get all holidays for a specific year.

        Args:
            year: Integer year (e.g., 2026)

        Returns:
            QuerySet of Holiday objects
        """
        return cls.objects.filter(
            date__year=year
        ).order_by('date')

    @classmethod
    def is_holiday(cls, check_date):
        """
        Check if a given date is a holiday.

        Args:
            check_date: Date object to check

        Returns:
            Boolean
        """
        return cls.objects.filter(date=check_date).exists()

    @classmethod
    def get_working_days_between(cls, start_date, end_date, include_weekends=True):
        """
        Calculate working days between two dates excluding holidays.

        Args:
            start_date: Start date
            end_date: End date
            include_weekends: Whether to count weekends as working days

        Returns:
            Integer count of working days
        """
        if start_date > end_date:
            return 0

        total_days = (end_date - start_date).days + 1
        holiday_count = cls.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).count()

        working_days = total_days - holiday_count

        # If not including weekends, subtract them
        if not include_weekends:
            from datetime import timedelta
            current = start_date
            weekend_count = 0
            while current <= end_date:
                if current.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    weekend_count += 1
                current += timedelta(days=1)
            working_days -= weekend_count

        return max(0, working_days)
