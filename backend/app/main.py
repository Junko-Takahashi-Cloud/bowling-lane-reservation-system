from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app.models.models import LaneSet
from app.routers import auth, reservations, admin

Base.metadata.create_all(bind=engine)


def seed_lane_sets():
    """初期データ: A(1・2番) / B(3・4番) のレーンセットを投入"""
    db: Session = SessionLocal()
    try:
        if db.query(LaneSet).count() == 0:
            db.add_all([
                LaneSet(lane_set_id="A", name="Aセット（1・2番）", status="available"),
                LaneSet(lane_set_id="B", name="Bセット（3・4番）", status="available"),
            ])
            db.commit()
    finally:
        db.close()


seed_lane_sets()

app = FastAPI(title="スポーツボウリング場予約システム API", version="0.1.0")

app.include_router(auth.router)
app.include_router(reservations.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "bowling-reservation-api"}
