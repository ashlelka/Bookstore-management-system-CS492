"""
Bookstore Management System
Sprint 2 - T2-004
Developer: Ashley Lindamood

BMS-005 Purchase Order Management:
  - Create purchase orders
  - Connect purchase orders to existing suppliers
  - Store purchase order records
  - Track purchase order status
  - Update inventory when purchase orders are received
"""

import json
from datetime import datetime
from pathlib import Path

from inventory import load_books, save_books
from suppliers import find_supplier


APP_DIR = Path(__file__).resolve().parent
PURCHASE_ORDERS_PATH = APP_DIR / "purchase_orders.json"


def load_purchase_orders():
    """Load all purchase orders from purchase_orders.json."""

    if not PURCHASE_ORDERS_PATH.exists():
        return []

    try:
        data = json.loads(
            PURCHASE_ORDERS_PATH.read_text()
        )
    except json.JSONDecodeError:
        return []

    if isinstance(data, list):
        return data

    return data.get("purchase_orders") or []


def save_purchase_orders(purchase_orders):
    """Save purchase orders to purchase_orders.json."""

    PURCHASE_ORDERS_PATH.write_text(
        json.dumps(
            {
                "purchase_orders": purchase_orders
            },
            indent=2,
        ) + "\n"
    )


def next_purchase_order_id(
    purchase_orders=None,
):
    """Return the next available purchase order ID."""

    if purchase_orders is None:
        purchase_orders = load_purchase_orders()

    if not purchase_orders:
        return 1

    return max(
        int(
            order.get(
                "purchase_order_id"
            ) or 0
        )
        for order in purchase_orders
    ) + 1


def find_purchase_order(
    purchase_order_id,
    purchase_orders=None,
):
    """Find one purchase order by ID."""

    target = str(purchase_order_id)

    if purchase_orders is None:
        purchase_orders = load_purchase_orders()

    for order in purchase_orders:
        if str(
            order.get("purchase_order_id")
        ) == target:
            return order

    return None


def create_purchase_order(
    supplier_id,
    items,
    created_by,
    notes="",
):
    """
    Create and save a new purchase order.

    items should contain dictionaries such as:
    {
        "book_id": 1,
        "title": "Book Title",
        "quantity": 5
    }
    """

    supplier = find_supplier(supplier_id)

    if supplier is None:
        return False, "Supplier was not found."

    if not supplier.get("active", True):
        return False, "Supplier is inactive."

    if not items:
        return False, "At least one book is required."

    clean_items = []

    for item in items:
        title = str(
            item.get("title") or ""
        ).strip()

        try:
            quantity = int(
                item.get("quantity") or 0
            )
        except (TypeError, ValueError):
            return (
                False,
                "Book quantity must be a whole number.",
            )

        if not title:
            return (
                False,
                "Each purchase order item needs a title.",
            )

        if quantity <= 0:
            return (
                False,
                "Book quantity must be greater than zero.",
            )

        clean_items.append(
            {
                "book_id": item.get("book_id"),
                "title": title,
                "quantity": quantity,
            }
        )

    purchase_orders = load_purchase_orders()

    purchase_order_id = next_purchase_order_id(
        purchase_orders
    )

    order = {
        "purchase_order_id": purchase_order_id,
        "supplier_id": supplier.get(
            "supplier_id"
        ),
        "supplier_name": supplier.get("name"),
        "status": "Pending",
        "created_by": created_by,
        "order_date": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "items": clean_items,
        "notes": str(notes or "").strip(),

        # Prevent the same shipment from being
        # added to inventory more than once.
        "inventory_received": False,
    }

    purchase_orders.append(order)

    save_purchase_orders(
        purchase_orders
    )

    return True, purchase_order_id


def receive_purchase_order(order):
    """
    Add received purchase order quantities
    to inventory.

    A purchase order can update inventory
    only once.
    """

    if order.get(
        "inventory_received",
        False,
    ):
        return (
            False,
            "This purchase order was already received.",
        )

    books = load_books()

    updates = []

    # Validate every item before changing inventory.
    for item in order.get("items", []):

        item_book_id = item.get("book_id")

        try:
            quantity_received = int(
                item.get("quantity") or 0
            )
        except (TypeError, ValueError):
            return (
                False,
                "Invalid received quantity.",
            )

        if quantity_received <= 0:
            return (
                False,
                "Received quantity must be "
                "greater than zero.",
            )

        matching_book = None

        for book in books:
            if str(
                book.get("book_id")
            ) == str(item_book_id):

                matching_book = book
                break

        if matching_book is None:
            return (
                False,
                "A book on this purchase order "
                "was not found in inventory.",
            )

        updates.append(
            (
                matching_book,
                quantity_received,
            )
        )

    # All items have been validated.
    # Inventory can now safely be updated.
    for book, quantity_received in updates:

        current_quantity = int(
            book.get("quantity") or 0
        )

        book["quantity"] = (
            current_quantity
            + quantity_received
        )

    save_books(books)

    # Mark this PO as already applied
    # to inventory.
    order["inventory_received"] = True

    return True, "Inventory updated."


def update_purchase_order_status(
    purchase_order_id,
    new_status,
):
    """
    Update an existing purchase order status.

    Received orders update inventory once.
    Closed and Cancelled orders are final
    and cannot be changed again.
    """

    allowed_statuses = {
        "Pending",
        "Ordered",
        "Received",
        "Closed",
        "Cancelled",
    }

    if new_status not in allowed_statuses:
        return (
            False,
            "Invalid purchase order status.",
        )

    purchase_orders = load_purchase_orders()

    order = find_purchase_order(
        purchase_order_id,
        purchase_orders,
    )

    if order is None:
        return (
            False,
            "Purchase order was not found.",
        )

    current_status = order.get(
        "status",
        "Pending",
    )

    # Closed and Cancelled purchase orders
    # are final and cannot be changed.
    if current_status in {
        "Closed",
        "Cancelled",
    }:
        return (
            False,
            "This purchase order is closed "
            "and cannot be changed.",
        )

    # A purchase order should only be closed
    # after the shipment has been received.
    if new_status == "Closed":

        if current_status != "Received":
            return (
                False,
                "A purchase order must be "
                "received before it can be closed.",
            )

        order["status"] = "Closed"

        save_purchase_orders(
            purchase_orders
        )

        return (
            True,
            "Purchase order closed.",
        )

    # Received updates inventory exactly once.
    if new_status == "Received":

        if not order.get(
            "inventory_received",
            False,
        ):

            ok, message = receive_purchase_order(
                order
            )

            if not ok:
                return False, message

    order["status"] = new_status

    save_purchase_orders(
        purchase_orders
    )

    return (
        True,
        "Purchase order status updated.",
    )