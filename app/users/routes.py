from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
from jose import JWTError, jwt
import os

router = APIRouter(prefix="/users", tags=["Users"])

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

client = AsyncIOMotorClient(MONGO_URL)
db = client["ems"]
users_collection = db["users"]

class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    roles: List[str]

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    roles: Optional[List[str]] = None

# Dependency to get current user from JWT
async def get_current_user(token: str = Depends(lambda: None)):
    from fastapi.security import OAuth2PasswordBearer
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    token = token or (await oauth2_scheme())
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        roles: list = payload.get("roles", [])
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await users_collection.find_one({"username": username})
    if user is None:
        raise credentials_exception
    user["roles"] = roles
    return user

def require_roles(required_roles: List[str]):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return role_checker

@router.get("/", response_model=List[UserOut], dependencies=[Depends(require_roles(["admin"]))])
async def list_users():
    users = []
    async for user in users_collection.find():
        users.append({
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "roles": user.get("roles", [])
        })
    return users

@router.get("/{id}", response_model=UserOut)
async def get_user(id: str, current_user: dict = Depends(get_current_user)):
    user = await users_collection.find_one({"_id": id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "roles": user.get("roles", [])
    }

@router.put("/{id}", response_model=UserOut)
async def update_user(id: str, update: UserUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    result = await users_collection.update_one({"_id": id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    user = await users_collection.find_one({"_id": id})
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "roles": user.get("roles", [])
    }

@router.delete("/{id}", status_code=204, dependencies=[Depends(require_roles(["admin"]))])
async def delete_user(id: str):
    result = await users_collection.delete_one({"_id": id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return None