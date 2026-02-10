# HR Leave Management System - Features by User Role

**Last Updated:** February 10, 2026
**Project Status:** Phase 4 In Progress

---

## 1. EMPLOYEE Role Features

### Authentication & Profile
- ✅ **Login/Logout** - Secure authentication system
- ✅ **Profile Management** - View and update personal information
- ✅ **Change Password** - Update account password

### Dashboard
- ✅ **Employee Dashboard** - Personalized overview with:
  - Leave balance summary (by leave type)
  - Upcoming leaves display
  - Recent attendance records
  - Quick action buttons

### Leave Management
- ✅ **Apply for Leave** - Submit leave requests with:
  - Leave type selection (CL, SL, EL, LWP)
  - Date range picker
  - Reason for leave
  - Optional file attachment
  - Real-time balance validation
- ✅ **My Leaves** - View all leave requests with:
  - Status tracking (Pending, Approved, Rejected, Cancelled)
  - Filtering by status and leave type
  - Detailed view of each request
  - Manager approval details
- ✅ **Cancel Leave Request** - Cancel pending leave requests
- ✅ **Leave Balance View** - Check available leave balance by type

### Attendance Management
- ✅ **Mark Attendance** - Daily attendance marking with:
  - Status options (Present, WFH, Half Day, Absent)
  - Current date marking only
  - Automatic date validation
  - Leave status check (prevents duplicate marking)
  - HTMX-based instant submission
- ✅ **My Attendance** - View personal attendance history with:
  - Monthly calendar view
  - Date range filtering
  - Daily attendance list
  - Status color coding
  - Export capability

### Summary for Employee
**Total Features:** 11 completed features across 3 main categories

---

## 2. MANAGER Role Features

### Dashboard
- ✅ **Manager Dashboard** - Team management overview with:
  - Team size statistics
  - Pending approvals count
  - Team members on leave today
  - Team attendance summary
  - Quick action buttons for team management

### Leave Approval & Management
- ✅ **Leave Approvals** - Process team leave requests with:
  - List of pending leave requests from team members
  - Filtering by employee and status
  - Detailed request information
  - Approve/Reject actions with comments
  - HTMX-based instant updates
  - Email notifications (backend ready)
- ✅ **Approve Leave Request** - Approve with:
  - Manager comments
  - Automatic balance deduction
  - Status update to employee
  - Audit trail logging
- ✅ **Reject Leave Request** - Reject with:
  - Mandatory rejection reason
  - No balance impact
  - Status update to employee
  - Audit trail logging

### Team Monitoring
- ✅ **Team Leave Calendar** - Visual calendar showing:
  - Month view with navigation
  - All team members' approved leaves
  - Filter by employee
  - Filter by leave type
  - Holiday markers
  - Weekend highlighting
  - Color-coded leave indicators
  - Tooltips with employee details
- ✅ **Team Attendance** - Monitor team attendance with:
  - Daily view - See who's present/absent/WFH today
  - Weekly view - Week-at-a-glance attendance
  - Monthly summary - Aggregate statistics per employee
  - Date filtering
  - Leave status integration
  - Export to CSV (backend ready)
- ✅ **Team Reports** - Placeholder for detailed analytics

### Inherited Employee Features
- ✅ All Employee features (managers can also apply for leaves, mark attendance, etc.)

### Summary for Manager
**Total Features:** 6 unique manager features + 11 employee features = 17 total features

---

## 3. ADMIN/HR Role Features

### Dashboard
- ✅ **Admin Dashboard** - Organization-wide overview with:
  - Total employees count
  - Active employees count
  - Departments count
  - Designations count
  - Employees on leave today
  - Pending leave requests (all employees)
  - Attendance marked today
  - Quick access to all admin functions

### Master Data Management

#### Department Management (✅ COMPLETED)
- ✅ **View Departments** - List all departments with:
  - Department name
  - Description
  - Created date
  - Employee count (implied)
- ✅ **Add Department** - Create new departments with:
  - Name (unique validation)
  - Description
  - HTMX modal form
  - Instant feedback
- ✅ **Edit Department** - Update department details with:
  - Same validation as create
  - Duplicate name prevention
  - HTMX-based editing
- ✅ **Delete Department** - Remove departments with:
  - Validation (cannot delete if employees assigned)
  - Confirmation modal
  - Safe deletion

#### Designation Management (✅ COMPLETED)
- ✅ **View Designations** - List all job titles with:
  - Designation title
  - Description
  - Created date
  - Employee count (implied)
- ✅ **Add Designation** - Create new designations with:
  - Title (unique validation)
  - Description
  - HTMX modal form
- ✅ **Edit Designation** - Update designation details
- ✅ **Delete Designation** - Remove designations with:
  - Validation (cannot delete if employees assigned)
  - Confirmation modal

#### Leave Types Management (✅ COMPLETED)
- ✅ **View Leave Types** - List all leave types with:
  - Code (CL, SL, EL, LWP)
  - Full name
  - Paid/Unpaid status
  - Documentation requirement
  - Max consecutive days
  - Description
- ✅ **Add Leave Type** - Create new leave types with:
  - Code (unique, auto-uppercase)
  - Name
  - Paid checkbox
  - Requires documentation checkbox
  - Max consecutive days (optional)
  - Description
  - Full validation
- ✅ **Edit Leave Type** - Update leave type configuration
- ✅ **Delete Leave Type** - Remove leave types with:
  - Validation (cannot delete if used in leave requests)
  - Validation (cannot delete if used in leave balances)
  - Safe deletion

#### Holiday Management (✅ COMPLETED)
- ✅ **View Holidays** - Organization-wide holiday calendar with:
  - Filter by year
  - Date display with day of week
  - Holiday name
  - Type (Mandatory/Optional)
  - Description
  - Holiday statistics (total, mandatory, optional)
- ✅ **Add Holiday** - Create holidays with:
  - Name
  - Date (with date picker)
  - Optional checkbox
  - Description
  - Duplicate date validation
  - Creator tracking
- ✅ **Edit Holiday** - Update holiday details with:
  - Same validation as create
  - Year filtering maintained
- ✅ **Delete Holiday** - Remove holidays with:
  - Confirmation modal
  - Immediate removal

### Employee Management (⏳ PENDING)
- ⏳ **View All Employees** - List all employees with details
- ⏳ **Add Employee** - Create new employee accounts
- ⏳ **Edit Employee** - Update employee information
- ⏳ **Deactivate Employee** - Soft delete employees
- ⏳ **Assign Department** - Change employee department
- ⏳ **Assign Designation** - Change employee designation
- ⏳ **Assign Manager** - Set reporting manager

### Leave Balance Management (⏳ PENDING)
- ⏳ **View Leave Balances** - See all employee leave balances
- ⏳ **Allocate Leave Balance** - Assign yearly leave quotas by:
  - Employee selection
  - Leave type
  - Year
  - Allocated days
  - Bulk allocation option
- ⏳ **Adjust Leave Balance** - Manual adjustments with reason
- ⏳ **Balance History** - Track all balance changes

### Attendance Management
- ✅ **All Leave Approvals** - Can view and approve ANY leave request (not just team)
- ⏳ **Attendance Correction** - Correct employee attendance with:
  - Employee selection
  - Date selection
  - Status change
  - Correction reason
  - Audit trail

### Reports & Analytics (⏳ PENDING)
- ⏳ **Leave Reports** - Generate reports by:
  - Department
  - Employee
  - Leave type
  - Date range
  - Export to CSV/PDF
- ⏳ **Attendance Reports** - Organization-wide attendance analytics
- ⏳ **Balance Reports** - Leave balance summary reports
- ⏳ **Custom Reports** - Flexible report builder

### Audit & Compliance (⏳ PENDING)
- ⏳ **Audit Logs** - View all system actions with:
  - User who performed action
  - Action type
  - Timestamp
  - Before/after values
  - IP address
  - Search and filter capabilities

### Inherited Features
- ✅ All Manager features (can manage teams if assigned as manager)
- ✅ All Employee features (can apply for leaves, mark attendance)

### Summary for Admin
**Completed:** 16 admin-specific features
**Pending:** ~15 admin-specific features
**Total (when complete):** 31 admin features + 17 manager/employee features = 48 total features

---

## Feature Completion Summary

### ✅ Phase 1: Setup & Authentication (100% Complete)
- User authentication (login/logout)
- Role-based access control (ADMIN, MANAGER, EMPLOYEE)
- Password management
- Profile management

### ✅ Phase 2: Employee Features (100% Complete)
- Employee dashboard
- Leave application
- Leave tracking
- Attendance marking
- Attendance history
- Leave balance viewing

### ✅ Phase 3: Manager Features (100% Complete)
- Manager dashboard
- Team leave approvals
- Team leave calendar
- Team attendance monitoring
- Approval workflow (approve/reject)

### 🔄 Phase 4: Admin Features (55% Complete)
**Completed:**
- Admin dashboard ✅
- Department management (CRUD) ✅
- Designation management (CRUD) ✅
- Leave types management (CRUD) ✅
- Holiday management (CRUD) ✅

**In Progress/Pending:**
- Employee management (CRUD) ⏳
- Leave balance allocation ⏳
- Attendance correction ⏳
- Reports & analytics ⏳
- Audit logs ⏳

---

## Technical Features (All Roles)

### User Interface
- ✅ Responsive design (Bootstrap 5.3.2)
- ✅ HTMX-based dynamic interactions
- ✅ Modal forms for CRUD operations
- ✅ Toast notifications for feedback
- ✅ Color-coded status badges
- ✅ Calendar widgets
- ✅ Date pickers
- ✅ File upload support

### Security
- ✅ Role-based access control
- ✅ Permission checks on all views
- ✅ CSRF protection
- ✅ SQL injection protection (Django ORM)
- ✅ XSS protection (Django templates)
- ✅ Password hashing (Django auth)

### Data Validation
- ✅ Unique constraint checks
- ✅ Date range validation
- ✅ Balance availability checks
- ✅ Overlapping leave detection
- ✅ Business rule enforcement
- ✅ Cascade delete prevention

### Performance
- ✅ Query optimization with select_related()
- ✅ Database indexes on foreign keys
- ✅ Efficient pagination ready
- ✅ HTMX for reduced page loads

---

## API Endpoints (Backend REST API - Already Built)

### Authentication Endpoints
- `POST /api/auth/login/` - Login
- `POST /api/auth/logout/` - Logout
- `POST /api/auth/change-password/` - Change password

### Employee Endpoints
- `GET /api/employees/profile/` - Get profile
- `PUT /api/employees/profile/` - Update profile
- `GET /api/employees/` - List employees (admin/manager)

### Leave Endpoints
- `GET /api/leaves/types/` - List leave types
- `GET /api/leaves/balance/` - Get leave balance
- `POST /api/leaves/request/` - Apply for leave
- `GET /api/leaves/my-requests/` - My leave requests
- `PUT /api/leaves/requests/{id}/cancel/` - Cancel request
- `GET /api/leaves/pending-approvals/` - Pending (manager)
- `PUT /api/leaves/requests/{id}/approve/` - Approve (manager)
- `PUT /api/leaves/requests/{id}/reject/` - Reject (manager)

### Attendance Endpoints
- `POST /api/attendance/mark/` - Mark attendance
- `GET /api/attendance/my-attendance/` - Get my attendance
- `GET /api/attendance/team/` - Team attendance (manager)
- `PUT /api/attendance/{id}/correct/` - Correct (admin)

### Admin Endpoints
- `GET/POST /api/departments/` - Department CRUD
- `GET/POST /api/designations/` - Designation CRUD
- `GET/POST /api/leave-types/` - Leave type CRUD
- `GET/POST /api/holidays/` - Holiday CRUD
- Many more... (64+ endpoints total)

**Note:** Full REST API with 64+ endpoints is already implemented in the backend. Frontend is progressively connecting to these endpoints.

---

## Testing Accounts

| Username | Password | Role | Purpose |
|----------|----------|------|---------|
| admin | admin123 | ADMIN | Full system access |
| manager | manager123 | MANAGER | Team management testing |
| employee | employee123 | EMPLOYEE | Basic feature testing |

---

## Next Steps for Phase 4 Completion

1. ⏳ **Employee Management** (Complex - requires user creation, profile, assignments)
2. ⏳ **Leave Balance Allocation** (Requires employee management first)
3. ⏳ **Attendance Correction** (Straightforward admin override functionality)
4. ⏳ **Reports Module** (Complex - requires report builder, export functionality)
5. ⏳ **Audit Logs** (Read-only view of system actions)

---

## Technology Stack

- **Backend:** Django 5.0.1 + Django REST Framework
- **Frontend:** Django Templates + HTMX 1.9.10 + Bootstrap 5.3.2
- **Database:** PostgreSQL (configured)
- **Authentication:** Django built-in authentication
- **UI Framework:** Bootstrap Icons, custom CSS

---

**Document Version:** 1.0
**Generated:** Phase 4 (Admin Features) - 55% Complete
**Total System Completion:** ~80% (3.5 out of 4 phases complete)
