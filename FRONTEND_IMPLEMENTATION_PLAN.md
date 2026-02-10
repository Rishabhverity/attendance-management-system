# Frontend Implementation Plan
## HR Leave & Attendance Management System

---

## Executive Summary

This document outlines the complete frontend implementation plan for the HR Leave & Attendance Management System using **Django Templates + HTMX + Bootstrap**. The backend is **fully functional** with 64+ REST API endpoints tested and ready for integration.

**Backend Status:** ✅ 100% Complete & Tested
**Frontend Status:** 🚧 In Progress (Base templates created)

---

## Technology Stack

### Selected Approach: Django Templates + HTMX + Bootstrap

**Why This Stack?**
- ✅ **Single Codebase:** Frontend and backend in one Django project
- ✅ **Faster Development:** No separate build process or API integration complexity
- ✅ **Modern UX:** HTMX provides dynamic, SPA-like interactivity
- ✅ **Simpler Deployment:** Single application to deploy
- ✅ **Less Complexity:** No state management libraries needed
- ✅ **Built-in Security:** Django's CSRF protection and session management

**Tech Stack:**
```
- Django 5.0.1 (Backend + Frontend)
- Django Templates (Server-side rendering)
- HTMX 1.9.10 (Dynamic interactions)
- Bootstrap 5.3.2 (UI components)
- Bootstrap Icons 1.11.3 (Icons)
- Vanilla JavaScript (Custom interactions)
```

**Comparison with React:**
| Feature | Django Templates + HTMX | React + API |
|---------|------------------------|-------------|
| Learning Curve | Easy | Moderate |
| Development Speed | Fast | Slower |
| Deployment | Simple | Complex |
| Interactivity | Good (HTMX) | Excellent |
| SEO | Native | Requires SSR |
| State Management | Server-side | Client-side |

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Browser (Client)                     │
├─────────────────────────────────────────────────────┤
│              HTML + HTMX + Bootstrap                 │
│  ┌──────────────────────────────────────────────┐  │
│  │     HTMX handles dynamic interactions        │  │
│  │     (form submissions, partial updates)      │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                         ↓ HTTP Requests
┌─────────────────────────────────────────────────────┐
│         Django Server (Backend + Frontend)           │
│         http://localhost:8000/                       │
│  ┌──────────────────────────────────────────────┐  │
│  │     Django Views render HTML templates       │  │
│  │     HTMX endpoints return HTML fragments     │  │
│  │     REST APIs available for advanced use     │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Folder Structure

```
leave_management/
├── frontend/                    # New Django app for frontend views
│   ├── __init__.py
│   ├── apps.py
│   ├── views.py                 # All frontend views
│   ├── urls.py                  # Frontend URL routing
│   └── forms.py                 # Django forms for validation
├── templates/                   # HTML templates
│   ├── base.html               # ✅ Base template with navbar
│   ├── registration/
│   │   └── login.html          # ✅ Login page
│   └── frontend/               # Frontend app templates
│       ├── dashboard/
│       │   ├── employee.html
│       │   ├── manager.html
│       │   └── admin.html
│       ├── leaves/
│       │   ├── apply.html
│       │   ├── my_leaves.html
│       │   ├── leave_balance.html
│       │   ├── approvals.html
│       │   └── team_calendar.html
│       ├── attendance/
│       │   ├── mark.html
│       │   ├── my_attendance.html
│       │   ├── team_attendance.html
│       │   └── monthly_view.html
│       ├── admin/
│       │   ├── employees/
│       │   │   ├── list.html
│       │   │   ├── form.html
│       │   │   └── detail.html
│       │   ├── departments.html
│       │   ├── leave_types.html
│       │   ├── holidays.html
│       │   ├── reports.html
│       │   └── audit_logs.html
│       ├── profile.html
│       ├── change_password.html
│       └── components/          # Reusable template fragments
│           ├── stats_card.html
│           ├── leave_card.html
│           ├── attendance_calendar.html
│           └── pagination.html
├── static/                      # Static files
│   ├── css/
│   │   └── custom.css          # ✅ Custom styles
│   ├── js/
│   │   └── custom.js           # ✅ Custom JavaScript
│   └── images/
├── employees/                   # Existing apps (REST API)
├── leaves/
├── attendance/
└── core/
```

---

## How HTMX Works

### HTMX Basics

HTMX allows you to make AJAX requests directly from HTML attributes:

```html
<!-- Load content dynamically -->
<button hx-get="/api/dashboard/" hx-target="#content">
    Refresh Dashboard
</button>

<!-- Submit form with AJAX -->
<form hx-post="/leave/apply/" hx-target="#leave-list">
    <!-- form fields -->
</form>

<!-- Auto-refresh every 30 seconds -->
<div hx-get="/notifications/" hx-trigger="every 30s">
    Notifications
</div>
```

**HTMX Attributes:**
- `hx-get`, `hx-post`, `hx-put`, `hx-delete` - HTTP methods
- `hx-target` - Where to put the response
- `hx-swap` - How to swap content (innerHTML, outerHTML, etc.)
- `hx-trigger` - What triggers the request (click, submit, etc.)
- `hx-indicator` - Show loading spinner

### Django View Pattern for HTMX

```python
def leave_list(request):
    if request.htmx:  # HTMX request - return partial HTML
        leaves = LeaveRequest.objects.filter(employee=request.user)
        return render(request, 'frontend/components/leave_list_partial.html', {
            'leaves': leaves
        })
    else:  # Regular request - return full page
        leaves = LeaveRequest.objects.filter(employee=request.user)
        return render(request, 'frontend/leaves/my_leaves.html', {
            'leaves': leaves
        })
```

---

## Pages & Screens by Role

### Common Pages (All Roles)

#### 1. Login Page (`/login/`) ✅ COMPLETED
- Username/password fields
- Bootstrap styled form
- Error messages display
- Demo credentials info
- **Django View:** `LoginView` (built-in)
- **Template:** `templates/registration/login.html`

#### 2. Dashboard (`/dashboard/`)
- Role-based redirect:
  - Employee → Employee Dashboard
  - Manager → Manager Dashboard
  - Admin → Admin Dashboard
- **Django View:** `dashboard_view`
- **Templates:**
  - `frontend/dashboard/employee.html`
  - `frontend/dashboard/manager.html`
  - `frontend/dashboard/admin.html`

#### 3. Profile Page (`/profile/`)
- View user profile information
- Edit personal details
- Profile picture upload
- **Django View:** `profile_view`
- **Template:** `frontend/profile.html`

#### 4. Change Password (`/change-password/`)
- Old password verification
- New password with confirmation
- Validation rules display
- **Django View:** `change_password_view`
- **Template:** `frontend/change_password.html`

---

### Employee Dashboard & Pages

#### 1. Employee Dashboard (`/dashboard/`)
**Components:**
- Leave balance cards (by type)
- Pending leave requests count
- Attendance summary (this month)
- Quick action buttons:
  - Apply Leave
  - Mark Attendance Today
- Upcoming holidays
- Recent leave history

**Django View:**
```python
@login_required
def employee_dashboard(request):
    # Fetch dashboard data
    balances = LeaveBalance.objects.filter(
        employee__user=request.user,
        year=timezone.now().year
    )
    recent_leaves = LeaveRequest.objects.filter(
        employee__user=request.user
    ).order_by('-created_at')[:5]

    # Attendance stats for current month
    today = timezone.now().date()
    attendance_stats = Attendance.objects.filter(
        employee__user=request.user,
        date__month=today.month,
        date__year=today.year
    ).aggregate(
        present=Count('id', filter=Q(status='PRESENT')),
        wfh=Count('id', filter=Q(status='WFH')),
        half_day=Count('id', filter=Q(status='HALF_DAY'))
    )

    context = {
        'balances': balances,
        'recent_leaves': recent_leaves,
        'attendance_stats': attendance_stats,
        'upcoming_holidays': Holiday.objects.filter(
            date__gte=today
        ).order_by('date')[:5]
    }
    return render(request, 'frontend/dashboard/employee.html', context)
```

#### 2. My Leaves (`/leaves/my-leaves/`)
**Features:**
- Table with all leave requests
- Columns: Type, Dates, Days, Status, Applied On, Actions
- Filter dropdown (All, Pending, Approved, Rejected)
- Cancel button for pending leaves (HTMX)
- Status badges with colors
- Pagination

**HTMX Feature:**
```html
<!-- Cancel button with HTMX -->
<button class="btn btn-sm btn-danger"
        hx-post="/leaves/{{ leave.id }}/cancel/"
        hx-confirm="Are you sure you want to cancel this leave?"
        hx-target="#leave-row-{{ leave.id }}"
        hx-swap="outerHTML">
    Cancel
</button>
```

#### 3. Apply Leave (`/leaves/apply/`)
**Form Fields:**
- Leave type (dropdown)
- Start date (date picker)
- End date (date picker)
- Total days (auto-calculated with JS)
- Reason (textarea)
- Attachment (file upload, optional)

**Django Form:**
```python
class LeaveApplicationForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason', 'attachment']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Show available balance for each leave type
            self.fields['leave_type'].queryset = LeaveType.objects.all()
```

**Client-side Validation:**
```javascript
// Calculate days on date change
function updateLeaveDays() {
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    if (startDate && endDate) {
        const days = daysBetween(startDate, endDate);
        document.getElementById('days_display').textContent = `${days} day(s)`;
    }
}
```

#### 4. Leave Balance (`/leaves/balance/`)
**Features:**
- Cards for each leave type
- Shows: Allocated, Used, Available
- Progress bar visualization
- Year selector dropdown
- Color-coded: Green (>50%), Yellow (20-50%), Red (<20%)

#### 5. Mark Attendance (`/attendance/mark/`)
**Features:**
- Large prominent "Mark Attendance" button
- Status selector: Present, Work From Home, Half Day
- Shows if already marked today
- Confirmation message
- HTMX for instant update

**HTMX Implementation:**
```html
<form hx-post="/attendance/mark/"
      hx-target="#attendance-status"
      hx-swap="innerHTML">
    {% csrf_token %}
    <div class="mb-3">
        <label>Status</label>
        <select name="status" class="form-select" required>
            <option value="PRESENT">Present</option>
            <option value="WFH">Work From Home</option>
            <option value="HALF_DAY">Half Day</option>
        </select>
    </div>
    <button type="submit" class="btn btn-primary btn-lg w-100">
        Mark Attendance
    </button>
</form>
```

#### 6. My Attendance (`/attendance/my-attendance/`)
**Features:**
- Monthly calendar view
- Color-coded cells:
  - Green: Present/WFH
  - Orange: Half Day
  - Red: Absent
  - Yellow: On Leave
  - Purple: Holiday
  - Gray: Weekend
- Month/Year selector
- Summary stats (Present, Absent, WFH, Half Day)
- HTMX for month navigation

---

### Manager Dashboard & Pages

#### 1. Manager Dashboard (`/manager/dashboard/`)
**Components:**
- Team size stat card
- Pending approvals (with count badge)
- Team on leave today (list with names)
- Team attendance today stats
- Upcoming team leaves calendar
- Quick links

**Additional Stats:**
- Team attendance rate (this month)
- Most used leave type
- Team availability today

#### 2. Pending Approvals (`/leaves/approvals/`)
**Features:**
- List/cards of pending leave requests
- Employee info (name, ID, photo, department)
- Leave details (type, dates, days, reason)
- Attachment view (if uploaded)
- Approve/Reject buttons
- Comments modal for approval/rejection
- Filter by employee
- Sort by date

**HTMX Approval Modal:**
```html
<!-- Approve button opens modal -->
<button class="btn btn-success"
        data-bs-toggle="modal"
        data-bs-target="#approveModal{{ leave.id }}">
    Approve
</button>

<!-- Modal with HTMX form -->
<div class="modal" id="approveModal{{ leave.id }}">
    <form hx-post="/leaves/{{ leave.id }}/approve/"
          hx-target="#leave-card-{{ leave.id }}"
          hx-swap="outerHTML">
        {% csrf_token %}
        <textarea name="comments" class="form-control"
                  placeholder="Comments (optional)"></textarea>
        <button type="submit" class="btn btn-success">
            Confirm Approval
        </button>
    </form>
</div>
```

#### 3. Team Leave Calendar (`/leaves/team-calendar/`)
**Features:**
- Full calendar view (monthly)
- Each day shows employees on leave
- Color-coded by leave type
- Legend for leave types
- Date range selector
- Filter by leave type
- Export as PDF option

#### 4. Team Attendance (`/attendance/team/`)
**Features:**
- Team member list with today's status
- Search by employee name
- Date selector (view past dates)
- Status filter dropdown
- Summary stats

#### 5. Team Reports (`/reports/team/`)
**Features:**
- Leave summary for team
- Attendance summary for team
- Month/year selector
- Department filter
- Export as CSV button

---

### Admin Dashboard & Pages

#### 1. Admin Dashboard (`/admin/dashboard/`)
**Components:**
- Total employees, Active employees
- Departments count, Designations count
- Employees on leave today
- Pending leave requests (org-wide)
- Attendance marked today
- Leave utilization charts (by type)
- Recent activities
- Quick actions

**Charts (using Chart.js):**
- Leave distribution by type (pie chart)
- Monthly attendance trends (line chart)
- Department-wise leave utilization (bar chart)

#### 2. Employee Management (`/admin/employees/`)
**Features:**
- Data table with all employees
- Columns: ID, Name, Email, Department, Designation, Role, Status
- Search box (name, employee ID, email)
- Filters: Department, Designation, Role, Status
- Actions: View, Edit, Deactivate
- Add New Employee button
- Bulk actions (deactivate selected)
- Pagination (50 per page)

**HTMX Search:**
```html
<input type="search"
       name="search"
       hx-get="/admin/employees/search/"
       hx-trigger="keyup changed delay:500ms"
       hx-target="#employee-table"
       placeholder="Search employees...">
```

#### 3. Employee Form (`/admin/employees/new/`, `/admin/employees/{id}/edit/`)
**Form Fields:**
- Basic Info:
  - Username, Employee ID
  - Email
  - First Name, Last Name
  - Password (creation only)
  - Role (Employee, Manager, Admin)
- Job Details:
  - Department (dropdown)
  - Designation (dropdown)
  - Reporting Manager (dropdown)
  - Date of Joining (date picker)
- Contact:
  - Phone Number
- Profile Picture Upload

**Django Form with Validation:**
```python
class EmployeeForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ['username', 'employee_id', 'email', 'first_name',
                  'last_name', 'role']

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk is None:  # New employee
            if not cleaned_data.get('password'):
                raise forms.ValidationError("Password is required for new employees")
        # Additional validation...
        return cleaned_data
```

#### 4. Department Management (`/admin/departments/`)
**Features:**
- List of all departments
- Add new department (inline form or modal)
- Edit department name
- Delete department (with confirmation)
- Show employee count per department

#### 5. Designation Management (`/admin/designations/`)
**Features:**
- List of all designations
- Add new designation
- Edit designation name
- Delete designation (with confirmation)
- Show employee count per designation

#### 6. Leave Types (`/admin/leave-types/`)
**Features:**
- List of leave types (CL, PL, SL, etc.)
- Add new leave type
- Edit: name, code, is_paid, requires_documentation
- Cannot delete if in use
- Default annual allocation per type

#### 7. Leave Balance Allocation (`/admin/leave-balances/`)
**Features:**
- Two modes:
  1. **Individual Allocation:**
     - Employee selector
     - Leave type selector
     - Year selector
     - Allocated days input
     - Adjustment field
  2. **Bulk Allocation:**
     - Leave type selector
     - Year selector
     - Days input
     - Apply to: All employees / Specific department
     - Confirmation before bulk update

**HTMX Bulk Allocation:**
```html
<form hx-post="/admin/leave-balances/bulk-allocate/"
      hx-target="#allocation-result"
      hx-confirm="Are you sure you want to allocate {{ days }} days of {{ leave_type }} to {{ employee_count }} employees?">
    <!-- form fields -->
</form>
```

#### 8. Attendance Correction (`/admin/attendance/correct/`)
**Features:**
- Employee selector (with search)
- Date picker
- Load existing attendance for that date
- Status dropdown (Present, WFH, Half Day, Absent)
- Correction reason (required textarea)
- Submit button
- History of corrections

#### 9. Holiday Management (`/admin/holidays/`)
**Features:**
- Holiday calendar/list view
- Add new holiday form:
  - Name
  - Date
  - Description (optional)
  - Is Optional Holiday (checkbox)
- Edit/Delete actions
- Import holidays (CSV upload)
- Year filter

**HTMX Quick Add:**
```html
<form hx-post="/admin/holidays/add/"
      hx-target="#holiday-list"
      hx-swap="afterbegin">
    {% csrf_token %}
    <input type="text" name="name" placeholder="Holiday Name" required>
    <input type="date" name="date" required>
    <button type="submit">Add Holiday</button>
</form>
```

#### 10. Reports & Analytics (`/admin/reports/`)
**Features:**
- Report type selector:
  - Leave Summary
  - Attendance Summary
  - Employee Report
  - Department-wise Analysis
- Filters:
  - Month/Year
  - Department
  - Employee
- Generate report button
- View results in table
- Export options: CSV, PDF, Excel

**Charts:**
- Leave trends over time
- Attendance patterns
- Department comparisons

#### 11. Audit Logs (`/admin/audit-logs/`)
**Features:**
- Chronological list of all actions
- Columns: Timestamp, User, Action, Entity, Details
- Filters:
  - Date range
  - User
  - Action type (Created, Updated, Deleted, Approved, Rejected)
  - Entity type (Employee, Leave, Attendance)
- Search functionality
- Export logs as CSV
- Read-only view (no edit/delete)

---

## URL Routing Plan

### URL Structure

```python
# frontend/urls.py
from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),

    # Dashboard (role-based)
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Leaves (Employee)
    path('leaves/apply/', views.leave_apply, name='leave_apply'),
    path('leaves/my-leaves/', views.my_leaves, name='my_leaves'),
    path('leaves/balance/', views.leave_balance, name='leave_balance'),
    path('leaves/<int:pk>/cancel/', views.leave_cancel, name='leave_cancel'),

    # Leaves (Manager)
    path('leaves/approvals/', views.leave_approvals, name='leave_approvals'),
    path('leaves/<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('leaves/<int:pk>/reject/', views.leave_reject, name='leave_reject'),
    path('leaves/team-calendar/', views.team_leave_calendar, name='team_leaves'),

    # Attendance (Employee)
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/my-attendance/', views.my_attendance, name='my_attendance'),

    # Attendance (Manager)
    path('attendance/team/', views.team_attendance, name='team_attendance'),

    # Admin - Employees
    path('admin/employees/', views.employee_list, name='employee_list'),
    path('admin/employees/new/', views.employee_create, name='employee_create'),
    path('admin/employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('admin/employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),

    # Admin - Departments & Designations
    path('admin/departments/', views.department_list, name='department_list'),
    path('admin/designations/', views.designation_list, name='designation_list'),

    # Admin - Leave Management
    path('admin/leave-types/', views.leave_types, name='leave_types'),
    path('admin/leave-balances/', views.leave_balance_allocation, name='leave_balance_allocation'),

    # Admin - Attendance
    path('admin/attendance/correct/', views.attendance_correction, name='attendance_correction'),

    # Admin - Holidays
    path('admin/holidays/', views.holiday_list, name='holiday_list'),

    # Admin - Reports
    path('admin/reports/', views.reports, name='reports'),
    path('admin/audit-logs/', views.audit_logs, name='audit_logs'),
]
```

### Main URLs Update

```python
# leave_management/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),

    # Frontend URLs (Django Templates)
    path('', include('frontend.urls')),

    # API endpoints (REST API - optional for advanced use)
    path('api/', include('employees.urls')),
    path('api/', include('leaves.urls')),
    path('api/', include('attendance.urls')),
    path('api/', include('core.urls')),
]
```

---

## Implementation Phases

### ✅ Phase 1: Setup & Authentication (COMPLETED)
**Tasks:**
1. ✅ Create `frontend` Django app
2. ✅ Configure settings (INSTALLED_APPS, STATICFILES_DIRS)
3. ✅ Create base template with navigation
4. ✅ Create login page
5. ✅ Add Bootstrap and HTMX
6. ✅ Create custom CSS and JS files

**Status:** Base infrastructure ready

### 📋 Phase 2: Employee Dashboard & Core Features
**Tasks:**
1. Employee Dashboard view and template
2. Leave balance display (cards)
3. Apply Leave form with validation
4. My Leaves list with cancel functionality (HTMX)
5. Mark Attendance page with HTMX
6. Monthly attendance calendar view
7. Profile page
8. Change password page

**Deliverable:** Complete employee self-service portal

**Estimated Time:** 2-3 days

### 📋 Phase 3: Manager Features
**Tasks:**
1. Manager Dashboard
2. Pending Approvals page with HTMX approve/reject
3. Team Leave Calendar view
4. Team Attendance view
5. Team Reports page

**Deliverable:** Manager approval and team management features

**Estimated Time:** 2-3 days

### 📋 Phase 4: Admin Features - Part 1
**Tasks:**
1. Admin Dashboard with charts
2. Employee Management (list, create, edit, deactivate)
3. Department Management (CRUD)
4. Designation Management (CRUD)
5. Leave Types Management
6. Holiday Management

**Deliverable:** Basic admin operations

**Estimated Time:** 3-4 days

### 📋 Phase 5: Admin Features - Part 2
**Tasks:**
1. Leave Balance Allocation (individual + bulk)
2. Attendance Correction with history
3. Reports page with filters
4. CSV/PDF export functionality
5. Audit Logs viewer with filters

**Deliverable:** Complete admin functionality

**Estimated Time:** 2-3 days

### 📋 Phase 6: Polish & Testing
**Tasks:**
1. Error handling improvements
2. Loading states (HTMX indicators)
3. Form validations (client + server)
4. Responsive design (mobile-friendly)
5. Cross-browser testing
6. Performance optimization
7. User acceptance testing

**Deliverable:** Production-ready frontend

**Estimated Time:** 2-3 days

---

## Django Views Pattern

### Example: Employee Dashboard

```python
# frontend/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone

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
        employee_profile = request.user.employeeprofile
    except:
        employee_profile = None

    # Leave balances for current year
    current_year = timezone.now().year
    balances = LeaveBalance.objects.filter(
        employee=employee_profile,
        year=current_year
    ).select_related('leave_type')

    # Recent leave requests
    recent_leaves = LeaveRequest.objects.filter(
        employee=employee_profile
    ).select_related('leave_type').order_by('-created_at')[:5]

    # Attendance stats for current month
    today = timezone.now().date()
    attendance_stats = Attendance.objects.filter(
        employee=employee_profile,
        date__month=today.month,
        date__year=today.year
    ).aggregate(
        present=Count('id', filter=Q(status='PRESENT')),
        wfh=Count('id', filter=Q(status='WFH')),
        half_day=Count('id', filter=Q(status='HALF_DAY'))
    )

    # Check if attendance marked today
    attendance_marked_today = Attendance.objects.filter(
        employee=employee_profile,
        date=today
    ).exists()

    # Upcoming holidays
    upcoming_holidays = Holiday.objects.filter(
        date__gte=today
    ).order_by('date')[:5]

    context = {
        'balances': balances,
        'recent_leaves': recent_leaves,
        'attendance_stats': attendance_stats,
        'attendance_marked_today': attendance_marked_today,
        'upcoming_holidays': upcoming_holidays,
    }

    return render(request, 'frontend/dashboard/employee.html', context)
```

### Example: HTMX Leave Cancel

```python
from django.http import HttpResponse
from django.template.loader import render_to_string

@login_required
def leave_cancel(request, pk):
    """
    Cancel a leave request (HTMX endpoint)
    """
    if request.method == 'POST':
        try:
            leave = LeaveRequest.objects.get(
                id=pk,
                employee__user=request.user,
                status='PENDING'
            )

            # Cancel the leave (calls model method)
            leave.cancel()

            # Return updated row HTML
            html = render_to_string(
                'frontend/components/leave_row.html',
                {'leave': leave},
                request=request
            )

            # Add success message to response
            response = HttpResponse(html)
            response['HX-Trigger'] = 'showMessage'  # Trigger success message
            return response

        except LeaveRequest.DoesNotExist:
            return HttpResponse(
                '<tr><td colspan="6" class="text-danger">Leave not found or cannot be cancelled</td></tr>',
                status=404
            )

    return HttpResponse(status=405)
```

---

## Forms with Django

### Example: Leave Application Form

```python
# frontend/forms.py
from django import forms
from leaves.models import LeaveRequest, LeaveType

class LeaveApplicationForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason', 'attachment']
        widgets = {
            'leave_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'start_date',
                'required': True
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'end_date',
                'required': True
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter reason for leave',
                'required': True
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'leave_type': 'Leave Type',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'reason': 'Reason',
            'attachment': 'Supporting Document (Optional)'
        }

    def __init__(self, *args, employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee

        # Only show active leave types
        self.fields['leave_type'].queryset = LeaveType.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        leave_type = cleaned_data.get('leave_type')

        if start_date and end_date:
            # Check if end date is after start date
            if end_date < start_date:
                raise forms.ValidationError("End date must be after start date")

            # Check for overlapping leaves
            from django.db.models import Q
            overlapping = LeaveRequest.objects.filter(
                employee=self.employee,
                status__in=['PENDING', 'APPROVED']
            ).filter(
                Q(start_date__lte=end_date, end_date__gte=start_date)
            ).exists()

            if overlapping:
                raise forms.ValidationError(
                    "You have an overlapping leave request for these dates"
                )

            # Check leave balance
            if leave_type and self.employee:
                days_requested = (end_date - start_date).days + 1
                try:
                    balance = LeaveBalance.objects.get(
                        employee=self.employee,
                        leave_type=leave_type,
                        year=start_date.year
                    )
                    if balance.available < days_requested:
                        raise forms.ValidationError(
                            f"Insufficient leave balance. Available: {balance.available} days"
                        )
                except LeaveBalance.DoesNotExist:
                    raise forms.ValidationError(
                        "Leave balance not allocated for this leave type"
                    )

        return cleaned_data
```

---

## Template Examples

### Employee Dashboard Template

```django
{% extends 'base.html' %}
{% load static %}

{% block title %}Employee Dashboard{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row mb-4">
        <div class="col">
            <h2>Welcome, {{ user.first_name }}!</h2>
            <p class="text-muted">Employee ID: {{ user.employee_id }}</p>
        </div>
    </div>

    <!-- Quick Actions -->
    <div class="row mb-4">
        <div class="col-md-6 col-lg-3">
            <a href="{% url 'frontend:leave_apply' %}" class="btn btn-primary btn-lg w-100">
                <i class="bi bi-calendar-plus"></i> Apply Leave
            </a>
        </div>
        <div class="col-md-6 col-lg-3">
            <a href="{% url 'frontend:mark_attendance' %}" class="btn btn-success btn-lg w-100">
                <i class="bi bi-check-circle"></i> Mark Attendance
            </a>
        </div>
    </div>

    <!-- Leave Balances -->
    <div class="row mb-4">
        <div class="col-12">
            <h4>Leave Balance</h4>
        </div>
        {% for balance in balances %}
        <div class="col-md-6 col-lg-3">
            <div class="card">
                <div class="card-body">
                    <h6 class="text-muted">{{ balance.leave_type.name }}</h6>
                    <h2 class="mb-0">{{ balance.available }} <small class="text-muted">/ {{ balance.allocated }}</small></h2>
                    <div class="progress mt-2" style="height: 8px;">
                        <div class="progress-bar {% if balance.available > 5 %}bg-success{% elif balance.available > 2 %}bg-warning{% else %}bg-danger{% endif %}"
                             style="width: {{ balance.available|floatformat:0 }}%"></div>
                    </div>
                    <small class="text-muted">Used: {{ balance.used }}</small>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- Attendance Stats -->
    <div class="row mb-4">
        <div class="col-12">
            <h4>Attendance This Month</h4>
        </div>
        <div class="col-md-4">
            <div class="stat-card success">
                <h3>{{ attendance_stats.present|default:0 }}</h3>
                <p>Days Present</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="stat-card info">
                <h3>{{ attendance_stats.wfh|default:0 }}</h3>
                <p>Work From Home</p>
            </div>
        </div>
        <div class="col-md-4">
            <div class="stat-card warning">
                <h3>{{ attendance_stats.half_day|default:0 }}</h3>
                <p>Half Days</p>
            </div>
        </div>
    </div>

    <!-- Recent Leaves & Upcoming Holidays -->
    <div class="row">
        <div class="col-lg-6">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Recent Leave Requests</h5>
                </div>
                <div class="card-body">
                    {% if recent_leaves %}
                    <div class="list-group list-group-flush">
                        {% for leave in recent_leaves %}
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>{{ leave.leave_type.name }}</strong><br>
                                    <small class="text-muted">{{ leave.start_date|date:"M d" }} - {{ leave.end_date|date:"M d, Y" }}</small>
                                </div>
                                <span class="badge badge-{{ leave.status|lower }}">{{ leave.get_status_display }}</span>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <p class="text-muted">No leave requests yet.</p>
                    {% endif %}
                </div>
                <div class="card-footer">
                    <a href="{% url 'frontend:my_leaves' %}" class="btn btn-sm btn-outline-primary">View All</a>
                </div>
            </div>
        </div>

        <div class="col-lg-6">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Upcoming Holidays</h5>
                </div>
                <div class="card-body">
                    {% if upcoming_holidays %}
                    <div class="list-group list-group-flush">
                        {% for holiday in upcoming_holidays %}
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>{{ holiday.name }}</strong><br>
                                    <small class="text-muted">{{ holiday.date|date:"l, F d, Y" }}</small>
                                </div>
                                {% if holiday.is_optional %}
                                <span class="badge bg-info">Optional</span>
                                {% endif %}
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <p class="text-muted">No upcoming holidays.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Security Considerations

1. **CSRF Protection:** Django's built-in CSRF middleware (already configured)
2. **Authentication:** `@login_required` decorator on all views
3. **Authorization:** Check user role before rendering admin/manager pages
4. **XSS Prevention:** Django templates auto-escape HTML
5. **SQL Injection:** Use Django ORM (parameterized queries)
6. **File Uploads:** Validate file types and sizes
7. **Session Security:** Secure session cookies in production

---

## Performance Optimization

1. **Database Queries:**
   - Use `select_related()` for foreign keys
   - Use `prefetch_related()` for many-to-many
   - Add database indexes on frequently queried fields

2. **Template Optimization:**
   - Use template fragment caching
   - Minimize queries in templates

3. **Static Files:**
   - Use Django's `collectstatic` for production
   - Enable compression (Whitenoise)

4. **HTMX Benefits:**
   - Reduces page reloads
   - Partial page updates
   - Smaller payload sizes

---

## Deployment Checklist

### Production Settings

```python
# settings.py for production
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Deployment Steps

1. Set environment variables
2. Run `python manage.py collectstatic`
3. Run migrations
4. Create superuser
5. Configure web server (Nginx/Apache)
6. Setup WSGI server (Gunicorn/uWSGI)
7. Enable HTTPS with SSL certificate

---

## Summary

**Technology:** Django Templates + HTMX + Bootstrap
**Total Pages:** ~30 pages
**Development Approach:** Server-side rendering with HTMX for dynamic interactions
**Estimated Development Time:** 2-3 weeks
**Complexity:** Lower than React (single codebase, no API integration complexity)

**Currently Completed:**
- ✅ Base template with navigation
- ✅ Login page
- ✅ Bootstrap and HTMX setup
- ✅ Custom CSS and JavaScript

**Next Steps:**
1. Implement Employee Dashboard
2. Leave application and management pages
3. Attendance marking and viewing
4. Manager approval workflows
5. Admin management pages
6. Reports and analytics

**Advantages of This Approach:**
- ✅ Faster development
- ✅ Single deployment
- ✅ Easier maintenance
- ✅ Good performance
- ✅ SEO-friendly
- ✅ Progressive enhancement
