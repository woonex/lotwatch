from datetime import date, datetime
from sqlalchemy import (
    Boolean, DateTime, Date, Float, ForeignKey,
    Integer, String, Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_url: Mapped[str] = mapped_column(Text)
    dealership_name: Mapped[str | None] = mapped_column(String)
    dealership_address: Mapped[str | None] = mapped_column(String)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    date_first_seen: Mapped[date] = mapped_column(Date, default=date.today)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    make: Mapped[str | None] = mapped_column(String, nullable=True)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    trim: Mapped[str | None] = mapped_column(String, nullable=True)
    mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    features: Mapped[dict] = mapped_column(JSONB, default=dict)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    possibly_sold: Mapped[bool] = mapped_column(Boolean, default=False)
    vin: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    price_history: Mapped[list["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="car", cascade="all, delete-orphan"
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    car_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cars.id", ondelete="CASCADE")
    )
    price: Mapped[int] = mapped_column(Integer)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    car: Mapped["Car"] = relationship("Car", back_populates="price_history")
