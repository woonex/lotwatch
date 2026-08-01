from datetime import datetime
from sqlalchemy.orm import Session
from app.models.car import Car, PriceHistory
from app.services.scraper import scrape_url


def refresh_car(db: Session, car: Car) -> None:
    result = scrape_url(car.source_url)

    if not result:
        # Scraping failed entirely — don't flag, could be temporary
        return

    if result.get("possibly_sold"):
        car.possibly_sold = True
        car.updated_at = datetime.utcnow()
        db.commit()
        return

    new_price = result.get("current_price")
    if new_price is not None and new_price != car.current_price:
        db.add(PriceHistory(car_id=car.id, price=new_price))
        car.current_price = new_price

    car.updated_at = datetime.utcnow()
    db.commit()
