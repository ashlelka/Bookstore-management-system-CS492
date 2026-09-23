"""
Bookstore Management System
Sprint 2 - T2-010
Developer: Alexis Silva

Search customer records, view purchase history, and test customer management.
"""

from customer_history import purchase_summary, purchases_for_customer, search_customers
from customer_management import get_customer, load_customers
from sales_app import app


print("\n--- CUSTOMER MANAGEMENT TESTS (T2-010) ---")

failed = False


def report(ok, label):
    global failed
    if ok:
        print("PASS:", label)
    else:
        failed = True
        print("FAIL:", label)


customers = load_customers()
maya = get_customer("c1a9e4d0b7f24a8e91d63c5b0a12f8e4")
owen = get_customer("a77b2c18e9044d6fb3c1d0e5a8f24690")
priya = get_customer("5e0d91c3a2b84711bf76e4d8c0139a22")

report(len(customers) >= 5, "Customer records are available to search.")
report(len(search_customers("hernandez")) == 1, "Search finds a customer by last name.")
report(len(search_customers("owen.patel")) == 1, "Search finds a customer by email.")
report(len(search_customers("555-0118")) == 1, "Search finds a customer by phone.")
report(len(search_customers("no-such-customer")) == 0, "Search returns no rows for an unknown query.")

maya_history = purchases_for_customer(maya)
owen_history = purchases_for_customer(owen)
priya_history = purchases_for_customer(priya)
report(len(maya_history) == 2, "Maya Hernandez has two linked purchases.")
report(len(owen_history) == 1, "Owen Patel has one linked purchase.")
report(len(priya_history) == 0, "A customer with no sales shows an empty history.")
report(purchase_summary(maya_history)["count"] == 2, "Purchase summary counts Maya's sales.")

app.config["TESTING"] = True
admin = app.test_client()
with admin.session_transaction() as session:
    session["username"] = "admin1"

page = admin.get("/customers")
html = page.get_data(as_text=True)
report(page.status_code == 200 and "Maya Hernandez" in html, "Admin can open customer records.")

search_page = admin.get("/customers?q=Patel")
search_html = search_page.get_data(as_text=True)
report(
    search_page.status_code == 200
    and "Owen Patel" in search_html
    and "Maya Hernandez" not in search_html,
    "Customer search page filters the list.",
)

profile = admin.get("/customers/c1a9e4d0b7f24a8e91d63c5b0a12f8e4")
profile_html = profile.get_data(as_text=True)
report(
    profile.status_code == 200
    and "Purchase history" in profile_html
    and "SALE-1042" in profile_html
    and "The Great Gatsby" in profile_html,
    "Customer profile shows purchase history.",
)

cashier = app.test_client()
with cashier.session_transaction() as session:
    session["username"] = "cashier1"
blocked = cashier.get("/customers")
report(blocked.status_code in (302, 403), "Cashier cannot open customer management.")

if failed:
    raise SystemExit(1)

print("T2-010 customer management tests passed.")
