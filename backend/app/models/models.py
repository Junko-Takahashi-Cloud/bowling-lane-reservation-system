"""
DBモデル定義

設計方針（レビューで確定した内容）：
- Users.role: user / competitor / admin（要件定義Ver.2準拠）
- LaneSet: MVPではセット単位の状態管理のみ（個別レーン管理はPhase2）
- Reservation: reservation_type（システム区分）のみMVP対象。purposeは対象外
- status は論理削除方式（reserved / cancelled）。物理削除は行わない
"""
from sqlalchemy import (
    Column, Integer, String, Date, Time, ForeignKey,
    CheckConstraint, DateTime, func
)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("role IN ('user','competitor','admin')", name="ck_users_role"),
    )

    reservations = relationship("Reservation", back_populates="user")


class LaneSet(Base):
    __tablename__ = "lane_sets"

    # 例: 'A', 'B'
    lane_set_id = Column(String(10), primary_key=True)
    name = Column(String(50), nullable=False)
    # MVPではセット単位の状態管理のみ（個別レーンの故障管理はPhase2で Lanes テーブルを分離）
    status = Column(String(20), nullable=False, default="available")

    __table_args__ = (
        CheckConstraint("status IN ('available','maintenance')", name="ck_lanesets_status"),
    )

    reservations = relationship("Reservation", back_populates="lane_set")


class Reservation(Base):
    __tablename__ = "reservations"

    reservation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    lane_set_id = Column(String(10), ForeignKey("lane_sets.lane_set_id"), nullable=False, index=True)

    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    # システム管理用区分。class(初心者教室)は将来拡張だが値としては予約しておく
    reservation_type = Column(String(30), nullable=False, default="general")
    status = Column(String(20), nullable=False, default="reserved")

    created_at = Column(DateTime, server_default=func.now())
    cancelled_at = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("reservation_type IN ('general','practice','class','group')", name="ck_res_type"),
        CheckConstraint("status IN ('reserved','cancelled')", name="ck_res_status"),
        CheckConstraint("end_time > start_time", name="ck_res_time_order"),
    )

    user = relationship("User", back_populates="reservations")
    lane_set = relationship("LaneSet", back_populates="reservations")


class ClassCourse(Base):
    """教室コース全体（全5回セット）。第二弾で追加。"""
    __tablename__ = "class_courses"

    course_id = Column(Integer, primary_key=True, autoincrement=True)
    lane_set_id = Column(String(10), ForeignKey("lane_sets.lane_set_id"), nullable=False, index=True)
    day_of_week = Column(String(10), nullable=False)  # 'monday'...'sunday'
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    first_date = Column(Date, nullable=False)
    session_count = Column(Integer, nullable=False, default=5)
    capacity = Column(Integer, nullable=False, default=10)
    instructor_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="scheduled")

    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_course_capacity"),
        CheckConstraint("session_count > 0", name="ck_course_session_count"),
        CheckConstraint("status IN ('scheduled','cancelled')", name="ck_course_status"),
        CheckConstraint("end_time > start_time", name="ck_course_time_order"),
    )

    lane_set = relationship("LaneSet")
    sessions = relationship("ClassSession", back_populates="course")
    enrollments = relationship("ClassEnrollment", back_populates="course")


class ClassSession(Base):
    """コースから自動生成される各回（session_number 1〜N）。第二弾で追加。"""
    __tablename__ = "class_sessions"

    class_session_id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("class_courses.course_id"), nullable=False, index=True)
    session_number = Column(Integer, nullable=False)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String(20), nullable=False, default="scheduled")

    __table_args__ = (
        CheckConstraint("status IN ('scheduled','cancelled')", name="ck_session_status"),
        CheckConstraint("end_time > start_time", name="ck_session_time_order"),
    )

    course = relationship("ClassCourse", back_populates="sessions")


class ClassEnrollment(Base):
    """生徒の申込。コース単位（1回申込で全セッション分参加扱い）。第二弾で追加。"""
    __tablename__ = "class_enrollments"

    enrollment_id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("class_courses.course_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="enrolled")
    created_at = Column(DateTime, server_default=func.now())
    cancelled_at = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('enrolled','cancelled')", name="ck_enrollment_status"),
    )

    course = relationship("ClassCourse", back_populates="enrollments")
    user = relationship("User")


class GroupReservationDetail(Base):
    """団体・グループ予約の追加情報。第二弾で追加。"""
    __tablename__ = "group_reservation_details"

    detail_id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, ForeignKey("reservations.reservation_id"), nullable=False, unique=True, index=True)
    contact_name = Column(String(100), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    headcount = Column(Integer, nullable=True)

    reservation = relationship("Reservation")
