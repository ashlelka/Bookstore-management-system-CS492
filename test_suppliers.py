from copy import deepcopy

from sales_app import app
from suppliers import (
    add_supplier,
    find_supplier,
    load_suppliers,
    save_suppliers,
)


print("\n SUPPLIER MANAGEMENT TESTS")


snapshot = deepcopy(load_suppliers())
failed = False


def report(ok, label):
    global failed
    if ok:
        print("PASS:", label)
    else:
        failed = True
        print("FAIL:", label)

# TEST 1: Supplier table exists

report(len(snapshot) >= 1, "Supplier table has seed records.")

# TEST 2: Reject a blank company name

ok, message = add_supplier({"name": ""})
report((not ok) and "required" in message.lower(), "Blank supplier name is rejected.")

# TEST 3: Add a supplier record

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
    ok and row is not None and row["name"] == "Test Wholesaler Co" and row["state"] == "TX",
    "New supplier record is saved with the next supplier_id.",
)

# TEST 4: Reject a duplicate name

ok, message = add_supplier({"name": "Test Wholesaler Co"})
report((not ok) and "already exists" in message.lower(), "Duplicate supplier name is rejected.")

# TEST 5: Maintenance screen (admin can add, cashier cannot)

app.config["TESTING"] = True
client = app.test_client()

login = client.post(
    "/login",
    data={"username": "admin1", "password": "Admin123!"},
    follow_redirects=False,
)
page = client.get("/suppliers", follow_redirects=False)
html = page.get_data(as_text=True)
report(
    login.status_code in (302, 303) and page.status_code == 200 and "Penguin Random House" in html,
    "Admin can open the supplier maintenance screen.",
)

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
    and any(row["name"] == "Chronicle Books" for row in load_suppliers()),
    "Admin can add a supplier from the maintenance screen.",
)

cashier = app.test_client()
cashier.post(
    "/login",
    data={"username": "testcashier", "password": "Password123"},
    follow_redirects=False,
)
blocked = cashier.get("/suppliers", follow_redirects=False)
report(blocked.status_code in (302, 303), "Cashier cannot open supplier maintenance.")


save_suppliers(snapshot)
report(
    [row["name"] for row in load_suppliers()] == [row["name"] for row in snapshot],
    "suppliers.json restored after tests.",
)

if failed:
    raise SystemExit(1)

print("T2-002 supplier tests passed.")
