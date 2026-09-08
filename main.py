"""
Bookstore Management System
Sprint 1 - T1-003
Developer: Ashley Lindamood

Description:
This program provides the main menu for the bookstore
inventory CRUD system. Inventory information is stored
in a JSON file.
"""

from inventory import (
    add_book,
    view_inventory,
    search_book,
    edit_book,
    remove_book
)


def display_menu():
    """
    Displays the bookstore inventory CRUD menu.
    """

    print("\n================================")
    print("  BOOKSTORE MANAGEMENT SYSTEM")
    print("     INVENTORY MANAGEMENT")
    print("================================")
    print("1. Add Book")
    print("2. View Inventory")
    print("3. Search Inventory")
    print("4. Edit Book")
    print("5. Remove Book")
    print("6. Exit")


def main():
    """
    Runs the main bookstore inventory menu.
    """

    while True:

        display_menu()

        choice = input(
            "\nSelect an option: "
        ).strip()

        # CREATE
        if choice == "1":
            add_book()

        # READ
        elif choice == "2":
            view_inventory()

        # READ / SEARCH
        elif choice == "3":
            search_book()

        # UPDATE
        elif choice == "4":
            edit_book()

        # DELETE
        elif choice == "5":
            remove_book()

        elif choice == "6":

            print(
                "\nBookstore Management System closed."
            )

            break

        else:

            print(
                "\nInvalid selection. "
                "Please choose 1 through 6."
            )


if __name__ == "__main__":
    main()