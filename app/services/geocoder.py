import httpx
import time

_cache: dict[str, tuple[float, float]] = {}


def geocode(address: str) -> tuple[float, float] | None:
    if address in _cache:
        return _cache[address]
    time.sleep(1)
    resp = httpx.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": address, "format": "json", "limit": 1},
        headers={"User-Agent": "LotWatch/1.0"},
        timeout=10,
    )
    data = resp.json()
    if data:
        result = (float(data[0]["lat"]), float(data[0]["lon"]))
        _cache[address] = result
        return result
    return None
