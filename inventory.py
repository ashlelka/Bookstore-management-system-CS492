"""
Bookstore Management System
Sprint 1 - T1-001
Developer: Ashley Lindamood

Description:
This module manages the bookstore's inventory using a JSON file
as the data storage system. It allows the user to add, view,
search, edit, and remove books from inventory.
"""

# Import json so Python can read and write JSON data.
import json

# Import os so the program can check whether the JSON file exists.
import os


# Name of the JSON file used to store bookstore inventory.
FILE_NAME = "books.json"


def load_books():
    """
    Loads all book records from the JSON inventory file.
    Returns an empty list if the file does not exist or
    contains invalid JSON data.
    """

    # Check whether the inventory file already exists.
    if not os.path.exists(FILE_NAME):
        return []

    try:
        # Open the JSON file in read mode.
        with open(FILE_NAME, "r") as file:
            return json.load(file)

    except json.JSONDecodeError:
        # Prevent the program from crashing if the JSON file is empty
        # or contains incorrectly formatted JSON.
        return []


def save_books(books):
    """
    Saves the current list of books to the JSON inventory file.
    """

    # Open the JSON file in write mode.
    with open(FILE_NAME, "w") as file:

        # indent=4 makes the JSON file easier for humans to read.
        json.dump(books, file, indent=4)


def add_book():
    """
    Collects information about a new book and adds it
    to the bookstore inventory.
    """

    # Load the current inventory before adding another book.
    books = load_books()

    # Generate a simple unique ID for the new book.
    # The first book receives ID 1.
    book_id = len(books) + 1

    print("\n--- ADD NEW BOOK ---")

    # Collect book information from the user.
    title = input("Enter book title: ")
    author = input("Enter author: ")
    isbn = input("Enter ISBN: ")
    category = input("Enter category: ")
    publication_year = input("Enter publication year: ")
    edition = input("Enter edition: ")
    book_format = input("Enter format: ")

    # Price must be a decimal number and quantity must be an integer.
    try:
        price = float(input("Enter price: $"))
        quantity = int(input("Enter quantity: "))

    except ValueError:
        print("Price and quantity must be numeric.")
        return

    # A bookstore item cannot have a negative price.
    if price < 0:
        print("Price cannot be negative.")
        return

    # Inventory is not allowed to contain a negative quantity.
    if quantity < 0:
        print("Quantity cannot be negative.")
        return

    # Store location helps employees locate the physical book.
    location = input("Enter store location: ")

    # Create a dictionary containing all information about the book.
    new_book = {
        "book_id": book_id,
        "isbn": isbn,
        "title": title,
        "author": author,
        "category": category,
        "publication_year": publication_year,
        "edition": edition,
        "format": book_format,
        "price": price,
        "quantity": quantity,
        "location": location
    }

    # Add the new book dictionary to the inventory list.
    books.append(new_book)

    # Save the updated inventory to books.json.
    save_books(books)

    print("\nBook added successfully.")


def view_inventory():
    """
    Displays all books currently stored in the inventory.
    """

    # Load inventory information from the JSON file.
    books = load_books()

    # Check whether there are any books to display.
    if not books:
        print("\nInventory is empty.")
        return

    print("\n--- BOOKSTORE INVENTORY ---")

    # Loop through each book and display its information.
    for book in books:

        print(f"\nBook ID: {book['book_id']}")
        print(f"Title: {book['title']}")
        print(f"Author: {book['author']}")
        print(f"ISBN: {book['isbn']}")
        print(f"Category: {book['category']}")
        print(f"Year: {book['publication_year']}")
        print(f"Edition: {book['edition']}")
        print(f"Format: {book['format']}")
        print(f"Price: ${book['price']:.2f}")
        print(f"Quantity: {book['quantity']}")
        print(f"Location: {book['location']}")


def search_book():
    """
    Searches inventory using a title, author, or ISBN.
    """

    # Load all books from the JSON inventory.
    books = load_books()

    print("\n--- SEARCH INVENTORY ---")

    # Convert the search value to lowercase so the search
    # is not affected by capitalization.
    search_term = input(
        "Enter title, author, or ISBN to search: "
    ).lower()

    # Create an empty list to hold matching books.
    results = []

    # Check each book for the user's search value.
    for book in books:

        if (
            search_term in book["title"].lower()
            or search_term in book["author"].lower()
            or search_term in book["isbn"].lower()
        ):
            results.append(book)

    # Tell the user if no matching book was found.
    if not results:
        print("\nNo matching books found.")
        return

    print("\n--- SEARCH RESULTS ---")

    # Display all books that matched the search.
    for book in results:

        print(
            f"{book['book_id']} | "
            f"{book['title']} | "
            f"{book['author']} | "
            f"Qty: {book['quantity']}"
        )


def edit_book():
    """
    Allows an existing inventory record to be updated
    using its Book ID.
    """

    # Load the existing inventory.
    books = load_books()

    print("\n--- EDIT BOOK ---")

    # Validate that the entered Book ID is a number.
    try:
        book_id = int(input("Enter Book ID to edit: "))

    except ValueError:
        print("Book ID must be a number.")
        return

    # Search the inventory for the requested Book ID.
    for book in books:

        if book["book_id"] == book_id:

            print("\nLeave a field blank to keep the current value.")

            # Display the current values while requesting new values.
            title = input(
                f"Title [{book['title']}]: "
            )

            author = input(
                f"Author [{book['author']}]: "
            )

            category = input(
                f"Category [{book['category']}]: "
            )

            quantity = input(
                f"Quantity [{book['quantity']}]: "
            )

            # Only update a value if the user entered something.
            if title:
                book["title"] = title

            if author:
                book["author"] = author

            if category:
                book["category"] = category

            if quantity:

                try:
                    new_quantity = int(quantity)

                    # Prevent inventory from becoming negative.
                    if new_quantity < 0:
                        print("Quantity cannot be negative.")
                        return

                    book["quantity"] = new_quantity

                except ValueError:
                    print("Quantity must be a number.")
                    return

            # Save the updated inventory back to the JSON file.
            save_books(books)

            print("\nBook updated successfully.")
            return

    # This message appears if no matching Book ID was found.
    print("\nBook not found.")


def remove_book():
    """
    Removes a book from inventory using its Book ID.
    """

    # Load the current inventory.
    books = load_books()

    print("\n--- REMOVE BOOK ---")

    # Validate the Book ID entered by the user.
    try:
        book_id = int(
            input("Enter Book ID to remove: ")
        )

    except ValueError:
        print("Book ID must be a number.")
        return

    # Search for the matching book.
    for book in books:

        if book["book_id"] == book_id:

            # Remove the book from the list.
            books.remove(book)

            # Save the updated list to the JSON file.
            save_books(books)

            print(
                f"\n{book['title']} removed successfully."
            )
            return

    # Display an error if the requested ID does not exist.
    print("\nBook not found.")