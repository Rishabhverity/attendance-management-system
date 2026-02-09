# HR Leave & Attendance Management System - Database Models

## Overview
This project contains Django database models for an HR Leave & Attendance Management System supporting 3 user roles: Employee, Manager, and Admin/HR.

## Database Models Created

### 1. **employees** app
- **User** - Custom user model with role-based access (EMPLOYEE, MANAGER, ADMIN)
- **Department** - Organization departments
- **Designation** - Job titles/designations
- **EmployeeProfile** - Extended employee information with reporting manager hierarchy

### 2. **leaves** app
- **LeaveType** - Leave types (CL, SL, EL, LWP)
- **LeaveBalance** - Employee leave balances by type and year
- **LeaveRequest** - Leave application and approval workflow

### 3. **attendance** app
- **Attendance** - Daily attendance records with correction tracking
- **Holiday** - Organization-wide holiday calendar

### 4. **core** app
- **AuditLog** - Audit trail for critical actions

## Project Structure

```
leave_management/
├── requirements.txt              # Python dependencies
├── employees/                    # Employee management app
│   ├── __init__.py
│   ├── models.py                 # User, EmployeeProfile, Department, Designation
│   ├── admin.py                  # Django admin configuration
│   └── apps.py
├── leaves/                       # Leave management app
│   ├── __init__.py
│   ├── models.py                 # LeaveType, LeaveBalance, LeaveRequest\n│   ├── admin.py
│   ├── apps.py
│   └── fixtures/
│       └── initial_leave_types.json  # Initial leave type data
├── attendance/                   # Attendance management app
│   ├── __init__.py
│   ├── models.py                 # Attendance, Holiday
│   ├── admin.py
│   └── apps.py
└── core/                         # Core utilities app
    ├── __init__.py
    ├── models.py                 # AuditLog
    ├── admin.py
    └── apps.py
```

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- PostgreSQL 13 or higher
- pip (Python package manager)

### Step 1: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\\Scripts\\activate
# On Unix/Mac:
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Create Django Project Configuration

You need to create the Django project configuration manually or use `django-admin`:

```bash
django-admin startproject leave_management .
```

This will create:
- `manage.py`
- `leave_management/` directory with `settings.py`, `urls.py`, etc.

### Step 4: Configure Database in settings.py

Edit `leave_management/settings.py`:

```python
# Custom User Model
AUTH_USER_MODEL = 'employees.User'

# Installed Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'corsheaders',

    # Local apps
    'employees.apps.EmployeesConfig',
    'leaves.apps.LeavesConfig',
    'attendance.apps.AttendanceConfig',
    'core.apps.CoreConfig',
]

# Database Configuration (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'leave_management_db',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# For development, you can use SQLite:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
```

### Step 5: Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE leave_management_db;
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
GRANT ALL PRIVILEGES ON DATABASE leave_management_db TO your_db_user;
\\q
```

Or use SQLite for quick development (no setup needed).

### Step 6: Run Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Step 7: Load Initial Data

```bash
# Load leave types (CL, SL, EL, LWP)
python manage.py loaddata initial_leave_types
```

### Step 8: Create Superuser

```bash
python manage.py createsuperuser
# Follow prompts to create admin user
# Enter: username, email, password, employee_id, role=ADMIN
```

### Step 9: Run Development Server

```bash
python manage.py runserver
```

Access Django admin at: `http://localhost:8000/admin/`

## Model Relationships

```
User (role: EMPLOYEE/MANAGER/ADMIN)
  │
  ├─1:1─> EmployeeProfile
  │         ├─FK─> Department
  │         ├─FK─> Designation
  │         └─FK─> User (reporting_manager, self-referential)
  │
  ├─1:M─> LeaveBalance
  │         └─FK─> LeaveType
  │
  ├─1:M─> LeaveRequest (as employee)
  │         ├─FK─> LeaveType
  │         └─FK─> User (approved_by)
  │
  ├─1:M─> Attendance
  │         └─FK─> User (marked_by)
  │
  └─1:M─> AuditLog

Standalone:
  - Holiday (organization-wide)
```

## Key Features

### User Model
- Custom Django user with `role` field (EMPLOYEE, MANAGER, ADMIN)
- Unique `employee_id` for company identification
- Methods: `is_employee()`, `is_manager()`, `is_admin_role()`

### EmployeeProfile
- One-to-one with User
- Self-referential FK for reporting manager hierarchy
- Soft delete with `is_active` field
- Method: `get_team_members()` for managers

### LeaveBalance
- Tracks allocated, used, and adjusted leave days
- Property: `available` (calculated as allocated + adjusted - used)
- Methods: `deduct(days)`, `restore(days)`

### LeaveRequest
- Status workflow: PENDING → APPROVED/REJECTED/CANCELLED
- Methods: `approve()`, `reject()`, `cancel()`
- Auto-updates leave balance on approval/cancellation
- Validates overlapping leaves

### Attendance
- Unique constraint: (employee, date)
- Tracks self-marking vs admin correction
- Method: `mark_correction()` for admin
- Prevents marking on holidays

### Holiday
- Unique date constraint
- Class method: `get_holidays_for_year(year)`
- Class method: `get_working_days_between(start, end)`

### AuditLog
- Tracks critical actions (leave approvals, balance adjustments, etc.)
- Class method: `log_action()` for creating entries
- Prevent manual creation/deletion in admin

## Admin Interface

All models are registered in Django admin with:
- List displays with key fields
- Search functionality
- Filters
- Readonly fields for timestamps
- Custom fieldsets for better organization

Access admin at: `http://localhost:8000/admin/`

## Sample Data Creation

After setup, you can create sample data via Django admin or shell:

```bash
python manage.py shell
```

```python
from employees.models import User, Department, Designation, EmployeeProfile
from leaves.models import LeaveType, LeaveBalance
from attendance.models import Holiday
from datetime import date

# Create department
dept = Department.objects.create(name="Engineering", description="Software Development")

# Create designation
desig = Designation.objects.create(title="Software Engineer", description="Develops software")

# Create admin user
admin = User.objects.create_user(
    username='admin',
    email='admin@company.com',
    password='admin123',
    employee_id='EMP001',
    role='ADMIN',
    first_name='Admin',
    last_name='User'
)
admin.is_staff = True
admin.is_superuser = True
admin.save()

# Create employee
employee = User.objects.create_user(
    username='john.doe',
    email='john@company.com',
    password='password123',
    employee_id='EMP002',
    role='EMPLOYEE',
    first_name='John',
    last_name='Doe'
)

# Create employee profile
profile = EmployeeProfile.objects.create(
    user=employee,
    department=dept,
    designation=desig,
    date_of_joining=date(2024, 1, 1),
    phone_number='+1234567890'
)

# Allocate leave balances
cl_type = LeaveType.objects.get(code='CL')
LeaveBalance.objects.create(
    employee=employee,
    leave_type=cl_type,
    year=2026,
    allocated=12.0
)

# Create holiday
Holiday.objects.create(
    name="New Year",
    date=date(2026, 1, 1),
    description="New Year's Day",
    created_by=admin
)
```

## Next Steps

1. **Create Views/APIs:** Build REST API using Django REST Framework
2. **Implement Permissions:** Create custom permission classes for RBAC
3. **Build Frontend:** React/Vue.js or Django templates
4. **Reports:** Query builders for monthly summaries
5. **Testing:** Write unit and integration tests
6. **Deployment:** Dockerize and deploy to production

## Database Constraints

### Unique Constraints
- `User.employee_id`
- `Department.name`
- `Designation.title`
- `LeaveType.code`
- `LeaveBalance`: (employee, leave_type, year)
- `Attendance`: (employee, date)
- `Holiday.date`

### Validation Rules
- LeaveRequest: start_date <= end_date
- LeaveRequest: No overlapping approved/pending leaves
- EmployeeProfile: reporting_manager cannot be self
- Attendance: Cannot mark on holidays

## Business Logic

### Leave Approval Workflow
1. Employee applies leave → Status = PENDING
2. Manager approves → Balance deducted, Status = APPROVED
3. Manager rejects → No balance change, Status = REJECTED
4. Employee cancels → Balance restored (if approved), Status = CANCELLED

### Attendance Marking
- **Employee:** Can only mark today's date
- **Admin:** Can mark/correct any date (with reason)
- **Validation:** One entry per employee per day

### Balance Management
- Auto-updated on leave approval/cancellation
- Admin can manually adjust via `adjusted` field
- Audit logged for all adjustments

## Troubleshooting

### Error: "No module named 'employees'"
- Ensure `employees.apps.EmployeesConfig` is in `INSTALLED_APPS`
- Check that `__init__.py` files exist in all app directories

### Error: "Table doesn't exist"
- Run `python manage.py makemigrations`
- Run `python manage.py migrate`

### Error: "Custom user model not found"
- Ensure `AUTH_USER_MODEL = 'employees.User'` is set BEFORE first migration
- If you already ran migrations, you may need to reset the database

### PostgreSQL Connection Error
-  Ensure PostgreSQL is running
- Check database credentials in `settings.py`
- Verify database exists: `psql -U postgres -l`

## Support

For questions or issues:
1. Review the SRS document (`Software_requirement_specification`)
2. Check the project understanding document (`PROJECT_UNDERSTANDING.md`)
3. Review Django documentation: https://docs.djangoproject.com/

## License

Internal use only - HR Leave & Attendance Management System
