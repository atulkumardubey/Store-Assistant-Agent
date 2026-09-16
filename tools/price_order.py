import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent / "data" / "discounts.json"


def price_order(product: str, quantity: int) -> dict:
    product = product.strip().lower()

    if quantity <= 0:
        return {"error": "invalid_quantity", "message": "Quantity must be at least 1"}

    try:
        with open(_DATA_PATH) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {"error": "data_read_error", "message": str(exc)}

    prices = data.get("prices", {})
    if product not in prices:
        return {
            "error": "product_not_found",
            "message": f"Pricing not available for '{product}'"
        }

    base_price = prices[product]["base_price"]
    currency = prices[product]["currency"]

    discount_pct = 0
    for tier in data.get("discount_tiers", []):
        min_q = tier["min_qty"]
        max_q = tier["max_qty"]
        if quantity >= min_q and (max_q is None or quantity <= max_q):
            discount_pct = tier["discount_pct"]
            break

    discounted_unit = round(base_price * (1 - discount_pct / 100), 2)
    total = round(discounted_unit * quantity, 2)

    return {
        "product": product,
        "quantity": quantity,
        "base_price": base_price,
        "discount_pct": discount_pct,
        "discounted_unit_price": discounted_unit,
        "total": total,
        "currency": currency
    }
