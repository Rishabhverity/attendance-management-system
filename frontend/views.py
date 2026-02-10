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
        employee=request.user,
        year=current_year
    ).select_related('leave_type')

    # Recent leave requests
    recent_leaves = LeaveRequest.objects.filter(
        employee=request.user
    ).select_related('leave_type').order_by('-created_at')[:5]

    # Pending leave requests count
    pending_leaves_count = LeaveRequest.objects.filter(
        employee=request.user,
        status='PENDING'
    ).count()

    # Attendance stats for current month
    today = timezone.now().date()
    attendance_stats = Attendance.objects.filter(
        employee=request.user,
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
        employee=request.user,
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

    # Get team members (those who report to this manager)
    team_members = EmployeeProfile.objects.filter(
        reporting_manager=request.user
    ).select_related('user')

    # Pending approvals count
    pending_approvals = LeaveRequest.objects.filter(
        employee__profile__reporting_manager=request.user,
        status='PENDING'
    ).count()

    # Team on leave today
    today = timezone.now().date()
    team_on_leave_today = LeaveRequest.objects.filter(
        employee__profile__reporting_manager=request.user,
        status='APPROVED',
        start_date__lte=today,
        end_date__gte=today
    ).select_related('employee', 'leave_type')

    # Team attendance today
    team_attendance_today = Attendance.objects.filter(
        employee__profile__reporting_manager=request.user,
        date=today
    ).aggregate(
        present=Count('id', filter=Q(status='PRESENT')),
        wfh=Count('id', filter=Q(status='WFH')),
        absent=Count('id', filter=Q(status='ABSENT'))
    )

    # Upcoming team leaves
    upcoming_team_leaves = LeaveRequest.objects.filter(
        employee__profile__reporting_manager=request.user,
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
                        employee=request.user,
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
                employee=request.user,
                status__in=['PENDING', 'APPROVED']
            ).filter(
                Q(start_date__lte=end_date_obj, end_date__gte=start_date_obj)
            ).exists()

            if overlapping:
                errors.append('You already have a leave request for overlapping dates.')

            # If no errors, create leave request
            if not errors:
                leave_request = LeaveRequest.objects.create(
                    employee=request.user,
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
        employee=request.user,
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
        employee=request.user
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
        employee=request.user
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
            employee=request.user
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
        employee=request.user,
        date=today
    ).first()

    # Check if today is a holiday
    is_holiday = Holiday.objects.filter(date=today).first()

    # Check if on approved leave today
    on_leave = LeaveRequest.objects.filter(
        employee=request.user,
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
                employee=request.user,
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
        employee=request.user,
        date__month=today.month,
        date__year=today.year
    ).order_by('-date')

    # Monthly stats
    monthly_stats = Attendance.objects.filter(
        employee=request.user,
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
        employee=request.user,
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
        employee=request.user,
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
        employee=request.user,
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


# =============================================================================
# MANAGER VIEWS - Leave Approvals
# =============================================================================

@login_required
def leave_approvals_view(request):
    """
    Manager view for pending leave approvals from team members
    """
    # Check if user is manager or admin
    if request.user.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('frontend:dashboard')

    try:
        employee_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        employee_profile = EmployeeProfile.objects.create(
            user=request.user,
            employee_id=request.user.employee_id
        )

    # Get filter parameters
    status_filter = request.GET.get('status', 'PENDING')
    employee_filter = request.GET.get('employee', 'ALL')

    # Base query - get leave requests from team members
    if request.user.role == 'ADMIN':
        # Admin can see all leave requests
        leave_requests = LeaveRequest.objects.all()
    else:
        # Manager can only see their team's leave requests
        leave_requests = LeaveRequest.objects.filter(
            employee__profile__reporting_manager=request.user
        )

    # Apply status filter
    if status_filter != 'ALL':
        leave_requests = leave_requests.filter(status=status_filter)

    # Apply employee filter
    if employee_filter != 'ALL':
        leave_requests = leave_requests.filter(employee_id=employee_filter)

    # Select related for performance
    leave_requests = leave_requests.select_related(
        'employee',
        'employee__profile',
        'leave_type',
        'approved_by'
    ).order_by('-created_at')

    # Get team members for filter dropdown
    if request.user.role == 'ADMIN':
        team_members = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    else:
        team_members = User.objects.filter(
            profile__reporting_manager=request.user,
            is_active=True
        ).order_by('first_name', 'last_name')

    # Calculate stats
    stats = {
        'pending': leave_requests.filter(status='PENDING').count() if status_filter == 'ALL' else None,
        'approved': leave_requests.filter(status='APPROVED').count() if status_filter == 'ALL' else None,
        'rejected': leave_requests.filter(status='REJECTED').count() if status_filter == 'ALL' else None,
        'total': leave_requests.count(),
    }

    context = {
        'leave_requests': leave_requests,
        'status_filter': status_filter,
        'employee_filter': employee_filter,
        'team_members': team_members,
        'stats': stats,
    }

    return render(request, 'frontend/manager/leave_approvals.html', context)


@login_required
@require_http_methods(["POST"])
def approve_leave_request(request, leave_id):
    """
    Approve a leave request (Manager/Admin only)
    """
    # Check if user is manager or admin
    if request.user.role not in ['MANAGER', 'ADMIN']:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to approve leave requests.'
        }, status=403)

    try:
        employee_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Profile not found.'
        }, status=400)

    comments = request.POST.get('comments', '')

    try:
        # Get the leave request
        if request.user.role == 'ADMIN':
            leave_request = LeaveRequest.objects.get(id=leave_id)
        else:
            # Manager can only approve their team's requests
            leave_request = LeaveRequest.objects.get(
                id=leave_id,
                employee__profile__reporting_manager=request.user
            )

        # Can only approve PENDING requests
        if leave_request.status != 'PENDING':
            return JsonResponse({
                'success': False,
                'message': f'Cannot approve {leave_request.status.lower()} leave request.'
            }, status=400)

        # Approve the leave request
        leave_request.status = 'APPROVED'
        leave_request.approved_by = request.user
        leave_request.decision_at = timezone.now()
        leave_request.manager_comments = comments
        leave_request.save()

        # Deduct from leave balance if it's a paid leave
        if leave_request.leave_type.is_paid:
            try:
                leave_balance = LeaveBalance.objects.get(
                    employee=leave_request.employee,
                    leave_type=leave_request.leave_type,
                    year=leave_request.start_date.year
                )
                leave_balance.used += leave_request.total_days
                leave_balance.save()
            except LeaveBalance.DoesNotExist:
                pass  # No balance to deduct from

        # HTMX response - return updated row
        if request.headers.get('HX-Request'):
            html = f'''
            <tr id="leave-row-{leave_request.id}" class="table-success">
                <td>{leave_request.employee.get_full_name() or leave_request.employee.username}</td>
                <td>{leave_request.leave_type.name}</td>
                <td>{leave_request.start_date.strftime('%b %d, %Y')}</td>
                <td>{leave_request.end_date.strftime('%b %d, %Y')}</td>
                <td>{leave_request.total_days}</td>
                <td><span class="badge badge-approved">Approved</span></td>
                <td>
                    <small>{request.user.get_full_name() or request.user.username}</small><br>
                    <small class="text-muted">{timezone.now().strftime('%b %d, %Y')}</small>
                </td>
                <td><span class="text-success">✓ Approved</span></td>
            </tr>
            '''
            return HttpResponse(html)

        return JsonResponse({
            'success': True,
            'message': 'Leave request approved successfully.'
        })

    except LeaveRequest.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Leave request not found or you do not have permission to approve it.'
        }, status=404)


@login_required
@require_http_methods(["POST"])
def reject_leave_request(request, leave_id):
    """
    Reject a leave request (Manager/Admin only)
    """
    # Check if user is manager or admin
    if request.user.role not in ['MANAGER', 'ADMIN']:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to reject leave requests.'
        }, status=403)

    try:
        employee_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Profile not found.'
        }, status=400)

    comments = request.POST.get('comments', '')

    if not comments:
        return JsonResponse({
            'success': False,
            'message': 'Rejection reason is required.'
        }, status=400)

    try:
        # Get the leave request
        if request.user.role == 'ADMIN':
            leave_request = LeaveRequest.objects.get(id=leave_id)
        else:
            # Manager can only reject their team's requests
            leave_request = LeaveRequest.objects.get(
                id=leave_id,
                employee__profile__reporting_manager=employee_profile
            )

        # Can only reject PENDING requests
        if leave_request.status != 'PENDING':
            return JsonResponse({
                'success': False,
                'message': f'Cannot reject {leave_request.status.lower()} leave request.'
            }, status=400)

        # Reject the leave request
        leave_request.status = 'REJECTED'
        leave_request.approved_by = request.user
        leave_request.decision_at = timezone.now()
        leave_request.manager_comments = comments
        leave_request.save()

        # HTMX response - return updated row
        if request.headers.get('HX-Request'):
            html = f'''
            <tr id="leave-row-{leave_request.id}" class="table-danger">
                <td>{leave_request.employee.get_full_name() or leave_request.employee.username}</td>
                <td>{leave_request.leave_type.name}</td>
                <td>{leave_request.start_date.strftime('%b %d, %Y')}</td>
                <td>{leave_request.end_date.strftime('%b %d, %Y')}</td>
                <td>{leave_request.total_days}</td>
                <td><span class="badge badge-rejected">Rejected</span></td>
                <td>
                    <small>{request.user.get_full_name() or request.user.username}</small><br>
                    <small class="text-muted">{timezone.now().strftime('%b %d, %Y')}</small>
                </td>
                <td>
                    <span class="text-danger">✗ Rejected</span><br>
                    <small class="text-muted">{comments[:50]}...</small>
                </td>
            </tr>
            '''
            return HttpResponse(html)

        return JsonResponse({
            'success': True,
            'message': 'Leave request rejected.'
        })

    except LeaveRequest.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Leave request not found or you do not have permission to reject it.'
        }, status=404)


# =============================================================================
# MANAGER VIEWS - Team Management
# =============================================================================

@login_required
def team_leave_calendar_view(request):
    """
    Manager view for team leave calendar - shows all team members' leaves
    """
    # Check if user is manager or admin
    if request.user.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('frontend:dashboard')

    try:
        employee_profile = request.user.profile
    except EmployeeProfile.DoesNotExist:
        employee_profile = EmployeeProfile.objects.create(
            user=request.user,
            employee_id=request.user.employee_id
        )

    # Get month and year from query params
    today = timezone.now().date()
    selected_month = int(request.GET.get('month', today.month))
    selected_year = int(request.GET.get('year', today.year))

    # Get filter parameters
    employee_filter = request.GET.get('employee', 'ALL')
    leave_type_filter = request.GET.get('leave_type', 'ALL')

    # Get team members
    if request.user.role == 'ADMIN':
        team_members = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    else:
        team_members = User.objects.filter(
            profile__reporting_manager=request.user,
            is_active=True
        ).order_by('first_name', 'last_name')

    # Base query for leave requests
    if request.user.role == 'ADMIN':
        leave_requests = LeaveRequest.objects.filter(
            status='APPROVED',
            start_date__year=selected_year,
            start_date__month__lte=selected_month,
            end_date__month__gte=selected_month
        )
    else:
        leave_requests = LeaveRequest.objects.filter(
            employee__profile__reporting_manager=request.user,
            status='APPROVED',
            start_date__year=selected_year,
            start_date__month__lte=selected_month,
            end_date__month__gte=selected_month
        )

    # Apply filters
    if employee_filter != 'ALL':
        leave_requests = leave_requests.filter(employee_id=employee_filter)

    if leave_type_filter != 'ALL':
        leave_requests = leave_requests.filter(leave_type_id=leave_type_filter)

    leave_requests = leave_requests.select_related('employee', 'leave_type').order_by('start_date')

    # Get calendar for selected month
    cal = calendar.monthcalendar(selected_year, selected_month)

    # Create calendar data structure
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                date_obj = datetime(selected_year, selected_month, day).date()

                # Get leaves for this date
                leaves_on_date = []
                for leave in leave_requests:
                    if leave.start_date <= date_obj <= leave.end_date:
                        leaves_on_date.append(leave)

                # Get holidays
                holiday = Holiday.objects.filter(date=date_obj).first()

                day_info = {
                    'day': day,
                    'date': date_obj,
                    'is_today': date_obj == today,
                    'is_weekend': date_obj.weekday() >= 5,
                    'is_holiday': holiday is not None,
                    'holiday': holiday,
                    'leaves': leaves_on_date,
                }
                week_data.append(day_info)
        calendar_data.append(week_data)

    # Navigation months
    current_date = datetime(selected_year, selected_month, 1).date()
    prev_month = (current_date.replace(day=1) - timedelta(days=1))
    next_month_first = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)

    # Get leave types for filter
    leave_types = LeaveType.objects.all()

    context = {
        'calendar_data': calendar_data,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': calendar.month_name[selected_month],
        'prev_month': prev_month.month,
        'prev_year': prev_month.year,
        'next_month': next_month_first.month,
        'next_year': next_month_first.year,
        'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'team_members': team_members,
        'leave_types': leave_types,
        'employee_filter': employee_filter,
        'leave_type_filter': leave_type_filter,
    }

    return render(request, 'frontend/manager/team_calendar.html', context)


@login_required
def team_attendance_view(request):
    """
    Manager view for team attendance - daily/weekly/monthly view
    """
    # Check if user is manager or admin
    if request.user.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('frontend:dashboard')

    # Get date filter
    today = timezone.now().date()
    date_filter = request.GET.get('date', str(today))
    view_type = request.GET.get('view', 'daily')  # daily, weekly, monthly

    try:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
    except ValueError:
        filter_date = today

    # Get team members
    if request.user.role == 'ADMIN':
        team_members = User.objects.filter(is_active=True).select_related('profile')
    else:
        team_members = User.objects.filter(
            profile__reporting_manager=request.user,
            is_active=True
        ).select_related('profile')

    # Get attendance based on view type
    attendance_data = []

    if view_type == 'daily':
        # Single day view
        for member in team_members:
            attendance = Attendance.objects.filter(
                employee=member,
                date=filter_date
            ).first()

            # Check if on leave
            on_leave = LeaveRequest.objects.filter(
                employee=member,
                status='APPROVED',
                start_date__lte=filter_date,
                end_date__gte=filter_date
            ).first()

            attendance_data.append({
                'employee': member,
                'attendance': attendance,
                'on_leave': on_leave,
            })

    elif view_type == 'weekly':
        # Week view
        start_of_week = filter_date - timedelta(days=filter_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        for member in team_members:
            weekly_attendance = Attendance.objects.filter(
                employee=member,
                date__gte=start_of_week,
                date__lte=end_of_week
            ).order_by('date')

            attendance_data.append({
                'employee': member,
                'weekly_attendance': weekly_attendance,
                'start_date': start_of_week,
                'end_date': end_of_week,
            })

    elif view_type == 'monthly':
        # Month view
        start_of_month = filter_date.replace(day=1)
        if filter_date.month == 12:
            end_of_month = filter_date.replace(year=filter_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = filter_date.replace(month=filter_date.month + 1, day=1) - timedelta(days=1)

        for member in team_members:
            monthly_stats = Attendance.objects.filter(
                employee=member,
                date__gte=start_of_month,
                date__lte=end_of_month
            ).aggregate(
                total=Count('id'),
                present=Count('id', filter=Q(status='PRESENT')),
                wfh=Count('id', filter=Q(status='WFH')),
                half_day=Count('id', filter=Q(status='HALF_DAY')),
                absent=Count('id', filter=Q(status='ABSENT'))
            )

            attendance_data.append({
                'employee': member,
                'monthly_stats': monthly_stats,
                'month': filter_date.strftime('%B %Y'),
            })

    context = {
        'attendance_data': attendance_data,
        'view_type': view_type,
        'filter_date': filter_date,
        'today': today,
    }

    return render(request, 'frontend/manager/team_attendance.html', context)


# =============================================================================
# ADMIN VIEWS - Master Data Management
# =============================================================================

@login_required
def department_list_view(request):
    """
    Admin view for managing departments (CRUD operations)
    """
    # Check if user is admin
    if request.user.role != 'ADMIN':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('frontend:dashboard')

    from employees.models import Department

    departments = Department.objects.all().order_by('name')

    context = {
        'departments': departments,
    }

    return render(request, 'frontend/admin/departments.html', context)


@login_required
@require_http_methods(["POST"])
def department_create_view(request):
    """
    Create a new department (HTMX endpoint)
    """
    if request.user.role != 'ADMIN':
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    from employees.models import Department

    name = request.POST.get('name')
    description = request.POST.get('description', '')

    if not name:
        return HttpResponse(
            '<div class="alert alert-danger">Department name is required.</div>',
            status=400
        )

    # Check if department already exists
    if Department.objects.filter(name=name).exists():
        return HttpResponse(
            '<div class="alert alert-danger">A department with this name already exists.</div>',
            status=400
        )

    # Create department
    department = Department.objects.create(
        name=name,
        description=description
    )

    messages.success(request, f'Department "{name}" created successfully!')

    # Return HTMX response - redirect to refresh page
    if request.headers.get('HX-Request'):
        response = HttpResponse(status=200)
        response['HX-Redirect'] = '/settings/departments/'
        return response

    return redirect('frontend:department_list')


@login_required
@require_http_methods(["POST"])
def department_edit_view(request, dept_id):
    """
    Edit an existing department (HTMX endpoint)
    """
    if request.user.role != 'ADMIN':
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    from employees.models import Department

    try:
        department = Department.objects.get(id=dept_id)
    except Department.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Department not found.</div>',
            status=404
        )

    name = request.POST.get('name')
    description = request.POST.get('description', '')

    if not name:
        return HttpResponse(
            '<div class="alert alert-danger">Department name is required.</div>',
            status=400
        )

    # Check if another department has this name
    if Department.objects.filter(name=name).exclude(id=dept_id).exists():
        return HttpResponse(
            '<div class="alert alert-danger">A department with this name already exists.</div>',
            status=400
        )

    # Update department
    department.name = name
    department.description = description
    department.save()

    messages.success(request, f'Department "{name}" updated successfully!')

    # Return HTMX response - redirect to refresh page
    if request.headers.get('HX-Request'):
        response = HttpResponse(status=200)
        response['HX-Redirect'] = '/settings/departments/'
        return response

    return redirect('frontend:department_list')


@login_required
@require_http_methods(["POST"])
def department_delete_view(request, dept_id):
    """
    Delete a department (HTMX endpoint)
    """
    if request.user.role != 'ADMIN':
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    from employees.models import Department

    try:
        department = Department.objects.get(id=dept_id)
        dept_name = department.name

        # Check if department has employees
        if department.employees.exists():
            return HttpResponse(
                '<div class="alert alert-danger">Cannot delete department with assigned employees.</div>',
                status=400
            )

        department.delete()
        messages.success(request, f'Department "{dept_name}" deleted successfully!')

        # Return HTMX response
        if request.headers.get('HX-Request'):
            return HttpResponse(f'<tr id="dept-row-{dept_id}"></tr>')

        return redirect('frontend:department_list')

    except Department.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Department not found.</div>',
            status=404
        )


# =============================================
# ADMIN - DESIGNATION MANAGEMENT VIEWS
# =============================================

@login_required
def designation_list_view(request):
    """
    Admin view for managing designations
    """
    if request.user.role != 'ADMIN':
        messages.error(request, 'Permission denied.')
        return redirect('frontend:dashboard')

    from employees.models import Designation

    designations = Designation.objects.all().order_by('title')

    context = {
        'designations': designations,
    }
    return render(request, 'frontend/admin/designations.html', context)


@login_required
@require_http_methods(["POST"])
def designation_create_view(request):
    """
    Create a new designation (HTMX endpoint)
    """
    if request.user.role != 'ADMIN':
        return HttpResponse(
            '<div class="alert alert-danger">Permission denied.</div>',
            status=403
        )

    from employees.models import Designation

    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()

    if not title:
        return HttpResponse(
            '<div class="alert alert-danger">Designation title is required.</div>',
            status=400
        )

    # Check if designation already exists
    if Designation.objects.filter(title=title).exists():
        return HttpResponse(
            '<div class="alert alert-danger">A designation with this title already exists.</div>',
            status=400
        )

    # Create designation
    Designation.objects.create(
        title=title,
        description=description
    )

    messages.success(request, f'Designation "{title}" created successfully!')

    # Return HTMX response - redirect to refresh page
    if request.headers.get('HX-Request'):
        response = HttpResponse(status=200)
        response['HX-Redirect'] = '/settings/designations/'
        return response

    return redirect('frontend:designation_list')


@login_required
@require_http_methods(["POST"])
def designation_edit_view(request, desig_id):
    """
    Edit a designation (HTMX endpoint)
    """
    if request.user.role != 'ADMIN':
        return HttpResponse(
            '<div class="alert alert-danger">Permission denied.</div>',
            status=403
        )

    from employees.models import Designation

    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()

    if not title:
        return HttpResponse(
            '<div class="alert alert-danger">Designation title is required.</div>',
            status=400
        )

    try:
        designation = Designation.objects.get(id=desig_id)
    except Designation.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Designation not found.</div>',
            status=404
        )

    # Check if another designation has this title
    if Designation.objects.filter(title=title).exclude(id=desig_id).exists():
        return HttpResponse(
            '<div class="alert alert-danger">A designation with this title already exists.</div>',
            status=400
        )

    # Update designation
    designation.title = title
    designation.description = description
    designation.save()

    messages.success(request, f'Designation "{title}" updated successfully!')

    # Return HTMX response - redirect to refresh page
    if request.headers.get('HX-Request'):
        response = HttpResponse(status=200)
        response['HX-Redirect'] = '/settings/designations/'
        return response

    return redirect('frontend:designation_list')


@login_required
@require_http_methods(["POST"])
def designation_delete_view(request, desig_id):
    """
    Delete a designation (HTMX endpoint)
    """
    if request.user.role != 'ADMIN':
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    from employees.models import Designation

    try:
        designation = Designation.objects.get(id=desig_id)
        desig_title = designation.title

        # Check if designation has employees
        if designation.employees.exists():
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete designation with assigned employees.'
            }, status=400)

        designation.delete()

        return JsonResponse({
            'success': True,
            'message': f'Designation "{desig_title}" deleted successfully!'
        })

    except Designation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Designation not found.'
        }, status=404)


# =============================================
# ADMIN - LEAVE TYPES MANAGEMENT VIEWS
# =============================================

@login_required
def leave_types_list_view(request):
    """
    Admin view for managing leave types
    """
    if request.user.role != 'ADMIN':
        messages.error(request, 'Permission denied.')
        return redirect('frontend:dashboard')

    from leaves.models import LeaveType

    leave_types = LeaveType.objects.all().order_by('code')

    context = {
        'leave_types': leave_types,
    }
    return render(request, 'frontend/admin/leave_types.html', context)


@login_required
@require_http_methods(["POST"])
def leave_type_create_view(request):
    """
    Create a new leave type (HTMX endpoint)
    """
    if request.user.role != 'ADMIN':
        return HttpResponse(
            '<div class="alert alert-danger">Permission denied.</div>',
            status=403
        )

    from leaves.models import LeaveType

    code = request.POST.get('code', '').strip().upper()
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    is_paid = request.POST.get('is_paid') == 'on'
    requires_documentation = request.POST.get('requires_documentation') == 'on'
    max_consecutive_days = request.POST.get('max_consecutive_days', '').strip()

    if not code or not name:
        return HttpResponse(
            '<div class="alert alert-danger">Leave type code and name are required.</div>',
            status=400
        )

    # Validate max_consecutive_days if provided
    if max_consecutive_days:
        try:
            max_consecutive_days = int(max_consecutive_days)
            if max_consecutive_days <= 0:
                return HttpResponse(
                    '<div class="alert alert-danger">Max consecutive days must be a positive number.</div>',
                    status=400
                )
        except ValueError:
            return HttpResponse(
                '<div class="alert alert-danger">Max consecutive days must be a valid number.</div>',
                status=400
            )
    else:
        max_consecutive_days = None

    # Check if leave type code already exists
    if LeaveType.objects.filter(code=code).exists():
        return HttpResponse(
            '<div class="alert alert-danger">A leave type with this code already exists.</div>',
            status=400
        )

    # Create leave type
    LeaveType.objects.create(
        code=code,
        name=name,
        description=description,
        is_paid=is_paid,
        requires_documentation=requires_documentation,
        max_consecutive_days=max_consecutive_days
    )

    messages.success(request, f'Leave type "{code}" created successfully!')

    # Return HTMX response - redirect to refresh page
    if request.headers.get('HX-Request'):
        response = HttpResponse(status=200)
        response['HX-Redirect'] = '/settings/leave-types/'
        return response

    return redirect('frontend:leave_types')


@login_required
@require_http_methods(["POST"])
def leave_type_edit_view(request, lt_id):
    """
    Edit a leave type (HTMX endpoint)
    """
    if request.user.role != 'ADMIN':
        return HttpResponse(
            '<div class="alert alert-danger">Permission denied.</div>',
            status=403
        )

    from leaves.models import LeaveType

    code = request.POST.get('code', '').strip().upper()
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    is_paid = request.POST.get('is_paid') == 'on'
    requires_documentation = request.POST.get('requires_documentation') == 'on'
    max_consecutive_days = request.POST.get('max_consecutive_days', '').strip()

    if not code or not name:
        return HttpResponse(
            '<div class="alert alert-danger">Leave type code and name are required.</div>',
            status=400
        )

    # Validate max_consecutive_days if provided
    if max_consecutive_days:
        try:
            max_consecutive_days = int(max_consecutive_days)
            if max_consecutive_days <= 0:
                return HttpResponse(
                    '<div class="alert alert-danger">Max consecutive days must be a positive number.</div>',
                    status=400
                )
        except ValueError:
            return HttpResponse(
                '<div class="alert alert-danger">Max consecutive days must be a valid number.</div>',
                status=400
            )
    else:
        max_consecutive_days = None

    try:
        leave_type = LeaveType.objects.get(id=lt_id)
    except LeaveType.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Leave type not found.</div>',
            status=404
        )

    # Check if another leave type has this code
    if LeaveType.objects.filter(code=code).exclude(id=lt_id).exists():
        return HttpResponse(
            '<div class="alert alert-danger">A leave type with this code already exists.</div>',
            status=400
        )

    # Update leave type
    leave_type.code = code
    leave_type.name = name
    leave_type.description = description
    leave_type.is_paid = is_paid
    leave_type.requires_documentation = requires_documentation
    leave_type.max_consecutive_days = max_consecutive_days
    leave_type.save()

    messages.success(request, f'Leave type "{code}" updated successfully!')

    # Return HTMX response - redirect to refresh page
    if request.headers.get('HX-Request'):
        response = HttpResponse(status=200)
        response['HX-Redirect'] = '/settings/leave-types/'
        return response

    return redirect('frontend:leave_types')


@login_required
@require_http_methods(["POST"])
def leave_type_delete_view(request, lt_id):
    """
    Delete a leave type (HTMX endpoint)
    """
    if request.user.role != 'ADMIN':
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    from leaves.models import LeaveType

    try:
        leave_type = LeaveType.objects.get(id=lt_id)
        lt_code = leave_type.code

        # Check if leave type is being used in leave requests
        if leave_type.leave_requests.exists():
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete leave type that has been used in leave requests.'
            }, status=400)

        # Check if leave type is being used in leave balances
        if leave_type.leave_balances.exists():
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete leave type that has leave balances allocated.'
            }, status=400)

        leave_type.delete()

        return JsonResponse({
            'success': True,
            'message': f'Leave type "{lt_code}" deleted successfully!'
        })

    except LeaveType.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Leave type not found.'
        }, status=404)


# =============================================
# ADMIN - HOLIDAY MANAGEMENT VIEWS
# =============================================

@login_required
def holiday_list_view(request):
    """
    Admin view for managing holidays
    """
    if request.user.role != 'ADMIN':
        messages.error(request, 'Permission denied.')
        return redirect('frontend:dashboard')

    from attendance.models import Holiday
    from datetime import datetime

    year = request.GET.get('year')
    if year:
        try:
            year = int(year)
            holidays = Holiday.objects.filter(date__year=year).order_by('date')
        except ValueError:
            holidays = Holiday.objects.all().order_by('date')
    else:
        # Default to current year
        year = datetime.now().year
        holidays = Holiday.objects.filter(date__year=year).order_by('date')

    # Get available years for filter
    available_years = Holiday.objects.dates('date', 'year', order='DESC')

    context = {
        'holidays': holidays,
        'selected_year': year,
        'available_years': available_years,
    }
    return render(request, 'frontend/admin/holidays.html', context)


@login_required
@require_http_methods(["POST"])
def holiday_create_view(request):
    """
    Create a new holiday (HTMX endpoint)
    """
    if request.user.role != 'ADMIN':
        return HttpResponse(
            '<div class="alert alert-danger">Permission denied.</div>',
            status=403
        )

    from attendance.models import Holiday
    from datetime import datetime

    name = request.POST.get('name', '').strip()
    date_str = request.POST.get('date', '').strip()
    description = request.POST.get('description', '').strip()
    is_optional = request.POST.get('is_optional') == 'on'

    if not name or not date_str:
        return HttpResponse(
            '<div class="alert alert-danger">Holiday name and date are required.</div>',
            status=400
        )

    # Parse and validate date
    try:
        holiday_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse(
            '<div class="alert alert-danger">Invalid date format.</div>',
            status=400
        )

    # Check if holiday already exists for this date
    if Holiday.objects.filter(date=holiday_date).exists():
        return HttpResponse(
            '<div class="alert alert-danger">A holiday already exists for this date.</div>',
            status=400
        )

    # Create holiday
    Holiday.objects.create(
        name=name,
        date=holiday_date,
        description=description,
        is_optional=is_optional,
        created_by=request.user
    )

    messages.success(request, f'Holiday "{name}" created successfully!')

    # Return HTMX response - redirect to refresh page
    if request.headers.get('HX-Request'):
        response = HttpResponse(status=200)
        response['HX-Redirect'] = f'/settings/holidays/?year={holiday_date.year}'
        return response

    return redirect('frontend:holiday_list')


@login_required
@require_http_methods(["POST"])
def holiday_edit_view(request, holiday_id):
    """
    Edit a holiday (HTMX endpoint)
    """
    if request.user.role != 'ADMIN':
        return HttpResponse(
            '<div class="alert alert-danger">Permission denied.</div>',
            status=403
        )

    from attendance.models import Holiday
    from datetime import datetime

    name = request.POST.get('name', '').strip()
    date_str = request.POST.get('date', '').strip()
    description = request.POST.get('description', '').strip()
    is_optional = request.POST.get('is_optional') == 'on'

    if not name or not date_str:
        return HttpResponse(
            '<div class="alert alert-danger">Holiday name and date are required.</div>',
            status=400
        )

    # Parse and validate date
    try:
        holiday_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse(
            '<div class="alert alert-danger">Invalid date format.</div>',
            status=400
        )

    try:
        holiday = Holiday.objects.get(id=holiday_id)
    except Holiday.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Holiday not found.</div>',
            status=404
        )

    # Check if another holiday has this date
    if Holiday.objects.filter(date=holiday_date).exclude(id=holiday_id).exists():
        return HttpResponse(
            '<div class="alert alert-danger">A holiday already exists for this date.</div>',
            status=400
        )

    # Update holiday
    holiday.name = name
    holiday.date = holiday_date
    holiday.description = description
    holiday.is_optional = is_optional
    holiday.save()

    messages.success(request, f'Holiday "{name}" updated successfully!')

    # Return HTMX response - redirect to refresh page
    if request.headers.get('HX-Request'):
        response = HttpResponse(status=200)
        response['HX-Redirect'] = f'/settings/holidays/?year={holiday_date.year}'
        return response

    return redirect('frontend:holiday_list')


@login_required
@require_http_methods(["POST"])
def holiday_delete_view(request, holiday_id):
    """
    Delete a holiday (HTMX endpoint)
    """
    if request.user.role != 'ADMIN':
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    from attendance.models import Holiday

    try:
        holiday = Holiday.objects.get(id=holiday_id)
        holiday_name = holiday.name

        holiday.delete()

        return JsonResponse({
            'success': True,
            'message': f'Holiday "{holiday_name}" deleted successfully!'
        })

    except Holiday.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Holiday not found.'
        }, status=404)


# =======================
# EMPLOYEE MANAGEMENT
# =======================

@login_required
def employee_list_view(request):
    """
    List all employees with filtering and search
    """
    if request.user.role != 'ADMIN':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('frontend:dashboard')

    from employees.models import User, EmployeeProfile, Department, Designation

    # Get all employees with related data
    employees = User.objects.select_related(
        'profile',
        'profile__department',
        'profile__designation',
        'profile__reporting_manager'
    ).all()

    # Filters
    department_filter = request.GET.get('department', '')
    designation_filter = request.GET.get('designation', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '').strip()

    if department_filter:
        employees = employees.filter(profile__department_id=department_filter)

    if designation_filter:
        employees = employees.filter(profile__designation_id=designation_filter)

    if role_filter:
        employees = employees.filter(role=role_filter)

    if status_filter:
        if status_filter == 'active':
            employees = employees.filter(profile__is_active=True)
        elif status_filter == 'inactive':
            employees = employees.filter(profile__is_active=False)

    if search_query:
        from django.db.models import Q
        employees = employees.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )

    # Get all departments, designations, and managers for dropdowns
    departments = Department.objects.all().order_by('name')
    designations = Designation.objects.all().order_by('title')
    managers = User.objects.filter(role='MANAGER', profile__is_active=True).order_by('first_name', 'last_name')

    # Role choices
    role_choices = User.ROLE_CHOICES

    context = {
        'employees': employees.order_by('first_name', 'last_name'),
        'departments': departments,
        'designations': designations,
        'managers': managers,
        'role_choices': role_choices,
        'department_filter': department_filter,
        'designation_filter': designation_filter,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search_query': search_query,
    }

    return render(request, 'frontend/admin/employees.html', context)


@login_required
@require_http_methods(["POST"])
def employee_create_view(request):
    """
    Create a new employee (User + EmployeeProfile)
    """
    if request.user.role != 'ADMIN':
        return HttpResponse(
            '<div class="alert alert-danger">Permission denied.</div>',
            status=403
        )

    from employees.models import User, EmployeeProfile, Department, Designation
    from django.contrib.auth.hashers import make_password

    # Get User fields
    username = request.POST.get('username', '').strip()
    email = request.POST.get('email', '').strip()
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    employee_id = request.POST.get('employee_id', '').strip()
    role = request.POST.get('role', 'EMPLOYEE')
    password = request.POST.get('password', '').strip()

    # Get Profile fields
    department_id = request.POST.get('department', '')
    designation_id = request.POST.get('designation', '')
    reporting_manager_id = request.POST.get('reporting_manager', '')
    date_of_joining = request.POST.get('date_of_joining', '')
    phone_number = request.POST.get('phone_number', '').strip()

    # Validation
    if not username or not email or not first_name or not last_name or not employee_id or not password:
        return HttpResponse(
            '<div class="alert alert-danger">Username, email, first name, last name, employee ID, and password are required.</div>',
            status=400
        )

    # Check username uniqueness
    if User.objects.filter(username=username).exists():
        return HttpResponse(
            '<div class="alert alert-danger">Username already exists.</div>',
            status=400
        )

    # Check employee_id uniqueness
    if User.objects.filter(employee_id=employee_id).exists():
        return HttpResponse(
            '<div class="alert alert-danger">Employee ID already exists.</div>',
            status=400
        )

    # Check email uniqueness
    if User.objects.filter(email=email).exists():
        return HttpResponse(
            '<div class="alert alert-danger">Email already exists.</div>',
            status=400
        )

    # Validate password length
    if len(password) < 8:
        return HttpResponse(
            '<div class="alert alert-danger">Password must be at least 8 characters long.</div>',
            status=400
        )

    try:
        # Create User
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            employee_id=employee_id,
            role=role,
            password=make_password(password)
        )

        # Get related objects
        department = Department.objects.get(id=department_id) if department_id else None
        designation = Designation.objects.get(id=designation_id) if designation_id else None
        reporting_manager = User.objects.get(id=reporting_manager_id) if reporting_manager_id else None

        # Validate reporting manager role
        if reporting_manager and reporting_manager.role != 'MANAGER':
            user.delete()
            return HttpResponse(
                '<div class="alert alert-danger">Reporting manager must have MANAGER role.</div>',
                status=400
            )

        # Parse date of joining
        from datetime import datetime
        doj = None
        if date_of_joining:
            try:
                doj = datetime.strptime(date_of_joining, '%Y-%m-%d').date()
            except ValueError:
                user.delete()
                return HttpResponse(
                    '<div class="alert alert-danger">Invalid date format.</div>',
                    status=400
                )

        # Create EmployeeProfile
        EmployeeProfile.objects.create(
            user=user,
            department=department,
            designation=designation,
            reporting_manager=reporting_manager,
            date_of_joining=doj,
            phone_number=phone_number,
            is_active=True
        )

        messages.success(request, f'Employee "{first_name} {last_name}" created successfully!')

        # Return HTMX response - redirect to employee list
        if request.headers.get('HX-Request'):
            response = HttpResponse(status=200)
            response['HX-Redirect'] = '/settings/employees/'
            return response

        return redirect('frontend:employee_list')

    except Exception as e:
        return HttpResponse(
            f'<div class="alert alert-danger">Error creating employee: {str(e)}</div>',
            status=500
        )


@login_required
@require_http_methods(["POST"])
def employee_edit_view(request, employee_id):
    """
    Edit an employee (User + EmployeeProfile)
    """
    if request.user.role != 'ADMIN':
        return HttpResponse(
            '<div class="alert alert-danger">Permission denied.</div>',
            status=403
        )

    from employees.models import User, EmployeeProfile, Department, Designation

    try:
        user = User.objects.get(id=employee_id)
        profile = user.profile
    except (User.DoesNotExist, EmployeeProfile.DoesNotExist):
        return HttpResponse(
            '<div class="alert alert-danger">Employee not found.</div>',
            status=404
        )

    # Get User fields
    email = request.POST.get('email', '').strip()
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    employee_id_new = request.POST.get('employee_id', '').strip()
    role = request.POST.get('role', 'EMPLOYEE')

    # Get Profile fields
    department_id = request.POST.get('department', '')
    designation_id = request.POST.get('designation', '')
    reporting_manager_id = request.POST.get('reporting_manager', '')
    date_of_joining = request.POST.get('date_of_joining', '')
    phone_number = request.POST.get('phone_number', '').strip()

    # Validation
    if not email or not first_name or not last_name or not employee_id_new:
        return HttpResponse(
            '<div class="alert alert-danger">Email, first name, last name, and employee ID are required.</div>',
            status=400
        )

    # Check employee_id uniqueness (excluding current user)
    if User.objects.filter(employee_id=employee_id_new).exclude(id=employee_id).exists():
        return HttpResponse(
            '<div class="alert alert-danger">Employee ID already exists.</div>',
            status=400
        )

    # Check email uniqueness (excluding current user)
    if User.objects.filter(email=email).exclude(id=employee_id).exists():
        return HttpResponse(
            '<div class="alert alert-danger">Email already exists.</div>',
            status=400
        )

    try:
        # Update User
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.employee_id = employee_id_new
        user.role = role
        user.save()

        # Get related objects
        department = Department.objects.get(id=department_id) if department_id else None
        designation = Designation.objects.get(id=designation_id) if designation_id else None
        reporting_manager = User.objects.get(id=reporting_manager_id) if reporting_manager_id else None

        # Validate reporting manager role
        if reporting_manager and reporting_manager.role != 'MANAGER':
            return HttpResponse(
                '<div class="alert alert-danger">Reporting manager must have MANAGER role.</div>',
                status=400
            )

        # Parse date of joining
        from datetime import datetime
        doj = None
        if date_of_joining:
            try:
                doj = datetime.strptime(date_of_joining, '%Y-%m-%d').date()
            except ValueError:
                return HttpResponse(
                    '<div class="alert alert-danger">Invalid date format.</div>',
                    status=400
                )

        # Update EmployeeProfile
        profile.department = department
        profile.designation = designation
        profile.reporting_manager = reporting_manager
        profile.date_of_joining = doj
        profile.phone_number = phone_number
        profile.save()

        messages.success(request, f'Employee "{first_name} {last_name}" updated successfully!')

        # Return HTMX response - redirect to employee list
        if request.headers.get('HX-Request'):
            response = HttpResponse(status=200)
            response['HX-Redirect'] = '/settings/employees/'
            return response

        return redirect('frontend:employee_list')

    except Exception as e:
        return HttpResponse(
            f'<div class="alert alert-danger">Error updating employee: {str(e)}</div>',
            status=500
        )


@login_required
@require_http_methods(["POST"])
def employee_deactivate_view(request, employee_id):
    """
    Deactivate/activate an employee (soft delete)
    """
    if request.user.role != 'ADMIN':
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    from employees.models import User, EmployeeProfile

    try:
        user = User.objects.get(id=employee_id)
        profile = user.profile

        # Get desired status from request
        action = request.POST.get('action', 'deactivate')

        if action == 'deactivate':
            profile.is_active = False
            profile.save()
            message = f'Employee "{user.get_full_name()}" deactivated successfully!'
        else:
            profile.is_active = True
            profile.save()
            message = f'Employee "{user.get_full_name()}" activated successfully!'

        return JsonResponse({
            'success': True,
            'message': message
        })

    except (User.DoesNotExist, EmployeeProfile.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': 'Employee not found.'
        }, status=404)


# =======================
# LEAVE BALANCE ALLOCATION
# =======================

@login_required
def leave_balance_list_view(request):
    """
    List all leave balances with filtering
    """
    if request.user.role != 'ADMIN':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('frontend:dashboard')

    from leaves.models import LeaveBalance, LeaveType
    from employees.models import User
    from datetime import date

    # Get current year as default
    current_year = date.today().year

    # Get all balances with related data
    balances = LeaveBalance.objects.select_related(
        'employee',
        'employee__profile',
        'leave_type'
    ).all()

    # Filters
    employee_filter = request.GET.get('employee', '')
    leave_type_filter = request.GET.get('leave_type', '')
    year_filter = request.GET.get('year', str(current_year))
    search_query = request.GET.get('search', '').strip()

    if employee_filter:
        balances = balances.filter(employee_id=employee_filter)

    if leave_type_filter:
        balances = balances.filter(leave_type_id=leave_type_filter)

    if year_filter:
        balances = balances.filter(year=int(year_filter))

    if search_query:
        from django.db.models import Q
        balances = balances.filter(
            Q(employee__first_name__icontains=search_query) |
            Q(employee__last_name__icontains=search_query) |
            Q(employee__employee_id__icontains=search_query)
        )

    # Get all employees, leave types for dropdowns
    employees = User.objects.filter(profile__is_active=True).order_by('first_name', 'last_name')
    leave_types = LeaveType.objects.all().order_by('code')

    # Get available years (from existing balances)
    available_years = LeaveBalance.objects.values_list('year', flat=True).distinct().order_by('-year')
    if not available_years:
        available_years = [current_year]

    context = {
        'balances': balances.order_by('employee__first_name', 'leave_type__code'),
        'employees': employees,
        'leave_types': leave_types,
        'available_years': available_years,
        'employee_filter': employee_filter,
        'leave_type_filter': leave_type_filter,
        'year_filter': year_filter,
        'search_query': search_query,
        'current_year': current_year,
    }

    return render(request, 'frontend/admin/leave_balances.html', context)


@login_required
@require_http_methods(["POST"])
def leave_balance_create_view(request):
    """
    Create/allocate a new leave balance
    """
    if request.user.role != 'ADMIN':
        return HttpResponse(
            '<div class="alert alert-danger">Permission denied.</div>',
            status=403
        )

    from leaves.models import LeaveBalance, LeaveType
    from employees.models import User
    from decimal import Decimal

    # Get form data
    employee_id = request.POST.get('employee', '')
    leave_type_id = request.POST.get('leave_type', '')
    year = request.POST.get('year', '')
    allocated = request.POST.get('allocated', '0')

    # Validation
    if not employee_id or not leave_type_id or not year or not allocated:
        return HttpResponse(
            '<div class="alert alert-danger">Employee, leave type, year, and allocated days are required.</div>',
            status=400
        )

    try:
        employee = User.objects.get(id=employee_id)
        leave_type = LeaveType.objects.get(id=leave_type_id)
        year_int = int(year)
        allocated_decimal = Decimal(allocated)

        if allocated_decimal < 0:
            return HttpResponse(
                '<div class="alert alert-danger">Allocated days cannot be negative.</div>',
                status=400
            )

    except User.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Employee not found.</div>',
            status=404
        )
    except LeaveType.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Leave type not found.</div>',
            status=404
        )
    except (ValueError, TypeError):
        return HttpResponse(
            '<div class="alert alert-danger">Invalid year or allocated days.</div>',
            status=400
        )

    # Check if balance already exists
    if LeaveBalance.objects.filter(employee=employee, leave_type=leave_type, year=year_int).exists():
        return HttpResponse(
            '<div class="alert alert-danger">Balance already exists for this employee, leave type, and year.</div>',
            status=400
        )

    try:
        # Create balance
        LeaveBalance.objects.create(
            employee=employee,
            leave_type=leave_type,
            year=year_int,
            allocated=allocated_decimal,
            used=Decimal('0'),
            adjusted=Decimal('0')
        )

        messages.success(request, f'Leave balance allocated successfully for {employee.get_full_name()}!')

        # Return HTMX response - redirect to balance list
        if request.headers.get('HX-Request'):
            response = HttpResponse(status=200)
            response['HX-Redirect'] = f'/settings/leave-balances/?year={year_int}'
            return response

        return redirect('frontend:leave_balance_allocation')

    except Exception as e:
        return HttpResponse(
            f'<div class="alert alert-danger">Error creating balance: {str(e)}</div>',
            status=500
        )


@login_required
@require_http_methods(["POST"])
def leave_balance_adjust_view(request, balance_id):
    """
    Adjust an existing leave balance (allocated or adjusted fields)
    """
    if request.user.role != 'ADMIN':
        return HttpResponse(
            '<div class="alert alert-danger">Permission denied.</div>',
            status=403
        )

    from leaves.models import LeaveBalance
    from decimal import Decimal

    try:
        balance = LeaveBalance.objects.get(id=balance_id)
    except LeaveBalance.DoesNotExist:
        return HttpResponse(
            '<div class="alert alert-danger">Balance not found.</div>',
            status=404
        )

    # Get form data
    allocated = request.POST.get('allocated', '')
    adjusted = request.POST.get('adjusted', '')

    # Validation
    if not allocated and not adjusted:
        return HttpResponse(
            '<div class="alert alert-danger">At least one field (allocated or adjusted) must be provided.</div>',
            status=400
        )

    try:
        if allocated:
            allocated_decimal = Decimal(allocated)
            if allocated_decimal < 0:
                return HttpResponse(
                    '<div class="alert alert-danger">Allocated days cannot be negative.</div>',
                    status=400
                )
            balance.allocated = allocated_decimal

        if adjusted:
            adjusted_decimal = Decimal(adjusted)
            balance.adjusted = adjusted_decimal

        balance.save()

        messages.success(request, f'Balance adjusted successfully for {balance.employee.get_full_name()}!')

        # Return HTMX response - redirect to balance list
        if request.headers.get('HX-Request'):
            response = HttpResponse(status=200)
            response['HX-Redirect'] = f'/settings/leave-balances/?year={balance.year}'
            return response

        return redirect('frontend:leave_balance_allocation')

    except (ValueError, TypeError):
        return HttpResponse(
            '<div class="alert alert-danger">Invalid allocated or adjusted value.</div>',
            status=400
        )
    except Exception as e:
        return HttpResponse(
            f'<div class="alert alert-danger">Error adjusting balance: {str(e)}</div>',
            status=500
        )


@login_required
@require_http_methods(["POST"])
def leave_balance_delete_view(request, balance_id):
    """
    Delete a leave balance
    """
    if request.user.role != 'ADMIN':
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)

    from leaves.models import LeaveBalance

    try:
        balance = LeaveBalance.objects.get(id=balance_id)

        # Check if balance has been used
        if balance.used > 0:
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete balance that has been used. Consider adjusting instead.'
            }, status=400)

        employee_name = balance.employee.get_full_name()
        leave_type_name = balance.leave_type.name

        balance.delete()

        return JsonResponse({
            'success': True,
            'message': f'Balance deleted successfully for {employee_name} - {leave_type_name}!'
        })

    except LeaveBalance.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Balance not found.'
        }, status=404)
