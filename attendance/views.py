"""
Views for Attendance Management APIs.
Handles Attendance and Holiday endpoints.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from datetime import date, datetime, timedelta
from calendar import monthrange

from .models import Attendance, Holiday
from .serializers import (
    AttendanceSerializer, AttendanceListSerializer,
    AttendanceMarkSerializer, AttendanceCorrectionSerializer,
    MonthlyAttendanceSerializer, AttendanceSummarySerializer,
    HolidaySerializer
)
from employees.models import EmployeeProfile, User
from leaves.models import LeaveRequest
from core.permissions import IsAdmin, IsOwnerOrManager, IsAdminOrReadOnly, CanCorrectAttendance
from core.models import AuditLog


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Attendance management.
    Employees can mark own attendance, admins can mark/correct any.
    """
    queryset = Attendance.objects.select_related('employee', 'marked_by').all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return AttendanceListSerializer
        return AttendanceSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy', 'correct']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        queryset = self.queryset

        if user.role == 'EMPLOYEE':
            # Employees see only their own attendance
            queryset = queryset.filter(employee=user)
        elif user.role == 'MANAGER':
            # Managers see their own and team members' attendance
            team_member_ids = EmployeeProfile.objects.filter(
                reporting_manager=user
            ).values_list('user_id', flat=True)
            queryset = queryset.filter(Q(employee=user) | Q(employee_id__in=team_member_ids))
        # Admin sees all

        # Apply filters
        date_filter = self.request.query_params.get('date')
        if date_filter:
            queryset = queryset.filter(date=date_filter)

        employee = self.request.query_params.get('employee')
        if employee and user.role in ['MANAGER', 'ADMIN']:
            queryset = queryset.filter(employee_id=employee)

        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-date')

    def create(self, request, *args, **kwargs):
        """
        Mark attendance.
        Employees can only mark for today, admins can mark for any date.
        """
        # For employees marking own attendance (simplified)
        if request.user.role == 'EMPLOYEE' and 'date' not in request.data:
            serializer = AttendanceMarkSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                # Create attendance for today
                attendance = Attendance.mark_for_employee(
                    employee=request.user,
                    date_to_mark=date.today(),
                    status=serializer.validated_data['status'],
                    marked_by=request.user
                )
                response_serializer = AttendanceSerializer(attendance, context={'request': request})
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # For admin marking attendance with date
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_attendance(self, request):
        """
        Get current user's attendance records.
        GET /api/attendance/my-attendance/
        """
        # Get month and year from query params, default to current month
        month = int(request.query_params.get('month', date.today().month))
        year = int(request.query_params.get('year', date.today().year))

        attendance_records = Attendance.objects.filter(
            employee=request.user,
            date__month=month,
            date__year=year
        ).order_by('date')

        serializer = AttendanceSerializer(attendance_records, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def monthly(self, request):
        """
        Get monthly attendance view with all days.
        Shows attendance, leaves, and holidays.
        GET /api/attendance/monthly/?month=2&year=2026
        """
        # Get month and year
        month = int(request.query_params.get('month', date.today().month))
        year = int(request.query_params.get('year', date.today().year))

        # Get employee (self or specified if manager/admin)
        employee_id = request.query_params.get('employee')
        if employee_id:
            if request.user.role == 'EMPLOYEE':
                return Response(
                    {'error': 'You can only view your own attendance.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            try:
                employee = User.objects.get(id=employee_id)
                # Check if manager has permission
                if request.user.role == 'MANAGER':
                    if not hasattr(employee, 'profile') or employee.profile.reporting_manager != request.user:
                        return Response(
                            {'error': 'You can only view your team members\' attendance.'},
                            status=status.HTTP_403_FORBIDDEN
                        )
            except User.DoesNotExist:
                return Response(
                    {'error': 'Employee not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            employee = request.user

        # Get attendance records
        attendance_dict = {}
        attendance_records = Attendance.objects.filter(
            employee=employee,
            date__month=month,
            date__year=year
        )
        for att in attendance_records:
            attendance_dict[att.date.day] = att

        # Get holidays
        holidays_dict = {}
        holidays = Holiday.objects.filter(date__month=month, date__year=year)
        for holiday in holidays:
            holidays_dict[holiday.date.day] = holiday

        # Get approved leaves
        leaves = LeaveRequest.objects.filter(
            employee=employee,
            status='APPROVED',
            start_date__lte=date(year, month, monthrange(year, month)[1]),
            end_date__gte=date(year, month, 1)
        )

        # Build response for each day of the month
        _, num_days = monthrange(year, month)
        result = []

        for day in range(1, num_days + 1):
            current_date = date(year, month, day)
            day_data = {
                'date': current_date,
                'status': None,
                'is_holiday': False,
                'holiday_name': None,
                'is_self_marked': None,
                'correction_reason': ''
            }

            # Check if it's a holiday
            if day in holidays_dict:
                day_data['is_holiday'] = True
                day_data['holiday_name'] = holidays_dict[day].name
                day_data['status'] = 'HOLIDAY'

            # Check if on leave
            elif any(leave.start_date <= current_date <= leave.end_date for leave in leaves):
                day_data['status'] = 'ON_LEAVE'

            # Check attendance
            elif day in attendance_dict:
                att = attendance_dict[day]
                day_data['status'] = att.status
                day_data['is_self_marked'] = att.is_self_marked
                day_data['correction_reason'] = att.correction_reason

            # Future date or not marked
            elif current_date > date.today():
                day_data['status'] = 'FUTURE'
            else:
                day_data['status'] = 'ABSENT'

            result.append(day_data)

        serializer = MonthlyAttendanceSerializer(result, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, CanCorrectAttendance])
    def correct(self, request, pk=None):
        """
        Correct attendance (admin only).
        PATCH /api/attendance/{id}/correct/
        """
        attendance = self.get_object()

        serializer = AttendanceCorrectionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                attendance.mark_correction(
                    admin_user=request.user,
                    new_status=serializer.validated_data['status'],
                    reason=serializer.validated_data['correction_reason']
                )

                # Log correction
                AuditLog.log_action(
                    user=request.user,
                    action='ATTENDANCE_CORRECTED',
                    model_name='Attendance',
                    object_id=attendance.id,
                    description=f"Corrected attendance for {attendance.employee.get_full_name()} on {attendance.date}",
                    metadata={
                        'employee_id': attendance.employee.employee_id,
                        'date': str(attendance.date),
                        'new_status': serializer.validated_data['status'],
                        'reason': serializer.validated_data['correction_reason']
                    }
                )

                response_serializer = AttendanceSerializer(attendance, context={'request': request})
                return Response(response_serializer.data)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HolidayViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Holiday management.
    All authenticated users can read, only admins can write.
    """
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        """Filter holidays based on query parameters."""
        queryset = self.queryset

        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(date__year=year)

        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(date__month=month)

        is_optional = self.request.query_params.get('is_optional')
        if is_optional is not None:
            is_optional_bool = is_optional.lower() == 'true'
            queryset = queryset.filter(is_optional=is_optional_bool)

        return queryset.order_by('date')

    @action(detail=False, methods=['get'], url_path='year/(?P<year>[0-9]{4})')
    def year_holidays(self, request, year=None):
        """
        Get all holidays for a specific year.
        GET /api/holidays/year/{year}/
        """
        holidays = Holiday.get_holidays_for_year(int(year))
        serializer = HolidaySerializer(holidays, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Log holiday creation."""
        instance = serializer.save()
        AuditLog.log_action(
            user=self.request.user,
            action='HOLIDAY_CREATED',
            model_name='Holiday',
            object_id=instance.id,
            description=f"Created holiday: {instance.name} on {instance.date}",
            metadata={
                'name': instance.name,
                'date': str(instance.date)
            }
        )

    def perform_destroy(self, instance):
        """Log holiday deletion."""
        AuditLog.log_action(
            user=self.request.user,
            action='HOLIDAY_DELETED',
            model_name='Holiday',
            object_id=instance.id,
            description=f"Deleted holiday: {instance.name} on {instance.date}",
            metadata={
                'name': instance.name,
                'date': str(instance.date)
            }
        )
        instance.delete()
