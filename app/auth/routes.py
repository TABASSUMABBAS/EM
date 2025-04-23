from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.database import Database
import os
import datetime
import random
import string

router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

db = Database.get_db()
users_collection = db["users"]
otp_collection = db["otp"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirm(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_user_by_email(email: str):
    return await users_collection.find_one({"email": email})

async def get_user_by_username(username: str):
    return await users_collection.find_one({"username": username})

async def authenticate_user(username: str, password: str):
    user = await get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserOut, status_code=201)
async def register(user: UserCreate):
    if await get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await get_user_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed_password = get_password_hash(user.password)
    doc = {"username": user.username, "email": user.email, "password": hashed_password}
    result = await users_collection.insert_one(doc)
    return {"id": str(result.inserted_id), "username": user.username, "email": user.email}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    return {"message": "Logout endpoint (client should remove token)"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    user = await get_user_by_email(request.email)
    if not user:
        return {"message": "If this email is registered, you will receive a reset link."}
    otp = ''.join(random.choices(string.digits, k=6))
    await otp_collection.insert_one({"email": request.email, "otp": otp, "created": datetime.datetime.utcnow()})
    # Here, send OTP via email (mocked)
    print(f"Send OTP {otp} to {request.email}")
    return {"message": "If this email is registered, you will receive a reset link."}

@router.post("/reset-password/confirm")
async def reset_password_confirm(data: ResetPasswordConfirm):
    otp_doc = await otp_collection.find_one({"email": data.email, "otp": data.otp})
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    await users_collection.update_one({"email": data.email}, {"$set": {"password": get_password_hash(data.new_password)}})
    await otp_collection.delete_many({"email": data.email})
    return {"message": "Password reset successful"}

@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"id": str(current_user["_id"]), "username": current_user["username"], "email": current_user["email"]}

@router.get("/health", tags=["Health"])
async def health_check():
    try:
        # The ping command is cheap and does not require auth.
        await db.command("ping")
        return {"status": "ok", "message": "MongoDB connection successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB connection failed: {str(e)}")