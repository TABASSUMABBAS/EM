from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/payroll", tags=["Payroll"])

# Example role-based dependency
def get_current_user_role():
    # Placeholder: Replace with actual authentication logic
    return "employee"

def require_role(roles: List[str]):
    def role_checker(role: str = Depends(get_current_user_role)):
        if role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return role_checker

class PayrollBase(BaseModel):
    employee_id: int
    period: str  # e.g., "2024-06"
    base_salary: float
    bonus: Optional[float] = 0.0
    deductions: Optional[float] = 0.0
    net_pay: Optional[float] = 0.0
    status: Optional[str] = "pending"  # pending, processed, paid
    notes: Optional[str] = None

class PayrollCreate(PayrollBase):
    pass

class PayrollUpdate(BaseModel):
    base_salary: Optional[float] = None
    bonus: Optional[float] = None
    deductions: Optional[float] = None
    net_pay: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class Payroll(PayrollBase):
    id: int

# In-memory DB placeholder
payroll_db = {}

@router.get("", response_model=List[Payroll], dependencies=[Depends(require_role(["admin", "manager"]))])
def list_payrolls(employee_id: Optional[int] = None, period: Optional[str] = None):
    records = list(payroll_db.values())
    if employee_id is not None:
        records = [r for r in records if r.employee_id == employee_id]
    if period is not None:
        records = [r for r in records if r.period == period]
    return records

@router.post("", response_model=Payroll, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["admin", "manager"]))])
def add_payroll(payroll: PayrollCreate):
    new_id = len(payroll_db) + 1
    net_pay = payroll.base_salary + (payroll.bonus or 0) - (payroll.deductions or 0)
    record = Payroll(id=new_id, **payroll.dict(), net_pay=net_pay)
    payroll_db[new_id] = record
    try:
        from app.notifications.logic import create_notification
        create_notification(user_id=record.employee_id, message=f"Payroll for {record.period} has been created.", type_="payroll_created")
    except ImportError:
        pass
    return record

@router.get("/{payroll_id}", response_model=Payroll, dependencies=[Depends(require_role(["admin", "manager", "employee"]))])
def get_payroll(payroll_id: int):
    record = payroll_db.get(payroll_id)
    if not record:
        raise HTTPException(status_code=404, detail="Payroll not found")
    return record

@router.put("/{payroll_id}", response_model=Payroll, dependencies=[Depends(require_role(["admin", "manager"]))])
def update_payroll(payroll_id: int, update: PayrollUpdate):
    record = payroll_db.get(payroll_id)
    if not record:
        raise HTTPException(status_code=404, detail="Payroll not found")
    updated_data = update.dict(exclude_unset=True)
    # Recalculate net_pay if any relevant field is updated
    base_salary = updated_data.get("base_salary", record.base_salary)
    bonus = updated_data.get("bonus", record.bonus)
    deductions = updated_data.get("deductions", record.deductions)
    net_pay = base_salary + (bonus or 0) - (deductions or 0)
    updated = record.copy(update={**updated_data, "net_pay": net_pay})
    payroll_db[payroll_id] = updated
    try:
        from app.notifications.logic import create_notification
        if update.status == "paid":
            create_notification(user_id=updated.employee_id, message=f"Your payroll for {updated.period} has been marked as paid.", type_="payroll_paid")
    except ImportError:
        pass
    return updated

@router.delete("/{payroll_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(["admin"]))])
def delete_payroll(payroll_id: int):
    if payroll_id not in payroll_db:
        raise HTTPException(status_code=404, detail="Payroll not found")
    del payroll_db[payroll_id]
    return None

@router.post("/process/{employee_id}", response_model=Payroll, dependencies=[Depends(require_role(["admin", "manager"]))])
def process_payroll(employee_id: int, period: str, base_salary: float, bonus: Optional[float] = 0.0, deductions: Optional[float] = 0.0):
    # Calculate net pay and create payroll record
    net_pay = base_salary + (bonus or 0) - (deductions or 0)
    new_id = len(payroll_db) + 1
    record = Payroll(id=new_id, employee_id=employee_id, period=period, base_salary=base_salary, bonus=bonus, deductions=deductions, net_pay=net_pay, status="processed")
    payroll_db[new_id] = record
    try:
        from app.notifications.logic import create_notification
        create_notification(user_id=employee_id, message=f"Payroll for {period} has been processed. Net pay: {net_pay}", type_="payroll_processed")
    except ImportError:
        pass
    return record