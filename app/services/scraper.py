import json
import re
import httpx
from bs4 import BeautifulSoup


def _parse_html(html: str, url: str) -> dict:
    result = {}
    soup = BeautifulSoup(html, "html.parser")

    # 1. JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            t = item.get("@type", "")
            if t not in ("Vehicle", "Product", "Car"):
                continue
            if "vehicleModelDate" in item:
                try:
                    result["year"] = int(item["vehicleModelDate"])
                except (ValueError, TypeError):
                    pass
            if "name" in item and "year" not in result:
                m = re.search(r"\b(19|20)\d{2}\b", item["name"])
                if m:
                    result["year"] = int(m.group())
            if "manufacturer" in item:
                mfr = item["manufacturer"]
                result["make"] = mfr.get("name") if isinstance(mfr, dict) else str(mfr)
            if "vehicleModelDate" in item and "model" not in result:
                result["model"] = item.get("name", "")
            if "model" in item:
                result["model"] = item["model"]
            if "vehicleIdentificationNumber" in item:
                result["vin"] = item["vehicleIdentificationNumber"]
            if "image" in item:
                img = item["image"]
                result["photo_url"] = img[0] if isinstance(img, list) else img
            if "offers" in item:
                offers = item["offers"]
                if isinstance(offers, list):
                    offers = offers[0]
                try:
                    result["current_price"] = int(float(str(offers.get("price", "")).replace(",", "")))
                except (ValueError, TypeError):
                    pass
            if "fuelType" in item:
                fuel = item["fuelType"].lower()
                if "electric" in fuel:
                    result.setdefault("features", {})["drivetrain"] = "ev"
                elif "plug" in fuel or "phev" in fuel:
                    result.setdefault("features", {})["drivetrain"] = "phev"
                elif "hybrid" in fuel:
                    result.setdefault("features", {})["drivetrain"] = "hybrid"
                else:
                    result.setdefault("features", {})["drivetrain"] = "gas"
            break

    # 2. CarGurus embedded JSON patterns
    cg_patterns = {
        "current_price": r'"price"\s*:\s*(\d+)',
        "mileage": r'"mileage"\s*:\s*(\d+)',
        "make": r'"make"\s*:\s*"([^"]+)"',
        "model": r'"model"\s*:\s*"([^"]+)"',
        "year": r'"year"\s*:\s*(\d{4})',
        "vin": r'"vin"\s*:\s*"([^"]+)"',
        "dealership_name": r'"dealerName"\s*:\s*"([^"]+)"',
    }
    for field, pattern in cg_patterns.items():
        if field not in result:
            m = re.search(pattern, html)
            if m:
                val = m.group(1)
                if field in ("current_price", "mileage", "year"):
                    try:
                        result[field] = int(val)
                    except ValueError:
                        pass
                else:
                    result[field] = val

    # CarGurus city+stateCode → dealership_address
    if "dealership_address" not in result:
        city_m = re.search(r'"city"\s*:\s*"([^"]+)"', html)
        state_m = re.search(r'"stateCode"\s*:\s*"([^"]+)"', html) or re.search(r'"state"\s*:\s*"([A-Z]{2})"', html)
        if city_m and state_m:
            result["dealership_address"] = f"{city_m.group(1)}, {state_m.group(1)}"
        elif city_m:
            result["dealership_address"] = city_m.group(1)

    # 3. Generic OG tags
    og_title = soup.find("meta", property="og:title")
    if og_title and "year" not in result:
        content = og_title.get("content", "")
        m = re.search(r"\b(19|20)\d{2}\b", content)
        if m:
            result["year"] = int(m.group())
    og_image = soup.find("meta", property="og:image")
    if og_image and "photo_url" not in result:
        result["photo_url"] = og_image.get("content", "")

    result["source_url"] = url
    return result


def _fetch_with_httpx(url: str) -> tuple[int, str]:
    resp = httpx.get(
        url,
        follow_redirects=True,
        timeout=15,
        headers={"User-Agent": "Mozilla/5.0 (compatible; LotWatch/1.0)"},
    )
    return resp.status_code, resp.text


def _fetch_with_playwright(url: str) -> tuple[int, str]:
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth

    html = ""
    status = 200
    with sync_playwright() as p:
        Stealth().hook_playwright_context(p)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
        if response:
            status = response.status
        page.wait_for_timeout(3000)
        html = page.content()
        browser.close()
    return status, html


def scrape_url(url: str) -> dict:
    status, html = None, ""
    try:
        status, html = _fetch_with_httpx(url)
    except Exception:
        pass

    if not html or (status and status >= 400):
        try:
            status, html = _fetch_with_playwright(url)
        except Exception:
            return {}

    if status == 404:
        return {"possibly_sold": True}

    if not html:
        return {}

    result = _parse_html(html, url)

    # Possibly sold: VIN known but not in HTML
    if result.get("vin") and result["vin"] not in html:
        result["possibly_sold"] = True

    return result
