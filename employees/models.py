from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds role-based access control and employee ID.
    """

    ROLE_CHOICES = (
        ('EMPLOYEE', 'Employee'),
        ('MANAGER', 'Manager'),
        ('ADMIN', 'Admin/HR'),
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='EMPLOYEE',
        help_text='User role for access control'
    )
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        help_text='Unique employee identifier'
    )

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.employee_id})" if self.get_full_name() else self.username

    def is_employee(self):
        return self.role == 'EMPLOYEE'

    def is_manager(self):
        return self.role == 'MANAGER'

    def is_admin_role(self):
        return self.role == 'ADMIN'


class Department(models.Model):
    """
    Master data for organizational departments.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Department name'
    )
    description = models.TextField(
        blank=True,
        help_text='Department description'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'departments'
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering = ['name']

    def __str__(self):
        return self.name


class Designation(models.Model):
    """
    Master data for job titles/designations.
    """
    title = models.CharField(
        max_length=100,
        unique=True,
        help_text='Designation title'
    )
    description = models.TextField(
        blank=True,
        help_text='Role description'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'designations'
        verbose_name = 'Designation'
        verbose_name_plural = 'Designations'
        ordering = ['title']

    def __str__(self):
        return self.title


class EmployeeProfile(models.Model):
    """
    Extended employee information beyond authentication.
    One-to-one relationship with User model.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='profile'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        help_text='Employee department'
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        help_text='Employee designation'
    )
    reporting_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_members',
        help_text='Direct reporting manager'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Is employee active? (soft delete)'
    )
    date_of_joining = models.DateField(
        null=True,
        blank=True,
        help_text='Date of joining the organization'
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        help_text='Contact phone number'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee_profiles'
        verbose_name = 'Employee Profile'
        verbose_name_plural = 'Employee Profiles'

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def clean(self):
        """Validate that reporting manager is not self."""
        if self.reporting_manager and self.reporting_manager == self.user:
            raise ValidationError("An employee cannot be their own reporting manager.")

    def get_team_members(self):
        """Get all direct reports (if user is a manager)."""
        if self.user.is_manager() or self.user.is_admin_role():
            return EmployeeProfile.objects.filter(
                reporting_manager=self.user,
                is_active=True
            )
        return EmployeeProfile.objects.none()
