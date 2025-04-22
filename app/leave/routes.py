from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/leave", tags=["Leave"])

# Example role-based dependency
def get_current_user_role():
    # Placeholder: Replace with actual authentication logic
    return "employee"

def require_role(roles: List[str]):
    def role_checker(role: str = Depends(get_current_user_role)):
        if role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return role_checker

class LeaveBase(BaseModel):
    employee_id: int
    start_date: str
    end_date: str
    type: str
    reason: Optional[str] = None
    status: Optional[str] = "pending"

class LeaveCreate(LeaveBase):
    pass

class LeaveUpdate(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    type: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None

class Leave(LeaveBase):
    id: int

# In-memory DB placeholder
leave_db = {}

@router.get("", response_model=List[Leave])
def list_leaves(role: str = Depends(get_current_user_role)):
    return list(leave_db.values())

@router.post("", response_model=Leave, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["admin", "manager", "employee"]))])
def apply_leave(leave: LeaveCreate):
    new_id = len(leave_db) + 1
    record = Leave(id=new_id, **leave.dict())
    leave_db[new_id] = record
    try:
        from app.notifications.logic import create_notification
        create_notification(user_id=record.employee_id, message=f"Your leave application from {record.start_date} to {record.end_date} has been submitted.", type_="leave_applied", related_leave=record.id)
        # Optionally notify manager (assuming manager id is 1 for demo)
        create_notification(user_id=1, message=f"Employee {record.employee_id} applied for leave from {record.start_date} to {record.end_date}.", type_="leave_applied", related_leave=record.id)
    except ImportError:
        pass
    return record

@router.get("/{leave_id}", response_model=Leave)
def get_leave(leave_id: int):
    record = leave_db.get(leave_id)
    if not record:
        raise HTTPException(status_code=404, detail="Leave not found")
    return record

@router.put("/{leave_id}", response_model=Leave, dependencies=[Depends(require_role(["admin", "manager"]))])
def update_leave(leave_id: int, update: LeaveUpdate):
    record = leave_db.get(leave_id)
    if not record:
        raise HTTPException(status_code=404, detail="Leave not found")
    updated = record.copy(update=update.dict(exclude_unset=True))
    leave_db[leave_id] = updated
    try:
        from app.notifications.logic import create_notification
        if update.status == "approved":
            create_notification(user_id=updated.employee_id, message=f"Your leave from {updated.start_date} to {updated.end_date} has been approved.", type_="leave_approved", related_leave=updated.id)
            create_notification(user_id=1, message=f"Leave for employee {updated.employee_id} has been approved.", type_="leave_approved", related_leave=updated.id)
        elif update.status == "rejected":
            create_notification(user_id=updated.employee_id, message=f"Your leave from {updated.start_date} to {updated.end_date} has been rejected.", type_="leave_rejected", related_leave=updated.id)
            create_notification(user_id=1, message=f"Leave for employee {updated.employee_id} has been rejected.", type_="leave_rejected", related_leave=updated.id)
    except ImportError:
        pass
    return updated

@router.delete("/{leave_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(["admin"]))])
def delete_leave(leave_id: int):
    if leave_id not in leave_db:
        raise HTTPException(status_code=404, detail="Leave not found")
    del leave_db[leave_id]
    return None