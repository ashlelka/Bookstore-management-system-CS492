import json
from pathlib import Path

from sales_app import app
from inventory import (
    find_book_by_id,
    update_book_quantity
)

from database import (
    load_sales,
    connection_status
)


print("\n--- DATABASE INTEGRATION TESTS ---")


# ---------------------------------------------------------
# TEST SETTINGS
# ---------------------------------------------------------

BOOK_ID = 1

USERNAME = "testcashier"
PASSWORD = "Password123"

SALES_FILE = Path(__file__).resolve().parent / "sales.json"


# ---------------------------------------------------------
# BACK UP ORIGINAL SALES.JSON
# ---------------------------------------------------------

if SALES_FILE.exists():
    original_sales_file = SALES_FILE.read_text()
else:
    original_sales_file = None


# ---------------------------------------------------------
# TEST 1: Check database stores
# ---------------------------------------------------------

status = connection_status()

if status["all_stores_ok"]:
    print("PASS: All JSON database stores are connected.")
else:
    print("FAIL: One or more database stores are unavailable.")


# ---------------------------------------------------------
# TEST 2: Find test book
# ---------------------------------------------------------

book = find_book_by_id(BOOK_ID)

if book is not None:

    original_quantity = book["quantity"]

    print("PASS: Test book found in inventory.")

else:

    print("FAIL: Test book was not found.")
    raise SystemExit


if original_quantity <= 0:

    print("FAIL: Test book is out of stock.")
    raise SystemExit


# ---------------------------------------------------------
# RECORD NUMBER OF SALES BEFORE CHECKOUT
# ---------------------------------------------------------

sales_before = load_sales()

starting_sale_count = len(sales_before)

print(
    f"Sales before checkout: "
    f"{starting_sale_count}"
)


# ---------------------------------------------------------
# CREATE FLASK TEST CLIENT
# ---------------------------------------------------------

app.config["TESTING"] = True

client = app.test_client()


# ---------------------------------------------------------
# TEST 3: Login
# ---------------------------------------------------------

login_response = client.post(
    "/login",
    data={
        "username": USERNAME,
        "password": PASSWORD
    },
    follow_redirects=False
)


if login_response.status_code in (302, 303):

    print("PASS: Cashier successfully logged in.")

else:

    print(
        "FAIL: Cashier login failed. "
        f"Status: {login_response.status_code}"
    )


# ---------------------------------------------------------
# TEST 4: Open POS
# ---------------------------------------------------------

pos_response = client.get(
    "/",
    follow_redirects=False
)


if pos_response.status_code == 200:

    print("PASS: Cashier can access POS.")

else:

    print("FAIL: Cashier could not access POS.")


# ---------------------------------------------------------
# TEST 5: Add book to cart
# ---------------------------------------------------------

client.post(
    f"/add/{BOOK_ID}",
    follow_redirects=False
)


with client.session_transaction() as session_data:

    cart = session_data.get(
        "cart",
        {}
    )


if str(BOOK_ID) in cart:

    print("PASS: Book added to cart.")

else:

    print("FAIL: Book was not added to cart.")


# ---------------------------------------------------------
# TEST 6: Select tax state
# ---------------------------------------------------------

client.post(
    "/tax",
    data={
        "state": "CO"
    },
    follow_redirects=False
)


with client.session_transaction() as session_data:

    tax_state = session_data.get(
        "tax_state"
    )


if tax_state == "CO":

    print("PASS: Tax state selected.")

else:

    print("FAIL: Tax state was not selected.")


# ---------------------------------------------------------
# TEST 7: Checkout
# ---------------------------------------------------------

checkout_response = client.post(
    "/checkout",
    follow_redirects=False
)


if checkout_response.status_code in (302, 303):

    print("PASS: Checkout completed.")

else:

    print("FAIL: Checkout failed.")


# ---------------------------------------------------------
# TEST 8: Inventory decreased
# ---------------------------------------------------------

updated_book = find_book_by_id(
    BOOK_ID
)


if (
    updated_book is not None
    and updated_book["quantity"]
    == original_quantity - 1
):

    print(
        "PASS: Inventory decreased "
        "after checkout."
    )

else:

    print(
        "FAIL: Inventory did not decrease."
    )


# ---------------------------------------------------------
# TEST 9: Sale written to sales.json
# ---------------------------------------------------------

sales_after = load_sales()


if len(sales_after) == starting_sale_count + 1:

    print(
        "PASS: Checkout created "
        "a sales.json record."
    )

else:

    print(
        "FAIL: Checkout was not "
        "saved to sales.json."
    )


# ---------------------------------------------------------
# GET NEW SALE
# ---------------------------------------------------------

if sales_after:

    new_sale = sales_after[-1]

else:

    new_sale = {}


# ---------------------------------------------------------
# TEST 10: Sale ID saved
# ---------------------------------------------------------

sale_id = new_sale.get(
    "sale_id"
)


if sale_id:

    print(
        f"PASS: Sale ID stored: "
        f"{sale_id}"
    )

else:

    print(
        "FAIL: Sale ID was not stored."
    )


# ---------------------------------------------------------
# TEST 11: Cashier relationship
# ---------------------------------------------------------

if (
    new_sale.get("cashier_user_id")
    and
    new_sale.get("cashier_username")
    == USERNAME
):

    print(
        "PASS: Sale linked to "
        "Cashier employee account."
    )

else:

    print(
        "FAIL: Sale is not linked "
        "to Cashier account."
    )


# ---------------------------------------------------------
# TEST 12: Book relationship
# ---------------------------------------------------------

items = new_sale.get(
    "items",
    []
)


book_link_found = False


for item in items:

    if str(
        item.get("book_id")
    ) == str(BOOK_ID):

        book_link_found = True
        break


if book_link_found:

    print(
        "PASS: Sale linked to "
        "inventory book ID."
    )

else:

    print(
        "FAIL: Sale does not contain "
        "the inventory book ID."
    )


# ---------------------------------------------------------
# TEST 13: Tax relationship
# ---------------------------------------------------------

if new_sale.get(
    "tax_state"
) == "CO":

    print(
        "PASS: Sale linked to "
        "Colorado tax record."
    )

else:

    print(
        "FAIL: Sale tax relationship "
        "was not stored."
    )


# ---------------------------------------------------------
# TEST 14: Financial values
# ---------------------------------------------------------

if (
    new_sale.get("subtotal") is not None
    and
    new_sale.get("tax") is not None
    and
    new_sale.get("total") is not None
):

    print(
        "PASS: Subtotal, tax, "
        "and total were stored."
    )

else:

    print(
        "FAIL: Financial values "
        "are incomplete."
    )


# ---------------------------------------------------------
# TEST 15: Database relationship integrity
# ---------------------------------------------------------

status_after = connection_status()


if status_after["integrity"]["broken"] == 0:

    print(
        "PASS: Database foreign-key "
        "relationships are valid."
    )

else:

    print(
        "FAIL: Database contains "
        "broken relationships."
    )


# ---------------------------------------------------------
# TEST 16: Database page
# ---------------------------------------------------------

database_response = client.get(
    "/database",
    follow_redirects=False
)


# Cashier may be redirected because database
# management is restricted.
if database_response.status_code in (
    200,
    302,
    303
):

    print(
        "PASS: Database route responded "
        "correctly."
    )

else:

    print(
        "FAIL: Database route error. "
        f"Status: "
        f"{database_response.status_code}"
    )


# ---------------------------------------------------------
# RESTORE INVENTORY
# ---------------------------------------------------------

update_book_quantity(
    BOOK_ID,
    original_quantity
)


restored_book = find_book_by_id(
    BOOK_ID
)


if (
    restored_book is not None
    and
    restored_book["quantity"]
    == original_quantity
):

    print(
        "PASS: Original inventory "
        "quantity restored."
    )

else:

    print(
        "FAIL: Inventory quantity "
        "was not restored."
    )


# ---------------------------------------------------------
# RESTORE SALES.JSON
# ---------------------------------------------------------

if original_sales_file is not None:

    SALES_FILE.write_text(
        original_sales_file
    )

else:

    SALES_FILE.write_text(
        json.dumps(
            {
                "title":
                "Bookstore Management System",

                "sales": []
            },
            indent=2
        )
        + "\n"
    )


restored_sales = load_sales()


if len(restored_sales) == starting_sale_count:

    print(
        "PASS: Original sales.json "
        "data restored."
    )

else:

    print(
        "FAIL: sales.json was "
        "not restored."
    )


print(
    "\n--- DATABASE INTEGRATION "
    "TESTING COMPLETE ---"
)