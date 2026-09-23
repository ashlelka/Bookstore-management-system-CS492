"""
Bookstore Management System
Inventory CRUD Testing

Developer: Ashley Lindamood

Description:
Tests the Create, Read, Update, and Delete operations
of the bookstore inventory system.
"""

import os
import json
import inventory


# ---------------------------------------------------------
# TEST SETTINGS
# ---------------------------------------------------------

TEST_FILE = "test_books.json"

# Remember the real inventory file so it can be restored.
ORIGINAL_FILE = inventory.FILE_NAME


# ---------------------------------------------------------
# TEST HELPERS
# ---------------------------------------------------------

def reset_test_inventory():
    """
    Creates a clean temporary inventory file before
    each test and points inventory.py to that file.
    """

    inventory.FILE_NAME = TEST_FILE

    with open(TEST_FILE, "w") as file:
        json.dump([], file)


def cleanup_test_file():
    """
    Deletes the temporary inventory file and restores
    inventory.py to the real inventory file.
    """

    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

    inventory.FILE_NAME = ORIGINAL_FILE


def create_test_book():
    """
    Creates a standard temporary book for tests that
    require an existing inventory record.
    """

    success, book_id = inventory.create_book_record(
        "9780000000001",
        "Inventory Test Book",
        "Test Author",
        "Testing",
        "2026",
        "First",
        "Paperback",
        10.99,
        8,
        "TEST"
    )

    assert success is True
    assert book_id is not None
    assert isinstance(book_id, int)

    return book_id


# ---------------------------------------------------------
# TEST 1: CREATE
# ---------------------------------------------------------

def test_create():
    """
    Tests CREATE functionality.
    """

    reset_test_inventory()

    success, book_id = inventory.create_book_record(
        "9780743273565",
        "The Great Gatsby",
        "F. Scott Fitzgerald",
        "Fiction",
        "1925",
        "First",
        "Paperback",
        10.99,
        5,
        "A1"
    )

    assert success is True
    assert book_id is not None
    assert isinstance(book_id, int)

    book = inventory.find_book_by_id(book_id)

    assert book is not None
    assert book["title"] == "The Great Gatsby"
    assert book["quantity"] == 5

    print("Test 1 - CREATE: PASSED")


# ---------------------------------------------------------
# TEST 2: READ
# ---------------------------------------------------------

def test_read():
    """
    Tests READ functionality.
    """

    reset_test_inventory()

    success, book_id = inventory.create_book_record(
        "9780061120084",
        "To Kill a Mockingbird",
        "Harper Lee",
        "Fiction",
        "1960",
        "First",
        "Paperback",
        12.99,
        5,
        "A2"
    )

    assert success is True

    book = inventory.find_book_by_id(book_id)

    assert book is not None
    assert book["title"] == "To Kill a Mockingbird"
    assert book["author"] == "Harper Lee"

    print("Test 2 - READ: PASSED")


# ---------------------------------------------------------
# TEST 3: UPDATE
# ---------------------------------------------------------

def test_update():
    """
    Tests UPDATE functionality.
    """

    reset_test_inventory()

    book_id = create_test_book()

    success = inventory.update_book_quantity(
        book_id,
        8
    )

    assert success is True

    book = inventory.find_book_by_id(book_id)

    assert book is not None
    assert book["quantity"] == 8

    print("Test 3 - UPDATE: PASSED")


# ---------------------------------------------------------
# TEST 4: INVENTORY UPDATE AFTER SALE
# ---------------------------------------------------------

def test_inventory_update_after_sale():
    """
    Tests T1-007 inventory update after
    a successful sale.
    """

    reset_test_inventory()

    book_id = create_test_book()

    # Simulate a sale of 2 copies.
    sale_items = [
        {
            "book_id": book_id,
            "quantity": 2
        }
    ]

    results = inventory.decrement_quantities(
        sale_items
    )

    assert results[0]["success"] is True
    assert results[0]["remaining_quantity"] == 6

    # Reload the book and verify that the
    # updated quantity was saved.
    book = inventory.find_book_by_id(book_id)

    assert book is not None
    assert book["quantity"] == 6

    print(
        "Test 4 - INVENTORY UPDATE "
        "AFTER SALE: PASSED"
    )


# ---------------------------------------------------------
# TEST 5: DELETE
# ---------------------------------------------------------

def test_delete():
    """
    Tests DELETE functionality.
    """

    reset_test_inventory()

    book_id = create_test_book()

    success = inventory.delete_book_by_id(
        book_id
    )

    assert success is True

    book = inventory.find_book_by_id(book_id)

    assert book is None

    print("Test 5 - DELETE: PASSED")


# ---------------------------------------------------------
# TEST 6: NEGATIVE QUANTITY
# ---------------------------------------------------------

def test_negative_quantity():
    """
    Makes sure negative inventory is rejected.
    """

    reset_test_inventory()

    success, message = inventory.create_book_record(
        "1111111111111",
        "Invalid Test Book",
        "Test Author",
        "Testing",
        "2026",
        "First",
        "Paperback",
        10.00,
        -5,
        "TEST"
    )

    assert success is False

    print(
        "Test 6 - NEGATIVE QUANTITY: PASSED"
    )


# ---------------------------------------------------------
# RUN TESTS DIRECTLY
# ---------------------------------------------------------

if __name__ == "__main__":

    try:

        test_create()
        test_read()
        test_update()
        test_inventory_update_after_sale()
        test_delete()
        test_negative_quantity()

        print(
            "\nAll Inventory tests PASSED."
        )

    finally:

        cleanup_test_file()