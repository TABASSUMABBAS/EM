from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/employees", tags=["Employees"])

from typing import List, Optional
from pydantic import BaseModel

class Employee(BaseModel):
    id: int
    name: str
    department_id: Optional[int] = None
    department: Optional[str] = None
    tasks: Optional[List[int]] = []
    performance_scores: Optional[List[float]] = []
    performance_notes: Optional[List[str]] = []

# In-memory DB placeholder
employee_db = {}

@router.get("", response_model=List[Employee])
def list_employees(
    department: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
):
    employees = list(employee_db.values())
    # Filter by department if provided
    if department:
        employees = [e for e in employees if getattr(e, "department", None) == department]
    # Enhanced search: partial match on name, department, and performance_notes
    if search:
        search_lower = search.lower()
        def match(e):
            if search_lower in e.name.lower():
                return True
            if getattr(e, "department", None) and search_lower in e.department.lower():
                return True
            if any(search_lower in note.lower() for note in getattr(e, "performance_notes", [])):
                return True
            return False
        employees = [e for e in employees if match(e)]
    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    employees = employees[start:end]
    return employees

@router.post("", response_model=Employee)
def add_employee(employee: Employee):
    # Link department name if department_id is provided
    if getattr(employee, "department_id", None) is not None:
        from app.settings.routes import department_db
        dept = department_db.get(employee.department_id)
        if dept:
            employee.department = dept.name
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department does not exist")
    employee_db[employee.id] = employee
    return employee

@router.get("/{id}", response_model=Employee)
def get_employee(id: int):
    record = employee_db.get(id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee {id} not found")
    return record

@router.put("/{id}", response_model=Employee)
def update_employee(id: int, employee: Employee):
    if id not in employee_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee {id} not found")
    # Update department name if department_id is provided
    if getattr(employee, "department_id", None) is not None:
        from app.settings.routes import department_db
        dept = department_db.get(employee.department_id)
        if dept:
            employee.department = dept.name
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department does not exist")
    employee_db[id] = employee
    return employee

@router.delete("/{id}")
def delete_employee(id: int):
    if id not in employee_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee {id} not found")
    del employee_db[id]
    return {"message": f"Employee {id} deleted successfully"}

from fastapi.responses import StreamingResponse
import csv
import io
from fpdf import FPDF

@router.get("/export/csv")
def export_employees_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "department", "tasks", "performance_scores", "performance_notes"])
    for e in employee_db.values():
        writer.writerow([
            e.id,
            e.name,
            getattr(e, "department", ""),
            ",".join(map(str, e.tasks)),
            ",".join(map(str, e.performance_scores)),
            ",".join(e.performance_notes)
        ])
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=employees.csv"})

@router.get("/export/pdf")
def export_employees_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Employee Directory", ln=True, align="C")
    pdf.ln(10)
    for e in employee_db.values():
        pdf.cell(0, 10, txt=f"ID: {e.id}, Name: {e.name}, Dept: {getattr(e, 'department', '')}", ln=True)
    pdf_output = io.BytesIO(pdf.output(dest='S').encode('latin1'))
    pdf_output.seek(0)
    return StreamingResponse(pdf_output, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=employees.pdf"})