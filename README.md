# Human-Centered Employee Management System (EMS)

## Overview
A modular Employee Management System built with Python FastAPI backend and a frontend adhering to Apple Human Interface Guidelines (HIG). Designed for scalability, security, and user-centric experience.

## Tech Stack
- **Backend:** Python FastAPI
- **Database:** PostgreSQL or MongoDB
- **Frontend:** React (HIG compliant)
- **Hosting:** Docker + Cloud

## Folder Structure
```
EMS/
├── app/
│   ├── __init__.py
│   ├── auth/
│   ├── employee/
│   ├── attendance/
│   ├── leave/
│   ├── payroll/
│   ├── tasks/
│   ├── documents/
│   ├── notifications/
│   ├── settings/
│   └── reports/
├── main.py
├── requirements.txt
└── README.md
```

## Getting Started
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```
3. **API Docs:**
   Visit [http://localhost:8000/docs](http://localhost:8000/docs)

## Modules
- **auth:** Authentication & authorization
- **employee:** Employee directory management
- **attendance:** Clock-in/out, history, corrections
- **leave:** Leave application, approval, calendar
- **payroll:** Salary, payslips, tax
- **tasks:** Task assignment, performance
- **documents:** Document center
- **notifications:** Email & in-app alerts
- **settings:** Roles, departments, branding
- **reports:** Exportable analytics

## Contribution
- Follow modular structure for new features
- Write clear docstrings and type hints
- Ensure code passes linting and tests

## License
MIT