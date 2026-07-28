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
        if v not in ("general", "practice", "class", "group"):
            raise ValueError("reservation_type must be one of: general, practice, class, group")
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


# ---------- ClassCourse (第二弾で追加) ----------

class ClassCourseCreate(BaseModel):
    lane_set_id: str
    day_of_week: str
    start_time: time
    end_time: time
    first_date: date
    session_count: int = 5
    capacity: int = 10
    instructor_name: str

    @field_validator("day_of_week")
    @classmethod
    def validate_day_of_week(cls, v):
        valid_days = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
        if v not in valid_days:
            raise ValueError(f"day_of_week must be one of: {', '.join(valid_days)}")
        return v

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_30min_unit(cls, v: time):
        if v.minute not in (0, 30) or v.second != 0:
            raise ValueError("予約時間は30分単位で指定してください（例: 10:00, 10:30）")
        return v

    @model_validator(mode="after")
    def validate_time_order(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self

    @field_validator("first_date")
    @classmethod
    def validate_not_past(cls, v: date):
        if v < date.today():
            raise ValueError("過去の日付には予約できません")
        return v

    @field_validator("session_count")
    @classmethod
    def validate_session_count(cls, v):
        if v <= 0:
            raise ValueError("session_count must be greater than 0")
        return v

    @field_validator("capacity")
    @classmethod
    def validate_capacity(cls, v):
        if v <= 0:
            raise ValueError("capacity must be greater than 0")
        return v

    @field_validator("instructor_name")
    @classmethod
    def validate_instructor_name(cls, v):
        if not v.strip():
            raise ValueError("instructor_name must not be empty")
        return v


class ClassCourseOut(BaseModel):
    course_id: int
    lane_set_id: str
    day_of_week: str
    start_time: time
    end_time: time
    first_date: date
    session_count: int
    capacity: int
    instructor_name: str
    status: str
    enrolled_count: Optional[int] = None

    class Config:
        from_attributes = True


# ---------- ClassSession (第二弾で追加) ----------

class ClassSessionOut(BaseModel):
    class_session_id: int
    course_id: int
    session_number: int
    date: date
    start_time: time
    end_time: time
    status: str

    class Config:
        from_attributes = True


class ClassSessionStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ("scheduled", "cancelled"):
            raise ValueError("status must be 'scheduled' or 'cancelled'")
        return v


# ---------- ClassEnrollment (第二弾で追加) ----------

class ClassEnrollmentCreate(BaseModel):
    course_id: int


class ClassEnrollmentOut(BaseModel):
    enrollment_id: int
    course_id: int
    user_id: int
    status: str
    created_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------- Group Reservation (第二弾で追加) ----------

class GroupReservationCreate(BaseModel):
    lane_set_id: str
    date: date
    start_time: time
    end_time: time
    contact_name: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    headcount: Optional[int] = None

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_30min_unit(cls, v: time):
        if v.minute not in (0, 30) or v.second != 0:
            raise ValueError("予約時間は30分単位で指定してください（例: 10:00, 10:30）")
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

    @field_validator("headcount")
    @classmethod
    def validate_headcount(cls, v):
        if v is not None and v <= 0:
            raise ValueError("headcount must be greater than 0")
        return v


class GroupReservationOut(BaseModel):
    reservation_id: int
    lane_set_id: str
    date: date
    start_time: time
    end_time: time
    contact_name: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    headcount: Optional[int] = None
    status: str

    class Config:
        from_attributes = True
