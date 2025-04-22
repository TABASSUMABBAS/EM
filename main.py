from fastapi import FastAPI
from app.auth.routes import router as auth_router
from app.employee.routes import router as employee_router
from app.attendance.routes import router as attendance_router
from app.leave.routes import router as leave_router
from app.payroll.routes import router as payroll_router
from app.tasks.routes import router as tasks_router

app = FastAPI(title="Human-Centered Employee Management System", version="1.0.0")

app.include_router(auth_router)
app.include_router(employee_router)
app.include_router(attendance_router)
app.include_router(leave_router)
app.include_router(payroll_router)
app.include_router(tasks_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Human-Centered Employee Management System API"}