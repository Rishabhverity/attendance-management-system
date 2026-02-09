# REST API Endpoints Design Plan
## HR Leave & Attendance Management System

---

## Overview

This document outlines all REST API endpoints to be created for the 3-role system:
- **Employee** - Own data access
- **Manager** - Team data access + own data
- **Admin/HR** - Full system access

---

## API Structure

All API endpoints will be prefixed with `/api/`

**Base URL:** `http://localhost:8000/api/`

---

## 1. Authentication & User Management

### 1.1 Authentication Endpoints

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/auth/login/` | Login user (returns token/session) | Public |
| POST | `/api/auth/logout/` | Logout user | Authenticated |
| POST | `/api/auth/change-password/` | Change own password | Authenticated |
| GET | `/api/auth/me/` | Get current user profile | Authenticated |
| PUT | `/api/auth/me/` | Update own profile | Authenticated |

**Request/Response Examples:**

```json
// POST /api/auth/login/
Request: {
  "username": "john.doe",
  "password": "password123"
}
Response: {
  "user": {
    "id": 1,
    "username": "john.doe",
    "employee_id": "EMP001",
    "role": "EMPLOYEE",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@company.com"
  },
  "token": "abc123..." // If using JWT
}

// GET /api/auth/me/
Response: {
  "id": 1,
  "username": "john.doe",
  "employee_id": "EMP001",
  "role": "EMPLOYEE",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@company.com",
  "profile": {
    "department": "Engineering",
    "designation": "Software Engineer",
    "reporting_manager": "Jane Smith",
    "date_of_joining": "2024-01-01",
    "phone_number": "+1234567890",
    "is_active": true
  }
}
```

---

## 2. Employee Management APIs

### 2.1 Employee CRUD (Admin Only)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/employees/` | List all employees | Admin |
| POST | `/api/employees/` | Create new employee | Admin |
| GET | `/api/employees/{id}/` | Get employee details | Admin / Self / Manager (if direct report) |
| PUT | `/api/employees/{id}/` | Update employee | Admin |
| PATCH | `/api/employees/{id}/` | Partial update employee | Admin |
| DELETE | `/api/employees/{id}/` | Deactivate employee (soft delete) | Admin |

**Query Parameters for List:**
- `?department=<id>` - Filter by department
- `?designation=<id>` - Filter by designation
- `?is_active=true/false` - Filter active/inactive
- `?role=EMPLOYEE/MANAGER/ADMIN` - Filter by role
- `?search=<name>` - Search by name or employee_id

**Response Example:**

```json
// GET /api/employees/
Response: {
  "count": 50,
  "next": "http://localhost:8000/api/employees/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "username": "john.doe",
      "employee_id": "EMP001",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@company.com",
      "role": "EMPLOYEE",
      "profile": {
        "department": "Engineering",
        "designation": "Software Engineer",
        "reporting_manager_name": "Jane Smith",
        "is_active": true
      }
    }
  ]
}
```

### 2.2 Team Members (Manager Only)

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/employees/team/` | List manager's direct reports | Manager, Admin |

---

## 3. Department & Designation APIs

### 3.1 Departments

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/departments/` | List all departments | All authenticated |
| POST | `/api/departments/` | Create department | Admin |
| GET | `/api/departments/{id}/` | Get department details | All authenticated |
| PUT | `/api/departments/{id}/` | Update department | Admin |
| DELETE | `/api/departments/{id}/` | Delete department | Admin |

### 3.2 Designations

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/designations/` | List all designations | All authenticated |
| POST | `/api/designations/` | Create designation | Admin |
| GET | `/api/designations/{id}/` | Get designation details | All authenticated |
| PUT | `/api/designations/{id}/` | Update designation | Admin |
| DELETE | `/api/designations/{id}/` | Delete designation | Admin |

---

## 4. Leave Management APIs

### 4.1 Leave Types

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/leave-types/` | List all leave types | All authenticated |
| POST | `/api/leave-types/` | Create leave type | Admin |
| GET | `/api/leave-types/{id}/` | Get leave type details | All authenticated |
| PUT | `/api/leave-types/{id}/` | Update leave type | Admin |
| DELETE | `/api/leave-types/{id}/` | Delete leave type | Admin |

### 4.2 Leave Balances

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/leave-balances/` | List leave balances | Employee (own), Manager (team), Admin (all) |
| POST | `/api/leave-balances/` | Allocate leave balance | Admin |
| GET | `/api/leave-balances/{id}/` | Get balance details | Employee (own), Manager (team), Admin |
| PUT | `/api/leave-balances/{id}/` | Update/adjust balance | Admin |
| GET | `/api/leave-balances/my-balance/` | Get own leave balances | Employee, Manager |
| GET | `/api/leave-balances/employee/{emp_id}/` | Get employee balances | Manager (if team member), Admin |

**Response Example:**

```json
// GET /api/leave-balances/my-balance/
Response: [
  {
    "id": 1,
    "leave_type": {
      "id": 1,
      "code": "CL",
      "name": "Casual Leave"
    },
    "year": 2026,
    "allocated": 12.0,
    "used": 3.0,
    "adjusted": 0.0,
    "available": 9.0
  },
  {
    "id": 2,
    "leave_type": {
      "id": 2,
      "code": "SL",
      "name": "Sick Leave"
    },
    "year": 2026,
    "allocated": 10.0,
    "used": 1.0,
    "adjusted": 0.0,
    "available": 9.0
  }
]
```

### 4.3 Leave Requests

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/leave-requests/` | List leave requests | Employee (own), Manager (team), Admin (all) |
| POST | `/api/leave-requests/` | Apply for leave | Employee, Manager |
| GET | `/api/leave-requests/{id}/` | Get leave request details | Employee (own), Manager (if team member), Admin |
| PATCH | `/api/leave-requests/{id}/cancel/` | Cancel leave request | Employee (own pending/approved) |
| GET | `/api/leave-requests/my-requests/` | Get own leave requests | Employee, Manager |
| GET | `/api/leave-requests/pending/` | Get pending approvals | Manager (team), Admin |
| PATCH | `/api/leave-requests/{id}/approve/` | Approve leave request | Manager (if reporting manager), Admin |
| PATCH | `/api/leave-requests/{id}/reject/` | Reject leave request | Manager (if reporting manager), Admin |
| GET | `/api/leave-requests/team-calendar/` | Get team leave calendar | Manager (team), Admin |

**Query Parameters:**
- `?status=PENDING/APPROVED/REJECTED/CANCELLED` - Filter by status
- `?employee=<id>` - Filter by employee
- `?start_date=YYYY-MM-DD` - Filter from date
- `?end_date=YYYY-MM-DD` - Filter to date
- `?leave_type=<id>` - Filter by leave type

**Request/Response Examples:**

```json
// POST /api/leave-requests/ (Apply for leave)
Request: {
  "leave_type": 1,
  "start_date": "2026-03-01",
  "end_date": "2026-03-03",
  "total_days": 3.0,
  "reason": "Family vacation",
  "attachment": null // or file upload
}
Response: {
  "id": 45,
  "employee": {
    "id": 1,
    "name": "John Doe",
    "employee_id": "EMP001"
  },
  "leave_type": {
    "id": 1,
    "code": "CL",
    "name": "Casual Leave"
  },
  "start_date": "2026-03-01",
  "end_date": "2026-03-03",
  "total_days": 3.0,
  "reason": "Family vacation",
  "status": "PENDING",
  "applied_at": "2026-02-09T10:30:00Z",
  "approved_by": null,
  "manager_comments": ""
}

// PATCH /api/leave-requests/45/approve/
Request: {
  "comments": "Approved. Enjoy your vacation!"
}
Response: {
  "id": 45,
  "status": "APPROVED",
  "approved_by": {
    "id": 5,
    "name": "Jane Smith"
  },
  "decision_at": "2026-02-09T14:30:00Z",
  "manager_comments": "Approved. Enjoy your vacation!"
}

// GET /api/leave-requests/team-calendar/
Response: [
  {
    "employee": "John Doe",
    "leave_type": "CL",
    "start_date": "2026-03-01",
    "end_date": "2026-03-03",
    "total_days": 3.0,
    "status": "APPROVED"
  },
  {
    "employee": "Sarah Wilson",
    "leave_type": "EL",
    "start_date": "2026-03-05",
    "end_date": "2026-03-10",
    "total_days": 6.0,
    "status": "PENDING"
  }
]
```

---

## 5. Attendance Management APIs

### 5.1 Attendance CRUD

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/attendance/` | List attendance records | Employee (own), Manager (team), Admin (all) |
| POST | `/api/attendance/` | Mark attendance | Employee (today only), Admin (any date) |
| GET | `/api/attendance/{id}/` | Get attendance details | Employee (own), Manager (team), Admin |
| PUT | `/api/attendance/{id}/` | Update/correct attendance | Admin only |
| GET | `/api/attendance/my-attendance/` | Get own attendance | Employee, Manager |
| GET | `/api/attendance/monthly/` | Get monthly attendance | Employee (own), Manager (team), Admin (all) |
| PATCH | `/api/attendance/{id}/correct/` | Correct attendance with reason | Admin only |

**Query Parameters:**
- `?date=YYYY-MM-DD` - Filter by date
- `?employee=<id>` - Filter by employee
- `?month=MM&year=YYYY` - Filter by month
- `?status=PRESENT/WFH/HALF_DAY/ABSENT` - Filter by status

**Request/Response Examples:**

```json
// POST /api/attendance/ (Mark today's attendance)
Request: {
  "status": "PRESENT"
}
Response: {
  "id": 123,
  "employee": {
    "id": 1,
    "name": "John Doe"
  },
  "date": "2026-02-09",
  "status": "PRESENT",
  "is_self_marked": true,
  "marked_by": "John Doe",
  "marked_at": "2026-02-09T09:15:00Z",
  "correction_reason": ""
}

// GET /api/attendance/monthly/?month=2&year=2026
Response: [
  {
    "date": "2026-02-01",
    "status": "ABSENT",
    "is_holiday": true,
    "holiday_name": "Republic Day"
  },
  {
    "date": "2026-02-03",
    "status": "PRESENT",
    "is_self_marked": true
  },
  {
    "date": "2026-02-04",
    "status": "WFH",
    "is_self_marked": true
  },
  {
    "date": "2026-02-05",
    "status": "HALF_DAY",
    "is_self_marked": false,
    "correction_reason": "Adjusted for late arrival"
  }
]

// PATCH /api/attendance/123/correct/ (Admin correction)
Request: {
  "status": "HALF_DAY",
  "correction_reason": "Employee left early due to emergency"
}
Response: {
  "id": 123,
  "status": "HALF_DAY",
  "is_self_marked": false,
  "corrected_at": "2026-02-09T16:00:00Z",
  "correction_reason": "Employee left early due to emergency"
}
```

### 5.2 Holidays

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/holidays/` | List all holidays | All authenticated |
| POST | `/api/holidays/` | Create holiday | Admin |
| GET | `/api/holidays/{id}/` | Get holiday details | All authenticated |
| PUT | `/api/holidays/{id}/` | Update holiday | Admin |
| DELETE | `/api/holidays/{id}/` | Delete holiday | Admin |
| GET | `/api/holidays/year/{year}/` | Get holidays for a year | All authenticated |

**Response Example:**

```json
// GET /api/holidays/?year=2026
Response: [
  {
    "id": 1,
    "name": "New Year",
    "date": "2026-01-01",
    "description": "New Year's Day",
    "is_optional": false
  },
  {
    "id": 2,
    "name": "Republic Day",
    "date": "2026-01-26",
    "description": "Republic Day of India",
    "is_optional": false
  },
  {
    "id": 3,
    "name": "Independence Day",
    "date": "2026-08-15",
    "description": "Independence Day of India",
    "is_optional": false
  }
]
```

---

## 6. Reports APIs

### 6.1 Leave Reports

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/reports/leave-summary/` | Monthly leave summary | Employee (own), Manager (team), Admin (all) |
| GET | `/api/reports/leave-summary/export/` | Export leave summary as CSV | Admin, Manager (team) |

**Query Parameters:**
- `?month=MM&year=YYYY` - Required
- `?employee=<id>` - Filter by employee (Admin only)
- `?department=<id>` - Filter by department (Admin only)

**Response Example:**

```json
// GET /api/reports/leave-summary/?month=2&year=2026
Response: {
  "month": 2,
  "year": 2026,
  "summary": [
    {
      "employee": {
        "id": 1,
        "name": "John Doe",
        "employee_id": "EMP001",
        "department": "Engineering"
      },
      "leave_breakdown": {
        "CL": {
          "applied": 2,
          "approved": 2,
          "rejected": 0,
          "pending": 0
        },
        "SL": {
          "applied": 1,
          "approved": 1,
          "rejected": 0,
          "pending": 0
        }
      },
      "total_leaves_taken": 3.0
    }
  ]
}
```

### 6.2 Attendance Reports

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/reports/attendance-summary/` | Monthly attendance summary | Employee (own), Manager (team), Admin (all) |
| GET | `/api/reports/attendance-summary/export/` | Export attendance as CSV | Admin, Manager (team) |

**Query Parameters:**
- `?month=MM&year=YYYY` - Required
- `?employee=<id>` - Filter by employee (Admin only)
- `?department=<id>` - Filter by department (Admin only)

**Response Example:**

```json
// GET /api/reports/attendance-summary/?month=2&year=2026
Response: {
  "month": 2,
  "year": 2026,
  "total_working_days": 20,
  "summary": [
    {
      "employee": {
        "id": 1,
        "name": "John Doe",
        "employee_id": "EMP001"
      },
      "attendance_stats": {
        "present_days": 15,
        "wfh_days": 3,
        "half_days": 1,
        "absent_days": 0,
        "on_leave": 1,
        "holidays": 2,
        "attendance_percentage": 95.0
      }
    }
  ]
}
```

---

## 7. Dashboard/Statistics APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/dashboard/` | Get dashboard statistics | All authenticated |
| GET | `/api/dashboard/admin/` | Admin dashboard (org-wide stats) | Admin |
| GET | `/api/dashboard/manager/` | Manager dashboard (team stats) | Manager |

**Response Examples:**

```json
// GET /api/dashboard/ (Employee)
Response: {
  "user": {
    "name": "John Doe",
    "role": "EMPLOYEE"
  },
  "leave_balance_summary": [
    {"type": "CL", "available": 9.0},
    {"type": "SL", "available": 9.0},
    {"type": "EL", "available": 12.0}
  ],
  "pending_leave_requests": 1,
  "upcoming_leaves": [
    {
      "start_date": "2026-03-01",
      "end_date": "2026-03-03",
      "leave_type": "CL",
      "status": "PENDING"
    }
  ],
  "attendance_this_month": {
    "present": 6,
    "absent": 0,
    "wfh": 1
  },
  "upcoming_holidays": [
    {
      "name": "Holi",
      "date": "2026-03-14"
    }
  ]
}

// GET /api/dashboard/manager/
Response: {
  "team_size": 8,
  "pending_approvals": 3,
  "team_on_leave_today": 2,
  "team_attendance_today": {
    "present": 5,
    "wfh": 1,
    "absent": 0,
    "on_leave": 2
  },
  "upcoming_team_leaves": [
    {
      "employee": "Sarah Wilson",
      "start_date": "2026-02-15",
      "end_date": "2026-02-17",
      "leave_type": "EL"
    }
  ]
}

// GET /api/dashboard/admin/
Response: {
  "total_employees": 50,
  "active_employees": 48,
  "total_departments": 5,
  "stats": {
    "employees_on_leave_today": 5,
    "pending_leave_requests": 12,
    "attendance_marked_today": 43,
    "attendance_pending_today": 0
  },
  "leave_utilization": {
    "CL": {"allocated": 600, "used": 150, "percentage": 25},
    "SL": {"allocated": 500, "used": 80, "percentage": 16},
    "EL": {"allocated": 600, "used": 200, "percentage": 33}
  }
}
```

---

## 8. Audit Log APIs

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/audit-logs/` | List audit logs | Admin |
| GET | `/api/audit-logs/{id}/` | Get audit log details | Admin |

**Query Parameters:**
- `?action=LEAVE_APPROVED/BALANCE_ADJUSTED/etc.` - Filter by action
- `?user=<id>` - Filter by user who performed action
- `?date=YYYY-MM-DD` - Filter by date

---

## API Authentication & Permissions

### Authentication Method
**Session-based authentication** (default for MVP)
- Login via `/api/auth/login/`
- Session cookie stored in browser
- Logout via `/api/auth/logout/`

**Optional JWT authentication** (can be added later):
- Login returns JWT token
- Include token in header: `Authorization: Bearer <token>`

### Permission Classes

**IsEmployee:**
- Can access own records only
- Cannot access team or org-wide data

**IsManager:**
- Can access own records
- Can access direct reports' data
- Can approve/reject team leave requests
- Cannot access other teams' data

**IsAdmin:**
- Full system access
- Can CRUD all resources
- Can access all reports
- Can allocate/adjust balances

---

## Error Responses

All endpoints return standard error responses:

```json
// 400 Bad Request
{
  "error": "Invalid input",
  "detail": {
    "start_date": ["This field is required."],
    "end_date": ["End date must be after start date."]
  }
}

// 401 Unauthorized
{
  "error": "Authentication required",
  "detail": "Authentication credentials were not provided."
}

// 403 Forbidden
{
  "error": "Permission denied",
  "detail": "You do not have permission to perform this action."
}

// 404 Not Found
{
  "error": "Not found",
  "detail": "Leave request with id 999 not found."
}

// 500 Internal Server Error
{
  "error": "Server error",
  "detail": "An unexpected error occurred."
}
```

---

## Summary of Endpoints

| Module | Endpoints Count | Access Levels |
|--------|-----------------|---------------|
| Authentication | 5 | Public + Authenticated |
| Employees | 7 | Admin (mostly), Self (read) |
| Departments | 5 | All (read), Admin (write) |
| Designations | 5 | All (read), Admin (write) |
| Leave Types | 5 | All (read), Admin (write) |
| Leave Balances | 6 | Role-based |
| Leave Requests | 9 | Role-based |
| Attendance | 7 | Role-based |
| Holidays | 6 | All (read), Admin (write) |
| Reports | 4 | Role-based |
| Dashboard | 3 | Role-based |
| Audit Logs | 2 | Admin only |

**Total: ~64 API endpoints**

---

## Implementation Order

### Phase 1 (Core APIs):
1. Authentication APIs
2. Employee management APIs
3. Department & Designation APIs
4. Leave Type APIs

### Phase 2 (Leave Workflow):
5. Leave Balance APIs
6. Leave Request APIs (apply, approve, reject, cancel)

### Phase 3 (Attendance):
7. Attendance APIs (mark, correct)
8. Holiday APIs

### Phase 4 (Reports & Analytics):
9. Report APIs (leave summary, attendance summary)
10. Dashboard APIs
11. Audit Log APIs

---

## Next Steps

Once you approve this API design, I will:

1. **Create serializers** for all models (data validation & transformation)
2. **Create permission classes** (IsEmployee, IsManager, IsAdmin)
3. **Create viewsets/views** for all endpoints
4. **Configure URL routing** for all APIs
5. **Test all endpoints** using Django REST Framework's browsable API
6. **Create API documentation** (optional: using drf-spectacular for OpenAPI/Swagger)

**Estimated implementation time:** 2-3 hours

Would you like me to proceed with this API design, or would you like to modify/add/remove any endpoints?
