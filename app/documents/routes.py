from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import os

router = APIRouter(prefix="/documents", tags=["Documents"])

# In-memory DB placeholder for documents
document_db = {}

# Document categories and access levels
CATEGORIES = ["ID", "Contract", "Certificate", "Other"]
ACCESS_LEVELS = ["employee", "manager", "admin"]

# Directory to store uploaded files (for demo, in-memory, not persistent)
UPLOAD_DIR = "/tmp/ems_documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_current_user_role():
    # Placeholder: Replace with actual authentication logic
    return "employee"

def require_role(roles: List[str]):
    def role_checker(role: str = Depends(get_current_user_role)):
        if role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return role_checker

class DocumentBase(BaseModel):
    employee_id: int
    category: str
    access_level: str
    expiry_date: Optional[str] = None  # ISO format
    notes: Optional[str] = None

class DocumentCreate(DocumentBase):
    filename: str
    content_type: str

class Document(DocumentBase):
    id: int
    filename: str
    content_type: str
    uploaded_at: str
    path: str

@router.post("/upload", response_model=Document, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["admin", "manager"]))])
def upload_document(
    employee_id: int = Form(...),
    category: str = Form(...),
    access_level: str = Form(...),
    expiry_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    if category not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")
    if access_level not in ACCESS_LEVELS:
        raise HTTPException(status_code=400, detail="Invalid access level")
    new_id = len(document_db) + 1
    filename = f"{employee_id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    doc = Document(
        id=new_id,
        employee_id=employee_id,
        category=category,
        access_level=access_level,
        expiry_date=expiry_date,
        notes=notes,
        filename=file.filename,
        content_type=file.content_type,
        uploaded_at=datetime.utcnow().isoformat(),
        path=file_path
    )
    document_db[new_id] = doc
    return doc

@router.get("", response_model=List[Document], dependencies=[Depends(require_role(["admin", "manager"]))])
def list_documents(employee_id: Optional[int] = None, category: Optional[str] = None):
    docs = list(document_db.values())
    if employee_id is not None:
        docs = [d for d in docs if d.employee_id == employee_id]
    if category is not None:
        docs = [d for d in docs if d.category == category]
    return docs

@router.get("/{doc_id}", response_model=Document, dependencies=[Depends(require_role(["admin", "manager", "employee"]))])
def get_document(doc_id: int):
    doc = document_db.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/download/{doc_id}", dependencies=[Depends(require_role(["admin", "manager", "employee"]))])
def download_document(doc_id: int):
    from fastapi.responses import FileResponse
    doc = document_db.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(doc.path, filename=doc.filename, media_type=doc.content_type)

@router.get("/preview/{doc_id}", dependencies=[Depends(require_role(["admin", "manager", "employee"]))])
def preview_document(doc_id: int):
    from fastapi.responses import FileResponse
    doc = document_db.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    # For preview, just return the file (browser will preview if possible)
    return FileResponse(doc.path, filename=doc.filename, media_type=doc.content_type)

@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(["admin"]))])
def delete_document(doc_id: int):
    doc = document_db.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        os.remove(doc.path)
    except Exception:
        pass
    del document_db[doc_id]
    return None

@router.get("/expiry/alerts", response_model=List[Document], dependencies=[Depends(require_role(["admin", "manager"]))])
def expiry_alerts(days: int = 30):
    now = datetime.utcnow()
    alerts = []
    for doc in document_db.values():
        if doc.expiry_date:
            try:
                expiry = datetime.fromisoformat(doc.expiry_date)
                if expiry - now <= timedelta(days=days):
                    alerts.append(doc)
            except Exception:
                continue
    return alerts