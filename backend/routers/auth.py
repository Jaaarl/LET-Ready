from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from models.user import create_user, get_user_by_email, verify_password
from auth.jwt_handler import create_access_token
from auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(data: RegisterRequest):
    try:
        user = create_user(data.email, data.name, data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    token = create_access_token(user["id"])
    return {
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
        "token": token,
    }


@router.post("/login")
def login(data: LoginRequest):
    user = get_user_by_email(data.email)
    if not user or not verify_password(user["password_hash"], data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user["id"])
    return {
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
        "token": token,
    }


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user
