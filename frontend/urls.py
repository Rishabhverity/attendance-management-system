"""
URL Configuration for frontend app
"""
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from . import views

app_name = 'frontend'

# Temporary placeholder view
def placeholder_view(request):
    from django.http import HttpResponse
    return HttpResponse("<h1>Coming Soon</h1><p>This page will be implemented in the next phase.</p><br><a href='/dashboard/'>Back to Dashboard</a>")

urlpatterns = [
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
    path('leaves/approvals/', placeholder_view, name='leave_approvals'),
    path('leaves/team-calendar/', placeholder_view, name='team_leaves'),

    # Attendance Management
    path('attendance/mark/', views.mark_attendance_view, name='mark_attendance'),
    path('attendance/my-attendance/', views.my_attendance_view, name='my_attendance'),
    path('attendance/team/', placeholder_view, name='team_attendance'),
    path('reports/team/', placeholder_view, name='team_reports'),

    # Admin placeholders
    path('admin/employees/', placeholder_view, name='employee_list'),
    path('admin/departments/', placeholder_view, name='department_list'),
    path('admin/designations/', placeholder_view, name='designation_list'),
    path('admin/leave-types/', placeholder_view, name='leave_types'),
    path('admin/leave-balances/', placeholder_view, name='leave_balance_allocation'),
    path('admin/attendance/correct/', placeholder_view, name='attendance_correction'),
    path('admin/holidays/', placeholder_view, name='holiday_list'),
    path('admin/reports/', placeholder_view, name='reports'),
    path('admin/audit-logs/', placeholder_view, name='audit_logs'),
]
