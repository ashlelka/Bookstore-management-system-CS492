"""
Bookstore Management System
Sprint 1 - T1-004 Low Stock Alerts
Developer: Ashley Lindamood

Description:
This test verifies the low-stock alert functionality for the
Bookstore Management System. It checks reorder-threshold logic,
stock-status reporting, low-stock notifications, POS inventory
updates, and restoration of the original inventory quantity.
"""

from inventory import (
    find_book_by_id,
    update_book_quantity,
    get_reorder_threshold,
    get_stock_status,
    get_low_stock_books,
    decrement_quantities
)


BOOK_ID = 1


def print_result(condition, pass_message, fail_message):
    """
    Prints a consistent PASS or FAIL message.
    """
    if condition:
        print(f"PASS: {pass_message}")
        return True

    print(f"FAIL: {fail_message}")
    return False


def main():
    print("\n--- LOW STOCK ALERT TESTS ---")

    # -------------------------------------------------
    # TEST 1: Locate a book in inventory
    # -------------------------------------------------

    book = find_book_by_id(BOOK_ID)

    if not print_result(
        book is not None,
        "Test book found in inventory.",
        "Test book was not found in inventory."
    ):
        return

    original_quantity = book["quantity"]
    threshold = get_reorder_threshold(book)

    print(f"Original quantity: {original_quantity}")
    print(f"Reorder threshold: {threshold}")

    try:
        # -------------------------------------------------
        # TEST 2: Quantity above threshold
        # -------------------------------------------------

        update_book_quantity(
            BOOK_ID,
            threshold + 2
        )

        book = find_book_by_id(BOOK_ID)

        print_result(
            get_stock_status(book) == "In Stock",
            "Book above the reorder threshold is marked In Stock.",
            "Book above the reorder threshold was not marked In Stock."
        )

        # -------------------------------------------------
        # TEST 3: Quantity at threshold
        # -------------------------------------------------

        update_book_quantity(
            BOOK_ID,
            threshold
        )

        book = find_book_by_id(BOOK_ID)

        print_result(
            get_stock_status(book) == "Low Stock",
            "Book at the reorder threshold is marked Low Stock.",
            "Book at the reorder threshold was not marked Low Stock."
        )

        # -------------------------------------------------
        # TEST 4: Low-stock notification list
        # -------------------------------------------------

        low_stock_books = get_low_stock_books()

        alert_found = any(
            alert["book_id"] == BOOK_ID
            for alert in low_stock_books
        )

        print_result(
            alert_found,
            "Book appears in the low-stock notification list.",
            "Book did not appear in the low-stock notification list."
        )

        # -------------------------------------------------
        # TEST 5: Out-of-stock status
        # -------------------------------------------------

        update_book_quantity(
            BOOK_ID,
            0
        )

        book = find_book_by_id(BOOK_ID)

        print_result(
            get_stock_status(book) == "Out of Stock",
            "Zero quantity is marked Out of Stock.",
            "Zero quantity was not marked Out of Stock."
        )

        # -------------------------------------------------
        # TEST 6: POS sale triggers low-stock alert data
        # -------------------------------------------------

        update_book_quantity(
            BOOK_ID,
            threshold + 1
        )

        sale_items = [
            {
                "productId": str(BOOK_ID),
                "qty": 1
            }
        ]

        results = decrement_quantities(
            sale_items
        )

        sale_result = results[0]

        print_result(
            sale_result.get("success") is True,
            "POS-style sale successfully updated inventory.",
            "POS-style sale did not update inventory."
        )

        print_result(
            sale_result.get("remaining_quantity") == threshold,
            "POS sale reduced inventory to the reorder threshold.",
            "POS sale did not reduce inventory to the expected quantity."
        )

        print_result(
            sale_result.get("low_stock") is True,
            "POS sale triggered the low-stock alert flag.",
            "POS sale did not trigger the low-stock alert flag."
        )

        print_result(
            sale_result.get("stock_status") == "Low Stock",
            "POS sale returned Low Stock status.",
            "POS sale did not return Low Stock status."
        )

        notification = sale_result.get(
            "notification"
        )

        print_result(
            notification is not None
            and "LOW STOCK ALERT" in notification,
            "Low-stock notification was generated after the sale.",
            "Low-stock notification was not generated after the sale."
        )

    finally:
        # -------------------------------------------------
        # RESTORE ORIGINAL INVENTORY
        # -------------------------------------------------

        update_book_quantity(
            BOOK_ID,
            original_quantity
        )

        restored_book = find_book_by_id(
            BOOK_ID
        )

        print_result(
            restored_book["quantity"] == original_quantity,
            "Original inventory quantity restored.",
            "Original inventory quantity was not restored."
        )

    print(
        "\n--- LOW STOCK ALERT "
        "TESTING COMPLETE ---"
    )


if __name__ == "__main__":
    main()
