"""
Bookstore Management System
Sprint 1 - NF-003
Developer: Alexis Silva

Create initial database interconnections.

Sprint 1 stores data in JSON files instead of SQL. This module is the
shared connection point between those stores:

  books.json              inventory (T1-001 / T1-003, Ashley)
  users.json              employee accounts (T1-009, Ashley)
  user_overrides.json     roles / permissions / locks (T1-010, Alexis)
  tax_rates.json          statewide tax table (T1-006, Alexis)
  sales.json              sale records that join the stores above (this file)

A completed sale stores foreign keys:
  - cashier_user_id  -> users.json
  - book_id          -> books.json
  - tax_state        -> tax_rates.json

"""

import json
from pathlib import Path

import user_management
from inventory import load_books
from tax_rates import load_tax_rates, state_rate
from user_management import load_users as load_employees

APP_DIR = Path(__file__).resolve().parent
SALES_PATH = APP_DIR / "sales.json"

# Teammate modules keep their own loaders; NF-003 pins them to this folder
# so Flask and the CLI read the same files.
user_management.USERS_FILE = APP_DIR / "users.json"

# Named stores other modules already own. NF-003 only reads them.
STORES = (
    {
        "name": "inventory",
        "file": "books.json",
        "owner": "T1-001 / T1-003 Ashley Lindamood",
        "key": "book_id",
    },
    {
        "name": "employees",
        "file": "users.json",
        "owner": "T1-009 Ashley Lindamood",
        "key": "user_id",
    },
    {
        "name": "user overrides",
        "file": "user_overrides.json",
        "owner": "T1-010 Alexis Silva",
        "key": "username",
    },
    {
        "name": "tax rates",
        "file": "tax_rates.json",
        "owner": "T1-006 Alexis Silva",
        "key": "code",
    },
    {
        "name": "sales",
        "file": "sales.json",
        "owner": "NF-003 Alexis Silva",
        "key": "sale_id",
    },
)

# Foreign-key map shown on the Data links page.
RELATIONSHIPS = (
    {
        "from_store": "sales",
        "from_key": "cashier_user_id",
        "to_store": "employees",
        "to_key": "user_id",
        "note": "Cashier who rang the sale",
    },
    {
        "from_store": "sales",
        "from_key": "items[].book_id",
        "to_store": "inventory",
        "to_key": "book_id",
        "note": "Each line item points at one book",
    },
    {
        "from_store": "sales",
        "from_key": "tax_state",
        "to_store": "tax rates",
        "to_key": "code",
        "note": "State used to look up the tax rate",
    },
    {
        "from_store": "user overrides",
        "from_key": "username",
        "to_store": "employees",
        "to_key": "username",
        "note": "T1-010 overlays Ashley's employee file without rewriting it",
    },
)


def _as_list(data):
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        for key in ("users", "sales", "states", "books"):
            if isinstance(data.get(key), list):
                return _as_list(data[key])
    return []


def _employee_records():
    employees = load_employees()
    if isinstance(employees, dict):
        employees = employees.get("users") or []
    return [row for row in employees if isinstance(row, dict)]


def load_sales():
    if not SALES_PATH.exists():
        return []
    try:
        data = json.loads(SALES_PATH.read_text())
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return data
    return data.get("sales") or []


def save_sales(sales):
    SALES_PATH.write_text(json.dumps({
        "title": "Bookstore Management System",
        "sales": sales,
    }, indent=2) + "\n")


def next_sale_id():
    numbers = []
    for sale in load_sales():
        raw = str(sale.get("sale_id", "")).replace("SALE-", "")
        if raw.isdigit():
            numbers.append(int(raw))
    return "SALE-" + str(max(numbers, default=1041) + 1)


def find_book(book_id):
    target = str(book_id)
    for book in load_books():
        if str(book.get("book_id")) == target:
            return book
    return None


def find_employee(user_id=None, username=None):
    for employee in _employee_records():
        if user_id is not None and str(employee.get("user_id")) == str(user_id):
            return employee
        if username and employee.get("username", "").lower() == str(username).lower():
            return employee
    return None


def interconnect_sale(sale, cashier):
    
    # Build one sales.json row that points at employee, book, and tax records.
    
    cashier = cashier or {}
    lines = []
    for item in sale.get("items") or []:
        book = find_book(item.get("productId"))
        lines.append({
            "book_id": item.get("productId"),
            "isbn": book.get("isbn") if book else None,
            "title": item.get("name"),
            "qty": item.get("qty"),
            "unit_price": item.get("unitPrice"),
            "line_total": item.get("lineTotal"),
            "exempt": item.get("exempt"),
        })
    tax_code = sale.get("taxState")
    return {
        "sale_id": sale.get("id"),
        "timestamp": sale.get("timestamp"),
        "cashier_user_id": cashier.get("user_id"),
        "cashier_username": cashier.get("username"),
        "cashier_name": ((cashier.get("first_name") or "") + " " + (cashier.get("last_name") or "")).strip(),
        "tax_state": tax_code,
        "tax_rate": state_rate(tax_code) if tax_code else sale.get("taxRate"),
        "subtotal": sale.get("subtotal"),
        "tax": sale.get("tax"),
        "total": sale.get("total"),
        "items": lines,
        "inventory_results": sale.get("inventoryResults") or [],
    }


def record_sale(sale, cashier):
    """NF-003: persist the joined sale after checkout."""
    sales = load_sales()
    sales.append(interconnect_sale(sale, cashier))
    save_sales(sales)
    return sales[-1]


def _tax_ok(tax_code):
    load_tax_rates()
    from tax_rates import STATES_BY_CODE
    return bool(tax_code) and tax_code in STATES_BY_CODE


def sale_with_lookups(sale_row):
    """Resolve stored IDs back to live inventory, employee, and tax records."""
    cashier = find_employee(
        user_id=sale_row.get("cashier_user_id"),
        username=sale_row.get("cashier_username"),
    )
    items = []
    books_ok = True
    for line in sale_row.get("items") or []:
        book = find_book(line.get("book_id"))
        linked = book is not None
        if not linked:
            books_ok = False
        items.append({
            **line,
            "in_inventory": linked,
            "quantity_now": book.get("quantity") if book else None,
        })
    cashier_ok = cashier is not None
    tax_ok = _tax_ok(sale_row.get("tax_state"))
    return {
        **sale_row,
        "cashier_ok": cashier_ok,
        "tax_ok": tax_ok,
        "books_ok": books_ok,
        "links_ok": cashier_ok and tax_ok and books_ok,
        "cashier_active": None if cashier is None else cashier.get("active"),
        "items": items,
        "lines": items,  # template alias; sale.items collides with dict.items()
    }


def store_health():
    # Confirm each JSON store exists, parses, and can be counted.
    rows = []
    for store in STORES:
        path = APP_DIR / store["file"]
        exists = path.exists()
        readable = False
        count = 0
        if exists:
            try:
                data = json.loads(path.read_text())
                readable = True
                if store["name"] == "user overrides":
                    accounts = data.get("accounts") if isinstance(data, dict) else {}
                    count = len(accounts) if isinstance(accounts, dict) else 0
                elif store["name"] == "tax rates":
                    load_tax_rates()
                    from tax_rates import STATES
                    count = len(STATES)
                elif store["name"] == "sales":
                    count = len(load_sales())
                elif store["name"] == "employees":
                    count = len(_employee_records())
                elif store["name"] == "inventory":
                    count = len(load_books())
                else:
                    count = len(_as_list(data))
            except json.JSONDecodeError:
                readable = False
        rows.append({
            **store,
            "exists": exists,
            "readable": readable,
            "count": count,
            "ok": exists and readable,
        })
    return rows


def connection_status():
    load_tax_rates()
    from tax_rates import STATES
    stores = store_health()
    sales = [sale_with_lookups(sale) for sale in load_sales()]
    linked = sum(1 for sale in sales if sale["links_ok"])
    return {
        "stores": stores,
        "relationships": RELATIONSHIPS,
        "book_count": len(load_books()),
        "employee_count": len(_employee_records()),
        "tax_state_count": len(STATES),
        "sale_count": len(sales),
        "sales": sales[-10:][::-1],
        "integrity": {
            "total": len(sales),
            "linked": linked,
            "broken": len(sales) - linked,
        },
        "all_stores_ok": all(store["ok"] for store in stores),
    }


if __name__ == "__main__":
    status = connection_status()
    print("NF-003 database interconnections")
    print("Stores:")
    for store in status["stores"]:
        flag = "ok" if store["ok"] else "MISSING"
        print(f"  [{flag}] {store['file']:<24} {store['count']} rows  key={store['key']}")
    print("Foreign keys:")
    for rel in status["relationships"]:
        print(f"  {rel['from_store']}.{rel['from_key']} -> {rel['to_store']}.{rel['to_key']}")
    print(
        "Integrity:",
        status["integrity"]["linked"],
        "of",
        status["integrity"]["total"],
        "sales fully linked",
    )
