"""
Bookstore Management System
Sprint 1 - T1-003
Developer: Ashley Lindamood

Description:
This module provides complete CRUD functionality for the
Bookstore Management System inventory.

CRUD Operations:
Create - Add a new book
Read   - View and search books
Update - Edit an existing book
Delete - Remove a book

Book information is stored in a JSON file named books.json.
"""

import json
import os
from book import Book

# JSON file used as the bookstore inventory database.
FILE_NAME = "books.json"


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
    location
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
    books.append(new_book.to_dict())

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

    Args:
        sale_items: List of books and quantities sold.

    Returns:
        list: Results of each inventory update.
    """

    books = load_books()
    results = []

    for sale_item in sale_items:

        book_id = sale_item.get("book_id")
        quantity_sold = sale_item.get("quantity", 0)

        book_found = False

        for book in books:

            if book["book_id"] == book_id:
                book_found = True

                # Quantity sold must be greater than zero.
                if quantity_sold <= 0:
                    results.append({
                        "book_id": book_id,
                        "success": False,
                        "message": "Sale quantity must be greater than zero."
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

                results.append({
                    "book_id": book_id,
                    "success": True,
                    "message": "Inventory updated successfully.",
                    "remaining_quantity": book["quantity"]
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
    books.append(new_book.to_dict())

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