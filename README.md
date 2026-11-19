# University Community Services Library Management System
### Supporting UN Sustainable Development Goal 4 (Quality Education)

An enterprise-grade, production-quality Web Application built with **Python Flask**, **SQLAlchemy ORM**, **MySQL** (with automated fallback to SQLite for zero-setup execution), and a modern, responsive **Bootstrap 5** frontend. Designed for university community service projects to ensure equitable, transparent, and inclusive access to physical and digital educational literature.

---

## 📖 Project Overview & SDG 4 Alignment

The **United Nations Sustainable Development Goal 4 (Quality Education)** aims to ensure inclusive and equitable quality education and promote lifelong learning opportunities for all. This Library Management System directly addresses Target 4.1 and Target 4.6 by providing:
- **Democratized Access to Knowledge**: Real-time catalogue discovery for textbooks, research periodicals, and academic literature.
- **Fair Resource Allocation**: Strict 3-book borrow limit and 14-day loan cycles ensuring books circulate continuously rather than being monopolized.
- **Automated Fine & Accountability System**: Transparent, tamper-evident late return fine tracking (Rs. 2.00 / day).
- **Waiting List Equity**: Priority-based reservations for high-demand course materials when physical copies are out of stock.

---

## 🏗️ Architecture & Tech Stack

```
                          [ Client Browser ]
                     (Bootstrap 5, Chart.js, JS)
                                  │
                                  ▼
                        [ Flask WSGI Engine ]
     (Application Factory Pattern • Blueprints • CSRFProtect • LoginManager)
       ├── auth_bp   : User authentication, registration, password recovery
       ├── admin_bp  : Dashboard, circulation, inventory, reports, audit logs
       ├── books_bp  : Public catalogue, live search, reservation queue
       └── member_bp : Student loan status, fine liability, reading history
                                  │
                                  ▼
                        [ SQLAlchemy ORM ]
                       (Parameterized Queries)
                                  │
                                  ▼
                       [ Database Layer ]
     MySQL (Production / schema.sql) ◄──► SQLite (Instant dev fallback)
```

- **Backend**: Python 3.10+ / Flask 3.x (Blueprints & Application Factory Pattern).
- **Database**: MySQL 8.x (using SQLAlchemy ORM + PyMySQL) with SQLite automatic fallback for zero-configuration testing.
- **Security**:
  - Werkzeug scrypt/pbkdf2 password hashing.
  - Flask-Login secure session management with "Remember me" cookies.
  - Flask-WTF CSRF tokens on all state-altering forms.
  - Time-limited cryptographic tokens (`itsdangerous.URLSafeTimedSerializer`) for password resets.
  - Role-based Access Control via `@admin_required` and `@active_member_required` decorators.
  - Strict input sanitization and parameterized SQL execution.
- **Frontend**: Jinja2 semantic templates, Bootstrap 5.3, Bootstrap Icons, FontAwesome 6, Chart.js for data visualization, and client-side form validation.
- **Exporting**: CSV streaming and PDF document generation via ReportLab.

---

## 🗄️ Database Schema & Relational Integrity

The schema uses foreign keys with cascading updates/deletes, check constraints on stock counts, and indexes on lookup fields:

```
┌──────────────────┐           ┌──────────────────┐
│    categories    │           │      users       │
├──────────────────┤           ├──────────────────┤
│ id (PK)          │           │ id (PK)          │
│ name (UNIQUE)    │           │ name             │
└────────┬─────────┘           │ email (UNIQUE)   │
         │ 1                   │ student_id (UNIQ)│
         │                     │ password_hash    │
         │ N                   │ role (admin/mem) │
┌────────┴─────────┐           │ status (act/ina) │
│      books       │           │ created_at       │
├──────────────────┤           └────────┬─────────┘
│ id (PK)          │                    │
│ title            │                    │ 1
│ author           │                    │
│ category_id (FK) │                    │
│ isbn (UNIQUE)    │                    │
│ total_copies     │                    │
│ available_copies │                    │
│ cover_image      │                    │
│ created_at       │                    │
└────────┬─────────┘                    │
         │                              │
         ├──────────────────┐           │
         │ 1                │ 1         │
         │                  │           │
         │ N                │ N         │ N
┌────────┴─────────┐   ┌────┴───────────┴─┐   ┌──────────────────┐
│   transactions   │   │   reservations   │   │  activity_logs   │
├──────────────────┤   ├──────────────────┤   ├──────────────────┤
│ id (PK)          │   │ id (PK)          │   │ id (PK)          │
│ user_id (FK)     │   │ user_id (FK)     │   │ user_id (FK)     │
│ book_id (FK)     │   │ book_id (FK)     │   │ action           │
│ issue_date       │   │ status           │   │ timestamp        │
│ due_date         │   │ created_at       │   └──────────────────┘
│ return_date      │   └──────────────────┘
│ fine_amount      │
│ status           │
└──────────────────┘
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have Python 3.10 or later installed.
Check version:
```bash
python --version
```

### 2. Clone / Open Project
Navigate to the project directory:
```bash
cd library_management_system
```

### 3. Setup Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables (`.env`)
Copy `.env.example` to `.env`:
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

To run with **MySQL**, update the `DATABASE_URL` in `.env`:
```ini
DATABASE_URL=mysql+pymysql://root:your_mysql_password@localhost:3306/library_db
```
To run with **SQLite** (zero configuration, works out of the box):
```ini
DATABASE_URL=sqlite:///library.db
```

### 6. Initialize & Seed Database
Run the seed script to create all schema tables, seed academic categories, 32 curated textbooks, 10 student members, 1 librarian administrator, and sample transactions:
```bash
python seed.py
```

### 7. Run Automated Test Suite
```bash
python -m pytest -v
```

### 8. Start the Web Server
```bash
python run.py
```
Open your browser and navigate to: **[http://127.0.0.1:5000/](http://127.0.0.1:5000/)**

---

## 🔑 Default Credentials

| Role | Email | Password | Student ID | Quota / Privileges |
| :--- | :--- | :--- | :--- | :--- |
| **Librarian (Admin)** | `admin@univ.edu` | `Admin@123` | — | Full access to circulation, book CRUD, member status, reports, and audit logs |
| **Student Member #1** | `student1@univ.edu` | `Student@123` | `STU-2026-001` | Active loan + 1 Overdue book (demonstrates fine notice) |
| **Student Member #2** | `student2@univ.edu` | `Student@123` | `STU-2026-002` | Active on-time loan |
| **Student Members 3-10**| `student3@univ.edu` .. `student10@univ.edu` | `Student@123` | `STU-2026-003` .. `010` | Standard borrowing eligibility |

*(New students can also self-register via the **Register** button).*

---

## 🎯 Key Feature Walkthrough

### 👨‍💼 Administrator / Librarian Portal
1. **Interactive Dashboard**:
   - Real-time KPI summary (Total Titles, Available Shelf Copies, Issued Books, Overdue Count, Fine Revenue).
   - **Circulation Analytics (Chart.js)**: Monthly issues bar graph and category composition doughnut chart.
   - Live stream of recent circulation transactions and audit events.
2. **Book Inventory Management**:
   - Add new books with optional cover image upload (PNG, JPG, WebP up to 5MB).
   - Edit titles, authors, categories, ISBNs, and adjust physical stock.
   - Delete protection: Books cannot be deleted if any copies are actively borrowed.
3. **Member Directory**:
   - Search by name, email, or Student ID.
   - One-click account activation / deactivation.
   - Complete borrowing history view per member.
4. **Circulation Workflow (Issue / Return)**:
   - **Issue Book**: Select member and book. Checks borrow quota (max 3) and stock (>0). Auto-computes due date (today + 14 days).
   - **Process Return**: Auto-computes late fine at Rs. 2.00 / overdue day. Restocks shelf inventory and alerts if a reservation is waiting.
5. **Reporting & Audit Center**:
   - Overdue loans liability tracker.
   - Top most frequently issued titles.
   - Top active student readers.
   - **One-click Export**: Generate downloadable **PDF Reports** or **CSV spreadsheets**.
   - Audit trail capturing timestamps and actors for administrative actions.

### 👩‍🎓 Student / Member Portal
1. **Personal Dashboard**:
   - Summary of active loans, remaining days, and overdue warnings.
   - Real-time late fine calculations.
   - Active book reservation statuses.
2. **Live Book Catalogue**:
   - Debounced instant search across Title, Author, ISBN, and Catalog ID.
   - Academic category filter badges and availability filters.
   - Real-time shelf inventory counter.
3. **Reservation System**:
   - When a book's physical copies reach 0, members can place a reservation to be notified upon return.
4. **Account & Profile Management**:
   - Edit personal details, change passwords securely, or request password reset links.

---

## 🎓 Viva & Technical Presentation Guide

When explaining this project in an examination or viva:
1. **Application Factory (`create_app`)**: Explain how decoupling extension initialization from the application instance prevents circular dependencies and allows creating isolated instances for testing (`TestingConfig`).
2. **Relational Database Design**: Highlight foreign key cascading rules (`ON UPDATE CASCADE`, `ON DELETE RESTRICT`), relational indexes on high-query columns (`isbn`, `email`, `student_id`), and table check constraints.
3. **Defense-in-depth Security**:
   - **CSRF Protection**: Form inputs contain unique cryptographic tokens validated by `Flask-WTF`.
   - **Role Decorators**: `@admin_required` checks both `current_user.is_authenticated` and `current_user.is_admin`, aborting with HTTP 403 on violations.
   - **Password Hashing**: Passwords are never stored in plaintext; Werkzeug's salted cryptographic hashes protect user credentials.
   - **SQL Injection Prevention**: SQLAlchemy ORM compiles all database operations into parameterized queries.
4. **Business Logic Integrity**:
   - Borrow limit check: `len(active_transactions) < 3`.
   - Due date logic: `date.today() + timedelta(days=14)`.
   - Late fee formula: `max(0, (return_date - due_date).days) * 2.0`.
   - Race conditions prevented by atomic decrement/increment of `available_copies`.

---

## 🧪 Running Automated Tests

Run the complete test suite with verbose reporting:
```bash
python -m pytest -v
```
All 14 tests covering authentication, access control, catalogue queries, issue limit validation, overdue fine calculation, and reservation queues should pass.
