"""
Views for Leave Management APIs.
Handles LeaveType, LeaveBalance, and LeaveRequest endpoints.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import datetime

from .models import LeaveType, LeaveBalance, LeaveRequest
from .serializers import (
    LeaveTypeSerializer, LeaveBalanceSerializer, LeaveBalanceSimpleSerializer,
    LeaveRequestSerializer, LeaveRequestListSerializer,
    LeaveApprovalSerializer, LeaveCancellationSerializer,
    TeamLeaveCalendarSerializer
)
from employees.models import EmployeeProfile
from core.permissions import IsAdmin, IsOwnerOrManager, IsAdminOrReadOnly, CanApproveLeave
from core.models import AuditLog


class LeaveTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LeaveType management.
    All authenticated users can read, only admins can write.
    """
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class LeaveBalanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LeaveBalance management.
    Employees can view own balances, managers can view team balances, admins can manage all.
    """
    queryset = LeaveBalance.objects.select_related('employee', 'leave_type').all()
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        queryset = self.queryset

        if user.role == 'EMPLOYEE':
            # Employees see only their own balances
            queryset = queryset.filter(employee=user)
        elif user.role == 'MANAGER':
            # Managers see their own and team members' balances
            team_member_ids = EmployeeProfile.objects.filter(
                reporting_manager=user
            ).values_list('user_id', flat=True)
            queryset = queryset.filter(Q(employee=user) | Q(employee_id__in=team_member_ids))
        # Admin sees all

        # Apply filters
        employee = self.request.query_params.get('employee')
        if employee and user.role == 'ADMIN':
            queryset = queryset.filter(employee_id=employee)

        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)

        leave_type = self.request.query_params.get('leave_type')
        if leave_type:
            queryset = queryset.filter(leave_type_id=leave_type)

        return queryset.order_by('-year', 'leave_type__code')

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_balance(self, request):
        """
        Get current user's leave balances.
        GET /api/leave-balances/my-balance/
        """
        current_year = datetime.now().year
        balances = LeaveBalance.objects.filter(
            employee=request.user,
            year=current_year
        ).select_related('leave_type')

        serializer = LeaveBalanceSimpleSerializer(balances, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='employee/(?P<emp_id>[^/.]+)')
    def employee_balance(self, request, emp_id=None):
        """
        Get specific employee's leave balances.
        GET /api/leave-balances/employee/{emp_id}/
        """
        user = request.user

        # Check permissions
        if user.role == 'EMPLOYEE' and user.employee_id != emp_id:
            return Response(
                {'error': 'You can only view your own leave balance.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if user.role == 'MANAGER':
            # Check if employee is in team
            try:
                employee = User.objects.get(employee_id=emp_id)
                if employee != user and (not hasattr(employee, 'profile') or employee.profile.reporting_manager != user):
                    return Response(
                        {'error': 'You can only view your team members\' leave balance.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except User.DoesNotExist:
                return Response(
                    {'error': 'Employee not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Get balances
        current_year = datetime.now().year
        balances = LeaveBalance.objects.filter(
            employee__employee_id=emp_id,
            year=current_year
        ).select_related('leave_type', 'employee')

        serializer = LeaveBalanceSerializer(balances, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Log balance allocation in audit log."""
        instance = serializer.save()
        AuditLog.log_action(
            user=self.request.user,
            action='BALANCE_ALLOCATED',
            model_name='LeaveBalance',
            object_id=instance.id,
            description=f"Allocated {instance.allocated} {instance.leave_type.code} leaves to {instance.employee.get_full_name()} for {instance.year}",
            metadata={
                'employee_id': instance.employee.employee_id,
                'leave_type': instance.leave_type.code,
                'year': instance.year,
                'allocated': float(instance.allocated)
            }
        )

    def perform_update(self, serializer):
        """Log balance adjustment in audit log."""
        old_instance = self.get_object()
        instance = serializer.save()

        # Check if adjusted was changed
        if old_instance.adjusted != instance.adjusted:
            AuditLog.log_action(
                user=self.request.user,
                action='BALANCE_ADJUSTED',
                model_name='LeaveBalance',
                object_id=instance.id,
                description=f"Adjusted {instance.leave_type.code} balance for {instance.employee.get_full_name()}",
                metadata={
                    'employee_id': instance.employee.employee_id,
                    'leave_type': instance.leave_type.code,
                    'year': instance.year,
                    'old_adjusted': float(old_instance.adjusted),
                    'new_adjusted': float(instance.adjusted)
                }
            )


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LeaveRequest management.
    Handles leave application, approval, rejection, and cancellation.
    """
    queryset = LeaveRequest.objects.select_related(
        'employee', 'leave_type', 'approved_by'
    ).all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return LeaveRequestListSerializer
        return LeaveRequestSerializer

    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        queryset = self.queryset

        if user.role == 'EMPLOYEE':
            # Employees see only their own requests
            queryset = queryset.filter(employee=user)
        elif user.role == 'MANAGER':
            # Managers see their own and team members' requests
            team_member_ids = EmployeeProfile.objects.filter(
                reporting_manager=user
            ).values_list('user_id', flat=True)
            queryset = queryset.filter(Q(employee=user) | Q(employee_id__in=team_member_ids))
        # Admin sees all

        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        employee = self.request.query_params.get('employee')
        if employee and user.role == 'ADMIN':
            queryset = queryset.filter(employee_id=employee)

        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)

        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)

        leave_type = self.request.query_params.get('leave_type')
        if leave_type:
            queryset = queryset.filter(leave_type_id=leave_type)

        return queryset.order_by('-applied_at')

    def get_serializer_context(self):
        """Add extra context to serializer."""
        context = super().get_serializer_context()
        context['employee'] = self.request.user
        return context

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_requests(self, request):
        """
        Get current user's leave requests.
        GET /api/leave-requests/my-requests/
        """
        requests = LeaveRequest.objects.filter(
            employee=request.user
        ).select_related('leave_type', 'approved_by').order_by('-applied_at')

        serializer = LeaveRequestSerializer(requests, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanApproveLeave])
    def pending(self, request):
        """
        Get pending leave requests for approval.
        Managers see team requests, admins see all.
        GET /api/leave-requests/pending/
        """
        user = request.user

        if user.role == 'MANAGER':
            # Get pending requests from team members
            team_member_ids = EmployeeProfile.objects.filter(
                reporting_manager=user
            ).values_list('user_id', flat=True)
            pending_requests = LeaveRequest.objects.filter(
                employee_id__in=team_member_ids,
                status='PENDING'
            )
        else:
            # Admin sees all pending requests
            pending_requests = LeaveRequest.objects.filter(status='PENDING')

        pending_requests = pending_requests.select_related('employee', 'leave_type').order_by('applied_at')

        serializer = LeaveRequestSerializer(pending_requests, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, CanApproveLeave])
    def approve(self, request, pk=None):
        """
        Approve a leave request.
        PATCH /api/leave-requests/{id}/approve/
        """
        leave_request = self.get_object()

        serializer = LeaveApprovalSerializer(
            data=request.data,
            context={'request': request, 'leave_request': leave_request}
        )

        if serializer.is_valid():
            try:
                comments = serializer.validated_data.get('comments', '')
                leave_request.approve(request.user, comments)

                # Log approval
                AuditLog.log_action(
                    user=request.user,
                    action='LEAVE_APPROVED',
                    model_name='LeaveRequest',
                    object_id=leave_request.id,
                    description=f"Approved {leave_request.leave_type.code} leave for {leave_request.employee.get_full_name()}",
                    metadata={
                        'employee_id': leave_request.employee.employee_id,
                        'leave_type': leave_request.leave_type.code,
                        'start_date': str(leave_request.start_date),
                        'end_date': str(leave_request.end_date),
                        'total_days': float(leave_request.total_days)
                    }
                )

                response_serializer = LeaveRequestSerializer(leave_request, context={'request': request})
                return Response(response_serializer.data)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, CanApproveLeave])
    def reject(self, request, pk=None):
        """
        Reject a leave request.
        PATCH /api/leave-requests/{id}/reject/
        """
        leave_request = self.get_object()

        serializer = LeaveApprovalSerializer(
            data=request.data,
            context={'request': request, 'leave_request': leave_request}
        )

        if serializer.is_valid():
            try:
                comments = serializer.validated_data.get('comments', '')
                leave_request.reject(request.user, comments)

                # Log rejection
                AuditLog.log_action(
                    user=request.user,
                    action='LEAVE_REJECTED',
                    model_name='LeaveRequest',
                    object_id=leave_request.id,
                    description=f"Rejected {leave_request.leave_type.code} leave for {leave_request.employee.get_full_name()}",
                    metadata={
                        'employee_id': leave_request.employee.employee_id,
                        'leave_type': leave_request.leave_type.code,
                        'reason': comments
                    }
                )

                response_serializer = LeaveRequestSerializer(leave_request, context={'request': request})
                return Response(response_serializer.data)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """
        Cancel a leave request (employee can cancel own requests).
        PATCH /api/leave-requests/{id}/cancel/
        """
        leave_request = self.get_object()

        serializer = LeaveCancellationSerializer(
            data={},
            context={'request': request, 'leave_request': leave_request}
        )

        if serializer.is_valid():
            try:
                leave_request.cancel()

                # Log cancellation
                AuditLog.log_action(
                    user=request.user,
                    action='LEAVE_CANCELLED',
                    model_name='LeaveRequest',
                    object_id=leave_request.id,
                    description=f"Cancelled {leave_request.leave_type.code} leave",
                    metadata={
                        'employee_id': leave_request.employee.employee_id,
                        'leave_type': leave_request.leave_type.code,
                        'start_date': str(leave_request.start_date),
                        'end_date': str(leave_request.end_date)
                    }
                )

                response_serializer = LeaveRequestSerializer(leave_request, context={'request': request})
                return Response(response_serializer.data)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def team_calendar(self, request):
        """
        Get team leave calendar (approved leaves).
        Managers get team calendar, admins get org-wide calendar.
        GET /api/leave-requests/team-calendar/
        """
        user = request.user

        if user.role == 'EMPLOYEE':
            return Response(
                {'error': 'Only managers and admins can access team calendar.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if user.role == 'MANAGER':
            team_member_ids = EmployeeProfile.objects.filter(
                reporting_manager=user
            ).values_list('user_id', flat=True)
            calendar_data = LeaveRequest.objects.filter(
                employee_id__in=team_member_ids,
                status='APPROVED'
            )
        else:
            calendar_data = LeaveRequest.objects.filter(status='APPROVED')

        # Apply date filters
        start_date = request.query_params.get('start_date')
        if start_date:
            calendar_data = calendar_data.filter(start_date__gte=start_date)

        end_date = request.query_params.get('end_date')
        if end_date:
            calendar_data = calendar_data.filter(end_date__lte=end_date)

        calendar_data = calendar_data.select_related('employee', 'leave_type').order_by('start_date')

        # Format response
        result = []
        for leave in calendar_data:
            result.append({
                'employee_id': leave.employee.employee_id,
                'employee_name': leave.employee.get_full_name(),
                'leave_type_code': leave.leave_type.code,
                'leave_type_name': leave.leave_type.name,
                'start_date': leave.start_date,
                'end_date': leave.end_date,
                'total_days': leave.total_days,
                'status': leave.status
            })

        serializer = TeamLeaveCalendarSerializer(result, many=True)
        return Response(serializer.data)
