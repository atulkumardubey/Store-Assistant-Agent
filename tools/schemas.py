TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": (
                "Use this tool to check whether a product is available in the required "
                "size and quantity. Always call this first before checking price or delivery."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {
                        "type": "string",
                        "description": "Product name in lowercase (e.g. 'shirt', 'jacket', 't-shirt', 'trouser')"
                    },
                    "size": {
                        "type": "string",
                        "description": "Size code (e.g. 'S', 'M', 'L', 'XL' for clothing; '30', '32', '34' for trousers)"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of units the customer wants to order"
                    }
                },
                "required": ["product", "size", "quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "price_order",
            "description": (
                "Use this tool to get the total price for an order, including any bulk discounts. "
                "Only call this after check_stock has confirmed the item is in stock."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {
                        "type": "string",
                        "description": "Product name in lowercase (e.g. 'shirt', 'jacket', 't-shirt', 'trouser')"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of units to price"
                    }
                },
                "required": ["product", "quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delivery_eta",
            "description": (
                "Use this tool to get the estimated delivery date for a pincode. "
                "Only call this after check_stock has confirmed the item is in stock."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pincode": {
                        "type": "string",
                        "description": "6-digit Indian postal code for the delivery address"
                    }
                },
                "required": ["pincode"]
            }
        }
    }
]
