from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models import Car, RefreshLog
from app.routers.cars import router as cars_router


def _refresh_all_cars():
    from app.services.refresh import refresh_car

    db = SessionLocal()
    try:
        cars = db.query(Car).filter(Car.is_deleted == False).all()
        attempted = len(cars)
        succeeded = 0
        failed = 0
        for car in cars:
            try:
                result = refresh_car(db, car)
                if result:
                    succeeded += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
        log = RefreshLog(cars_attempted=attempted, cars_succeeded=succeeded, cars_failed=failed)
        db.add(log)
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from alembic.config import Config
    from alembic import command
    from sqlalchemy import inspect, text
    from app.database import engine

    alembic_cfg = Config("alembic.ini")

    # Auto-stamp existing servers that pre-date Alembic
    with engine.connect() as conn:
        has_alembic = inspect(engine).has_table("alembic_version")
        if not has_alembic and inspect(engine).has_table("cars"):
            # Existing server — stamp at base so all migrations run (they're checkfirst-safe)
            command.stamp(alembic_cfg, "base")

    command.upgrade(alembic_cfg, "head")

    # Start scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _refresh_all_cars,
        CronTrigger(hour=8, jitter=7200),
        id="morning_refresh",
    )
    scheduler.add_job(
        _refresh_all_cars,
        CronTrigger(hour=18, jitter=7200),
        id="evening_refresh",
    )
    scheduler.start()

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(title="LotWatch", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

import json as _json
from app.features import FEATURES
templates.env.globals["FEATURES"] = FEATURES
templates.env.globals["FEATURES_JSON"] = _json.dumps(FEATURES)

from datetime import timezone as _tz
def _utc_to_local(dt):
    if dt is None:
        return ""
    return dt.replace(tzinfo=_tz.utc).astimezone(tz=None)
templates.env.filters["localtime"] = _utc_to_local

app.include_router(cars_router)
