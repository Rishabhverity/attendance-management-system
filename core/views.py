"""
Views for Reports, Dashboard, and Audit Log APIs.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count,Q, Sum
from django.http import HttpResponse
from datetime import date, datetime
from calendar import monthrange
import csv

from .models import AuditLog
from .serializers import AuditLogSerializer, DashboardSerializer, ManagerDashboardSerializer, AdminDashboardSerializer
from employees.models import User, EmployeeProfile, Department
from leaves.models import LeaveRequest, LeaveBalance, LeaveType
from attendance.models import Attendance, Holiday
from core.permissions import IsAdmin


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for AuditLog (read-only, admin only).
    """
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        """Filter audit logs based on query parameters."""
        queryset = self.queryset

        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        user = self.request.query_params.get('user')
        if user:
            queryset = queryset.filter(user_id=user)

        date_filter = self.request.query_params.get('date')
        if date_filter:
            queryset = queryset.filter(timestamp__date=date_filter)

        model_name = self.request.query_params.get('model_name')
        if model_name:
            queryset = queryset.filter(model_name=model_name)

        return queryset.order_by('-timestamp')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    """
    Get dashboard statistics based on user role.
    GET /api/dashboard/
    """
    user = request.user
    current_year = datetime.now().year

    # Get leave balances
    balances = LeaveBalance.objects.filter(
        employee=user,
        year=current_year
    ).select_related('leave_type')

    leave_balance_summary = [
        {'type': b.leave_type.code, 'available': float(b.available)}
        for b in balances
    ]

    # Get pending leave requests
    pending_count = LeaveRequest.objects.filter(
        employee=user,
        status='PENDING'
    ).count()

    # Get upcoming leaves
    upcoming = LeaveRequest.objects.filter(
        employee=user,
        status='APPROVED',
        start_date__gte=date.today()
    ).select_related('leave_type').order_by('start_date')[:5]

    upcoming_leaves = [
        {
            'start_date': leave.start_date,
            'end_date': leave.end_date,
            'leave_type': leave.leave_type.code,
            'status': leave.status
        }
        for leave in upcoming
    ]

    # Get attendance this month
    current_month = date.today().month
    attendance_stats = Attendance.objects.filter(
        employee=user,
        date__month=current_month,
        date__year=current_year
    ).values('status').annotate(count=Count('id'))

    attendance_this_month = {stat['status']: stat['count'] for stat in attendance_stats}

    # Get upcoming holidays
    upcoming_holidays = Holiday.objects.filter(
        date__gte=date.today()
    ).order_by('date')[:5]

    upcoming_holidays_list = [
        {'name': h.name, 'date': h.date}
        for h in upcoming_holidays
    ]

    data = {
        'user': {
            'name': user.get_full_name(),
            'role': user.role
        },
        'leave_balance_summary': leave_balance_summary,
        'pending_leave_requests': pending_count,
        'upcoming_leaves': upcoming_leaves,
        'attendance_this_month': attendance_this_month,
        'upcoming_holidays': upcoming_holidays_list
    }

    serializer = DashboardSerializer(data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def manager_dashboard_view(request):
    """
    Get manager dashboard with team statistics.
    GET /api/dashboard/manager/
    """
    user = request.user

    if user.role not in ['MANAGER', 'ADMIN']:
        return Response(
            {'error': 'Only managers and admins can access this dashboard.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Get team members
    if user.role == 'MANAGER':
        team_members = User.objects.filter(
            profile__reporting_manager=user,
            profile__is_active=True
        )
    else:
        team_members = User.objects.filter(profile__is_active=True)

    team_size = team_members.count()

    # Get pending approvals
    pending_approvals = LeaveRequest.objects.filter(
        employee__in=team_members,
        status='PENDING'
    ).count()

    # Get team on leave today
    team_on_leave = LeaveRequest.objects.filter(
        employee__in=team_members,
        status='APPROVED',
        start_date__lte=date.today(),
        end_date__gte=date.today()
    ).count()

    # Get team attendance today
    today_attendance = Attendance.objects.filter(
        employee__in=team_members,
        date=date.today()
    ).values('status').annotate(count=Count('id'))

    attendance_today = {stat['status']: stat['count'] for stat in today_attendance}
    attendance_today['on_leave'] = team_on_leave

    # Get upcoming team leaves
    upcoming_leaves = LeaveRequest.objects.filter(
        employee__in=team_members,
        status='APPROVED',
        start_date__gte=date.today()
    ).select_related('employee', 'leave_type').order_by('start_date')[:10]

    upcoming_team_leaves = [
        {
            'employee': leave.employee.get_full_name(),
            'start_date': leave.start_date,
            'end_date': leave.end_date,
            'leave_type': leave.leave_type.code
        }
        for leave in upcoming_leaves
    ]

    data = {
        'team_size': team_size,
        'pending_approvals': pending_approvals,
        'team_on_leave_today': team_on_leave,
        'team_attendance_today': attendance_today,
        'upcoming_team_leaves': upcoming_team_leaves
    }

    serializer = ManagerDashboardSerializer(data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_dashboard_view(request):
    """
    Get admin dashboard with organization-wide statistics.
    GET /api/dashboard/admin/
    """
    current_year = datetime.now().year

    # Get employee counts
    total_employees = User.objects.filter(role__in=['EMPLOYEE', 'MANAGER']).count()
    active_employees = User.objects.filter(
        role__in=['EMPLOYEE', 'MANAGER'],
        profile__is_active=True
    ).count()

    # Get department count
    total_departments = Department.objects.count()

    # Get today's stats
    employees_on_leave = LeaveRequest.objects.filter(
        status='APPROVED',
        start_date__lte=date.today(),
        end_date__gte=date.today()
    ).count()

    pending_requests = LeaveRequest.objects.filter(status='PENDING').count()

    attendance_today = Attendance.objects.filter(date=date.today()).count()

    stats = {
        'employees_on_leave_today': employees_on_leave,
        'pending_leave_requests': pending_requests,
        'attendance_marked_today': attendance_today,
        'attendance_pending_today': active_employees - attendance_today - employees_on_leave
    }

    # Get leave utilization
    leave_types = LeaveType.objects.all()
    leave_utilization = {}

    for lt in leave_types:
        balances = LeaveBalance.objects.filter(
            leave_type=lt,
            year=current_year
        ).aggregate(
            total_allocated=Sum('allocated'),
            total_used=Sum('used')
        )

        total_allocated = float(balances['total_allocated'] or 0)
        total_used = float(balances['total_used'] or 0)
        percentage = (total_used / total_allocated * 100) if total_allocated > 0 else 0

        leave_utilization[lt.code] = {
            'allocated': total_allocated,
            'used': total_used,
            'percentage': round(percentage, 1)
        }

    data = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'total_departments': total_departments,
        'stats': stats,
        'leave_utilization': leave_utilization
    }

    serializer = AdminDashboardSerializer(data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leave_summary_report(request):
    """
    Generate monthly leave summary report.
    GET /api/reports/leave-summary/?month=2&year=2026
    """
    user = request.user

    # Get month and year
    month = int(request.query_params.get('month', date.today().month))
    year = int(request.query_params.get('year', date.today().year))

    # Determine which employees to include based on role
    if user.role == 'EMPLOYEE':
        employees = [user]
    elif user.role == 'MANAGER':
        team_members = User.objects.filter(
            profile__reporting_manager=user,
            profile__is_active=True
        )
        employees = list(team_members) + [user]
    else:
        # Admin can filter by employee or department
        employees = User.objects.filter(profile__is_active=True)

        employee_id = request.query_params.get('employee')
        if employee_id:
            employees = employees.filter(id=employee_id)

        department_id = request.query_params.get('department')
        if department_id:
            employees = employees.filter(profile__department_id=department_id)

    # Get leave requests for the month
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    summary = []
    for emp in employees:
        leave_requests = LeaveRequest.objects.filter(
            employee=emp,
            start_date__lte=last_day,
            end_date__gte=first_day
        ).select_related('leave_type')

        # Breakdown by leave type
        leave_breakdown = {}
        for lt in LeaveType.objects.all():
            requests = leave_requests.filter(leave_type=lt)
            leave_breakdown[lt.code] = {
                'applied': requests.count(),
                'approved': requests.filter(status='APPROVED').count(),
                'rejected': requests.filter(status='REJECTED').count(),
                'pending': requests.filter(status='PENDING').count()
            }

        total_leaves = sum(
            float(lr.total_days) for lr in leave_requests.filter(status='APPROVED')
        )

        summary.append({
            'employee': {
                'id': emp.id,
                'name': emp.get_full_name(),
                'employee_id': emp.employee_id,
                'department': emp.profile.department.name if hasattr(emp, 'profile') and emp.profile.department else None
            },
            'leave_breakdown': leave_breakdown,
            'total_leaves_taken': total_leaves
        })

    return Response({
        'month': month,
        'year': year,
        'summary': summary
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_summary_report(request):
    """
    Generate monthly attendance summary report.
    GET /api/reports/attendance-summary/?month=2&year=2026
    """
    user = request.user

    # Get month and year
    month = int(request.query_params.get('month', date.today().month))
    year = int(request.query_params.get('year', date.today().year))

    # Determine which employees to include
    if user.role == 'EMPLOYEE':
        employees = [user]
    elif user.role == 'MANAGER':
        team_members = User.objects.filter(
            profile__reporting_manager=user,
            profile__is_active=True
        )
        employees = list(team_members) + [user]
    else:
        employees = User.objects.filter(profile__is_active=True)

        employee_id = request.query_params.get('employee')
        if employee_id:
            employees = employees.filter(id=employee_id)

        department_id = request.query_params.get('department')
        if department_id:
            employees = employees.filter(profile__department_id=department_id)

    # Calculate working days
    _, total_days = monthrange(year, month)
    holidays = Holiday.objects.filter(date__month=month, date__year=year).count()
    total_working_days = total_days - holidays

    summary = []
    for emp in employees:
        # Get attendance records
        attendance_records = Attendance.objects.filter(
            employee=emp,
            date__month=month,
            date__year=year
        ).values('status').annotate(count=Count('id'))

        attendance_stats = {stat['status']: stat['count'] for stat in attendance_records}

        # Get approved leaves
        first_day = date(year, month, 1)
        last_day = date(year, month, total_days)
        on_leave = LeaveRequest.objects.filter(
            employee=emp,
            status='APPROVED',
            start_date__lte=last_day,
            end_date__gte=first_day
        ).aggregate(total=Sum('total_days'))['total'] or 0

        present_days = attendance_stats.get('PRESENT', 0)
        wfh_days = attendance_stats.get('WFH', 0)
        half_days = attendance_stats.get('HALF_DAY', 0)
        absent_days = total_working_days - present_days - wfh_days - half_days - int(on_leave)

        attendance_percentage = ((present_days + wfh_days + half_days * 0.5) / total_working_days * 100) if total_working_days > 0 else 0

        summary.append({
            'employee_id': emp.employee_id,
            'employee_name': emp.get_full_name(),
            'department': emp.profile.department.name if hasattr(emp, 'profile') and emp.profile.department else None,
            'present_days': present_days,
            'wfh_days': wfh_days,
            'half_days': half_days,
            'absent_days': max(0, absent_days),
            'on_leave': int(on_leave),
            'holidays': holidays,
            'total_working_days': total_working_days,
            'attendance_percentage': round(attendance_percentage, 2)
        })

    return Response({
        'month': month,
        'year': year,
        'total_working_days': total_working_days,
        'summary': summary
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_leave_summary_csv(request):
    """
    Export leave summary as CSV.
    GET /api/reports/leave-summary/export/?month=2&year=2026
    """
    # Get the report data
    report_data = leave_summary_report(request)
    data = report_data.data

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="leave_summary_{data["month"]}_{data["year"]}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Employee ID', 'Employee Name', 'Department', 'Leave Type', 'Applied', 'Approved', 'Rejected', 'Pending', 'Total Leaves Taken'])

    for emp_summary in data['summary']:
        emp = emp_summary['employee']
        for leave_type, breakdown in emp_summary['leave_breakdown'].items():
            writer.writerow([
                emp['employee_id'],
                emp['name'],
                emp['department'] or 'N/A',
                leave_type,
                breakdown['applied'],
                breakdown['approved'],
                breakdown['rejected'],
                breakdown['pending'],
                emp_summary['total_leaves_taken']
            ])

    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_attendance_summary_csv(request):
    """
    Export attendance summary as CSV.
    GET /api/reports/attendance-summary/export/?month=2&year=2026
    """
    # Get the report data
    report_data = attendance_summary_report(request)
    data = report_data.data

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_summary_{data["month"]}_{data["year"]}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Employee ID', 'Employee Name', 'Department',
        'Present Days', 'WFH Days', 'Half Days', 'Absent Days',
        'On Leave', 'Holidays', 'Total Working Days', 'Attendance %'
    ])

    for emp_summary in data['summary']:
        writer.writerow([
            emp_summary['employee_id'],
            emp_summary['employee_name'],
            emp_summary['department'] or 'N/A',
            emp_summary['present_days'],
            emp_summary['wfh_days'],
            emp_summary['half_days'],
            emp_summary['absent_days'],
            emp_summary['on_leave'],
            emp_summary['holidays'],
            emp_summary['total_working_days'],
            f"{emp_summary['attendance_percentage']:.2f}%"
        ])

    return response
