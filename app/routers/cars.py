from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.features import assemble_features_from_form, FEATURES
from app.models.car import Car, PriceHistory
from app.services.geocoder import geocode
from app.services.refresh import refresh_car
from app.services.scraper import scrape_url

import json as _json
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["FEATURES"] = FEATURES
templates.env.globals["FEATURES_JSON"] = _json.dumps(FEATURES)



@router.get("/")
def root():
    return RedirectResponse(url="/cars")


@router.get("/cars", response_class=HTMLResponse)
def list_cars(request: Request, db: Session = Depends(get_db)):
    cars = db.query(Car).filter(Car.is_deleted == False).order_by(Car.date_first_seen.desc()).all()
    sold_count = sum(1 for c in cars if c.possibly_sold)
    today = date.today()
    return templates.TemplateResponse(
        request, "cars/table.html",
        {"cars": cars, "today": today, "sold_count": sold_count},
    )


@router.get("/map", response_class=HTMLResponse)
def map_view(request: Request, db: Session = Depends(get_db)):
    import json as _json

    cars = db.query(Car).filter(Car.is_deleted == False).all()
    sold_count = sum(1 for c in cars if c.possibly_sold)
    today = date.today()

    cars_json = _json.dumps(
        [
            {
                "id": c.id,
                "lat": c.lat,
                "lng": c.lng,
                "year": c.year,
                "make": c.make,
                "model": c.model,
                "trim": c.trim,
                "current_price": c.current_price,
                "photo_url": c.photo_url,
                "source_url": c.source_url,
                "date_first_seen": c.date_first_seen.isoformat() if c.date_first_seen else None,
                "possibly_sold": c.possibly_sold,
                "features": c.features or {},
                "max_price": max((ph.price for ph in c.price_history), default=c.current_price),
            }
            for c in cars
        ]
    )
    unmapped = [c for c in cars if c.lat is None or c.lng is None]
    return templates.TemplateResponse(
        request, "cars/map.html",
        {"cars_json": cars_json, "sold_count": sold_count, "today": today,
         "cars_total": len(cars), "cars_unmapped": unmapped},
    )


@router.get("/cars/new", response_class=HTMLResponse)
def new_car_form(request: Request):
    return templates.TemplateResponse(
        request, "cars/form.html",
        {"data": {}, "sold_count": 0, "today": date.today()},
    )


@router.post("/cars/parse-url", response_class=HTMLResponse)
def parse_url(
    request: Request,
    url: str = Form(...),
):
    data = scrape_url(url)
    return templates.TemplateResponse(
        request, "partials/form_fields.html",
        {"data": data, "today": date.today()},
    )


@router.post("/cars")
async def create_car(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    features = assemble_features_from_form(form)

    source_url = form.get('source_url', '')
    dealership_name = form.get('dealership_name', '')
    dealership_address = form.get('dealership_address', '')
    current_price = form.get('current_price', '')
    date_first_seen = form.get('date_first_seen', '')
    year = form.get('year', '')
    make = form.get('make', '')
    model = form.get('model', '')
    trim = form.get('trim', '')
    mileage = form.get('mileage', '')
    vin = form.get('vin', '')
    photo_url = form.get('photo_url', '')
    notes = form.get('notes', '')

    price_int = int(current_price) if current_price and current_price.strip() else None
    year_int = int(year) if year and year.strip() else None
    mileage_int = int(mileage) if mileage and mileage.strip() else None
    dfs = date.fromisoformat(date_first_seen) if date_first_seen and date_first_seen.strip() else date.today()

    car = Car(
        source_url=source_url,
        dealership_name=dealership_name or None,
        dealership_address=dealership_address or None,
        current_price=price_int,
        date_first_seen=dfs,
        year=year_int,
        make=make or None,
        model=model or None,
        trim=trim or None,
        mileage=mileage_int,
        vin=vin or None,
        photo_url=photo_url or None,
        notes=notes or None,
        features=features,
    )
    db.add(car)
    db.flush()  # get car.id

    if price_int is not None:
        db.add(PriceHistory(car_id=car.id, price=price_int))

    db.commit()

    # Geocode
    if dealership_address:
        try:
            coords = geocode(dealership_address)
            if coords:
                car.lat, car.lng = coords
                db.commit()
        except Exception:
            pass

    return RedirectResponse(url="/cars", status_code=303)


@router.post("/cars/{car_id}/refresh")
def refresh_car_route(car_id: int, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if car:
        refresh_car(db, car)
    return RedirectResponse(url="/cars", status_code=303)


@router.post("/cars/{car_id}/sold")
def dismiss_sold(car_id: int, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if car:
        car.possibly_sold = False
        car.updated_at = datetime.utcnow()
        db.commit()
    return RedirectResponse(url="/cars", status_code=303)


@router.get("/cars/{car_id}/edit", response_class=HTMLResponse)
def edit_car_form(car_id: int, request: Request, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        return RedirectResponse(url="/cars", status_code=303)
    features = car.features or {}
    data = {
        "source_url": car.source_url or "",
        "dealership_name": car.dealership_name or "",
        "dealership_address": car.dealership_address or "",
        "current_price": car.current_price or "",
        "date_first_seen": car.date_first_seen.isoformat() if car.date_first_seen else "",
        "year": car.year or "",
        "make": car.make or "",
        "model": car.model or "",
        "trim": car.trim or "",
        "mileage": car.mileage or "",
        "vin": car.vin or "",
        "photo_url": car.photo_url or "",
        "notes": car.notes or "",
        "features": features,
    }
    history = sorted(car.price_history, key=lambda x: x.observed_at)
    return templates.TemplateResponse(
        request, "cars/form.html",
        {"data": data, "car_id": car_id, "sold_count": 0, "today": date.today(), "price_history": history},
    )


@router.post("/cars/{car_id}")
async def update_car(car_id: int, request: Request, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        return RedirectResponse(url="/cars", status_code=303)

    form = await request.form()
    features = assemble_features_from_form(form)

    source_url = form.get('source_url', '')
    dealership_name = form.get('dealership_name', '')
    dealership_address = form.get('dealership_address', '')
    current_price = form.get('current_price', '')
    date_first_seen = form.get('date_first_seen', '')
    year = form.get('year', '')
    make = form.get('make', '')
    model = form.get('model', '')
    trim = form.get('trim', '')
    mileage = form.get('mileage', '')
    vin = form.get('vin', '')
    photo_url = form.get('photo_url', '')
    notes = form.get('notes', '')

    price_int = int(current_price) if current_price and current_price.strip() else None
    year_int = int(year) if year and year.strip() else None
    mileage_int = int(mileage) if mileage and mileage.strip() else None
    dfs = date.fromisoformat(date_first_seen) if date_first_seen and date_first_seen.strip() else car.date_first_seen

    if price_int and price_int != car.current_price:
        db.add(PriceHistory(car_id=car.id, price=price_int))

    address_changed = bool(dealership_address)

    car.source_url = source_url
    car.dealership_name = dealership_name or None
    car.dealership_address = dealership_address or None
    car.current_price = price_int
    car.date_first_seen = dfs
    car.year = year_int
    car.make = make or None
    car.model = model or None
    car.trim = trim or None
    car.mileage = mileage_int
    car.vin = vin or None
    car.photo_url = photo_url or None
    car.notes = notes or None
    car.features = features
    car.updated_at = datetime.utcnow()
    db.commit()

    if address_changed:
        try:
            coords = geocode(dealership_address)
            if coords:
                car.lat, car.lng = coords
                db.commit()
        except Exception:
            pass

    return RedirectResponse(url="/cars", status_code=303)


@router.delete("/cars/{car_id}")
def delete_car(car_id: int, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if car:
        car.is_deleted = True
        car.updated_at = datetime.utcnow()
        db.commit()
    return Response(
        status_code=200,
        headers={"HX-Refresh": "true"},
    )
