"""
Bookstore Management System
Sprint 1 - T1-003 / T1-004
Developer: Ashley Lindamood

Description:
This module provides complete CRUD functionality for the
Bookstore Management System inventory.

CRUD Operations:
Create - Add a new book
Read   - View and search books
Update - Edit an existing book
Delete - Remove a book

T1-004 Low Stock Alerts:
- Reorder threshold stored for each book
- Low-stock and out-of-stock status logic
- Low-stock notification generation
- Automatic alert check after POS inventory updates

Book information is stored in a JSON file named books.json.
"""

import json
import os
from book import Book

# JSON file used as the bookstore inventory database.
FILE_NAME = "books.json"

# Default reorder level used for older inventory records that
# do not already contain a reorder_threshold field.
DEFAULT_REORDER_THRESHOLD = 5


def load_books():
    """
    Reads inventory records from books.json.

    Returns:
        list: A list containing all book records.
    """

    # If the JSON file does not exist yet, return an empty inventory.
    if not os.path.exists(FILE_NAME):
        return []

    try:
        # Open the file and convert JSON data into a Python list.
        with open(FILE_NAME, "r") as file:
            return json.load(file)

    except json.JSONDecodeError:
        # Prevent the application from crashing if the JSON
        # file contains invalid or incomplete data.
        print("Warning: Inventory file contains invalid JSON.")
        return []


def save_books(books):
    """
    Saves the current inventory list to books.json.
    """

    # Open books.json in write mode and replace its contents
    # with the current inventory.
    with open(FILE_NAME, "w") as file:
        json.dump(books, file, indent=4)


def generate_book_id(books):
    """
    Generates the next available Book ID.

    This method prevents duplicate IDs if a book was previously
    deleted from inventory.
    """

    # If there are no books, the first ID will be 1.
    if not books:
        return 1

    # Find the largest current Book ID and add 1.
    return max(book["book_id"] for book in books) + 1


def isbn_exists(books, isbn, ignore_book_id=None):
    """
    Checks whether an ISBN already exists in inventory.

    Args:
        books: Current inventory list.
        isbn: ISBN being checked.
        ignore_book_id: Used while editing so the current book
                        does not count as a duplicate.

    Returns:
        bool: True if the ISBN already exists.
    """

    for book in books:

        if (
            book["isbn"] == isbn
            and book["book_id"] != ignore_book_id
        ):
            return True

    return False
# ==========================================================
# CRUD HELPER FUNCTIONS
# These functions allow CRUD operations to be tested
# without requiring keyboard input.
# ==========================================================


def create_book_record(
    isbn,
    title,
    author,
    category,
    publication_year,
    edition,
    book_format,
    price,
    quantity,
    location,
    reorder_threshold=DEFAULT_REORDER_THRESHOLD
):
    """
    Creates a new book record and saves it to the JSON file.
    """

    books = load_books()

    # Prevent duplicate ISBN numbers.
    if isbn_exists(books, isbn):
        return False, "Duplicate ISBN."

    # Prevent negative prices.
    if price < 0:
        return False, "Price cannot be negative."

    # Prevent negative inventory quantities.
    if quantity < 0:
        return False, "Quantity cannot be negative."

    # Prevent negative reorder thresholds.
    if reorder_threshold < 0:
        return False, "Reorder threshold cannot be negative."

    # Generate a unique Book ID.
    book_id = generate_book_id(books)

    # Create the Book object.
    new_book = Book(
        book_id,
        isbn,
        title,
        author,
        category,
        publication_year,
        edition,
        book_format,
        price,
        quantity,
        location
    )

    # Convert the Book object to a dictionary.
    # The reorder threshold is stored directly in the inventory
    # record so the existing Book class does not need to change.
    new_book_record = new_book.to_dict()
    new_book_record["reorder_threshold"] = reorder_threshold
    books.append(new_book_record)

    # Save the inventory.
    save_books(books)

    return True, book_id


def find_book_by_id(book_id):
    """
    Finds a book using its Book ID.
    """

    books = load_books()

    for book in books:
        if book["book_id"] == book_id:
            return book

    return None


def update_book_quantity(book_id, new_quantity):
    """
    Updates the quantity of an existing book.
    """

    # Inventory cannot be negative.
    if new_quantity < 0:
        return False

    books = load_books()

    for book in books:
        if book["book_id"] == book_id:

            book["quantity"] = new_quantity

            save_books(books)

            return True

    return False



# ==========================================================
# T1-004 LOW STOCK ALERT HELPERS
# ==========================================================

def get_reorder_threshold(book):
    """
    Returns the reorder threshold for a book.

    Older inventory records may not contain the field yet,
    so the default threshold is used when necessary.
    """

    try:
        return int(
            book.get(
                "reorder_threshold",
                DEFAULT_REORDER_THRESHOLD
            )
        )
    except (TypeError, ValueError):
        return DEFAULT_REORDER_THRESHOLD


def get_stock_status(book):
    """
    Returns the current stock status for a book.
    """

    quantity = int(book.get("quantity", 0))
    threshold = get_reorder_threshold(book)

    if quantity == 0:
        return "Out of Stock"

    if quantity <= threshold:
        return "Low Stock"

    return "In Stock"


def get_low_stock_books():
    """
    Returns books that have reached or fallen below
    their reorder threshold.
    """

    books = load_books()
    low_stock_books = []

    for book in books:
        quantity = int(book.get("quantity", 0))
        threshold = get_reorder_threshold(book)

        if quantity <= threshold:
            low_stock_books.append(book)

    return low_stock_books


def display_low_stock_alerts():
    """
    Displays low-stock notifications for inventory items
    that need to be reordered.
    """

    low_stock_books = get_low_stock_books()

    print("\n==============================")
    print("       LOW STOCK ALERTS")
    print("==============================")

    if not low_stock_books:
        print("\nNo books currently require reordering.")
        return []

    for book in low_stock_books:
        threshold = get_reorder_threshold(book)
        status = get_stock_status(book)

        print("--------------------------------")
        print(f"ALERT: {book['title']}")
        print(f"Book ID: {book['book_id']}")
        print(f"Quantity: {book.get('quantity', 0)}")
        print(f"Reorder Threshold: {threshold}")
        print(f"Status: {status}")

    print("--------------------------------")
    print(
        f"{len(low_stock_books)} book(s) "
        "require inventory attention."
    )

    return low_stock_books


def delete_book_by_id(book_id):
    """
    Deletes a book using its Book ID.
    """

    books = load_books()

    for book in books:
        if book["book_id"] == book_id:

            books.remove(book)

            save_books(books)

            return True

    return False
# Decrement book quantities after a sale. 
# This function is used by the sales system to update inventory after books are purchased.
def decrement_quantities(sale_items):
    """
    Decreases book quantities after a successful sale.

    This function is used by the sales system to update
    inventory after books are purchased.

    It also checks the reorder threshold after each
    successful inventory update so T1-004 can generate
    a low-stock notification.

    Args:
        sale_items: List of books and quantities sold.

    Returns:
        list: Results of each inventory update.
    """

    books = load_books()
    results = []

    for sale_item in sale_items:

        # Accept either Ashley's inventory field names
        # or Alexis's POS field names.
        book_id = sale_item.get(
            "book_id",
            sale_item.get("productId")
        )

        quantity_sold = sale_item.get(
            "quantity",
            sale_item.get("qty", 0)
        )

        try:
            book_id = int(book_id)
            quantity_sold = int(quantity_sold)

        except (ValueError, TypeError):
            results.append({
                "book_id": book_id,
                "success": False,
                "message": (
                    "Book ID and quantity must be integers."
                )
            })
            continue

        book_found = False

        for book in books:

            if book["book_id"] == book_id:
                book_found = True

                # Quantity sold must be greater than zero.
                if quantity_sold <= 0:
                    results.append({
                        "book_id": book_id,
                        "success": False,
                        "message": (
                            "Sale quantity must be "
                            "greater than zero."
                        )
                    })
                    break

                # Do not allow inventory to become negative.
                if book["quantity"] < quantity_sold:
                    results.append({
                        "book_id": book_id,
                        "success": False,
                        "message": "Insufficient inventory."
                    })
                    break

                # Subtract the sold quantity.
                book["quantity"] -= quantity_sold

                threshold = get_reorder_threshold(book)
                stock_status = get_stock_status(book)
                low_stock = (
                    book["quantity"] <= threshold
                )

                notification = None

                if low_stock:
                    notification = (
                        f"LOW STOCK ALERT: "
                        f"{book['title']} has "
                        f"{book['quantity']} remaining. "
                        f"Reorder threshold: {threshold}."
                    )

                results.append({
                    "book_id": book_id,
                    "success": True,
                    "message": (
                        "Inventory updated successfully."
                    ),
                    "remaining_quantity": book["quantity"],
                    "reorder_threshold": threshold,
                    "stock_status": stock_status,
                    "low_stock": low_stock,
                    "notification": notification
                })

                break

        if not book_found:
            results.append({
                "book_id": book_id,
                "success": False,
                "message": "Book not found."
            })

    # Save inventory changes.
    save_books(books)

    return results


# --------------------------------------------------
# CREATE
# --------------------------------------------------

def add_book():
    """
    Adds a new book to bookstore inventory.
    """

    books = load_books()

    print("\n==============================")
    print("       ADD INVENTORY")
    print("==============================")

    # Generate a unique ID for the new inventory record.
    book_id = generate_book_id(books)

    title = input("Enter book title: ").strip()
    author = input("Enter author: ").strip()
    isbn = input("Enter ISBN: ").strip()
    category = input("Enter category: ").strip()
    publication_year = input(
        "Enter publication year: "
    ).strip()

    edition = input("Enter edition: ").strip()
    book_format = input("Enter format: ").strip()
    location = input("Enter store location: ").strip()

    # Make sure required text fields are not empty.
    if not title or not author or not isbn:
        print(
            "\nTitle, author, and ISBN are required."
        )
        return

    # Prevent duplicate ISBN values.
    if isbn_exists(books, isbn):
        print(
            "\nA book with this ISBN already exists."
        )
        return

    # Validate price.
    try:
        price = float(
            input("Enter price: $")
        )

        if price < 0:
            print(
                "\nPrice cannot be negative."
            )
            return

    except ValueError:
        print(
            "\nPrice must be a valid number."
        )
        return

    # Validate quantity.
    try:
        quantity = int(
            input("Enter quantity: ")
        )

        if quantity < 0:
            print(
                "\nQuantity cannot be negative."
            )
            return

    except ValueError:
        print(
            "\nQuantity must be a whole number."
        )
        return

    # Validate reorder threshold.
    try:
        reorder_threshold_entry = input(
            f"Enter reorder threshold "
            f"[{DEFAULT_REORDER_THRESHOLD}]: "
        ).strip()

        if reorder_threshold_entry:
            reorder_threshold = int(
                reorder_threshold_entry
            )
        else:
            reorder_threshold = (
                DEFAULT_REORDER_THRESHOLD
            )

        if reorder_threshold < 0:
            print(
                "\nReorder threshold cannot be negative."
            )
            return

    except ValueError:
        print(
            "\nReorder threshold must be a whole number."
        )
        return

    # Create a Book object using the information entered by the user.
    new_book = Book(
        book_id,
        isbn,
        title,
        author,
        category,
        publication_year,
        edition,
        book_format,
        price,
        quantity,
        location
)

# Convert the Book object to a dictionary before saving it to JSON.
    new_book_record = new_book.to_dict()
    new_book_record["reorder_threshold"] = (
        reorder_threshold
    )
    books.append(new_book_record)

    # Save the updated list to JSON.
    save_books(books)

    print(
        f"\nBook added successfully."
        f" Book ID: {book_id}"
    )


# --------------------------------------------------
# READ
# --------------------------------------------------

def view_inventory():
    """
    Displays every book currently stored in inventory.
    """

    books = load_books()

    print("\n================================")
    print("       BOOKSTORE INVENTORY")
    print("================================")

    if not books:
        print("\nInventory is empty.")
        return

    # Display each book in an easy-to-read format.
    for book in books:

        print("--------------------------------")
        print(
            f"Book ID: {book['book_id']}"
        )
        print(
            f"ISBN: {book['isbn']}"
        )
        print(
            f"Title: {book['title']}"
        )
        print(
            f"Author: {book['author']}"
        )
        print(
            f"Category: {book['category']}"
        )
        print(
            f"Year: {book['publication_year']}"
        )
        print(
            f"Edition: {book['edition']}"
        )
        print(
            f"Format: {book['format']}"
        )
        print(
            f"Price: ${book['price']:.2f}"
        )
        print(
            f"Quantity: {book['quantity']}"
        )
        print(
            f"Reorder Threshold: "
            f"{get_reorder_threshold(book)}"
        )
        print(
            f"Stock Status: {get_stock_status(book)}"
        )
        print(
            f"Location: {book['location']}"
        )

    print("--------------------------------")


def search_book():
    """
    Searches inventory by Book ID, ISBN, title,
    author, or category.
    """

    books = load_books()

    if not books:
        print("\nInventory is empty.")
        return

    print("\n==============================")
    print("       SEARCH INVENTORY")
    print("==============================")

    search_term = input(
        "Enter ID, ISBN, title, author, or category: "
    ).strip().lower()

    results = []

    # Check multiple inventory fields for a match.
    for book in books:

        if (
            search_term == str(
                book["book_id"]
            ).lower()
            or search_term in
            book["isbn"].lower()
            or search_term in
            book["title"].lower()
            or search_term in
            book["author"].lower()
            or search_term in
            book["category"].lower()
        ):
            results.append(book)

    if not results:
        print(
            "\nNo matching books found."
        )
        return

    print("\n--- SEARCH RESULTS ---")

    for book in results:

        print("--------------------------------")
        print(
            f"Book ID: {book['book_id']}"
        )
        print(
            f"Title: {book['title']}"
        )
        print(
            f"Author: {book['author']}"
        )
        print(
            f"ISBN: {book['isbn']}"
        )
        print(
            f"Category: {book['category']}"
        )
        print(
            f"Price: ${book['price']:.2f}"
        )
        print(
            f"Quantity: {book['quantity']}"
        )
        print(
            f"Reorder Threshold: "
            f"{get_reorder_threshold(book)}"
        )
        print(
            f"Stock Status: {get_stock_status(book)}"
        )
        print(
            f"Location: {book['location']}"
        )


# --------------------------------------------------
# UPDATE
# --------------------------------------------------

def edit_book():
    """
    Updates an existing book using its Book ID.
    """

    books = load_books()

    if not books:
        print("\nInventory is empty.")
        return

    print("\n==============================")
    print("        EDIT INVENTORY")
    print("==============================")

    try:
        book_id = int(
            input("Enter Book ID to edit: ")
        )

    except ValueError:
        print(
            "\nBook ID must be a number."
        )
        return

    # Search for the selected book.
    for book in books:

        if book["book_id"] == book_id:

            print(
                "\nLeave a field blank to keep "
                "the current value."
            )

            title = input(
                f"Title [{book['title']}]: "
            ).strip()

            author = input(
                f"Author [{book['author']}]: "
            ).strip()

            isbn = input(
                f"ISBN [{book['isbn']}]: "
            ).strip()

            category = input(
                f"Category [{book['category']}]: "
            ).strip()

            publication_year = input(
                f"Publication Year "
                f"[{book['publication_year']}]: "
            ).strip()

            edition = input(
                f"Edition [{book['edition']}]: "
            ).strip()

            book_format = input(
                f"Format [{book['format']}]: "
            ).strip()

            price = input(
                f"Price [{book['price']}]: "
            ).strip()

            quantity = input(
                f"Quantity [{book['quantity']}]: "
            ).strip()

            current_threshold = get_reorder_threshold(
                book
            )

            reorder_threshold = input(
                f"Reorder Threshold "
                f"[{current_threshold}]: "
            ).strip()

            location = input(
                f"Location [{book['location']}]: "
            ).strip()

            # Update text fields only when new data
            # has been provided.
            if title:
                book["title"] = title

            if author:
                book["author"] = author

            if isbn:

                # Make sure another book does not
                # already use this ISBN.
                if isbn_exists(
                    books,
                    isbn,
                    book_id
                ):
                    print(
                        "\nAnother book already "
                        "uses this ISBN."
                    )
                    return

                book["isbn"] = isbn

            if category:
                book["category"] = category

            if publication_year:
                book[
                    "publication_year"
                ] = publication_year

            if edition:
                book["edition"] = edition

            if book_format:
                book["format"] = book_format

            # Validate the new price if one was entered.
            if price:

                try:
                    new_price = float(price)

                    if new_price < 0:
                        print(
                            "\nPrice cannot be negative."
                        )
                        return

                    book["price"] = new_price

                except ValueError:
                    print(
                        "\nPrice must be numeric."
                    )
                    return

            # Validate the new quantity.
            if quantity:

                try:
                    new_quantity = int(
                        quantity
                    )

                    if new_quantity < 0:
                        print(
                            "\nQuantity cannot "
                            "be negative."
                        )
                        return

                    book[
                        "quantity"
                    ] = new_quantity

                except ValueError:
                    print(
                        "\nQuantity must be a "
                        "whole number."
                    )
                    return

            # Validate the new reorder threshold.
            if reorder_threshold:

                try:
                    new_threshold = int(
                        reorder_threshold
                    )

                    if new_threshold < 0:
                        print(
                            "\nReorder threshold cannot "
                            "be negative."
                        )
                        return

                    book[
                        "reorder_threshold"
                    ] = new_threshold

                except ValueError:
                    print(
                        "\nReorder threshold must be a "
                        "whole number."
                    )
                    return

            elif "reorder_threshold" not in book:
                # Add the default to older records when
                # they are edited for the first time.
                book["reorder_threshold"] = (
                    DEFAULT_REORDER_THRESHOLD
                )

            if location:
                book["location"] = location

            # Save all updates to the JSON file.
            save_books(books)

            print(
                "\nBook updated successfully."
            )
            return

    print(
        "\nBook ID not found."
    )


# --------------------------------------------------
# DELETE
# --------------------------------------------------

def remove_book():
    """
    Deletes a book from inventory using its Book ID.
    """

    books = load_books()

    if not books:
        print("\nInventory is empty.")
        return

    print("\n==============================")
    print("       REMOVE INVENTORY")
    print("==============================")

    try:
        book_id = int(
            input("Enter Book ID to remove: ")
        )

    except ValueError:
        print(
            "\nBook ID must be a number."
        )
        return

    # Search for the requested inventory record.
    for book in books:

        if book["book_id"] == book_id:

            print(
                f"\nBook found: "
                f"{book['title']}"
            )

            # Ask for confirmation before permanently
            # deleting inventory data.
            confirm = input(
                "Are you sure you want to remove "
                "this book? (y/n): "
            ).strip().lower()

            if confirm == "y":

                books.remove(book)

                save_books(books)

                print(
                    "\nBook removed successfully."
                )

            else:
                print(
                    "\nRemoval cancelled."
                )

            return

    print(
        "\nBook ID not found."
    )