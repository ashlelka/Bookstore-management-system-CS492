"""T2-009 — customer profiles, Timur Tyulin. Uses the project's JSON storage."""
import json
import re
import os
import tempfile
from threading import RLock
from datetime import datetime
from pathlib import Path
from uuid import uuid4

CUSTOMERS_PATH = Path(__file__).resolve().parent / "customers.json"
_write_lock = RLock()


class CustomerStoreError(Exception):
    """The customer file could not be read or saved safely."""


class CustomerConflictError(Exception):
    """Another edit has changed this profile since the form was opened."""


def load_customers():
    if not CUSTOMERS_PATH.exists():
        return []
    # TT: Fail visibly on corrupt data instead of overwriting it with an empty list.
    try:
        data = json.loads(CUSTOMERS_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise CustomerStoreError("Customer records could not be read. No data was changed.") from exc
    if (not isinstance(data, list) or any(
            not isinstance(row, dict) or not isinstance(row.get("customer_id"), str)
            or not row["customer_id"] for row in data)):
        raise CustomerStoreError("Invalid customer store; no data was changed.")
    if len({row["customer_id"] for row in data}) != len(data):
        raise CustomerStoreError("Duplicate customer IDs; no data was changed.")
    return data


def get_customer(customer_id):
    return next((row for row in load_customers()
                 if row["customer_id"] == customer_id), None)


def save_customer(fields, customer_id=None, expected_updated_at=None):
    # TT: Serialize reads and writes within this application process.
    with _write_lock:
        return _save_customer(fields, customer_id, expected_updated_at)


def _save_customer(fields, customer_id, expected_updated_at):
    records = load_customers()
    record = next((r for r in records if r["customer_id"] == customer_id), None)
    if customer_id and record is None:
        raise LookupError("Customer not found.")
    if record is not None and expected_updated_at is not None and expected_updated_at != record.get("updated_at", ""):
        raise CustomerConflictError("This customer was edited elsewhere. Reload the profile before saving.")
    clean = {key: str(fields.get(key, "")).strip() for key in
             ("first_name", "last_name", "email", "phone", "address")}
    if not clean["first_name"] or not clean["last_name"]:
        raise ValueError("First and last name are required.")
    if any(len(value) > (500 if key == "address" else 120)
           for key, value in clean.items()):
        raise ValueError("A customer field is too long.")
    if clean["email"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", clean["email"]):
        raise ValueError("Enter a valid email address.")
    if clean["email"] and any(r["customer_id"] != customer_id and
                               str(r.get("email") or "").casefold() == clean["email"].casefold()
                               for r in records):
        raise ValueError("A customer with this email already exists.")
    if record is None:
        record = {"customer_id": uuid4().hex, "created_at": datetime.now().isoformat(),
                  "loyalty_points": 0}
        records.append(record)
    record.update(clean, updated_at=datetime.now().isoformat())
    # TT: Replace the file only after writing a complete copy; retain unknown fields.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=CUSTOMERS_PATH.parent,
                                         prefix=".customers-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(records, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(CUSTOMERS_PATH)
    except OSError as exc:
        raise CustomerStoreError("Customer records could not be saved. Please try again.") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return record
