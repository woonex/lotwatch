from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, engine, SessionLocal
from app.models import Car  # noqa: F401 – registers models with Base
from app.routers.cars import router as cars_router


def _refresh_all_cars():
    from app.services.refresh import refresh_car

    db = SessionLocal()
    try:
        cars = db.query(Car).all()
        for car in cars:
            try:
                refresh_car(db, car)
            except Exception:
                pass
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)

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

app.include_router(cars_router)
