from sales_app import app
from inventory import (
    find_book_by_id,
    update_book_quantity
)


print("\n--- FULL CHECKOUT INTEGRATION TESTS ---")


# ---------------------------------------------------------
# TEST SETTINGS
# ---------------------------------------------------------

BOOK_ID = 1
USERNAME = "testcashier"
PASSWORD = "Password123"


# ---------------------------------------------------------
# TEST 1: Find book before checkout
# ---------------------------------------------------------

book = find_book_by_id(BOOK_ID)

if book is not None:
    original_quantity = book["quantity"]

    print("PASS: Test book found in inventory.")
    print(
        f"Original quantity for book {BOOK_ID}: "
        f"{original_quantity}"
    )

else:
    print("FAIL: Test book was not found.")
    raise SystemExit


# Make sure there is inventory available.
if original_quantity <= 0:
    print("FAIL: Test book is out of stock.")
    raise SystemExit


# ---------------------------------------------------------
# CREATE FLASK TEST CLIENT
# ---------------------------------------------------------

app.config["TESTING"] = True

client = app.test_client()


# ---------------------------------------------------------
# TEST 2: Login through Greg's login route
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
        f"Status code: {login_response.status_code}"
    )


# ---------------------------------------------------------
# TEST 3: Open POS
# ---------------------------------------------------------

pos_response = client.get(
    "/",
    follow_redirects=False
)


if pos_response.status_code == 200:
    print("PASS: Logged-in Cashier can access POS.")
else:
    print(
        "FAIL: Cashier could not access POS. "
        f"Status code: {pos_response.status_code}"
    )


# ---------------------------------------------------------
# TEST 4: Add book to cart
# ---------------------------------------------------------

add_response = client.post(
    f"/add/{BOOK_ID}",
    follow_redirects=False
)


with client.session_transaction() as session_data:
    cart = session_data.get("cart", {})


if str(BOOK_ID) in cart:
    print("PASS: Book successfully added to POS cart.")
else:
    print("FAIL: Book was not added to POS cart.")


# ---------------------------------------------------------
# TEST 5: Select tax state
# ---------------------------------------------------------

tax_response = client.post(
    "/tax",
    data={
        "state": "CO"
    },
    follow_redirects=False
)


with client.session_transaction() as session_data:
    selected_state = session_data.get("tax_state")


if selected_state == "CO":
    print("PASS: Sales tax state selected.")
else:
    print("FAIL: Sales tax state was not selected.")


# ---------------------------------------------------------
# TEST 6: Complete checkout
# ---------------------------------------------------------

checkout_response = client.post(
    "/checkout",
    follow_redirects=False
)


if checkout_response.status_code in (302, 303):
    print("PASS: Checkout request completed.")
else:
    print(
        "FAIL: Checkout request failed. "
        f"Status code: {checkout_response.status_code}"
    )


# ---------------------------------------------------------
# TEST 7: Verify inventory decreased
# ---------------------------------------------------------

updated_book = find_book_by_id(BOOK_ID)

expected_quantity = original_quantity - 1


if (
    updated_book is not None
    and updated_book["quantity"] == expected_quantity
):
    print(
        "PASS: Checkout correctly decreased inventory."
    )

else:
    print(
        "FAIL: Checkout did not decrease inventory."
    )


# ---------------------------------------------------------
# TEST 8: Verify receipt was generated
# ---------------------------------------------------------

with client.session_transaction() as session_data:

    receipt = session_data.get("last_receipt")
    sale_id = session_data.get("last_sale_id")


if receipt and sale_id:
    print(
        f"PASS: Receipt generated for {sale_id}."
    )
else:
    print(
        "FAIL: Checkout did not generate a receipt."
    )


# ---------------------------------------------------------
# TEST 9: Verify cart was cleared
# ---------------------------------------------------------

with client.session_transaction() as session_data:
    cart_after_checkout = session_data.get(
        "cart",
        {}
    )


if cart_after_checkout == {}:
    print("PASS: Cart cleared after checkout.")
else:
    print("FAIL: Cart was not cleared after checkout.")


# ---------------------------------------------------------
# TEST 10: Verify receipt page can be opened
# ---------------------------------------------------------

receipt_response = client.get(
    "/receipt",
    follow_redirects=False
)


if receipt_response.status_code == 200:
    print("PASS: Receipt page opened successfully.")
else:
    print(
        "FAIL: Receipt page could not be opened. "
        f"Status code: {receipt_response.status_code}"
    )


# ---------------------------------------------------------
# RESTORE ORIGINAL INVENTORY
# ---------------------------------------------------------

update_book_quantity(
    BOOK_ID,
    original_quantity
)

restored_book = find_book_by_id(BOOK_ID)


if (
    restored_book is not None
    and restored_book["quantity"] == original_quantity
):
    print("PASS: Original inventory quantity restored.")
else:
    print("FAIL: Inventory quantity was not restored.")


print("\n--- FULL CHECKOUT TESTING COMPLETE ---")