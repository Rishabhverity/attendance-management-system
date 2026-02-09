"""
Serializers for Employee Management.
Handles User, EmployeeProfile, Department, and Designation models.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, EmployeeProfile, Department, Designation


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""

    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class DesignationSerializer(serializers.ModelSerializer):
    """Serializer for Designation model."""

    class Meta:
        model = Designation
        fields = ['id', 'title', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for nested representations."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'employee_id', 'first_name', 'last_name', 'full_name', 'email', 'role']

    def get_full_name(self, obj):
        """Get user's full name."""
        return obj.get_full_name() or obj.username


class EmployeeProfileSerializer(serializers.ModelSerializer):
    """Serializer for EmployeeProfile model."""
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_title = serializers.CharField(source='designation.title', read_only=True)
    reporting_manager_name = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeProfile
        fields = [
            'department', 'department_name',
            'designation', 'designation_title',
            'reporting_manager', 'reporting_manager_name',
            'is_active', 'date_of_joining', 'phone_number',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_reporting_manager_name(self, obj):
        """Get reporting manager's full name."""
        if obj.reporting_manager:
            return obj.reporting_manager.get_full_name() or obj.reporting_manager.username
        return None


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer with profile information."""
    profile = EmployeeProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'employee_id', 'email',
            'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'is_staff',
            'date_joined', 'last_login',
            'profile'
        ]
        read_only_fields = ['date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_full_name(self, obj):
        """Get user's full name."""
        return obj.get_full_name() or obj.username


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users (Admin only)."""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    # Profile fields (optional during user creation)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        required=False,
        allow_null=True
    )
    designation = serializers.PrimaryKeyRelatedField(
        queryset=Designation.objects.all(),
        required=False,
        allow_null=True
    )
    reporting_manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    date_of_joining = serializers.DateField(required=False, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'username', 'employee_id', 'email',
            'first_name', 'last_name', 'role',
            'password', 'password_confirm',
            'is_staff',
            # Profile fields
            'department', 'designation', 'reporting_manager',
            'date_of_joining', 'phone_number'
        ]

    def validate(self, attrs):
        """Validate password match and other constraints."""
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # Validate reporting manager cannot be self
        if attrs.get('reporting_manager') and 'username' in attrs:
            # This will be checked after user creation
            pass

        return attrs

    def create(self, validated_data):
        """Create user and profile."""
        # Remove password_confirm and profile fields
        validated_data.pop('password_confirm')
        department = validated_data.pop('department', None)
        designation = validated_data.pop('designation', None)
        reporting_manager = validated_data.pop('reporting_manager', None)
        date_of_joining = validated_data.pop('date_of_joining', None)
        phone_number = validated_data.pop('phone_number', '')

        # Create user
        user = User.objects.create_user(**validated_data)

        # Create profile
        EmployeeProfile.objects.create(
            user=user,
            department=department,
            designation=designation,
            reporting_manager=reporting_manager,
            date_of_joining=date_of_joining,
            phone_number=phone_number
        )

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information."""
    # Profile fields
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        required=False,
        allow_null=True
    )
    designation = serializers.PrimaryKeyRelatedField(
        queryset=Designation.objects.all(),
        required=False,
        allow_null=True
    )
    reporting_manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    date_of_joining = serializers.DateField(required=False, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'role', 'is_staff',
            # Profile fields
            'department', 'designation', 'reporting_manager',
            'date_of_joining', 'phone_number', 'is_active'
        ]

    def update(self, instance, validated_data):
        """Update user and profile."""
        # Extract profile fields
        department = validated_data.pop('department', None)
        designation = validated_data.pop('designation', None)
        reporting_manager = validated_data.pop('reporting_manager', None)
        date_of_joining = validated_data.pop('date_of_joining', None)
        phone_number = validated_data.pop('phone_number', None)
        is_active = validated_data.pop('is_active', None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update profile
        profile, created = EmployeeProfile.objects.get_or_create(user=instance)
        if department is not None:
            profile.department = department
        if designation is not None:
            profile.designation = designation
        if reporting_manager is not None:
            profile.reporting_manager = reporting_manager
        if date_of_joining is not None:
            profile.date_of_joining = date_of_joining
        if phone_number is not None:
            profile.phone_number = phone_number
        if is_active is not None:
            profile.is_active = is_active
        profile.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        """Validate password change."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "New password fields didn't match."})
        return attrs

    def validate_old_password(self, value):
        """Validate old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def save(self, **kwargs):
        """Change user password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
