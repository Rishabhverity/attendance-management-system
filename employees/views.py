"""
Views for Employee Management APIs.
Handles User, EmployeeProfile, Department, and Designation endpoints.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q

from .models import User, EmployeeProfile, Department, Designation
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    UserBasicSerializer, ChangePasswordSerializer,
    DepartmentSerializer, DesignationSerializer,
    EmployeeProfileSerializer
)
from core.permissions import IsAdmin, IsOwnerOrManager, IsAdminOrReadOnly


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet for authentication operations.
    Handles login, logout, password change, and profile management.
    """
    permission_classes = [AllowAny]
    serializer_class = UserSerializer  # Default serializer

    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Login user with username/email and password.
        POST /api/auth/login/
        """
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if user profile is active
            if hasattr(user, 'profile') and not user.profile.is_active:
                return Response(
                    {'error': 'Your account has been deactivated. Please contact HR.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            login(request, user)
            serializer = UserSerializer(user)
            return Response({
                'message': 'Login successful',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Logout current user.
        POST /api/auth/logout/
        """
        logout(request)
        return Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get', 'put'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get or update current user profile.
        GET/PUT /api/auth/me/
        """
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = UserUpdateSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                response_serializer = UserSerializer(request.user)
                return Response(response_serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change user password.
        POST /api/auth/change-password/
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Password changed successfully'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Employee/User management.
    Handles CRUD operations for employees.
    """
    queryset = User.objects.select_related('profile', 'profile__department', 'profile__designation').all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return UserBasicSerializer
        return UserSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        elif self.action in ['retrieve']:
            return [IsAuthenticated(), IsOwnerOrManager()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter queryset based on user role and query parameters."""
        user = self.request.user
        queryset = self.queryset

        # Filter by role
        if user.role == 'EMPLOYEE':
            # Employees can only see themselves
            queryset = queryset.filter(id=user.id)
        elif user.role == 'MANAGER':
            # Managers can see themselves and their team members
            team_member_ids = EmployeeProfile.objects.filter(
                reporting_manager=user
            ).values_list('user_id', flat=True)
            queryset = queryset.filter(Q(id=user.id) | Q(id__in=team_member_ids))
        # Admin can see all

        # Apply filters
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(profile__department_id=department)

        designation = self.request.query_params.get('designation')
        if designation:
            queryset = queryset.filter(profile__designation_id=designation)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(profile__is_active=is_active_bool)

        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_id__icontains=search) |
                Q(email__icontains=search)
            )

        return queryset.distinct()

    def destroy(self, request, *args, **kwargs):
        """Soft delete - deactivate employee instead of hard delete."""
        instance = self.get_object()
        if hasattr(instance, 'profile'):
            instance.profile.is_active = False
            instance.profile.save()
        instance.is_active = False
        instance.save()
        return Response(
            {'message': 'Employee deactivated successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def team(self, request):
        """
        Get manager's team members.
        GET /api/employees/team/
        """
        if request.user.role not in ['MANAGER', 'ADMIN']:
            return Response(
                {'error': 'Only managers and admins can access team members.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if request.user.role == 'MANAGER':
            team_members = User.objects.filter(
                profile__reporting_manager=request.user,
                profile__is_active=True
            ).select_related('profile', 'profile__department', 'profile__designation')
        else:
            # Admin can see all employees
            team_members = User.objects.filter(
                profile__is_active=True
            ).select_related('profile', 'profile__department', 'profile__designation')

        serializer = UserBasicSerializer(team_members, many=True)
        return Response(serializer.data)


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Department management.
    All authenticated users can read, only admins can write.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        """Filter departments based on search."""
        queryset = self.queryset
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class DesignationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Designation management.
    All authenticated users can read, only admins can write.
    """
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        """Filter designations based on search."""
        queryset = self.queryset
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        return queryset
