from copy import deepcopy

from sales_app import app
from suppliers import (
    add_supplier,
    find_supplier,
    load_suppliers,
    save_suppliers,
)


print("\nSUPPLIER MANAGEMENT TESTS")


# Load current supplier data.
original_suppliers = deepcopy(load_suppliers())

# Remove temporary records left by interrupted test runs.
snapshot = [
    supplier for supplier in original_suppliers
    if supplier.get("name") not in {
        "Test Wholesaler Co",
        "Chronicle Books",
    }
]

# Start with clean supplier test data.
save_suppliers(snapshot)

failed = False

def report(ok, label):
    """Print the result of each supplier management test."""
    global failed

    if ok:
        print("PASS:", label)
    else:
        failed = True
        print("FAIL:", label)


# ---------------------------------------------------------
# TEST 1: Supplier table exists
# ---------------------------------------------------------

report(
    len(snapshot) >= 1,
    "Supplier table has seed records."
)


# ---------------------------------------------------------
# TEST 2: Reject a blank company name
# ---------------------------------------------------------

ok, message = add_supplier({
    "name": ""
})

report(
    (not ok) and "required" in message.lower(),
    "Blank supplier name is rejected."
)


# ---------------------------------------------------------
# TEST 3: Add a supplier record
# ---------------------------------------------------------

ok, supplier_id = add_supplier({
    "name": "Test Wholesaler Co",
    "contact_name": "Sam Rivera",
    "email": "orders@test-wholesaler.example",
    "phone": "512-555-0199",
    "city": "Austin",
    "state": "tx",
    "categories": "Fiction, Textbooks",
    "notes": "Temporary test row",
})


row = find_supplier(supplier_id) if ok else None
report(
    ok
    and row is not None
    and row["name"] == "Test Wholesaler Co"
    and row["state"] == "TX",
    "New supplier record is saved with the next supplier_id."
)


# ---------------------------------------------------------
# TEST 4: Reject a duplicate supplier name
# ---------------------------------------------------------

ok, message = add_supplier({
    "name": "Test Wholesaler Co"
})

report(
    (not ok) and "already exists" in message.lower(),
    "Duplicate supplier name is rejected."
)


# ---------------------------------------------------------
# TEST 5: Admin can open supplier maintenance
# ---------------------------------------------------------

app.config["TESTING"] = True

client = app.test_client()

# Create an authenticated Admin session.
# This tests supplier permissions without depending on
# the separate login system.
with client.session_transaction() as session:
    session["username"] = "admin1"

page = client.get(
    "/suppliers",
    follow_redirects=False
)

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "Penguin Random House" in html,
    "Admin can open the supplier maintenance screen."
)


# ---------------------------------------------------------
# TEST 6: Admin can add a supplier from maintenance
# ---------------------------------------------------------

add_response = client.post(
    "/suppliers",
    data={
        "name": "Chronicle Books",
        "contact_name": "Lee Nguyen",
        "email": "orders@chronicle.example",
        "phone": "415-555-0101",
        "city": "San Francisco",
        "state": "CA",
        "categories": "Art, Gift",
        "notes": "West coast gift books",
    },
    follow_redirects=True,
)

added_html = add_response.get_data(as_text=True)

report(
    add_response.status_code == 200
    and "Chronicle Books" in added_html
    and any(
        row["name"] == "Chronicle Books"
        for row in load_suppliers()
    ),
    "Admin can add a supplier from the maintenance screen."
)


# ---------------------------------------------------------
# TEST 7: Cashier cannot open supplier maintenance
# ---------------------------------------------------------

cashier = app.test_client()

# Create an authenticated Cashier session.
with cashier.session_transaction() as session:
    session["username"] = "testcashier"

blocked = cashier.get(
    "/suppliers",
    follow_redirects=False
)

report(
    blocked.status_code in (302, 303),
    "Cashier cannot open supplier maintenance."
)


# ---------------------------------------------------------
# TEST 8: Restore suppliers.json after testing
# ---------------------------------------------------------

save_suppliers(snapshot)

report(
    [row["name"] for row in load_suppliers()]
    == [row["name"] for row in snapshot],
    "suppliers.json restored after tests."
)


# ---------------------------------------------------------
# Final result
# ---------------------------------------------------------

if failed:
    raise SystemExit(1)

print("\nT2-002 supplier tests passed.")