# Project Understanding Document
## HR Leave & Attendance Management System

---

## 1. Project Overview

### System Name
**HR Leave & Attendance Management System (3-Role MVP)**

### Purpose
A simple internal web application designed for small-to-medium organizations to streamline:
- Employee profile and reporting structure management
- Leave request application and approval workflow
- Leave balance tracking and allocation
- Manual attendance recording
- Holiday calendar maintenance
- Monthly summary generation for HR review and payroll support

### Target Audience
Small-to-medium teams (up to 500 employees) where:
- Attendance is maintained manually (no biometric devices)
- Leave approvals follow a reporting-manager workflow
- HR needs basic reporting for payroll and compliance

### Core Value Proposition
- Simplified leave and attendance management
- Role-based access control for data security
- Quick operations: Apply leave in ≤1 minute, approve in ≤30 seconds
- Audit trail for compliance

---

## 2. User Roles and Their Scopes

### Role Comparison Matrix

| Feature | Employee | Manager | Admin/HR |
|---------|----------|---------|----------|
| **Data Access Scope** | Own records only | Direct reports + own | All employees |
| **Apply Leave** | ✓ (Self) | ✓ (Self) | ✓ (Self) |
| **Approve/Reject Leave** | ✗ | ✓ (Team only) | ✗ |
| **Cancel Leave** | ✓ (Pending only) | ✓ (Pending only) | ✗ |
| **View Leave Balance** | ✓ (Own) | ✓ (Own) | ✓ (All) |
| **Allocate/Adjust Balance** | ✗ | ✗ | ✓ |
| **Mark Attendance** | ✓ (Self, current day) | ✓ (Self, current day) | ✓ (Any employee, any day) |
| **Correct Attendance** | ✗ | ✗ | ✓ |
| **View Attendance History** | ✓ (Own, monthly) | ✓ (Team + own) | ✓ (All, monthly) |
| **Manage Employees** | ✗ | ✗ | ✓ (CRUD) |
| **Manage Holidays** | ✗ | ✗ | ✓ |
| **View Holidays** | ✓ | ✓ | ✓ |
| **Generate Reports** | ✓ (Own only) | ✓ (Team only) | ✓ (System-wide) |
| **Export Reports (CSV)** | ✗ | ✗ | ✓ |

---

### Role 1: Employee

**Who They Are:**
Any staff member in the organization who uses the system to manage their leave and attendance.

**Access Scope:**
- **Strictly limited to own records** - Cannot view or modify other employees' data
- No access to system configuration or reports beyond personal summaries

**Capabilities:**

**Leave Management:**
- Apply for leave with details: type (CL/SL/EL/LWP), dates, reason, optional attachment
- View leave balance by type (real-time)
- Track all leave requests with status: Pending, Approved, Rejected, Cancelled
- View manager's comments on approval/rejection decisions
- Cancel pending leave requests (before manager approval)

**Attendance Management:**
- Mark daily attendance for current day only
- Choose status: Present, Work From Home (WFH), Half-day
- View monthly attendance history
- Cannot edit past attendance entries

**Information Access:**
- View organization holiday calendar
- View personal monthly leave and attendance summaries

**Primary Goals:**
1. Quick and easy leave application
2. Real-time visibility into leave balance
3. Daily attendance marking
4. Track leave approval status

**Usage Pattern:**
- **Daily:** Mark attendance (1-2 minutes)
- **Occasional:** Apply for leave, check balance, view calendar
- **Monthly:** Review personal summaries

**Restrictions:**
- No access to other employees' information
- Cannot approve or manage team leaves
- Cannot correct attendance after the day ends
- Cannot modify leave balances
- No system administration capabilities

---

### Role 2: Manager

**Who They Are:**
Team leaders or supervisors who manage direct reportees and are responsible for approving their leave requests.

**Access Scope:**
- **Direct reports only** - Can view and manage leave requests from assigned team members
- Additionally has all Employee role capabilities for self-service
- No cross-team access or system-wide visibility

**Capabilities:**

**Team Management:**
- View list of employees reporting to them
- See team structure and basic employee details (names, designations)

**Leave Approval Workflow:**
- View pending leave requests from direct reports
- Approve or reject leave requests with optional comments/reasons
- System automatically notifies employee of decision
- View team's approved leave schedule (calendar/list view for planning)

**Team Visibility:**
- View monthly leave summary for team members
- Track team attendance patterns
- Plan team availability based on upcoming approved leaves

**Self-Service:**
- All Employee role capabilities for personal leave and attendance

**Primary Goals:**
1. Efficient leave approval workflow (≤30 seconds per request)
2. Team availability planning and conflict management
3. Monitor team leave patterns for better scheduling
4. Maintain team productivity while approving time off

**Usage Pattern:**
- **Reactive:** When leave requests arrive (requires quick turnaround)
- **Periodic:** Weekly or bi-weekly review of team leave calendar
- **Monthly:** Review team leave summaries for planning

**Restrictions:**
- **Cannot access other teams' data** - Only direct reports visible
- Cannot modify employee profiles, designations, or reporting structure
- Cannot correct or modify attendance (even for team members)
- Cannot allocate or adjust leave balances
- Cannot generate system-wide reports
- Cannot manage holidays or system settings

**Key Difference from Admin:**
- Managers have **approval authority** but no **administrative control**
- Focus is on workflow management, not system configuration

---

### Role 3: Admin/HR

**Who They Are:**
HR staff or system administrators responsible for employee lifecycle management, policy enforcement, data integrity, and reporting.

**Access Scope:**
- **Full system access** - Can view and manage all employees' data
- Cross-employee visibility for reporting and corrections
- System configuration and maintenance rights

**Capabilities:**

**Employee Lifecycle Management:**
- Create new employee accounts with credentials
- Update employee details: name, designation, department, contact info
- Assign reporting managers to establish hierarchy
- Deactivate employees (upon resignation/termination) without data deletion
- Maintain department and designation master data

**Leave Policy Administration:**
- Allocate yearly leave balances for each employee by type (CL/SL/EL/LWP)
- Adjust leave balances for corrections (e.g., carry-forward overrides, errors)
- View all employees' leave balances system-wide
- Monitor leave utilization patterns across organization

**Attendance Management:**
- Mark attendance for any employee on any day (backdated entries)
- Correct existing attendance entries with mandatory reason/comment
- Handle attendance disputes and corrections
- Ensure data integrity (no duplicates per employee per day)

**Holiday Calendar Management:**
- Create, update, and delete organization-wide holidays
- Maintain holiday descriptions and dates
- Plan annual holiday calendar

**Reporting & Analytics:**
- Generate monthly leave summary reports:
  - Organization-wide view
  - Filter by department, designation, or individual employee
  - Track leave trends and utilization
- Generate monthly attendance summary reports:
  - Employee-wise, department-wise views
  - Identify attendance issues or patterns
- Export all reports as CSV for payroll integration and compliance
- Provide data for payroll processing team

**Audit & Monitoring:**
- Review system logs for key actions (leave approvals, balance edits, attendance corrections)
- Ensure data integrity and policy compliance
- Handle escalations and disputes

**Primary Goals:**
1. Employee onboarding and profile maintenance
2. Leave policy enforcement and balance management
3. Data accuracy and integrity (especially attendance corrections)
4. Timely report generation for payroll and compliance
5. System health and maintenance

**Usage Pattern:**
- **Daily/Weekly:** Employee management, attendance corrections, balance adjustments
- **Monthly:** Generate and export reports for payroll
- **Ad-hoc:** Handle escalations, disputes, and special requests

**Special Privileges:**
- **Override capabilities:** Can correct attendance and adjust balances
- **Cross-employee access:** View and manage all employee data
- **System configuration:** Manage holidays, leave types (if configurable)
- **Full reporting access:** Export and analyze system-wide data

**Restrictions:**
- **Cannot approve/reject leave requests** - That's the manager's responsibility
- Admins maintain the system but do not interfere with approval workflows

**Key Difference from Manager:**
- Admins have **administrative control** but no **approval authority**
- Focus is on system configuration and data management, not workflow decisions

---

## 3. System Modules Overview

### 3.1 Employee Management Module
**Purpose:** Manage employee lifecycle and organizational structure

**Features:**
- Create, read, update, deactivate employees
- Assign reporting managers
- Maintain department and designation details

**Access Control:**
- **Admin:** Full CRUD access
- **Manager:** Read-only view of direct reports
- **Employee:** View own profile only

---

### 3.2 Leave Management Module
**Purpose:** Handle leave application, approval, and tracking workflow

**Features:**
- Leave request submission with validation
- Approval/rejection workflow with comments
- Leave balance validation and auto-update
- Overlapping leave prevention
- Cancellation support (pending requests only)
- Status tracking: Pending → Approved/Rejected/Cancelled

**Access Control:**
- **Employee:** Apply, cancel (own pending), view own requests
- **Manager:** Approve/reject (team only), view team leave schedule
- **Admin:** View all requests, no approval rights

**Business Rules:**
- Leave balance must be sufficient for paid leave types (CL/SL/EL)
- LWP (Leave Without Pay) can be applied even with zero balance
- No overlapping approved leaves for same employee
- Cancellation allowed only for pending requests

---

### 3.3 Leave Balance Management Module
**Purpose:** Track and allocate employee leave entitlements

**Features:**
- Yearly leave allocation by type
- Real-time balance updates on approval/cancellation
- Manual balance adjustments for corrections
- Balance visibility for employees

**Access Control:**
- **Employee:** View own balance (read-only)
- **Manager:** View own balance (read-only)
- **Admin:** Allocate and adjust balances (full control)

**Business Rules:**
- Balances updated automatically:
  - Deducted on leave approval
  - Restored on leave cancellation
- Admin can manually adjust for special cases

---

### 3.4 Attendance Management Module
**Purpose:** Track daily employee attendance manually

**Features:**
- Self-marking for current day (Present/WFH/Half-day)
- Attendance correction by admin for any day
- Duplicate prevention (one entry per employee per day)
- Monthly attendance view and summaries

**Access Control:**
- **Employee:** Mark own attendance (current day only)
- **Manager:** Mark own attendance (current day only)
- **Admin:** Mark/correct attendance for any employee, any day (with reason)

**Business Rules:**
- Employees can only mark today's attendance
- No duplicate entries allowed for same day
- Admin corrections require mandatory reason/comment
- Holidays auto-marked (no manual entry needed)

---

### 3.5 Holiday Calendar Module
**Purpose:** Maintain organization-wide holiday list

**Features:**
- Create, update, delete holidays
- View holiday calendar by all users

**Access Control:**
- **Admin:** Full CRUD access
- **Employee & Manager:** Read-only access

**Business Rules:**
- Holidays apply organization-wide (no branch/region variations in MVP)
- Employees need not mark attendance on holidays

---

### 3.6 Reports Module
**Purpose:** Generate leave and attendance summaries for review and payroll

**Features:**
- Monthly leave summary reports
- Monthly attendance summary reports
- Filtering by department, designation, employee
- CSV export for external processing

**Access Control:**
- **Employee:** View own monthly summaries (no export)
- **Manager:** View team summaries (no export)
- **Admin:** Generate system-wide reports, filter, and export CSV

**Use Cases:**
- HR: Payroll data preparation, compliance reporting
- Managers: Team planning and review
- Employees: Personal record tracking

---

## 4. Key System Workflows

### Workflow 1: Leave Application and Approval

```
1. Employee logs in and navigates to "Apply Leave"
   ↓
2. Fills form: Leave type, start date, end date, reason, attachment (optional)
   ↓
3. System validates:
   - No overlapping pending/approved leaves
   - Sufficient balance (for CL/SL/EL)
   ↓
4. Leave request submitted → Status = "Pending"
   ↓
5. Manager receives notification (in-app or email)
   ↓
6. Manager reviews request details and team calendar
   ↓
7. Manager decides:
   - APPROVE with optional comment → Balance deducted, status = "Approved"
   - REJECT with reason → Balance unchanged, status = "Rejected"
   ↓
8. Employee views updated status and manager's comment
   ↓
9. (Optional) Employee cancels pending leave → Status = "Cancelled", balance restored
```

**Participants:** Employee, Manager, System
**Duration:** Employee <1 min, Manager <30 sec
**Key Point:** Manager approval required for all leave types

---

### Workflow 2: Daily Attendance Marking

```
1. Employee logs in (morning/during work hours)
   ↓
2. Navigates to "Mark Attendance"
   ↓
3. Selects status for today:
   - Present
   - Work From Home (WFH)
   - Half-day
   ↓
4. System validates:
   - No existing entry for today
   - Date is current date (cannot mark future/past)
   ↓
5. Attendance recorded successfully
   ↓
6. (If error/missed) Admin can later correct attendance with reason
   ↓
7. Monthly view updated automatically
```

**Participants:** Employee (self-marking), Admin (corrections)
**Duration:** <1 minute daily
**Key Point:** Attendance is manual, honor-based system

---

### Workflow 3: Monthly Reporting (for HR/Payroll)

```
1. Admin navigates to "Reports" section
   ↓
2. Selects report type:
   - Leave Summary
   - Attendance Summary
   ↓
3. Selects month and year
   ↓
4. Applies filters (optional):
   - Department
   - Designation
   - Specific employee
   ↓
5. System generates report with:
   - Leave: Applications, approvals, rejections, balances
   - Attendance: Present days, WFH days, absences, half-days
   ↓
6. Admin reviews report on-screen
   ↓
7. Admin exports as CSV for payroll team
   ↓
8. Payroll team processes data externally
```

**Participants:** Admin, Payroll Team
**Frequency:** Monthly (end of month)
**Key Point:** CSV export enables integration with payroll systems

---

## 5. Technical Constraints and Limitations

### In-Scope for MVP
- Web-based application with email/password login
- Manual attendance (honor system)
- Simple yearly leave allocation (no monthly accrual)
- Fixed leave types: CL, SL, EL, LWP
- Reporting manager hierarchy (single manager per employee)
- Basic CSV export for reports

### Out-of-Scope (Intentionally Excluded)
- **Payroll integration:** Salary calculation, payslips, deductions
- **Biometric/device integration:** Fingerprint, face recognition, RFID
- **Geo-location attendance:** GPS-based check-in, selfie verification
- **Advanced leave policies:** Carry-forward, encashment, monthly accrual, leave lapse
- **Multi-branch/region:** Different holiday calendars, region-specific policies
- **Shift management:** Rostering, overtime calculation, shift allowances
- **Mobile app:** Web-only for MVP
- **Email notifications:** In-app status updates only (email can be added later)

### System Constraints
- **Performance target:** <2 seconds for normal operations (up to 500 employees)
- **Manual attendance only:** No external device integration
- **Single reporting manager:** No matrix reporting structure
- **Yearly allocation:** Leave balances allocated once per year by admin

---

## 6. Security and Compliance

### Role-Based Access Control (RBAC)
- **Principle of Least Privilege:** Users can only access data necessary for their role
- **Data Isolation:**
  - Employees: Own records only
  - Managers: Direct reports only
  - Admin: Full access

### Data Integrity Rules
- No duplicate attendance entries (employee + date uniqueness)
- No overlapping approved leaves for same employee
- Balance cannot go negative (for paid leave types)
- Audit trail for critical actions:
  - Leave approvals/rejections
  - Attendance corrections
  - Balance adjustments

### Auditability (Recommended)
System should log:
- Who approved/rejected each leave request
- Who corrected attendance and why
- Who adjusted balances and when

### Authentication
- Email/password-based login
- Credentials managed by Admin during employee creation
- (Optional future enhancement: Password reset, SSO, 2FA)

---

## 7. Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| **Usability** | Apply leave | ≤1 minute |
| | Approve leave | ≤30 seconds |
| | Simple UI | Minimal steps, intuitive navigation |
| **Performance** | Response time | <2 seconds for typical operations |
| | Scalability | Support up to 500 employees |
| **Security** | Access control | Strict RBAC enforcement |
| | Data privacy | Employees cannot access others' data |
| **Reliability** | Data integrity | No duplicates, no overlaps |
| | Audit trail | Log critical actions |
| **Maintainability** | Codebase | Clean, modular architecture |
| | Documentation | Clear API and user docs |

---

## 8. Success Criteria

This system will be successful if it achieves:

1. **For Employees:**
   - Fast and easy leave application (<1 min)
   - Clear visibility into leave balance and status
   - Simple daily attendance marking

2. **For Managers:**
   - Quick leave approval workflow (<30 sec)
   - Team availability visibility for planning
   - Minimal time spent on administrative tasks

3. **For Admin/HR:**
   - Accurate employee and leave data management
   - Timely monthly reports for payroll
   - Easy attendance corrections and balance adjustments
   - Reduced manual effort in tracking leave/attendance

4. **For Organization:**
   - Centralized leave and attendance tracking
   - Audit trail for compliance
   - Data integrity and security
   - Foundation for future enhancements (biometric, mobile, etc.)

---

## 9. Future Enhancements (Post-MVP)

While out-of-scope for this project, potential future additions include:

- Email/SMS notifications for leave approvals
- Mobile app for on-the-go attendance marking
- Biometric device integration for automated attendance
- Advanced leave policies (carry-forward, encashment, accrual)
- Multi-branch/region support with different holiday calendars
- Shift scheduling and overtime management
- Payroll system integration
- Dashboard with analytics and charts
- Employee self-service portal (update profile, upload documents)
- Approval delegation (manager assigns alternate approver)

---

## Document Summary

This document captures the understanding of the **HR Leave & Attendance Management System**, a 3-role web application designed for small-to-medium organizations. The system emphasizes:

- **Simplicity:** Quick operations, minimal steps, intuitive UI
- **Security:** Strict role-based access control, data isolation
- **Efficiency:** Streamlined workflows for leave approval and attendance tracking
- **Compliance:** Audit trails, data integrity, and monthly reporting

The three user roles (Employee, Manager, Admin/HR) each have clearly defined scopes and capabilities, ensuring data security while enabling efficient operations. The system is intentionally scoped as an MVP, excluding complex features like payroll integration and biometric attendance to keep the project manageable.

---

**Document Version:** 1.0
**Created:** February 9, 2026
**Based on:** Software Requirements Specification (SRS) - HR Leave & Attendance Management System
