"""
URL configuration for attendance app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet, HolidayViewSet

router = DefaultRouter()
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'holidays', HolidayViewSet, basename='holiday')

urlpatterns = [
    path('', include(router.urls)),
]
