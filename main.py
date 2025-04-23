from fastapi import FastAPI, HTTPException
from app.auth.routes import router as auth_router
from app.employee.routes import router as employee_router
from app.attendance.routes import router as attendance_router
from app.leave.routes import router as leave_router
from app.payroll.routes import router as payroll_router
from app.tasks.routes import router as tasks_router
from fastapi.middleware.cors import CORSMiddleware
from app.database import Database
from fastapi.responses import JSONResponse
from fastapi.requests import Request

app = FastAPI(title="Human-Centered Employee Management System", version="1.0.0")

@app.on_event("startup")
async def startup_db_client():
    await Database.connect_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    await Database.close_db()

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(employee_router)
app.include_router(attendance_router)
app.include_router(leave_router)
app.include_router(payroll_router)
app.include_router(tasks_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Human-Centered Employee Management System API"}