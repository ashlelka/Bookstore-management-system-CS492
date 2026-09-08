"""
Bookstore Management System
Sprint 1 - T1-003
Developer: Ashley Lindamood

Description:
This module defines the Book class used by the bookstore
inventory system. Each Book object represents one inventory
record and can be converted to a dictionary for JSON storage.
"""


class Book:
    """
    Represents a book stored in the bookstore inventory.
    """

    def __init__(
        self,
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
    ):
        # Unique inventory identifier.
        self.book_id = book_id

        # Standard book identification number.
        self.isbn = isbn

        # Basic book information.
        self.title = title
        self.author = author
        self.category = category
        self.publication_year = publication_year
        self.edition = edition
        self.format = book_format

        # Inventory and sales-related information.
        self.price = price
        self.quantity = quantity

        # Physical bookstore location.
        self.location = location


    def to_dict(self):
        """
        Converts the Book object into a dictionary.

        The dictionary can then be saved in books.json.
        """

        return {
            "book_id": self.book_id,
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "publication_year": self.publication_year,
            "edition": self.edition,
            "format": self.format,
            "price": self.price,
            "quantity": self.quantity,
            "location": self.location
        }


    def __str__(self):
        """
        Returns a readable description of the book.
        """

        return (
            f"{self.book_id} | "
            f"{self.title} | "
            f"{self.author} | "
            f"Qty: {self.quantity}"
        )