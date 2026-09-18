"""
Bookstore Management System
Sprint 2 - T2-004
Developer: Ashley Lindamood

Purchase Order Tests:
  - Verify supplier connection
  - Reject invalid suppliers
  - Reject empty purchase orders
  - Reject invalid quantities
  - Create and save purchase orders
  - Verify sequential purchase order IDs
  - Update purchase order status
  - Reject invalid status changes
  - Update inventory when a PO is received
  - Prevent duplicate inventory updates
  - Restore purchase_orders.json after testing
  - Restore books.json after testing
"""

from copy import deepcopy

from inventory import (
    load_books,
    save_books,
)

from purchase_orders import (
    create_purchase_order,
    find_purchase_order,
    load_purchase_orders,
    save_purchase_orders,
    update_purchase_order_status,
)

from suppliers import load_suppliers


failed = False


def report(condition, message):
    """Display PASS or FAIL for each test."""

    global failed

    if condition:
        print(f"PASS: {message}")
    else:
        print(f"FAIL: {message}")
        failed = True


print("\nPURCHASE ORDER TESTS")


# ---------------------------------------------------------
# Save original JSON data.
#
# Both files are restored when testing is finished so the
# automated test does not permanently change real data.
# ---------------------------------------------------------

purchase_order_snapshot = deepcopy(
    load_purchase_orders()
)

book_snapshot = deepcopy(
    load_books()
)


try:

    # -----------------------------------------------------
    # TEST 1
    # Verify supplier records are available.
    # -----------------------------------------------------

    suppliers = load_suppliers()

    report(
        len(suppliers) > 0,
        "Supplier records are available for "
        "purchase orders.",
    )

    supplier = (
        suppliers[0]
        if suppliers
        else None
    )

    supplier_id = (
        supplier.get("supplier_id")
        if supplier
        else None
    )


    # -----------------------------------------------------
    # Get a real inventory book for integration testing.
    # -----------------------------------------------------

    books = load_books()

    test_book = (
        books[0]
        if books
        else None
    )

    report(
        test_book is not None,
        "Inventory contains a book for "
        "purchase order testing.",
    )

    test_book_id = (
        test_book.get("book_id")
        if test_book
        else None
    )

    test_book_title = (
        test_book.get("title")
        if test_book
        else "Test Book"
    )


    # -----------------------------------------------------
    # TEST 2
    # Invalid supplier IDs should be rejected.
    # -----------------------------------------------------

    ok, message = create_purchase_order(
        supplier_id=999999,
        items=[
            {
                "book_id": test_book_id,
                "title": test_book_title,
                "quantity": 5,
            }
        ],
        created_by="testadmin",
    )

    report(
        not ok
        and message == "Supplier was not found.",
        "Invalid supplier is rejected.",
    )


    # -----------------------------------------------------
    # TEST 3
    # A purchase order must contain at least one book.
    # -----------------------------------------------------

    ok, message = create_purchase_order(
        supplier_id=supplier_id,
        items=[],
        created_by="testadmin",
    )

    report(
        not ok
        and message
        == "At least one book is required.",
        "Empty purchase order is rejected.",
    )


    # -----------------------------------------------------
    # TEST 4
    # Quantity must be greater than zero.
    # -----------------------------------------------------

    ok, message = create_purchase_order(
        supplier_id=supplier_id,
        items=[
            {
                "book_id": test_book_id,
                "title": test_book_title,
                "quantity": 0,
            }
        ],
        created_by="testadmin",
    )

    report(
        not ok
        and message
        == "Book quantity must be greater than zero.",
        "Zero book quantity is rejected.",
    )


    # -----------------------------------------------------
    # TEST 5
    # Non-numeric quantities should be rejected.
    # -----------------------------------------------------

    ok, message = create_purchase_order(
        supplier_id=supplier_id,
        items=[
            {
                "book_id": test_book_id,
                "title": test_book_title,
                "quantity": "five",
            }
        ],
        created_by="testadmin",
    )

    report(
        not ok
        and message
        == "Book quantity must be a whole number.",
        "Non-numeric book quantity is rejected.",
    )


    # -----------------------------------------------------
    # TEST 6
    # Create a valid purchase order.
    # -----------------------------------------------------

    before_orders = load_purchase_orders()

    expected_id = (
        max(
            [
                int(
                    order.get(
                        "purchase_order_id",
                        0,
                    )
                    or 0
                )
                for order in before_orders
            ],
            default=0,
        )
        + 1
    )

    ok, purchase_order_id = create_purchase_order(
        supplier_id=supplier_id,
        items=[
            {
                "book_id": test_book_id,
                "title": test_book_title,
                "quantity": 10,
            }
        ],
        created_by="testadmin",
        notes="Temporary automated test order",
    )

    order = (
        find_purchase_order(
            purchase_order_id
        )
        if ok
        else None
    )

    report(
        ok
        and purchase_order_id == expected_id
        and order is not None,
        "Purchase order is saved with the next "
        "purchase_order_id.",
    )


    # -----------------------------------------------------
    # TEST 7
    # Verify supplier information is stored correctly.
    # -----------------------------------------------------

    report(
        order is not None
        and str(order.get("supplier_id"))
        == str(supplier_id)
        and order.get("supplier_name")
        == supplier.get("name"),
        "Purchase order is connected to the "
        "selected supplier.",
    )


    # -----------------------------------------------------
    # TEST 8
    # Verify purchase order contents.
    # -----------------------------------------------------

    report(
        order is not None
        and order.get("status") == "Pending"
        and order.get("created_by") == "testadmin"
        and len(order.get("items", [])) == 1
        and order["items"][0]["quantity"] == 10
        and order.get(
            "inventory_received"
        ) is False,
        "Purchase order stores status, employee, "
        "book quantity, and receiving state.",
    )


    # -----------------------------------------------------
    # TEST 9
    # Update purchase order status to Ordered.
    # Inventory should NOT change yet.
    # -----------------------------------------------------

    original_quantity = int(
        test_book.get("quantity") or 0
    )

    status_ok, status_message = (
        update_purchase_order_status(
            purchase_order_id,
            "Ordered",
        )
    )

    updated_order = find_purchase_order(
        purchase_order_id
    )

    books_after_ordered = load_books()

    ordered_book = next(
        (
            book
            for book in books_after_ordered
            if str(book.get("book_id"))
            == str(test_book_id)
        ),
        None,
    )

    report(
        status_ok
        and updated_order is not None
        and updated_order.get("status")
        == "Ordered",
        "Purchase order status can be updated.",
    )

    report(
        ordered_book is not None
        and int(
            ordered_book.get("quantity") or 0
        )
        == original_quantity,
        "Ordered status does not change inventory.",
    )


    # -----------------------------------------------------
    # TEST 10
    # Invalid statuses should be rejected.
    # -----------------------------------------------------

    status_ok, status_message = (
        update_purchase_order_status(
            purchase_order_id,
            "Bananas",
        )
    )

    report(
        not status_ok
        and status_message
        == "Invalid purchase order status.",
        "Invalid purchase order status is rejected.",
    )


    # -----------------------------------------------------
    # TEST 11
    # Receiving a purchase order should add its quantity
    # to the matching book in inventory.
    # -----------------------------------------------------

    receive_ok, receive_message = (
        update_purchase_order_status(
            purchase_order_id,
            "Received",
        )
    )

    received_order = find_purchase_order(
        purchase_order_id
    )

    books_after_received = load_books()

    received_book = next(
        (
            book
            for book in books_after_received
            if str(book.get("book_id"))
            == str(test_book_id)
        ),
        None,
    )

    expected_quantity = (
        original_quantity + 10
    )

    report(
        receive_ok
        and received_book is not None
        and int(
            received_book.get("quantity") or 0
        )
        == expected_quantity,
        "Received purchase order adds ordered "
        "quantity to inventory.",
    )

    report(
        received_order is not None
        and received_order.get("status")
        == "Received"
        and received_order.get(
            "inventory_received"
        ) is True,
        "Received purchase order is marked as "
        "applied to inventory.",
    )


    # -----------------------------------------------------
    # TEST 12
    # Changing away from Received and back to Received
    # must NOT add the quantity a second time.
    # -----------------------------------------------------

    update_purchase_order_status(
        purchase_order_id,
        "Ordered",
    )

    second_receive_ok, second_receive_message = (
        update_purchase_order_status(
            purchase_order_id,
            "Received",
        )
    )

    books_after_second_receive = load_books()

    duplicate_check_book = next(
        (
            book
            for book in books_after_second_receive
            if str(book.get("book_id"))
            == str(test_book_id)
        ),
        None,
    )

    report(
        second_receive_ok
        and duplicate_check_book is not None
        and int(
            duplicate_check_book.get(
                "quantity"
            ) or 0
        )
        == expected_quantity,
        "Purchase order cannot add inventory "
        "more than once.",
    )
    # -----------------------------------------------------
    # TEST 13
    # A received purchase order can be closed.
    # Closing the order should NOT change inventory.
    # -----------------------------------------------------

    quantity_before_close = int(
        duplicate_check_book.get("quantity") or 0
    )

    close_ok, close_message = (
        update_purchase_order_status(
            purchase_order_id,
            "Closed",
        )
    )

    closed_order = find_purchase_order(
        purchase_order_id
    )

    books_after_close = load_books()

    closed_book = next(
        (
            book
            for book in books_after_close
            if str(book.get("book_id"))
            == str(test_book_id)
        ),
        None,
    )

    report(
        close_ok
        and closed_order is not None
        and closed_order.get("status")
        == "Closed",
        "Received purchase order can be closed.",
    )

    report(
        closed_book is not None
        and int(
            closed_book.get("quantity") or 0
        )
        == quantity_before_close,
        "Closing a purchase order does not "
        "change inventory.",
    )


    # -----------------------------------------------------
    # TEST 14
    # A closed purchase order is final.
    # Attempts to change its status must be rejected.
    # -----------------------------------------------------

    locked_ok, locked_message = (
        update_purchase_order_status(
            purchase_order_id,
            "Ordered",
        )
    )

    locked_order = find_purchase_order(
        purchase_order_id
    )

    report(
        not locked_ok
        and locked_order is not None
        and locked_order.get("status")
        == "Closed",
        "Closed purchase order cannot be modified.",
    )

    report(
        locked_message
        == "This purchase order is closed "
        "and cannot be changed.",
        "Closed purchase order returns the "
        "correct lock message.",
    )

finally:

    # -----------------------------------------------------
    # Always restore both original JSON files.
    #
    # This prevents automated testing from permanently
    # changing purchase orders or bookstore inventory.
    # -----------------------------------------------------

    save_purchase_orders(
        purchase_order_snapshot
    )

    save_books(
        book_snapshot
    )


# ---------------------------------------------------------
# TEST 15
# Confirm purchase_orders.json was restored.
# ---------------------------------------------------------

restored_orders = load_purchase_orders()

report(
    restored_orders
    == purchase_order_snapshot,
    "purchase_orders.json restored after tests.",
)


# ---------------------------------------------------------
# TEST 16
# Confirm books.json was restored.
# ---------------------------------------------------------

restored_books = load_books()

report(
    restored_books
    == book_snapshot,
    "books.json restored after tests.",
)


# ---------------------------------------------------------
# Final result
# ---------------------------------------------------------

if failed:
    print(
        "\nOne or more T2-004 purchase order "
        "tests failed."
    )
else:
    print(
        "\nT2-004 purchase order tests passed."
    )