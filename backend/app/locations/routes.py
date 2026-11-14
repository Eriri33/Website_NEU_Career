
import json
import time
from collections import OrderedDict
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Blueprint, request, jsonify, current_app
from app.database import get_db
from app.textutil import like_pattern


locations_bp = Blueprint("locations", __name__)


# Cache autocomplete trong bộ nhớ của từng tiến trình Flask.
# Khi triển khai lớn có thể thay bằng Redis.
_photon_cache = OrderedDict()
_photon_cache_lock = Lock()


def get_cached_photon_result(key):
    now = time.time()

    with _photon_cache_lock:
        cached = _photon_cache.get(key)

        if not cached:
            return None

        expires_at, data = cached

        if now >= expires_at:
            del _photon_cache[key]
            return None

        _photon_cache.move_to_end(key)
        return data


def save_photon_result(key, data):
    now = time.time()

    ttl = current_app.config.get("PHOTON_CACHE_TTL", 300)
    max_size = current_app.config.get("PHOTON_CACHE_MAX_SIZE", 256)

    with _photon_cache_lock:
        _photon_cache[key] = (now + ttl, data)
        _photon_cache.move_to_end(key)

        while len(_photon_cache) > max_size:
            _photon_cache.popitem(last=False)


def format_photon_address(properties):
    """Tạo địa chỉ dễ đọc từ các trường Photon trả về."""

    parts = [
        properties.get("name"),
        properties.get("housenumber"),
        properties.get("street"),
        properties.get("district"),
        properties.get("city"),
        properties.get("county"),
        properties.get("state"),
        properties.get("postcode"),
        properties.get("country"),
    ]

    result = []
    seen = set()

    for part in parts:
        if not part:
            continue

        part = str(part).strip()

        if part and part.lower() not in seen:
            result.append(part)
            seen.add(part.lower())

    return ", ".join(result)


@locations_bp.get("/search")
def search_locations():
    """
    Tìm kiếm địa chỉ tại Việt Nam bằng Photon.

    GET /api/locations/search?q=...
    """

    query = (request.args.get("q") or "").strip()

    if len(query) < 3:
        return jsonify({
            "results": [],
            "message": "Vui lòng nhập ít nhất 3 ký tự."
        })

    if len(query) > 120:
        return jsonify({
            "error": "query_too_long",
            "message": "Địa chỉ tìm kiếm không được vượt quá 120 ký tự."
        }), 400

    # Chuẩn hóa cache key
    cache_key = query.casefold()

    cached = get_cached_photon_result(cache_key)

    if cached is not None:
        return jsonify({
            "results": cached,
            "cached": True
        })

    base_url = current_app.config.get(
        "PHOTON_BASE_URL",
        "https://photon.komoot.io"
    ).rstrip("/")

    params = urlencode({
        "q": query,
        "limit": 10,
        "countrycode": "VN",
    })

    url = f"{base_url}/api/?{params}"

    photon_timeout = current_app.config.get("PHOTON_TIMEOUT", 5)

    http_request = Request(
        url,
        headers={
            "User-Agent": "NEU-Career/1.0 (job location search)",
            "Accept": "application/json",
        }
    )

    try:
        with urlopen(http_request, timeout=photon_timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))

    except HTTPError as error:
        current_app.logger.warning(
            "Photon HTTP error: %s", error.code
        )

        return jsonify({
            "error": "location_service_error",
            "message": "Dịch vụ tìm kiếm địa chỉ đang gặp sự cố. Vui lòng thử lại."
        }), 502

    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        current_app.logger.warning(
            "Photon connection error: %s", error
        )

        return jsonify({
            "error": "location_service_unavailable",
            "message": "Không thể kết nối dịch vụ tìm kiếm địa chỉ. Vui lòng thử lại."
        }), 503

    results = []

    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}

        coordinates = geometry.get("coordinates") or []

        # Chỉ chấp nhận kết quả thuộc Việt Nam.
        if (properties.get("countrycode") or "").upper() != "VN":
            continue

        if len(coordinates) < 2:
            continue

        try:
            longitude = float(coordinates[0])
            latitude = float(coordinates[1])
        except (TypeError, ValueError):
            continue

        # Kiểm tra tọa độ nằm trong phạm vi địa lý Việt Nam.
        if not (102 <= longitude <= 110 and 8 <= latitude <= 24):
            continue

        label = format_photon_address(properties)

        if not label:
            continue

        results.append({
            "label": label,
            "latitude": latitude,
            "longitude": longitude,
            "type": properties.get("type") or "",
            "osm_id": properties.get("osm_id"),
        })

        if len(results) >= 5:
            break

    save_photon_result(cache_key, results)

    return jsonify({
        "results": results,
        "cached": False
    })


@locations_bp.get("/provinces")
def list_provinces():
    q = (request.args.get("q") or "").strip()

    sql = "SELECT code, name FROM provinces"
    params = []

    if q:
        sql += " WHERE fold(name) LIKE ? ESCAPE '\\'"
        params.append(like_pattern(q))

    sql += " ORDER BY name"

    rows = get_db().execute(sql, params).fetchall()
    return jsonify([dict(row) for row in rows])


def get_wards_by_province(province_code):
    db = get_db()

    province = db.execute(
        "SELECT code, name FROM provinces WHERE code = ?",
        (province_code,)
    ).fetchone()

    if not province:
        return None, jsonify({
            "error": "province_not_found",
            "message": "Không tìm thấy tỉnh/thành phố."
        }), 404

    q = (request.args.get("q") or "").strip()

    sql = """
        SELECT code, name, level, province_code
        FROM wards
        WHERE province_code = ?
    """
    params = [province_code]

    if q:
        sql += " AND fold(name) LIKE ? ESCAPE '\\'"
        params.append(like_pattern(q))

    sql += " ORDER BY name"

    rows = db.execute(sql, params).fetchall()
    return jsonify([dict(row) for row in rows]), None, None


@locations_bp.get("/wards")
def get_wards():
    province_code = (request.args.get("province_code") or "").strip()

    if not province_code:
        return jsonify({
            "error": "missing_province_code",
            "message": "Vui lòng cung cấp mã tỉnh/thành phố."
        }), 400

    result, error, status = get_wards_by_province(province_code)

    if error:
        return error, status

    return result


@locations_bp.get("/provinces/<province_code>/wards")
def list_wards(province_code):
    result, error, status = get_wards_by_province(province_code)

    if error:
        return error, status

    return result
