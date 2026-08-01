# Car Buyer Tracker
The car buyer app is designed to aggregate listings for cars similar to a Carvana or a Carfax application, except sorted by features that the user actually cares about, with an interactive map view showing where the dealerships are, and tracking how long the car has been on the lot.

This is primarily designed to replace having multiple tabs open or having a spreadsheet with information that has to be manually checked.

# Key Features
## Car Addition
Car addition should support the following fields:
- Website
- Dealership location
- Listed sale price (this should have a historical tracking view too to know when it's "time to move" on a car if the dealer has lowered a price, etc.)
- Date first seen
- Car year
- Make
- Model
- Trim level
- List of key features the user cares about (explained more below)
- A photo of the car parsed from the URL either automatically or given by the user if an obvious one is not available.

Ideally, these fields could be parsed from just a URL. The key features the car has should be scrutinized more and available to modify by the user (dealership websites are not very reliable for information).

Cars can be added in one of two ways:
- **Manual entry:** all fields are provided directly by the user via a form.
- **URL parsing:** the user provides a URL, the system attempts to scrape and populate the form fields automatically, then redirects to the same form pre-filled with whatever was parsed. The user can correct anything before saving.

### Key Features User Cares About
This should be an expandable list that the user can select that a car does or doesn't have.

Initial features:
- Drivetrain type (gas, hybrid, PHEV, EV)
- Drive type: FWD, RWD, AWD, 4x4
- Safety features are also in this, but probably tracked via a separate category with the initial values below
- Parking sensors (boolean)
- 360 camera view (boolean)
- Seat material type (cloth, cloth/leather, leather)
- Heated seats
- Ventilated seats

# Car Refreshing
- Every non-deterministic time during normal waking hours at non-fixed times the system should try to refresh to verify all tracked cars are available. If the page seems to show that the car has been removed, the system should set a flag on the car record to get the user to verify the car has been sold from the lot.
- e.g. run this at 8am ± 2 hrs, and also again at 6pm ± 2 hrs. These should be configurable by the user.

An additional "refresh now" should also be part of the system in cases of wanting to get the most up-to-date information immediately.

# Map View
The map view should display an overlay of a map with all the cars placed on them. Tapping on it should bring up a brief view that shows the following information:
- Picture
- Year, make, model, trim
- Time on the lot as compared to date today minus first day seen (in days, e.g. 31 days, not fractional precision)
- Current price (and if price has varied over time, the comparison of current price to all-time high)

## Filtering
The map should also allow the user to filter by features described above, including price.

## Table View
There should be another page that displays all of this information in a neat table view, allowing for typical sorting/filtering operations on any fields.

---

# Architectural Decisions

## Platform
- Single-user local web app (no authentication required)
- Python backend, runs locally via a virtualenv for development
- Deployable via Docker Compose for a more persistent local setup

## Web Framework: FastAPI + HTMX + Jinja2
- **FastAPI** for the backend — Python-native, async-capable (important for running background scrape/refresh jobs alongside web requests), with automatic API docs at `/docs`
- **Jinja2** for server-side HTML templating, built into FastAPI
- **HTMX** for frontend interactivity — allows dynamic page updates (filter changes, form submissions, table refreshes) with minimal JavaScript
- The **map view** is the one exception: **Leaflet.js** handles the interactive map with a GeoJSON endpoint from FastAPI. This is the only area that requires meaningful JavaScript (~30–40 lines)

## Scraping: Playwright
- Dealer sites are JS-heavy, so a headless browser is required
- Playwright (Python) handles scraping on demand (URL add flow) and scheduled refreshes
- Manual entry is always available as a fallback when scraping fails or produces bad data

## Database: PostgreSQL + SQLAlchemy + Alembic
- PostgreSQL for persistence
- Car features (the user-managed expandable list) stored as a **JSONB column** — flexible for schema evolution without migrations per new feature
- Price history stored as a separate `price_history` table (`car_id`, `price`, `observed_at`) — this is how historical tracking is implemented explicitly, not a built-in Postgres feature
- **SQLAlchemy** as the ORM
- **Alembic** for schema migrations

## Background Jobs: APScheduler
- Handles the randomized refresh schedule (e.g. 8am ± 2 hrs, 6pm ± 2 hrs)
- Runs in-process alongside FastAPI (sufficient for single-user local use)
- Refresh times are user-configurable

## Geocoding / Map Pins
- Dealership address → map pin via a geocoding step (provider TBD)

## Dependencies
- Runtime dependencies: `requirements.txt`
- Test dependencies: `requirements-test.txt`

## Dev Environments
- **Bare metal / local dev:** Python virtualenv (`venv`), run FastAPI directly
- **Devcontainer:** `.devcontainer/` config for VS Code,
- **Production-like local:** `Dockerfile` + `docker-compose.yml` for a fully containerized deployment including Postgres
