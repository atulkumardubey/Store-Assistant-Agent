import json
from datetime import date, timedelta
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent / "data" / "shipping.json"


def _add_business_days(start: date, days: int) -> date:
    """Add `days` calendar days, skipping Sundays."""
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() != 6:  # 6 = Sunday
            added += 1
    return current


def delivery_eta(pincode: str) -> dict:
    pincode = pincode.strip()

    try:
        with open(_DATA_PATH) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {"error": "data_read_error", "message": str(exc)}

    pincodes = data.get("pincodes", {})
    if pincode not in pincodes:
        return {
            "error": "pincode_not_found",
            "message": f"Delivery is not available to pincode '{pincode}'"
        }

    info = pincodes[pincode]
    zone = info["zone"]
    eta_days = data["zone_eta_days"][zone]

    delivery_date = _add_business_days(date.today(), eta_days)

    return {
        "pincode": pincode,
        "city": info["city"],
        "zone": zone,
        "eta_days": eta_days,
        "estimated_delivery_date": delivery_date.strftime("%Y-%m-%d")
    }
