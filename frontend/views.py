"""
Frontend views for HR Leave & Attendance Management System
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import calendar

from employees.models import User, EmployeeProfile
from leaves.models import LeaveType, LeaveBalance, LeaveRequest
from attendance.models import Attendance, Holiday


@login_required
def dashboard_view(request):
    """
    Role-based dashboard redirect
    """
    if request.user.role == 'ADMIN':
        return admin_dashboard(request)
    elif request.user.role == 'MANAGER':
        return manager_dashboard(request)
    else:
        return employee_dashboard(request)


def employee_dashboard(request):
    """
    Employee dashboard with leave balances and attendance stats
    """
    try:
        employee_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        # Create employee profile if it doesn't exist
        employee_profile = EmployeeProfile.objects.create(
            user=request.user,
            employee_id=request.user.employee_id
        )

    # Leave balances for current year
    current_year = timezone.now().year
    balances = LeaveBalance.objects.filter(
        employee=employee_profile,
        year=current_year
    ).select_related('leave_type')

    # Recent leave requests
    recent_leaves = LeaveRequest.objects.filter(
        employee=employee_profile
    ).select_related('leave_type').order_by('-created_at')[:5]

    # Pending leave requests count
    pending_leaves_count = LeaveRequest.objects.filter(
        employee=employee_profile,
        status='PENDING'
    ).count()

    # Attendance stats for current month
    today = timezone.now().date()
    attendance_stats = Attendance.objects.filter(
        employee=employee_profile,
        date__month=today.month,
        date__year=today.year
    ).aggregate(
        present=Count('id', filter=Q(status='PRESENT')),
        wfh=Count('id', filter=Q(status='WFH')),
        half_day=Count('id', filter=Q(status='HALF_DAY')),
        total=Count('id')
    )

    # Check if attendance marked today
    attendance_marked_today = Attendance.objects.filter(
        employee=employee_profile,
        date=today
    ).exists()

    # Upcoming holidays
    upcoming_holidays = Holiday.objects.filter(
        date__gte=today
    ).order_by('date')[:5]

    context = {
        'balances': balances,
        'recent_leaves': recent_leaves,
        'pending_leaves_count': pending_leaves_count,
        'attendance_stats': attendance_stats,
        'attendance_marked_today': attendance_marked_today,
        'upcoming_holidays': upcoming_holidays,
    }

    return render(request, 'frontend/dashboard/employee.html', context)


def manager_dashboard(request):
    """
    Manager dashboard with team stats
    """
    try:
        employee_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        employee_profile = EmployeeProfile.objects.create(
            user=request.user,
            employee_id=request.user.employee_id
        )

    # Get team members
    team_members = EmployeeProfile.objects.filter(
        reporting_manager=employee_profile
    ).select_related('user')

    # Pending approvals count
    pending_approvals = LeaveRequest.objects.filter(
        employee__reporting_manager=employee_profile,
        status='PENDING'
    ).count()

    # Team on leave today
    today = timezone.now().date()
    team_on_leave_today = LeaveRequest.objects.filter(
        employee__reporting_manager=employee_profile,
        status='APPROVED',
        start_date__lte=today,
        end_date__gte=today
    ).select_related('employee', 'leave_type')

    # Team attendance today
    team_attendance_today = Attendance.objects.filter(
        employee__reporting_manager=employee_profile,
        date=today
    ).aggregate(
        present=Count('id', filter=Q(status='PRESENT')),
        wfh=Count('id', filter=Q(status='WFH')),
        absent=Count('id', filter=Q(status='ABSENT'))
    )

    # Upcoming team leaves
    upcoming_team_leaves = LeaveRequest.objects.filter(
        employee__reporting_manager=employee_profile,
        status='APPROVED',
        start_date__gte=today
    ).select_related('employee', 'leave_type').order_by('start_date')[:5]

    context = {
        'team_size': team_members.count(),
        'pending_approvals': pending_approvals,
        'team_on_leave_today': team_on_leave_today,
        'team_attendance_today': team_attendance_today,
        'upcoming_team_leaves': upcoming_team_leaves,
    }

    return render(request, 'frontend/dashboard/manager.html', context)


def admin_dashboard(request):
    """
    Admin dashboard with organization-wide stats
    """
    today = timezone.now().date()

    # Employee stats
    total_employees = EmployeeProfile.objects.count()
    active_employees = EmployeeProfile.objects.filter(user__is_active=True).count()

    # Department and designation counts
    from employees.models import Department, Designation
    departments_count = Department.objects.count()
    designations_count = Designation.objects.count()

    # Employees on leave today
    employees_on_leave_today = LeaveRequest.objects.filter(
        status='APPROVED',
        start_date__lte=today,
        end_date__gte=today
    ).select_related('employee', 'leave_type')

    # Pending leave requests (org-wide)
    pending_leave_requests = LeaveRequest.objects.filter(
        status='PENDING'
    ).count()

    # Attendance marked today
    attendance_marked_today = Attendance.objects.filter(
        date=today
    ).count()

    # Leave utilization by type
    leave_utilization = LeaveBalance.objects.filter(
        year=today.year
    ).values('leave_type__name').annotate(
        total_allocated=Count('id'),
        total_used=Count('id')
    )

    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'departments_count': departments_count,
        'designations_count': designations_count,
        'employees_on_leave_today': employees_on_leave_today,
        'pending_leave_requests': pending_leave_requests,
        'attendance_marked_today': attendance_marked_today,
        'leave_utilization': leave_utilization,
    }

    return render(request, 'frontend/dashboard/admin.html', context)


# =============================================================================
# LEAVE MANAGEMENT VIEWS
# =============================================================================

@login_required
def apply_leave_view(request):
    """
    Apply for leave - Form submission with validation
    """
    try:
        employee_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        employee_profile = EmployeeProfile.objects.create(
            user=request.user,
            employee_id=request.user.employee_id
        )

    if request.method == 'POST':
        # Get form data
        leave_type_id = request.POST.get('leave_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')
        attachment = request.FILES.get('attachment')

        # Validation
        errors = []

        # Check required fields
        if not all([leave_type_id, start_date, end_date, reason]):
            errors.append('All fields are required.')

        try:
            leave_type = LeaveType.objects.get(id=leave_type_id)
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Validate date range
            if start_date_obj > end_date_obj:
                errors.append('End date must be after start date.')

            if start_date_obj < timezone.now().date():
                errors.append('Cannot apply for past dates.')

            # Calculate working days (excluding weekends and holidays)
            total_days = calculate_working_days(start_date_obj, end_date_obj)

            # Check leave balance (for paid leaves)
            if leave_type.is_paid:
                try:
                    leave_balance = LeaveBalance.objects.get(
                        employee=employee_profile,
                        leave_type=leave_type,
                        year=start_date_obj.year
                    )
                    available = leave_balance.allocated + leave_balance.adjusted - leave_balance.used

                    if total_days > available:
                        errors.append(f'Insufficient balance. Available: {available} days, Requested: {total_days} days.')
                except LeaveBalance.DoesNotExist:
                    errors.append('No leave balance found for this leave type.')

            # Check for overlapping leaves
            overlapping = LeaveRequest.objects.filter(
                employee=employee_profile,
                status__in=['PENDING', 'APPROVED']
            ).filter(
                Q(start_date__lte=end_date_obj, end_date__gte=start_date_obj)
            ).exists()

            if overlapping:
                errors.append('You already have a leave request for overlapping dates.')

            # If no errors, create leave request
            if not errors:
                leave_request = LeaveRequest.objects.create(
                    employee=employee_profile,
                    leave_type=leave_type,
                    start_date=start_date_obj,
                    end_date=end_date_obj,
                    total_days=total_days,
                    reason=reason,
                    attachment=attachment,
                    status='PENDING'
                )

                messages.success(request, f'Leave application submitted successfully! Request ID: {leave_request.id}')

                # Return HTMX response
                if request.headers.get('HX-Request'):
                    return HttpResponse(
                        '<div class="alert alert-success" role="alert">'
                        f'Leave application submitted successfully! Request ID: {leave_request.id}'
                        '</div>',
                        status=200
                    )

                return redirect('frontend:my_leaves')

        except LeaveType.DoesNotExist:
            errors.append('Invalid leave type selected.')
        except ValueError as e:
            errors.append(f'Invalid date format: {str(e)}')

        # Return errors for HTMX request
        if request.headers.get('HX-Request') and errors:
            error_html = '<div class="alert alert-danger" role="alert"><ul class="mb-0">'
            for error in errors:
                error_html += f'<li>{error}</li>'
            error_html += '</ul></div>'
            return HttpResponse(error_html, status=400)

        # Add errors to messages for regular request
        for error in errors:
            messages.error(request, error)

    # GET request - show form
    leave_types = LeaveType.objects.all()
    current_year = timezone.now().year
    balances = LeaveBalance.objects.filter(
        employee=employee_profile,
        year=current_year
    ).select_related('leave_type')

    context = {
        'leave_types': leave_types,
        'balances': balances,
    }

    return render(request, 'frontend/leaves/apply.html', context)


def calculate_working_days(start_date, end_date):
    """
    Calculate working days between two dates (excluding weekends and holidays)
    """
    working_days = 0
    current_date = start_date

    # Get holidays in the date range
    holidays = Holiday.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).values_list('date', flat=True)

    while current_date <= end_date:
        # Check if not a weekend (0 = Monday, 6 = Sunday)
        if current_date.weekday() < 5:  # Monday to Friday
            # Check if not a holiday
            if current_date not in holidays:
                working_days += 1
        current_date += timedelta(days=1)

    return working_days


@login_required
def my_leaves_view(request):
    """
    Display employee's leave requests with filter options
    """
    try:
        employee_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        employee_profile = EmployeeProfile.objects.create(
            user=request.user,
            employee_id=request.user.employee_id
        )

    # Get filter parameters
    status_filter = request.GET.get('status', 'ALL')
    year_filter = request.GET.get('year', str(timezone.now().year))

    # Base query
    leave_requests = LeaveRequest.objects.filter(
        employee=employee_profile
    ).select_related('leave_type', 'approved_by')

    # Apply status filter
    if status_filter != 'ALL':
        leave_requests = leave_requests.filter(status=status_filter)

    # Apply year filter
    if year_filter != 'ALL':
        leave_requests = leave_requests.filter(start_date__year=year_filter)

    # Order by most recent first
    leave_requests = leave_requests.order_by('-created_at')

    # Get distinct years for filter dropdown
    years = LeaveRequest.objects.filter(
        employee=employee_profile
    ).dates('start_date', 'year').distinct()

    context = {
        'leave_requests': leave_requests,
        'status_filter': status_filter,
        'year_filter': year_filter,
        'years': [date.year for date in years],
    }

    return render(request, 'frontend/leaves/my_leaves.html', context)


@login_required
@require_http_methods(["POST"])
def cancel_leave_request(request, leave_id):
    """
    Cancel a pending leave request (HTMX endpoint)
    """
    try:
        employee_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Employee profile not found.'
        }, status=400)

    try:
        leave_request = LeaveRequest.objects.get(
            id=leave_id,
            employee=employee_profile
        )

        # Can only cancel PENDING requests
        if leave_request.status != 'PENDING':
            return JsonResponse({
                'success': False,
                'message': f'Cannot cancel {leave_request.status.lower()} leave request.'
            }, status=400)

        # Update status to CANCELLED
        leave_request.status = 'CANCELLED'
        leave_request.save()

        # Return success response for HTMX
        if request.headers.get('HX-Request'):
            # Return updated table row
            html = f'''
            <tr id="leave-row-{leave_request.id}" class="table-secondary">
                <td>{leave_request.leave_type.name}</td>
                <td>{leave_request.start_date.strftime('%b %d, %Y')}</td>
                <td>{leave_request.end_date.strftime('%b %d, %Y')}</td>
                <td>{leave_request.total_days}</td>
                <td><span class="badge badge-cancelled">Cancelled</span></td>
                <td>-</td>
                <td>-</td>
            </tr>
            '''
            return HttpResponse(html)

        return JsonResponse({
            'success': True,
            'message': 'Leave request cancelled successfully.'
        })

    except LeaveRequest.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Leave request not found.'
        }, status=404)


# =============================================================================
# ATTENDANCE MANAGEMENT VIEWS
# =============================================================================

@login_required
def mark_attendance_view(request):
    """
    Mark attendance for today
    """
    try:
        employee_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        employee_profile = EmployeeProfile.objects.create(
            user=request.user,
            employee_id=request.user.employee_id
        )

    today = timezone.now().date()

    # Check if attendance already marked today
    existing_attendance = Attendance.objects.filter(
        employee=employee_profile,
        date=today
    ).first()

    # Check if today is a holiday
    is_holiday = Holiday.objects.filter(date=today).first()

    # Check if on approved leave today
    on_leave = LeaveRequest.objects.filter(
        employee=employee_profile,
        status='APPROVED',
        start_date__lte=today,
        end_date__gte=today
    ).first()

    if request.method == 'POST':
        status = request.POST.get('status')

        if not status or status not in ['PRESENT', 'WFH', 'HALF_DAY', 'ABSENT']:
            messages.error(request, 'Invalid attendance status.')
            return redirect('frontend:mark_attendance')

        # If already marked, update it
        if existing_attendance:
            if not existing_attendance.is_self_marked:
                messages.warning(request, 'Attendance was marked by admin. Cannot update.')
                return redirect('frontend:mark_attendance')

            existing_attendance.status = status
            existing_attendance.marked_at = timezone.now()
            existing_attendance.save()
            messages.success(request, f'Attendance updated successfully to {status}!')
        else:
            # Create new attendance record
            Attendance.objects.create(
                employee=employee_profile,
                date=today,
                status=status,
                marked_by=request.user,
                is_self_marked=True
            )
            messages.success(request, f'Attendance marked as {status}!')

        # HTMX response
        if request.headers.get('HX-Request'):
            return HttpResponse(
                f'<div class="alert alert-success" role="alert">'
                f'<i class="bi bi-check-circle"></i> Attendance marked as {status}!'
                f'</div>',
                status=200
            )

        return redirect('frontend:mark_attendance')

    # Get attendance history for current month
    attendance_history = Attendance.objects.filter(
        employee=employee_profile,
        date__month=today.month,
        date__year=today.year
    ).order_by('-date')

    # Monthly stats
    monthly_stats = Attendance.objects.filter(
        employee=employee_profile,
        date__month=today.month,
        date__year=today.year
    ).aggregate(
        present=Count('id', filter=Q(status='PRESENT')),
        wfh=Count('id', filter=Q(status='WFH')),
        half_day=Count('id', filter=Q(status='HALF_DAY')),
        absent=Count('id', filter=Q(status='ABSENT')),
        total=Count('id')
    )

    context = {
        'existing_attendance': existing_attendance,
        'is_holiday': is_holiday,
        'on_leave': on_leave,
        'attendance_history': attendance_history,
        'monthly_stats': monthly_stats,
        'today': today,
    }

    return render(request, 'frontend/attendance/mark.html', context)


@login_required
def my_attendance_view(request):
    """
    Display monthly attendance calendar view
    """
    try:
        employee_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        employee_profile = EmployeeProfile.objects.create(
            user=request.user,
            employee_id=request.user.employee_id
        )

    # Get month and year from query params or default to current month
    today = timezone.now().date()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))

    # Get calendar for selected month
    cal = calendar.monthcalendar(selected_year, selected_month)

    # Get all attendance for the month
    attendance_records = Attendance.objects.filter(
        employee=employee_profile,
        date__month=selected_month,
        date__year=selected_year
    ).select_related('marked_by')

    # Create attendance dict for easy lookup
    attendance_dict = {att.date: att for att in attendance_records}

    # Get holidays for the month
    holidays = Holiday.objects.filter(
        date__month=selected_month,
        date__year=selected_year
    )
    holiday_dict = {holiday.date: holiday for holiday in holidays}

    # Get leaves for the month
    leaves = LeaveRequest.objects.filter(
        employee=employee_profile,
        status='APPROVED',
        start_date__year=selected_year,
        start_date__month__lte=selected_month,
        end_date__month__gte=selected_month
    ).select_related('leave_type')

    # Create calendar data structure
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                date_obj = datetime(selected_year, selected_month, day).date()
                day_info = {
                    'day': day,
                    'date': date_obj,
                    'is_today': date_obj == today,
                    'is_weekend': date_obj.weekday() >= 5,  # Saturday or Sunday
                    'is_holiday': date_obj in holiday_dict,
                    'holiday': holiday_dict.get(date_obj),
                    'attendance': attendance_dict.get(date_obj),
                    'is_on_leave': False,
                }

                # Check if on leave
                for leave in leaves:
                    if leave.start_date <= date_obj <= leave.end_date:
                        day_info['is_on_leave'] = True
                        day_info['leave'] = leave
                        break

                week_data.append(day_info)
        calendar_data.append(week_data)

    # Monthly stats
    monthly_stats = Attendance.objects.filter(
        employee=employee_profile,
        date__month=selected_month,
        date__year=selected_year
    ).aggregate(
        present=Count('id', filter=Q(status='PRESENT')),
        wfh=Count('id', filter=Q(status='WFH')),
        half_day=Count('id', filter=Q(status='HALF_DAY')),
        absent=Count('id', filter=Q(status='ABSENT')),
        total=Count('id')
    )

    # Navigation months
    current_date = datetime(selected_year, selected_month, 1).date()
    prev_month = (current_date.replace(day=1) - timedelta(days=1))
    next_month_first = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)

    context = {
        'calendar_data': calendar_data,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': calendar.month_name[selected_month],
        'monthly_stats': monthly_stats,
        'prev_month': prev_month.month,
        'prev_year': prev_month.year,
        'next_month': next_month_first.month,
        'next_year': next_month_first.year,
        'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    }

    return render(request, 'frontend/attendance/calendar.html', context)


# =============================================================================
# PROFILE AND SETTINGS VIEWS
# =============================================================================

@login_required
def profile_view(request):
    """
    View and edit user profile
    """
    try:
        employee_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        employee_profile = EmployeeProfile.objects.create(
            user=request.user,
            employee_id=request.user.employee_id
        )

    if request.method == 'POST':
        # Update profile fields
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')

        # Update User model
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()

        # Update EmployeeProfile model
        employee_profile.phone_number = phone_number
        employee_profile.save()

        messages.success(request, 'Profile updated successfully!')

        # HTMX response
        if request.headers.get('HX-Request'):
            return HttpResponse(
                '<div class="alert alert-success" role="alert">'
                '<i class="bi bi-check-circle"></i> Profile updated successfully!'
                '</div>',
                status=200
            )

        return redirect('frontend:profile')

    context = {
        'employee_profile': employee_profile,
    }

    return render(request, 'frontend/profile/profile.html', context)


@login_required
def change_password_view(request):
    """
    Change user password
    """
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        errors = []

        # Validate old password
        if not request.user.check_password(old_password):
            errors.append('Current password is incorrect.')

        # Validate new password
        if new_password != confirm_password:
            errors.append('New passwords do not match.')

        if len(new_password) < 8:
            errors.append('Password must be at least 8 characters long.')

        # If no errors, change password
        if not errors:
            request.user.set_password(new_password)
            request.user.save()

            # Update session to prevent logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)

            messages.success(request, 'Password changed successfully!')

            # HTMX response
            if request.headers.get('HX-Request'):
                return HttpResponse(
                    '<div class="alert alert-success" role="alert">'
                    '<i class="bi bi-check-circle"></i> Password changed successfully!'
                    '</div>',
                    status=200
                )

            return redirect('frontend:profile')

        # Return errors
        if request.headers.get('HX-Request'):
            error_html = '<div class="alert alert-danger" role="alert"><ul class="mb-0">'
            for error in errors:
                error_html += f'<li>{error}</li>'
            error_html += '</ul></div>'
            return HttpResponse(error_html, status=400)

        for error in errors:
            messages.error(request, error)

    return render(request, 'frontend/profile/change_password.html')



