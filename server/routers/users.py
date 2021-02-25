from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session

from db import schemas, crud
from db.database import SessionLocal

router = APIRouter()

def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@router.get("/user/{id}", response_model=schemas.UserInfo)
async def get_user_details(id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_id(db, id=id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/register", response_model=schemas.UserInfo) 
async def register_user(user: schemas.UserRegister, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email_id=user.email_id)
    if db_user:
        raise HTTPException(status_code=400, detail="User already exists")
    return crud.create_user(db=db, user=user)

@router.post("/login", response_model=schemas.UserInfo) 
async def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email_id=user.email_id)
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")
    if db_user.passwd_hashed != user.passwd_hashed:
        raise HTTPException(status_code=401, detail="Incorrect password")
    return db_user