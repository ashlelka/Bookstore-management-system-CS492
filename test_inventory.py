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


# Use a separate JSON file during testing.
TEST_FILE = "test_books.json"


def setup_test_file():
    """
    Creates an empty test inventory file.
    """

    with open(TEST_FILE, "w") as file:
        json.dump([], file)


def cleanup_test_file():
    """
    Deletes the temporary test inventory file.
    """

    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)


def test_create():
    """
    Tests CREATE functionality.
    """

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
    assert book_id == 1

    print("Test 1 - CREATE: PASSED")


def test_read():
    """
    Tests READ functionality.
    """

    book = inventory.find_book_by_id(1)

    assert book is not None
    assert book["title"] == "The Great Gatsby"
    assert book["quantity"] == 5

    print("Test 2 - READ: PASSED")


def test_update():
    """
    Tests UPDATE functionality.
    """

    success = inventory.update_book_quantity(1, 8)

    assert success is True

    book = inventory.find_book_by_id(1)

    assert book["quantity"] == 8

    print("Test 3 - UPDATE: PASSED")


def test_delete():
    """
    Tests DELETE functionality.
    """

    success = inventory.delete_book_by_id(1)

    assert success is True

    book = inventory.find_book_by_id(1)

    assert book is None

    print("Test 4 - DELETE: PASSED")


def test_negative_quantity():
    """
    Makes sure negative inventory is rejected.
    """

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

    print("Test 5 - NEGATIVE QUANTITY: PASSED")


if __name__ == "__main__":

    # Remember the real inventory filename.
    original_file = inventory.FILE_NAME

    # Temporarily use our test JSON file.
    inventory.FILE_NAME = TEST_FILE

    try:
        setup_test_file()

        test_create()
        test_read()
        test_update()
        test_delete()
        test_negative_quantity()

        print("\nAll Inventory CRUD tests PASSED.")

    finally:

        # Delete the temporary testing file.
        cleanup_test_file()

        # Restore the real inventory filename.
        inventory.FILE_NAME = original_file