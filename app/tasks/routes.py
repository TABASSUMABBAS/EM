from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# Example role-based dependency
def get_current_user_role():
    # Placeholder: Replace with actual authentication logic
    return "employee"

def require_role(roles: List[str]):
    def role_checker(role: str = Depends(get_current_user_role)):
        if role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return role_checker

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: int
    due_date: Optional[str] = None
    status: Optional[str] = "pending"
    performance_score: Optional[float] = None
    review_notes: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[str] = None
    status: Optional[str] = None

class Task(TaskBase):
    id: int

# In-memory DB placeholder
task_db = {}

@router.get("", response_model=List[Task])
def list_tasks(role: str = Depends(get_current_user_role)):
    return list(task_db.values())

@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["admin", "manager"]))])
def add_task(task: TaskCreate):
    new_id = len(task_db) + 1
    record = Task(id=new_id, **task.dict())
    task_db[new_id] = record
    # Synchronize with employee_db
    try:
        from app.employee.routes import employee_db
        emp = employee_db.get(record.assigned_to)
        if emp:
            if record.id not in emp.tasks:
                emp.tasks.append(record.id)
            # Notify employee of new task assignment
            create_notification(user_id=record.assigned_to, message=f"You have been assigned a new task: {record.title}", type_="task_assigned", related_task=record.id)
    except ImportError:
        pass
    return record

@router.get("/{task_id}", response_model=Task)
def get_task(task_id: int):
    record = task_db.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    return record

@router.put("/{task_id}", response_model=Task, dependencies=[Depends(require_role(["admin", "manager"]))])
def update_task(task_id: int, update: TaskUpdate):
    record = task_db.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    prev_assigned = record.assigned_to
    updated = record.copy(update=update.dict(exclude_unset=True))
    task_db[task_id] = updated
    # Synchronize with employee_db if assigned_to changed
    try:
        from app.employee.routes import employee_db
        if update.assigned_to is not None and update.assigned_to != prev_assigned:
            prev_emp = employee_db.get(prev_assigned)
            if prev_emp and task_id in prev_emp.tasks:
                prev_emp.tasks.remove(task_id)
            new_emp = employee_db.get(update.assigned_to)
            if new_emp and task_id not in new_emp.tasks:
                new_emp.tasks.append(task_id)
    except ImportError:
        pass
    return updated

@router.put("/{task_id}/complete", response_model=Task, dependencies=[Depends(require_role(["admin", "manager", "employee"]))])
def complete_task(task_id: int):
    record = task_db.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    updated = record.copy(update={"status": "completed"})
    task_db[task_id] = updated
    # Synchronize with employee_db (optional: could track completed tasks)
    # Notify manager and employee of completion
    try:
        from app.employee.routes import employee_db
        emp = employee_db.get(record.assigned_to)
        if emp:
            create_notification(user_id=record.assigned_to, message=f"Your task '{record.title}' has been marked as completed.", type_="task_completed", related_task=record.id)
        # Optionally notify managers (assuming manager id is 1 for demo)
        create_notification(user_id=1, message=f"Task '{record.title}' assigned to employee {record.assigned_to} has been completed.", type_="task_completed", related_task=record.id)
    except ImportError:
        pass
    return updated

@router.post("/{task_id}/performance", response_model=Task, dependencies=[Depends(require_role(["admin", "manager"]))])
def review_task_performance(task_id: int, score: float, notes: Optional[str] = None):
    record = task_db.get(task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    updated = record.copy(update={"performance_score": score, "review_notes": notes})
    task_db[task_id] = updated
    # Synchronize with employee_db
    try:
        from app.employee.routes import employee_db
        emp = employee_db.get(record.assigned_to)
        if emp:
            if score is not None:
                emp.performance_scores.append(score)
            if notes:
                emp.performance_notes.append(notes)
            # Notify employee of performance review
            create_notification(user_id=record.assigned_to, message=f"Your task '{record.title}' has been reviewed. Score: {score}. Notes: {notes or ''}", type_="task_reviewed", related_task=record.id)
    except ImportError:
        pass
    return updated

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(["admin"]))])
def delete_task(task_id: int):
    if task_id not in task_db:
        raise HTTPException(status_code=404, detail="Task not found")
    # Synchronize with employee_db
    try:
        from app.employee.routes import employee_db
        for emp in employee_db.values():
            if task_id in emp.tasks:
                emp.tasks.remove(task_id)
    except ImportError:
        pass
    del task_db[task_id]
    return None