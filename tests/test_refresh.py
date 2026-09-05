"""
Tests for refresh_car() price update logic.

Uses an in-memory SQLite database and mocks scrape_url so no network calls are made.
"""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models.car import Car, PriceHistory
from app.services.refresh import refresh_car


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def make_car(db: Session, current_price: int | None = 25000) -> Car:
    car = Car(source_url="http://example.com/car/1", current_price=current_price)
    db.add(car)
    db.commit()
    db.refresh(car)
    return car


def price_history(db: Session, car: Car) -> list[int]:
    return [ph.price for ph in db.query(PriceHistory).filter_by(car_id=car.id).all()]


# ---------------------------------------------------------------------------
# Price drop
# ---------------------------------------------------------------------------

def test_price_drop_updates_current_price(db):
    car = make_car(db, current_price=25000)
    with patch("app.services.refresh.scrape_url", return_value={"current_price": 23000}):
        refresh_car(db, car)
    assert car.current_price == 23000


def test_price_drop_records_history(db):
    car = make_car(db, current_price=25000)
    with patch("app.services.refresh.scrape_url", return_value={"current_price": 23000}):
        refresh_car(db, car)
    assert price_history(db, car) == [23000]


# ---------------------------------------------------------------------------
# Price increase — should be ignored
# ---------------------------------------------------------------------------

def test_price_increase_does_not_update_current_price(db):
    car = make_car(db, current_price=25000)
    with patch("app.services.refresh.scrape_url", return_value={"current_price": 27000}):
        refresh_car(db, car)
    assert car.current_price == 25000


def test_price_increase_does_not_record_history(db):
    car = make_car(db, current_price=25000)
    with patch("app.services.refresh.scrape_url", return_value={"current_price": 27000}):
        refresh_car(db, car)
    assert price_history(db, car) == []


# ---------------------------------------------------------------------------
# Price unchanged
# ---------------------------------------------------------------------------

def test_same_price_does_not_record_history(db):
    car = make_car(db, current_price=25000)
    with patch("app.services.refresh.scrape_url", return_value={"current_price": 25000}):
        refresh_car(db, car)
    assert price_history(db, car) == []


# ---------------------------------------------------------------------------
# No existing price (first scrape)
# ---------------------------------------------------------------------------

def test_initial_price_is_set_when_none(db):
    car = make_car(db, current_price=None)
    with patch("app.services.refresh.scrape_url", return_value={"current_price": 25000}):
        refresh_car(db, car)
    assert car.current_price == 25000


def test_initial_price_records_history(db):
    car = make_car(db, current_price=None)
    with patch("app.services.refresh.scrape_url", return_value={"current_price": 25000}):
        refresh_car(db, car)
    assert price_history(db, car) == [25000]


# ---------------------------------------------------------------------------
# Scrape failure
# ---------------------------------------------------------------------------

def test_scrape_failure_does_not_change_price(db):
    car = make_car(db, current_price=25000)
    with patch("app.services.refresh.scrape_url", return_value={}):
        refresh_car(db, car)
    assert car.current_price == 25000
    assert price_history(db, car) == []


# ---------------------------------------------------------------------------
# Possibly sold
# ---------------------------------------------------------------------------

def test_possibly_sold_sets_flag(db):
    car = make_car(db, current_price=25000)
    with patch("app.services.refresh.scrape_url", return_value={"possibly_sold": True}):
        refresh_car(db, car)
    assert car.possibly_sold is True


def test_possibly_sold_does_not_change_price(db):
    car = make_car(db, current_price=25000)
    with patch("app.services.refresh.scrape_url", return_value={"possibly_sold": True}):
        refresh_car(db, car)
    assert car.current_price == 25000
    assert price_history(db, car) == []
