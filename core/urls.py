"""
URL configuration for core app (reports, dashboard, audit logs).
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuditLogViewSet,
    dashboard_view, manager_dashboard_view, admin_dashboard_view,
    leave_summary_report, attendance_summary_report,
    export_leave_summary_csv, export_attendance_summary_csv
)

router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('', include(router.urls)),

    # Dashboard endpoints
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/manager/', manager_dashboard_view, name='manager-dashboard'),
    path('dashboard/admin/', admin_dashboard_view, name='admin-dashboard'),

    # Report endpoints
    path('reports/leave-summary/', leave_summary_report, name='leave-summary-report'),
    path('reports/attendance-summary/', attendance_summary_report, name='attendance-summary-report'),
    path('reports/leave-summary/export/', export_leave_summary_csv, name='leave-summary-export'),
    path('reports/attendance-summary/export/', export_attendance_summary_csv, name='attendance-summary-export'),
]
