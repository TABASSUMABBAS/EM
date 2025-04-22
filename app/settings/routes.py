from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/departments", tags=["Departments"])

class Department(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

# In-memory DB placeholder
department_db = {}

@router.get("", response_model=List[Department])
def list_departments():
    return list(department_db.values())

@router.post("", response_model=Department)
def add_department(department: Department):
    if department.id in department_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department ID already exists")
    department_db[department.id] = department
    return department

@router.get("/{id}", response_model=Department)
def get_department(id: int):
    record = department_db.get(id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Department {id} not found")
    return record

@router.put("/{id}", response_model=Department)
def update_department(id: int, department: Department):
    if id not in department_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Department {id} not found")
    department_db[id] = department
    return department

@router.delete("/{id}")
def delete_department(id: int):
    if id not in department_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Department {id} not found")
    del department_db[id]
    # Update employees whose department_id matches the deleted department
    try:
        from app.employee.routes import employee_db
        for emp in employee_db.values():
            if getattr(emp, "department_id", None) == id:
                emp.department_id = None
                emp.department = None
    except ImportError:
        pass
    return {"message": f"Department {id} deleted successfully"}