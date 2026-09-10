from inventory import (
    find_book_by_id,
    decrement_quantities,
    update_book_quantity
)


print("\n--- POS / INVENTORY INTEGRATION TESTS ---")


# ---------------------------------------------------------
# TEST 1: Find book before sale
# ---------------------------------------------------------

book_id = 1

book = find_book_by_id(book_id)

if book is not None:
    print("PASS: Book found before POS sale.")
else:
    print("FAIL: Book not found.")


# ---------------------------------------------------------
# TEST 2: Save original quantity
# ---------------------------------------------------------

if book is not None:

    original_quantity = book["quantity"]

    print(
        f"Original quantity for book {book_id}: "
        f"{original_quantity}"
    )


# ---------------------------------------------------------
# TEST 3: Simulate Alexis POS sale format
# ---------------------------------------------------------

sale_items = [
    {
        "productId": book_id,
        "qty": 1
    }
]


if book is not None and original_quantity > 0:

    decrement_quantities(sale_items)

    print("POS sale sent to inventory system.")


# ---------------------------------------------------------
# TEST 4: Verify quantity decreased
# ---------------------------------------------------------

updated_book = find_book_by_id(book_id)

if (
    updated_book is not None
    and updated_book["quantity"] == original_quantity - 1
):
    print(
        "PASS: POS sale correctly decreased inventory."
    )
else:
    print(
        "FAIL: POS sale did not decrease inventory."
    )


print("\n--- POS / INVENTORY TESTING COMPLETE ---")
# ---------------------------------------------------------
# TEST 5: Restore original inventory quantity
# ---------------------------------------------------------

update_book_quantity(
    book_id,
    original_quantity
)

restored_book = find_book_by_id(book_id)

if (
    restored_book is not None
    and restored_book["quantity"] == original_quantity
):
    print("PASS: Original inventory quantity restored.")
else:
    print("FAIL: Inventory quantity was not restored.")