from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_admin_user, get_db
from app.core.security import get_password_hash
from app.models import User
from app.schemas.user import UserCreate, UserOut, UserUpdate


router = APIRouter()


@router.get("", response_model=list[UserOut])
def list_users(_: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return db.execute(select(User).order_by(User.created_at.desc())).scalars().all()


@router.post("", response_model=UserOut)
def create_user(payload: UserCreate, _: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    exists = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        status=payload.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, _: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    for field in ("email", "role", "status"):
        value = getattr(payload, field)
        if value is not None:
            setattr(user, field, value)
    if payload.password:
        user.password_hash = get_password_hash(payload.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, _: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"message": "删除成功"}
