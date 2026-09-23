"""
Bookstore Management System
Sprint 2 - T2-006

Customer UI Testing:
- Inventory availability
- Low-stock display
- Out-of-stock behavior
- Add confirmation
- Remove confirmation
- Clear-ticket confirmation
"""

from sales_app import app, product_by_id, load_products


print("\n--- CUSTOMER UI TESTS (T2-006) ---")

failed = False


def report(ok, label):
    """Print the result of each T2-006 test."""
    global failed

    if ok:
        print("PASS:", label)
    else:
        failed = True
        print("FAIL:", label)


def get_product_id(book_name):
    """Find a product ID using the book name."""
    load_products()

    # Check a reasonable range of product IDs.
    for pid in range(1, 100):
        product = product_by_id(str(pid))

        if product and product.get("name") == book_name:
            return str(pid)

    return None


# ---------------------------------------------------------
# Configure Flask test client
# ---------------------------------------------------------

app.config["TESTING"] = True

client = app.test_client()

with client.session_transaction() as session:
    session["username"] = "admin1"
    session["cart"] = {}


# ---------------------------------------------------------
# Find books used by the tests
# ---------------------------------------------------------

gatsby_id = get_product_id("The Great Gatsby")
hobbit_id = get_product_id("The Hobbit")


report(
    gatsby_id is not None,
    "Test book The Great Gatsby exists.",
)

report(
    hobbit_id is not None,
    "Test book The Hobbit exists.",
)


# ---------------------------------------------------------
# Test 1 - Inventory availability is displayed
# ---------------------------------------------------------

page = client.get("/")

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "in stock" in html,
    "Inventory availability is displayed on the POS.",
)


# ---------------------------------------------------------
# Test 2 - Low-stock feedback is displayed
# ---------------------------------------------------------

report(
    page.status_code == 200
    and "Low" in html,
    "Low-stock feedback is displayed.",
)


# ---------------------------------------------------------
# Test 3 - Low-stock alert is displayed
# ---------------------------------------------------------

report(
    page.status_code == 200
    and "Low Stock" in html,
    "Low-stock alert is displayed on the POS.",
)


# ---------------------------------------------------------
# Test 4 - Add book to ticket
# ---------------------------------------------------------

if hobbit_id:

    response = client.post(
        f"/add/{hobbit_id}",
        follow_redirects=True,
    )

    html = response.get_data(as_text=True)

    report(
        response.status_code == 200
        and "The Hobbit was added to the ticket." in html,
        "Adding a book displays a confirmation message.",
    )

else:
    report(
        False,
        "Adding a book displays a confirmation message.",
    )


# ---------------------------------------------------------
# Test 5 - Book was added to test-session cart
# ---------------------------------------------------------

with client.session_transaction() as session:
    test_cart = session.get("cart", {})

report(
    hobbit_id is not None
    and str(hobbit_id) in test_cart,
    "Selected book is added to the ticket.",
)


# ---------------------------------------------------------
# Test 6 - Remove book from ticket
# ---------------------------------------------------------

if hobbit_id:

    response = client.post(
        f"/remove/{hobbit_id}",
        follow_redirects=True,
    )

    html = response.get_data(as_text=True)

    report(
        response.status_code == 200
        and "The Hobbit was removed from the ticket." in html,
        "Removing a book displays a confirmation message.",
    )

else:
    report(
        False,
        "Removing a book displays a confirmation message.",
    )


# ---------------------------------------------------------
# Test 7 - Book was removed from test-session cart
# ---------------------------------------------------------

with client.session_transaction() as session:
    test_cart = session.get("cart", {})

report(
    hobbit_id is not None
    and str(hobbit_id) not in test_cart,
    "Selected book is removed from the ticket.",
)


# ---------------------------------------------------------
# Test 8 - Clear-ticket confirmation
# ---------------------------------------------------------

if hobbit_id:

    # Add an item first so there is something to clear.
    client.post(
        f"/add/{hobbit_id}",
        follow_redirects=True,
    )

    response = client.post(
        "/clear",
        follow_redirects=True,
    )

    html = response.get_data(as_text=True)

    report(
        response.status_code == 200
        and "The ticket was cleared." in html,
        "Clearing the ticket displays a confirmation message.",
    )

else:
    report(
        False,
        "Clearing the ticket displays a confirmation message.",
    )


# ---------------------------------------------------------
# Test 9 - Ticket is empty after Clear
# ---------------------------------------------------------

with client.session_transaction() as session:
    test_cart = session.get("cart", {})

report(
    test_cart == {},
    "Clear removes all items from the ticket.",
)


# ---------------------------------------------------------
# Test 10 - Confirmation uses accessible status message
# ---------------------------------------------------------

if hobbit_id:

    response = client.post(
        f"/add/{hobbit_id}",
        follow_redirects=True,
    )

    html = response.get_data(as_text=True)

    report(
        'role="status"' in html
        and 'aria-live="polite"' in html,
        "Confirmation message includes accessible UI feedback.",
    )

else:
    report(
        False,
        "Confirmation message includes accessible UI feedback.",
    )


# ---------------------------------------------------------
# Test 11 - POS still displays inventory after cart actions
# ---------------------------------------------------------

page = client.get("/")

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "The Hobbit" in html
    and "The Great Gatsby" in html,
    "Inventory remains available after ticket actions.",
)


# ---------------------------------------------------------
# Clean test-session cart
# ---------------------------------------------------------

with client.session_transaction() as session:
    session["cart"] = {}
    session.pop("pos_message", None)


# ---------------------------------------------------------
# Final Test Result
# ---------------------------------------------------------

if failed:
    raise SystemExit(1)

print("T2-006 customer UI tests passed.")