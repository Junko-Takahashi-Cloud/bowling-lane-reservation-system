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
        CheckConstraint("reservation_type IN ('general','practice','class')", name="ck_res_type"),
        CheckConstraint("status IN ('reserved','cancelled')", name="ck_res_status"),
        CheckConstraint("end_time > start_time", name="ck_res_time_order"),
    )

    user = relationship("User", back_populates="reservations")
    lane_set = relationship("LaneSet", back_populates="reservations")
