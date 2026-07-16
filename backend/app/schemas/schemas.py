"""
Pydanticスキーマ（API境界のバリデーション）

DB側のCHECK制約と二重で守る方針：
- 30分単位チェックはここで行う（DB制約では複雑になるため）
- end_time > start_time もここで先にチェックし、分かりやすいエラーメッセージを返す
"""
from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator


# ---------- User ----------

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "user"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("user", "competitor", "admin"):
            raise ValueError("role must be one of: user, competitor, admin")
        return v


class UserOut(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Reservation ----------

class ReservationCreate(BaseModel):
    lane_set_id: str
    date: date
    start_time: time
    end_time: time
    reservation_type: str = "general"

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_30min_unit(cls, v: time):
        if v.minute not in (0, 30) or v.second != 0:
            raise ValueError("予約時間は30分単位で指定してください（例: 10:00, 10:30）")
        return v

    @field_validator("reservation_type")
    @classmethod
    def validate_type(cls, v):
        if v not in ("general", "practice", "class"):
            raise ValueError("reservation_type must be one of: general, practice, class")
        return v

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self

    @field_validator("date")
    @classmethod
    def validate_not_past(cls, v: date):
        if v < date.today():
            raise ValueError("過去の日付には予約できません")
        return v


class ReservationOut(BaseModel):
    reservation_id: int
    user_id: int
    lane_set_id: str
    date: date
    start_time: time
    end_time: time
    reservation_type: str
    status: str
    created_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- LaneSet ----------

class LaneSetOut(BaseModel):
    lane_set_id: str
    name: str
    status: str

    class Config:
        from_attributes = True


class LaneSetStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ("available", "maintenance"):
            raise ValueError("status must be 'available' or 'maintenance'")
        return v
