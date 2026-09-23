"""
Bookstore Management System
Sprint 2 - T2-011

System Integration Testing

Tests integration between:
- Authentication / authorization
- Inventory
- POS
- Customer experience
- Customer management
- Suppliers
- Purchase orders
- Sales database
- Receipt history
- Sales reporting
- Financial dashboard
"""

from sales_app import app
from inventory import load_books
from database import load_sales, connection_status
from customer_management import load_customers
from suppliers import load_suppliers


print("\n--- SYSTEM INTEGRATION TESTS (T2-011) ---")

failed = False


def report(ok, label):
    """Display the result of an integration test."""

    global failed

    if ok:
        print("PASS:", label)
    else:
        failed = True
        print("FAIL:", label)


# =========================================================
# Flask Test Client
# =========================================================

app.config["TESTING"] = True

client = app.test_client()


def login_as(username):
    """
    Create an authenticated test session without requiring
    the user's real password.
    """

    with client.session_transaction() as session:
        session.clear()
        session["username"] = username
        session["cart"] = {}


# =========================================================
# TEST 1
# Unauthenticated users are protected
# =========================================================

client.get("/signout")

response = client.get(
    "/",
    follow_redirects=False,
)

report(
    response.status_code in (302, 303),
    "Authentication protects the POS.",
)


# =========================================================
# TEST 2
# Admin account integrates with POS
# =========================================================

login_as("admin1")

response = client.get("/")

html = response.get_data(as_text=True)

report(
    response.status_code == 200
    and "Bookstore Management System" in html,
    "Admin account can access the POS.",
)


# =========================================================
# TEST 3
# Inventory integrates with POS
# =========================================================

books = load_books()

report(
    isinstance(books, list)
    and len(books) > 0,
    "Inventory data loads successfully.",
)


first_book = next(
    (
        book for book in books
        if int(book.get("quantity", 0)) > 0
    ),
    None,
)

book_id = (
    first_book.get("book_id")
    if first_book
    else None
)

report(
    first_book is not None
    and first_book.get("title") in html,
    "Inventory books appear in the POS catalog.",
)


# =========================================================
# TEST 4
# Inventory availability integrates with POS
# =========================================================

report(
    "in stock" in html
    or "Out of stock" in html,
    "Inventory availability appears in the POS.",
)


# =========================================================
# TEST 5
# T2-005 Search integrates with inventory
# =========================================================

response = client.get(
    "/",
    query_string={
        "search": "Gatsby"
    },
)

html = response.get_data(as_text=True)

report(
    response.status_code == 200
    and "The Great Gatsby" in html,
    "Book search integrates with inventory data.",
)


# =========================================================
# TEST 6
# T2-005 Category navigation integrates with inventory
# =========================================================

response = client.get(
    "/",
    query_string={
        "cat": "Fantasy"
    },
)

html = response.get_data(as_text=True)

report(
    response.status_code == 200
    and "The Hobbit" in html,
    "Category navigation integrates with inventory.",
)


# =========================================================
# TEST 7
# POS cart integrates with inventory product
# =========================================================

response = client.post(
    f"/add/{book_id}",
    follow_redirects=True,
)

html = response.get_data(as_text=True)

report(
    response.status_code == 200
    and "was added to the ticket." in html,
    "POS cart accepts an inventory book.",
)


# =========================================================
# TEST 8
# T2-006 confirmation message integrates with POS
# =========================================================

report(
    'role="status"' in html
    and 'aria-live="polite"' in html,
    "Customer confirmation message integrates with POS UI.",
)


# =========================================================
# TEST 9
# Remove integrates with cart
# =========================================================

response = client.post(
    f"/remove/{book_id}",
    follow_redirects=True,
)

html = response.get_data(as_text=True)

report(
    response.status_code == 200
    and "was removed from the ticket." in html,
    "Remove action integrates with POS cart.",
)


# =========================================================
# TEST 10
# Clear integrates with cart
# =========================================================

client.post(
    f"/add/{book_id}",
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
    "Clear action integrates with POS cart.",
)


# =========================================================
# TEST 11
# Customer database loads
# =========================================================

customers = load_customers()

report(
    isinstance(customers, list)
    and len(customers) > 0,
    "Customer records load successfully.",
)


# =========================================================
# TEST 12
# Customer management integrates with Flask
# =========================================================

login_as("admin1")

response = client.get("/customers")

html = response.get_data(as_text=True)

report(
    response.status_code == 200,
    "Customer management integrates with the Flask application.",
)


# =========================================================
# TEST 13
# Customer profile integrates with purchase history
# =========================================================

if customers:

    customer_id = customers[0].get(
        "customer_id"
    )

    response = client.get(
        f"/customers/{customer_id}"
    )

    report(
        response.status_code == 200,
        "Customer profile integrates with purchase history.",
    )

else:

    report(
        False,
        "Customer profile integrates with purchase history.",
    )


# =========================================================
# TEST 14
# Supplier database loads
# =========================================================

suppliers = load_suppliers()

# suppliers.py may return either the list directly
# or a dictionary containing the supplier list.

if isinstance(suppliers, dict):

    supplier_records = suppliers.get(
        "suppliers",
        []
    )

else:

    supplier_records = suppliers


report(
    isinstance(supplier_records, list)
    and len(supplier_records) > 0,
    "Supplier records load successfully.",
)


# =========================================================
# TEST 15
# Supplier management integrates with Flask
# =========================================================

login_as("admin1")

response = client.get("/suppliers")

report(
    response.status_code == 200,
    "Supplier management integrates with the Flask application.",
)


# =========================================================
# TEST 16
# Purchase order management integrates with Flask
# =========================================================

response = client.get(
    "/purchase-orders"
)

report(
    response.status_code == 200,
    "Purchase order management integrates with the Flask application.",
)


# =========================================================
# TEST 17
# Sales database integration
# =========================================================

status = connection_status()

report(
    status.get("all_stores_ok") is True,
    "All JSON database stores are connected.",
)


# =========================================================
# TEST 18
# Existing sales can be loaded
# =========================================================

sales = load_sales()

report(
    isinstance(sales, list),
    "Sales database loads successfully.",
)


# =========================================================
# TEST 19
# Receipt history integrates with sales database
# =========================================================

login_as("admin1")

response = client.get("/receipts")

report(
    response.status_code == 200,
    "Receipt history integrates with sales data.",
)


# =========================================================
# TEST 20
# Sales reporting integrates with sales database
# =========================================================

response = client.get("/reports")

report(
    response.status_code == 200,
    "Sales reporting integrates with sales data.",
)


# =========================================================
# TEST 21
# Financial dashboard integrates with sales database
# =========================================================

response = client.get(
    "/financial-dashboard"
)

report(
    response.status_code == 200,
    "Financial dashboard integrates with sales data.",
)


# =========================================================
# TEST 22
# Employee management integrates with RBAC
# =========================================================

response = client.get("/users")

report(
    response.status_code == 200,
    "Employee management integrates with RBAC.",
)


# =========================================================
# TEST 23
# Cashier can access normal POS
# =========================================================

login_as("cashier1")

response = client.get("/")

report(
    response.status_code == 200,
    "Cashier can access the normal POS.",
)


# =========================================================
# TEST 24
# Cashier cannot access management customer pages
# =========================================================

response = client.get(
    "/customers",
    follow_redirects=False,
)

report(
    response.status_code == 403,
    "Cashier is blocked from customer management.",
)


# =========================================================
# TEST 25
# Cashier cannot access financial dashboard
# =========================================================

response = client.get(
    "/financial-dashboard",
    follow_redirects=False,
)

report(
    response.status_code in (
        302,
        303,
        403,
    ),
    "Cashier is blocked from financial management.",
)


# =========================================================
# TEST 26
# Application remains operational after integration tests
# =========================================================

response = client.get("/")

report(
    response.status_code == 200,
    "POS remains operational after integration testing.",
)


# =========================================================
# Clean Test Session
# =========================================================

with client.session_transaction() as session:

    session["cart"] = {}

    session.pop(
        "pos_message",
        None,
    )

    session.pop(
        "banner",
        None,
    )

    session.pop(
        "sale_customer_id",
        None,
    )


# =========================================================
# FINAL RESULT
# =========================================================

print()

if failed:

    print(
        "T2-011 system integration testing "
        "completed with failures."
    )

    raise SystemExit(1)


print(
    "T2-011 system integration tests passed."
)