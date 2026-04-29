from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    role: str = Field(default="viewer", pattern="^(admin|viewer)$")
    status: str = Field(default="active")


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=50)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: str | None = Field(default=None, pattern="^(admin|viewer)$")
    status: str | None = None
    password: str | None = Field(default=None, min_length=6, max_length=50)


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
