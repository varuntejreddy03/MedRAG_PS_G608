from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from ..core.database import get_db
from ..core.security import hash_password, verify_password, create_access_token
from ..core.session import create_session, get_session, delete_session
from ..models.user_model import User
from ..services.email_service import email_service

router = APIRouter(prefix="/auth", tags=["authentication"])

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/signup", response_model=dict)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    hashed_password = hash_password(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send verification email
    verification_token = create_access_token(user.email)
    email_service.send_verification_email(user.email, verification_token)
    
    return {"message": "User created successfully. Please check your email for verification."}

@router.post("/login", response_model=Token)
async def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not db_user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")
    
    # Create session
    session_id = create_session(user.email)
    
    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax",
        secure=False,
        path="/"
    )
    print(f"✅ Session cookie set: {session_id[:20]}...")
    
    # Also return JWT for compatibility
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/verify")
async def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        from ..core.security import verify_token
        payload = verify_token(token)
        email = payload.get("sub")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_verified = True
        db.commit()
        
        return {"message": "Email verified successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid verification token")

@router.post("/logout")
async def logout(response: Response, session_id: Optional[str] = Cookie(None)):
    """Logout user and clear session."""
    if session_id:
        delete_session(session_id)
    
    response.delete_cookie("session_id", path="/")
    return {"message": "Logged out successfully"}