# TaskFlow Pro

<div align="center">

**A production-quality task management platform built for modern teams.**

Next.js · Flask · MySQL · TypeScript · Tailwind CSS · Chart.js

[![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

</div>

---

## Overview

**TaskFlow Pro** is a full-stack SaaS-style task management system designed as a capstone-ready application. It combines a cinematic dark UI with robust backend APIs, role-based access control, and comprehensive modules for tasks, employees, projects, analytics, and reporting.

### Why TaskFlow Pro?

| Capability | Description |
|------------|-------------|
| **Premium UI** | Glassmorphism, gradient accents, Framer Motion animations, dark/light themes |
| **Full RBAC** | Admin, Manager, and Employee roles with scoped data access |
| **Task Management** | Kanban (drag-and-drop), list, and table views with priorities & subtasks |
| **Team Management** | Employee profiles, departments, skills, performance tracking |
| **Analytics** | Chart.js dashboards with department and productivity metrics |
| **Reports** | Export employees, tasks, projects, and overdue items as CSV or PDF |
| **Real-time UX** | Global search (⌘K), notifications, toast feedback, loading skeletons |

---

## Screenshots & Pages

| Page | Route | Description |
|------|-------|-------------|
| Landing | `/` | Hero, features, workflow, testimonials, FAQ |
| Login / Signup | `/login`, `/signup` | Auth with password strength meter |
| Dashboard | `/dashboard` | Stats widgets, charts, activity feed |
| Tasks | `/dashboard/tasks` | Kanban, list, table views |
| Employees | `/dashboard/employees` | Team directory and profiles |
| Projects | `/dashboard/projects` | Milestones, members, progress |
| Calendar | `/dashboard/calendar` | Monthly view with workload sidebar |
| Analytics | `/dashboard/analytics` | Performance and workload charts |
| Reports | `/dashboard/reports` | CSV & PDF exports |
| Settings | `/dashboard/settings` | Theme, notifications, password |

---

## Tech Stack

```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND          │  BACKEND           │  DATABASE      │
│  Next.js 16        │  Python Flask 3    │  MySQL 8.0+    │
│  TypeScript        │  SQLAlchemy        │  Normalized    │
│  Tailwind CSS v4   │  bcrypt auth       │  schema with   │
│  Framer Motion     │  REST APIs         │  foreign keys  │
│  Chart.js          │  ReportLab PDF     │                │
│  shadcn/ui patterns│  Flask-CORS        │                │
└─────────────────────────────────────────────────────────┘
```

---

## Prerequisites

Before you begin, ensure you have:

| Tool | Version | Check |
|------|---------|-------|
| **Node.js** | 18+ | `node --version` |
| **npm** | 9+ | `npm --version` |
| **Python** | 3.10+ | `python --version` |
| **MySQL** | 8.0+ | See setup below |
| **Git** | Any | `git --version` |

---

## Quick Start (Windows)

### Step 1 — Install & start MySQL

**Option A: XAMPP (recommended for students)**

1. Download [XAMPP](https://www.apachefriends.org/) and install
2. Open **XAMPP Control Panel** → click **Start** next to **MySQL**
3. Default credentials: user `root`, password **(empty)**

**Option B: MySQL Installer**

1. Download [MySQL Community Server](https://dev.mysql.com/downloads/installer/)
2. Install with a root password you'll remember
3. Start the **MySQL80** service in Windows Services

**Verify MySQL is running:**

```powershell
Test-NetConnection localhost -Port 3306
# TcpTestSucceeded should be True
```

---

### Step 2 — Clone & configure

```powershell
cd D:\Task_Management

# Configure database credentials
# Edit backend\.env — set MYSQL_PASSWORD if you use one
```

**`backend/.env`** (default for XAMPP):

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=taskflow_pro
SECRET_KEY=change-this-in-production
FLASK_DEBUG=1
CORS_ORIGINS=http://localhost:3000
```

**`frontend/.env.local`**:

```env
NEXT_PUBLIC_API_URL=http://localhost:5000/api
```

---

### Step 3 — One-command setup

```powershell
cd D:\Task_Management
powershell -ExecutionPolicy Bypass -File setup.ps1
```

This will:
- Install Python and Node dependencies
- Create the `taskflow_pro` database
- Create all tables
- Seed demo users, tasks, and projects

**Or run manually:**

```powershell
# Backend
cd backend
pip install -r requirements.txt --user
python setup_db.py

# Frontend
cd ..\frontend
npm install
```

---

### Step 4 — Run the application

Open **two terminals**:

**Terminal 1 — Backend API**

```powershell
cd D:\Task_Management\backend
python run.py
```

✅ API running at **http://localhost:5000**

**Terminal 2 — Frontend**

```powershell
cd D:\Task_Management\frontend
npm run dev
```

✅ App running at **http://localhost:3000**

---

### Step 5 — Login

Open **http://localhost:3000** and sign in:

| Email | Password | Role | Access |
|-------|----------|------|--------|
| `admin@taskflow.pro` | `Admin@123` | Admin | Full system control |
| `manager@taskflow.pro` | `Admin@123` | Manager | Employees + tasks |
| `employee@taskflow.pro` | `Admin@123` | Employee | Own tasks only |

---

## Project Structure

```
Task_Management/
│
├── database/                 # SQL schema & seed files
│   ├── schema.sql            # Full MySQL schema (manual setup)
│   └── seed.sql              # Demo data (manual setup)
│
├── backend/                  # Flask REST API
│   ├── app/
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── routes/           # API blueprints (auth, tasks, etc.)
│   │   └── utils/            # Auth helpers, pagination
│   ├── setup_db.py           # ⭐ Automated DB setup (recommended)
│   ├── seed_db.py            # Demo data seeder
│   ├── init_db.py            # Create tables only
│   ├── run.py                # Start Flask server
│   ├── requirements.txt
│   └── .env                  # Database & secret config
│
├── frontend/                 # Next.js application
│   ├── src/
│   │   ├── app/              # Pages (App Router)
│   │   │   ├── page.tsx      # Landing page
│   │   │   ├── login/        # Auth pages
│   │   │   └── dashboard/    # Protected app pages
│   │   ├── components/       # UI & layout components
│   │   └── lib/              # API client, auth, utils
│   ├── .env.local
│   └── package.json
│
├── setup.ps1                 # Windows one-click setup
└── README.md
```

---

## API Reference

Base URL: `http://localhost:5000/api`

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login` | Login with email & password |
| `POST` | `/auth/register` | Create new account |
| `POST` | `/auth/logout` | End session |
| `GET` | `/auth/me` | Get current user |
| `POST` | `/auth/forgot-password` | Request password reset |
| `POST` | `/auth/change-password` | Change password |

### Core Modules

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/stats` | Dashboard statistics |
| `GET` | `/dashboard/chart-data` | Chart.js data |
| `GET` | `/tasks?view=kanban` | Kanban board data |
| `GET` | `/tasks/:id` | Task detail with comments |
| `PUT` | `/tasks/:id` | Update task |
| `GET` | `/employees` | List employees |
| `GET` | `/projects` | List projects |
| `GET` | `/analytics` | Analytics data |
| `GET` | `/search?q=` | Global search |
| `GET` | `/reports/csv/:type` | Download CSV report |
| `GET` | `/reports/pdf/:type` | Download PDF report |

All protected endpoints require header: `Authorization: Bearer <token>`

---

## Features Guide

### Task Management
- **Kanban board** — drag cards between columns to change status
- **List & table views** — alternative layouts with inline status editing
- **Subtasks** — check off items; progress auto-calculates
- **Comments & history** — collaboration and audit trail per task

### Role-Based Access Control

| Feature | Admin | Manager | Employee |
|---------|:-----:|:-------:|:--------:|
| View all tasks | ✅ | ✅ | Own only |
| Manage employees | ✅ | ✅ | ❌ |
| Audit logs | ✅ | ❌ | ❌ |
| Analytics (org-wide) | ✅ | ✅ | Own data |
| Create tasks | ✅ | ✅ | ✅ |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + K` / `⌘ + K` | Open global search |
| `Escape` | Close modals |

### Password Reset (Development)

Email is not configured in development. When you use **Forgot Password**, the API returns a direct reset link on screen. Click it to set a new password.

---

## Testing Checklist

Use this to verify everything works after setup:

- [ ] `http://localhost:5000/api/health` returns `{"status":"ok"}`
- [ ] Landing page loads with animations
- [ ] Login with `admin@taskflow.pro` / `Admin@123`
- [ ] Dashboard shows stat cards and charts
- [ ] Tasks → Kanban → drag a card to another column
- [ ] Tasks → open a task → toggle a subtask
- [ ] Employees → view team members
- [ ] Projects → view project with milestones
- [ ] Calendar → see tasks on due dates
- [ ] Analytics → charts render
- [ ] Reports → download a CSV file
- [ ] Notifications → see unread badge
- [ ] Settings → toggle dark/light theme
- [ ] `Ctrl+K` → search for a task
- [ ] Mobile → hamburger menu opens sidebar
- [ ] Logout → redirected to login

---

## Troubleshooting

### `Can't connect to MySQL server`

MySQL is not running. Start it via XAMPP or Windows Services, then re-run:

```powershell
cd backend
python setup_db.py
```

### `Failed to load dashboard` / empty pages

The Flask backend is not running. Start it in a separate terminal:

```powershell
cd backend
python run.py
```

### Login fails with `Invalid credentials`

Re-seed the database:

```powershell
cd backend
python seed_db.py
```

If users already exist, drop and recreate:

```sql
DROP DATABASE taskflow_pro;
CREATE DATABASE taskflow_pro;
```

Then run `python setup_db.py` again.

### `Access denied for user 'root'`

Set the correct password in `backend/.env`:

```env
MYSQL_PASSWORD=your_mysql_password
```

### Port already in use

```powershell
# Use a different frontend port
npm run dev -- -p 3001

# Or change Flask port in backend/run.py
```

### CORS errors in browser

Ensure `CORS_ORIGINS=http://localhost:3000` in `backend/.env` matches your frontend URL.

---

## Production Build

```powershell
# Frontend production build
cd frontend
npm run build
npm start

# Backend (use gunicorn in production)
cd backend
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
```

> **Security note:** Change `SECRET_KEY`, disable `FLASK_DEBUG`, configure real email for password reset, and use HTTPS in production.

---

## Database Schema

Key tables and relationships:

```
users ──┬── employees ──┬── tasks
        │               └── departments
        ├── notifications
        ├── user_settings
        └── sessions

projects ──┬── project_members
           ├── project_milestones
           └── tasks

tasks ──┬── subtasks
        ├── comments
        ├── task_history
        └── attachments
```

---

## Contributing

This project was built as a final-year capstone. To extend it:

1. Fork the repository
2. Create a feature branch
3. Make changes and test with the checklist above
4. Submit a pull request

---

## License

Built as an academic capstone project. Free to use for educational purposes.

---

<div align="center">

**TaskFlow Pro** — Manage tasks with cinematic precision.

[Get Started](http://localhost:3000/signup) · [API Health](http://localhost:5000/api/health)

</div>
