import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent.parent / "data" / "inventory.json"


def check_stock(product: str, size: str, quantity: int) -> dict:
    product = product.strip().lower()
    size = size.strip().upper()

    if quantity <= 0:
        return {
            "in_stock": False,
            "error": "invalid_quantity",
            "message": "Quantity must be at least 1"
        }

    try:
        with open(_DATA_PATH) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {"in_stock": False, "error": "data_read_error", "message": str(exc)}

    products = data.get("products", {})

    if product not in products:
        return {
            "in_stock": False,
            "error": "product_not_found",
            "message": f"We do not carry '{product}'"
        }

    sizes = products[product]
    if size not in sizes:
        available_sizes = list(sizes.keys())
        return {
            "in_stock": False,
            "error": "size_not_found",
            "message": f"'{product}' is not available in size '{size}'",
            "available_sizes": available_sizes
        }

    record = sizes[size]
    available = record["available_qty"]

    if available == 0:
        return {
            "in_stock": False,
            "available_qty": 0,
            "requested_qty": quantity,
            "message": f"'{product}' size {size} is currently out of stock"
        }

    if quantity > available:
        return {
            "in_stock": False,
            "available_qty": available,
            "requested_qty": quantity,
            "message": f"Only {available} unit(s) available for '{product}' size {size}"
        }

    return {
        "in_stock": True,
        "product": product,
        "size": size,
        "color": record.get("color"),
        "available_qty": available,
        "requested_qty": quantity
    }
