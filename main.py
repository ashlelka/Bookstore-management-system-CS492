"""
Bookstore Management System
Sprint 1 - T1-001
Developer: Ashley Lindamood

Description:
This is the main program for the Bookstore Management System.
It provides a menu that allows bookstore employees to manage
inventory stored in the books.json file.
"""

# Import the inventory functions from inventory.py.
from inventory import (
    add_book,
    view_inventory,
    search_book,
    edit_book,
    remove_book
)


def display_menu():
    """
    Displays the main inventory management menu.
    """

    print("\n================================")
    print("  BOOKSTORE MANAGEMENT SYSTEM")
    print("================================")
    print("1. Add Book")
    print("2. View Inventory")
    print("3. Search Inventory")
    print("4. Edit Book")
    print("5. Remove Book")
    print("6. Exit")


def main():
    """
    Controls the main program loop and sends the user
    to the selected inventory function.
    """

    # Keep displaying the menu until the user selects Exit.
    while True:

        display_menu()

        # Ask the user which inventory operation to perform.
        choice = input("\nSelect an option: ")

        # Add a new book to the JSON inventory.
        if choice == "1":
            add_book()

        # Display all books currently in inventory.
        elif choice == "2":
            view_inventory()

        # Search for a book using title, author, or ISBN.
        elif choice == "3":
            search_book()

        # Modify an existing inventory record.
        elif choice == "4":
            edit_book()

        # Remove an existing book from inventory.
        elif choice == "5":
            remove_book()

        # End the application.
        elif choice == "6":
            print(
                "\nBookstore Management System closed."
            )
            break

        # Prevent invalid menu selections from stopping the program.
        else:
            print(
                "\nInvalid selection. Please choose 1-6."
            )


# This condition makes sure main() runs only when
# this file is executed directly.
if __name__ == "__main__":
    main()