from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/attendance", tags=["Attendance"])

# Example role-based dependency
def get_current_user_role():
    # Placeholder: Replace with actual authentication logic
    return "employee"

def require_role(roles: List[str]):
    def role_checker(role: str = Depends(get_current_user_role)):
        if role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return role_checker

class AttendanceBase(BaseModel):
    employee_id: int
    date: str
    status: str
    notes: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class Attendance(AttendanceBase):
    id: int

# In-memory DB placeholder
attendance_db = {}

@router.get("", response_model=List[Attendance])
def list_attendance(
    employee_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    role: str = Depends(get_current_user_role)
):
    records = list(attendance_db.values())
    if employee_id is not None:
        records = [r for r in records if r.employee_id == employee_id]
    if status is not None:
        records = [r for r in records if r.status == status]
    if start_date is not None:
        records = [r for r in records if r.date >= start_date]
    if end_date is not None:
        records = [r for r in records if r.date <= end_date]
    return records

@router.post("", response_model=Attendance, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["admin", "manager"]))])
def add_attendance(attendance: AttendanceCreate):
    new_id = len(attendance_db) + 1
    record = Attendance(id=new_id, **attendance.dict())
    attendance_db[new_id] = record
    try:
        from app.notifications.logic import create_notification
        if record.status == "late":
            create_notification(user_id=record.employee_id, message=f"You have been marked late for {record.date}.", type_="attendance_late", related_attendance=record.id)
            create_notification(user_id=1, message=f"Employee {record.employee_id} was late on {record.date}.", type_="attendance_late", related_attendance=record.id)
        elif record.status == "absent":
            create_notification(user_id=record.employee_id, message=f"You have been marked absent for {record.date}.", type_="attendance_absent", related_attendance=record.id)
            create_notification(user_id=1, message=f"Employee {record.employee_id} was absent on {record.date}.", type_="attendance_absent", related_attendance=record.id)
    except ImportError:
        pass
    return record

@router.get("/{attendance_id}", response_model=Attendance)
def get_attendance(attendance_id: int):
    record = attendance_db.get(attendance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Attendance not found")
    return record

@router.put("/{attendance_id}", response_model=Attendance, dependencies=[Depends(require_role(["admin", "manager"]))])
def update_attendance(attendance_id: int, update: AttendanceUpdate):
    record = attendance_db.get(attendance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Attendance not found")
    updated = record.copy(update=update.dict(exclude_unset=True))
    attendance_db[attendance_id] = updated
    try:
        from app.notifications.logic import create_notification
        if update.status == "late":
            create_notification(user_id=updated.employee_id, message=f"You have been marked late for {updated.date}.", type_="attendance_late", related_attendance=updated.id)
            create_notification(user_id=1, message=f"Employee {updated.employee_id} was late on {updated.date}.", type_="attendance_late", related_attendance=updated.id)
        elif update.status == "absent":
            create_notification(user_id=updated.employee_id, message=f"You have been marked absent for {updated.date}.", type_="attendance_absent", related_attendance=updated.id)
            create_notification(user_id=1, message=f"Employee {updated.employee_id} was absent on {updated.date}.", type_="attendance_absent", related_attendance=updated.id)
    except ImportError:
        pass
    return updated

@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(["admin"]))])
def delete_attendance(attendance_id: int):
    if attendance_id not in attendance_db:
        raise HTTPException(status_code=404, detail="Attendance not found")
    del attendance_db[attendance_id]
    return None


class CorrectionRequestBase(BaseModel):
    attendance_id: int
    employee_id: int
    requested_status: str
    reason: Optional[str] = None

class CorrectionRequestCreate(CorrectionRequestBase):
    pass

class CorrectionRequestUpdate(BaseModel):
    status: Optional[str] = None  # approved, rejected
    manager_notes: Optional[str] = None

class CorrectionRequest(CorrectionRequestBase):
    id: int
    status: str  # pending, approved, rejected
    manager_notes: Optional[str] = None

# In-memory DB placeholder for correction requests
correction_request_db = {}

@router.post("/corrections", response_model=CorrectionRequest, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["employee"]))])
def submit_correction_request(request: CorrectionRequestCreate):
    new_id = len(correction_request_db) + 1
    record = CorrectionRequest(id=new_id, status="pending", **request.dict())
    correction_request_db[new_id] = record
    try:
        from app.notifications.logic import create_notification
        create_notification(user_id=1, message=f"Attendance correction requested by employee {record.employee_id} for attendance {record.attendance_id}.", type_="correction_requested", related_attendance=record.attendance_id)
        create_notification(user_id=record.employee_id, message=f"Your correction request for attendance {record.attendance_id} has been submitted.", type_="correction_requested", related_attendance=record.attendance_id)
    except ImportError:
        pass
    return record

@router.get("/corrections", response_model=List[CorrectionRequest], dependencies=[Depends(require_role(["admin", "manager"]))])
def list_correction_requests():
    return list(correction_request_db.values())

@router.get("/corrections/{request_id}", response_model=CorrectionRequest)
def get_correction_request(request_id: int):
    record = correction_request_db.get(request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Correction request not found")
    return record

@router.put("/corrections/{request_id}", response_model=CorrectionRequest, dependencies=[Depends(require_role(["admin", "manager"]))])
def update_correction_request(request_id: int, update: CorrectionRequestUpdate):
    record = correction_request_db.get(request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Correction request not found")
    updated = record.copy(update=update.dict(exclude_unset=True))
    # If status is approved, update the attendance record
    if update.status == "approved":
        att = attendance_db.get(updated.attendance_id)
        if att:
            att = att.copy(update={"status": updated.requested_status})
            attendance_db[updated.attendance_id] = att
    correction_request_db[request_id] = updated
    try:
        from app.notifications.logic import create_notification
        if update.status == "approved":
            create_notification(user_id=updated.employee_id, message=f"Your correction request for attendance {updated.attendance_id} has been approved.", type_="correction_approved", related_attendance=updated.attendance_id)
        elif update.status == "rejected":
            create_notification(user_id=updated.employee_id, message=f"Your correction request for attendance {updated.attendance_id} has been rejected.", type_="correction_rejected", related_attendance=updated.attendance_id)
    except ImportError:
        pass
    return updated

@router.post("/bulk_upload", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["admin", "manager"]))])
def bulk_upload_attendance(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    content = file.file.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))
    new_records = []
    for row in reader:
        try:
            employee_id = int(row['employee_id'])
            date = row['date']
            status_ = row['status']
            notes = row.get('notes')
            new_id = len(attendance_db) + 1
            record = Attendance(id=new_id, employee_id=employee_id, date=date, status=status_, notes=notes)
            attendance_db[new_id] = record
            new_records.append(record)
        except Exception as e:
            continue  # Optionally collect errors for reporting
    return {"inserted": len(new_records)}

@router.get("/report/export", dependencies=[Depends(require_role(["admin", "manager"]))])
def export_attendance_report(
    employee_id: Optional[int] = None,
    department: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    format: str = Query("csv", enum=["csv", "excel", "pdf"])
):
    records = list(attendance_db.values())
    if employee_id is not None:
        records = [r for r in records if r.employee_id == employee_id]
    if department is not None:
        try:
            from app.employee.routes import employee_db
            dept_emp_ids = [e.id for e in employee_db.values() if getattr(e, "department", None) == department]
            records = [r for r in records if r.employee_id in dept_emp_ids]
        except ImportError:
            pass
    if start_date is not None:
        records = [r for r in records if r.date >= start_date]
    if end_date is not None:
        records = [r for r in records if r.date <= end_date]
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "employee_id", "date", "status", "notes"])
        for a in records:
            writer.writerow([a.id, a.employee_id, a.date, a.status, a.notes or ""])
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=attendance_report.csv"})
    elif format == "excel":
        if openpyxl is None:
            raise HTTPException(status_code=500, detail="openpyxl is not installed on the server")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["id", "employee_id", "date", "status", "notes"])
        for a in records:
            ws.append([a.id, a.employee_id, a.date, a.status, a.notes or ""])
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=attendance_report.xlsx"})
    elif format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Attendance Report", ln=True, align="C")
        pdf.ln(10)
        for a in records:
            pdf.cell(0, 10, txt=f"ID: {a.id}, Emp: {a.employee_id}, Date: {a.date}, Status: {a.status}, Notes: {a.notes or ''}", ln=True)
        pdf_output = io.BytesIO(pdf.output(dest='S').encode('latin1'))
        pdf_output.seek(0)
        return StreamingResponse(pdf_output, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=attendance_report.pdf"})
    else:
        raise HTTPException(status_code=400, detail="Invalid format")

@router.get("/kpi/today", dependencies=[Depends(require_role(["admin", "manager"]))])
def attendance_kpi_today():
    today_str = date.today().isoformat()
    present = 0
    late = 0
    absent = 0
    for a in attendance_db.values():
        if a.date == today_str:
            if a.status == "present":
                present += 1
            elif a.status == "late":
                late += 1
            elif a.status == "absent":
                absent += 1
    return {"date": today_str, "present": present, "late": late, "absent": absent}


@router.get("/summary", dependencies=[Depends(require_role(["admin", "manager"]))])
def attendance_summary(
    employee_id: Optional[int] = None,
    department: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    # For department, need to join with employee_db
    summary = {"present": 0, "late": 0, "absent": 0, "total": 0}
    records = list(attendance_db.values())
    if employee_id is not None:
        records = [r for r in records if r.employee_id == employee_id]
    if department is not None:
        try:
            from app.employee.routes import employee_db
            dept_emp_ids = [e.id for e in employee_db.values() if getattr(e, "department", None) == department]
            records = [r for r in records if r.employee_id in dept_emp_ids]
        except ImportError:
            pass
    if start_date is not None:
        records = [r for r in records if r.date >= start_date]
    if end_date is not None:
        records = [r for r in records if r.date <= end_date]
    for r in records:
        summary["total"] += 1
        if r.status in summary:
            summary[r.status] += 1
    return summary

@router.get("/trend", dependencies=[Depends(require_role(["admin", "manager"]))])
def attendance_trend(
    employee_id: Optional[int] = None,
    department: Optional[str] = None,
    period: str = Query("weekly", enum=["weekly", "monthly"]),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    # Returns trend data for plotting (e.g., per week/month)
    records = list(attendance_db.values())
    if employee_id is not None:
        records = [r for r in records if r.employee_id == employee_id]
    if department is not None:
        try:
            from app.employee.routes import employee_db
            dept_emp_ids = [e.id for e in employee_db.values() if getattr(e, "department", None) == department]
            records = [r for r in records if r.employee_id in dept_emp_ids]
        except ImportError:
            pass
    if start_date is not None:
        records = [r for r in records if r.date >= start_date]
    if end_date is not None:
        records = [r for r in records if r.date <= end_date]
    # Group by period
    trend: Dict[str, Dict[str, int]] = {}
    for r in records:
        dt = datetime.strptime(r.date, "%Y-%m-%d")
        if period == "weekly":
            key = f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"
        else:
            key = dt.strftime("%Y-%m")
        if key not in trend:
            trend[key] = {"present": 0, "late": 0, "absent": 0, "total": 0}
        trend[key]["total"] += 1
        if r.status in trend[key]:
            trend[key][r.status] += 1
    # Sort by period key
    sorted_trend = dict(sorted(trend.items()))
    return sorted_trend

@router.get("/status/{employee_id}", response_model=dict)
def get_employee_attendance_status(employee_id: int):
    records = [r for r in attendance_db.values() if r.employee_id == employee_id]
    if not records:
        raise HTTPException(status_code=404, detail="No attendance records found for this employee")
    latest = max(records, key=lambda r: r.date)
    return {"employee_id": employee_id, "date": latest.date, "status": latest.status, "notes": latest.notes}