# HR Leave & Attendance Management System

A web-based internal tool for small-to-medium organizations to manage employee leave requests, attendance tracking, and HR administration with role-based access control.

---

## Project Overview

This system streamlines leave and attendance operations across three user roles:

- **Employee** — Apply for leave, mark daily attendance, view balances and history
- **Manager** — Approve or reject team leave requests, monitor team attendance and calendar
- **Admin/HR** — Full system access: manage employees, departments, leave types, holidays, and generate reports

### Key Features

- Leave application and multi-step approval workflow (Pending → Approved / Rejected / Cancelled)
- Real-time leave balance tracking with automatic deduction on approval
- Daily attendance marking (Present, WFH, Half-day) with admin correction support
- Organization-wide holiday calendar management
- Department, designation, and employee lifecycle management
- Team leave calendar with monthly view for managers
- REST API with 60+ endpoints alongside a Django template + HTMX frontend
- Role-based access control enforced at every view and API endpoint
- Audit trail logging for critical actions (approvals, balance changes, corrections)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12.3 |
| Framework | Django 5.0.1 |
| REST API | Django REST Framework 3.14.0 |
| Frontend | Django Templates + HTMX 1.9.10 |
| UI Components | Bootstrap 5.3.2 + Bootstrap Icons |
| Database (dev) | SQLite 3 |
| Database (prod) | PostgreSQL |
| WSGI Server | Gunicorn |
| Static Files | WhiteNoise |
| CORS | django-cors-headers |
| Config | python-decouple, dj-database-url |

---

## Running the Project Locally

### Prerequisites

- Python 3.10 or higher
- pip

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd "leave man"
```

### 2. Create and activate a virtual environment

```bash
# Create
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Load initial leave types (CL, SL, EL, LWP)

```bash
python manage.py loaddata initial_leave_types
```

### 6. Create a superuser (Admin account)

```bash
python manage.py createsuperuser
```

You will be prompted for a username, email, password, employee ID, and role. Set role to `ADMIN`.

### 7. Run the development server

```bash
python manage.py runserver
```

Open your browser at: `http://localhost:8000`

Django admin panel: `http://localhost:8000/admin/`

---

## Default Test Accounts

After setup, you can create the following accounts via Django admin or the shell for testing:

| Username | Password | Role |
|---|---|---|
| admin | admin123 | ADMIN |
| manager | manager123 | MANAGER |
| employee | employee123 | EMPLOYEE |

> These credentials are for local development only. Change them before any production use.

---

## Project Structure

```
leave man/
├── employees/          # Custom User model, Department, Designation, EmployeeProfile
├── leaves/             # LeaveType, LeaveBalance, LeaveRequest models and APIs
├── attendance/         # Attendance records, Holiday calendar
├── core/               # AuditLog, shared permissions, dashboard views
├── frontend/           # Django template views (HTMX-based UI)
├── leave_management/   # Project settings, URLs, WSGI/ASGI config
├── templates/          # HTML templates
├── static/             # CSS, JS, images
├── requirements.txt
├── build.sh            # Render deployment build script
└── render.yaml         # Render hosting configuration
```

---

## Assumptions and Limitations

### Assumptions

- Attendance is **self-reported** (honor system) — no biometric or device integration
- Each employee has exactly **one reporting manager**; matrix reporting is not supported
- Leave balances are **allocated once per year** by the Admin — no monthly accrual or carry-forward
- The Admin role handles system configuration; **Admins do not approve leave requests** (that is the Manager's responsibility)
- Leave types are fixed to four categories: **CL** (Casual), **SL** (Sick), **EL** (Earned), **LWP** (Leave Without Pay)

### Current Limitations

- **No email notifications** — leave status updates are visible in-app only; email support is not yet implemented
- **No mobile app** — web-only; not optimized for small screens beyond Bootstrap's responsiveness
- **No payroll integration** — CSV export is available for Admin but no direct connection to payroll systems
- **No password reset flow** — passwords are managed by Admin during employee creation; self-service reset is not implemented
- **Single holiday calendar** — no multi-branch or region-specific holiday support
- **Reports module is partial** — leave and attendance reporting views are in progress; CSV export for Admins is planned but not fully complete
- **Media files** — uploaded leave attachments are stored locally; a cloud storage backend (e.g., S3) is recommended for production

### Out of Scope (Intentional MVP Exclusions)

- Payroll calculation or payslip generation
- Shift management or overtime tracking
- Leave carry-forward, encashment, or monthly accrual policies
- Biometric/geo-location-based attendance
- Multi-tenant or multi-organization support
