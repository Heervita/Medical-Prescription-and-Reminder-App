from fastapi import APIRouter, HTTPException
from model.user import UserCreate, UserLogin
from utils.auth import hash_password, verify_password, create_token
from database import db

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup")
async def signup(user: UserCreate):
    print("DEBUG PASSWORD RECEIVED:", user.password)  # <<< THIS LINE

    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(400, "Email already registered")

    hashed = hash_password(user.password)
    user_dict = {"name": user.name, "email": user.email, "password": hashed}

    await db.users.insert_one(user_dict)
    return {"message": "User created"}


@router.post("/login")
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(401, "Invalid credentials")

    token = create_token({"id": str(user["_id"]), "email": user["email"]})
    return {"token": token}
