"""
URL Configuration for frontend app
"""
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView, RedirectView
from . import views

app_name = 'frontend'

# Temporary placeholder view
def placeholder_view(request):
    from django.http import HttpResponse
    return HttpResponse("<h1>Coming Soon</h1><p>This page will be implemented in the next phase.</p><br><a href='/dashboard/'>Back to Dashboard</a>")

urlpatterns = [
    # Root redirect
    path('', RedirectView.as_view(pattern_name='frontend:login', permanent=False), name='home'),

    # Authentication
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Dashboard (role-based)
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Profile and Settings
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),

    # Leave Management
    path('leaves/apply/', views.apply_leave_view, name='leave_apply'),
    path('leaves/my-leaves/', views.my_leaves_view, name='my_leaves'),
    path('leaves/<int:leave_id>/cancel/', views.cancel_leave_request, name='cancel_leave'),
    path('leaves/balance/', placeholder_view, name='leave_balance'),

    # Manager Leave Approvals
    path('leaves/approvals/', views.leave_approvals_view, name='leave_approvals'),
    path('leaves/<int:leave_id>/approve/', views.approve_leave_request, name='approve_leave'),
    path('leaves/<int:leave_id>/reject/', views.reject_leave_request, name='reject_leave'),

    # Manager Team Management
    path('leaves/team-calendar/', views.team_leave_calendar_view, name='team_leaves'),
    path('attendance/team/', views.team_attendance_view, name='team_attendance'),
    path('reports/team/', placeholder_view, name='team_reports'),

    # Employee Attendance Management
    path('attendance/mark/', views.mark_attendance_view, name='mark_attendance'),
    path('attendance/my-attendance/', views.my_attendance_view, name='my_attendance'),


    # Admin/Settings - Department Management
    path('settings/departments/', views.department_list_view, name='department_list'),
    path('settings/departments/create/', views.department_create_view, name='department_create'),
    path('settings/departments/<int:dept_id>/edit/', views.department_edit_view, name='department_edit'),
    path('settings/departments/<int:dept_id>/delete/', views.department_delete_view, name='department_delete'),

    # Admin/Settings - Designation Management
    path('settings/designations/', views.designation_list_view, name='designation_list'),
    path('settings/designations/create/', views.designation_create_view, name='designation_create'),
    path('settings/designations/<int:desig_id>/edit/', views.designation_edit_view, name='designation_edit'),
    path('settings/designations/<int:desig_id>/delete/', views.designation_delete_view, name='designation_delete'),

    # Admin/Settings - Leave Types Management
    path('settings/leave-types/', views.leave_types_list_view, name='leave_types'),
    path('settings/leave-types/create/', views.leave_type_create_view, name='leave_type_create'),
    path('settings/leave-types/<int:lt_id>/edit/', views.leave_type_edit_view, name='leave_type_edit'),
    path('settings/leave-types/<int:lt_id>/delete/', views.leave_type_delete_view, name='leave_type_delete'),

    # Admin/Settings - Holiday Management
    path('settings/holidays/', views.holiday_list_view, name='holiday_list'),
    path('settings/holidays/create/', views.holiday_create_view, name='holiday_create'),
    path('settings/holidays/<int:holiday_id>/edit/', views.holiday_edit_view, name='holiday_edit'),
    path('settings/holidays/<int:holiday_id>/delete/', views.holiday_delete_view, name='holiday_delete'),

    # Admin/Settings - Employee Management
    path('settings/employees/', views.employee_list_view, name='employee_list'),
    path('settings/employees/create/', views.employee_create_view, name='employee_create'),
    path('settings/employees/<int:employee_id>/edit/', views.employee_edit_view, name='employee_edit'),
    path('settings/employees/<int:employee_id>/deactivate/', views.employee_deactivate_view, name='employee_deactivate'),

    # Admin/Settings - Leave Balance Allocation
    path('settings/leave-balances/', views.leave_balance_list_view, name='leave_balance_allocation'),
    path('settings/leave-balances/create/', views.leave_balance_create_view, name='leave_balance_create'),
    path('settings/leave-balances/<int:balance_id>/adjust/', views.leave_balance_adjust_view, name='leave_balance_adjust'),
    path('settings/leave-balances/<int:balance_id>/delete/', views.leave_balance_delete_view, name='leave_balance_delete'),

    # Admin/Settings placeholders
    path('settings/attendance/correct/', placeholder_view, name='attendance_correction'),
    path('settings/reports/', placeholder_view, name='reports'),
    path('settings/audit-logs/', placeholder_view, name='audit_logs'),
]
