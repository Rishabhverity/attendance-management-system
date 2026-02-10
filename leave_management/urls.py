"""
URL configuration for leave_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Frontend URLs (Django Templates + HTMX)
    path('', include('frontend.urls')),  # Main frontend

    # API endpoints (REST API - still available)
    path('api/', include('employees.urls')),  # Auth, employees, departments, designations
    path('api/', include('leaves.urls')),     # Leave types, balances, requests
    path('api/', include('attendance.urls')), # Attendance, holidays
    path('api/', include('core.urls')),       # Dashboard, reports, audit logs
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Note: Static files are automatically served by Django's runserver from STATICFILES_DIRS

# Customize admin site
admin.site.site_header = "HR Leave & Attendance Management"
admin.site.site_title = "Leave Management Admin"
admin.site.index_title = "Welcome to HR Leave & Attendance Management System"
