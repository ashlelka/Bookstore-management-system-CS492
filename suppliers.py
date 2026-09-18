"""
Bookstore Management System
Sprint 2 - T2-002
Developer: Alexis Silva

BMS-005 Supplier management:
  - Design supplier table
  - Create supplier maintenance screen
  - Add supplier records
  - Test supplier management
"""

import json
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
SUPPLIERS_PATH = APP_DIR / "suppliers.json"

FIELDS = (
    "name",
    "contact_name",
    "email",
    "phone",
    "city",
    "state",
    "categories",
    "notes",
)


def load_suppliers():
    if not SUPPLIERS_PATH.exists():
        return []
    try:
        data = json.loads(SUPPLIERS_PATH.read_text())
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return data
    return data.get("suppliers") or []


def save_suppliers(suppliers):
    SUPPLIERS_PATH.write_text(json.dumps({
        "suppliers": suppliers,
    }, indent=2) + "\n")


def next_supplier_id(suppliers=None):
    suppliers = load_suppliers() if suppliers is None else suppliers
    if not suppliers:
        return 1
    return max(int(row.get("supplier_id") or 0) for row in suppliers) + 1


def find_supplier(supplier_id, suppliers=None):
    #Lookup used by later tickets
    target = str(supplier_id)
    for row in (suppliers if suppliers is not None else load_suppliers()):
        if str(row.get("supplier_id")) == target:
            return row
    return None


def _clean(value):
    return (value or "").strip()


def _name_taken(suppliers, name, ignore_id=None):
    wanted = name.casefold()
    for row in suppliers:
        if ignore_id is not None and str(row.get("supplier_id")) == str(ignore_id):
            continue
        if (row.get("name") or "").casefold() == wanted:
            return True
    return False


def validate_supplier(payload, suppliers=None, ignore_id=None):
    name = _clean(payload.get("name"))
    if not name:
        return False, "Supplier name is required."
    email = _clean(payload.get("email"))
    if email and "@" not in email:
        return False, "Email must include @."
    suppliers = load_suppliers() if suppliers is None else suppliers
    if _name_taken(suppliers, name, ignore_id=ignore_id):
        return False, "A supplier with this name already exists."
    return True, "Supplier is valid."


def add_supplier(payload):
    #T2-002: insert one supplier row. Returns (ok, message_or_id).
    suppliers = load_suppliers()
    ok, message = validate_supplier(payload, suppliers)
    if not ok:
        return False, message
    supplier_id = next_supplier_id(suppliers)
    record = {
        "supplier_id": supplier_id,
        "active": True,
    }
    for field in FIELDS:
        record[field] = _clean(payload.get(field))
    record["state"] = record["state"].upper()
    suppliers.append(record)
    save_suppliers(suppliers)
    return True, supplier_id
