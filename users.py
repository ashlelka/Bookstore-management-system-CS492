"""
Bookstore Management System
Sprint 1 - T1-010
Developer: Alexis Silva

BMS-007 User management:
  - Assign user roles
  - Modify user permissions
  - Lock or disable user accounts

Reads employee accounts from Ashley's T1-009 module (user_management.py).
Saves T1-010 changes only to user_overrides.json.
"""

import json
from pathlib import Path

from user_management import load_users as load_employee_file

OVERRIDES_PATH = Path(__file__).resolve().parent / "user_overrides.json"

ROLES = {
    "Admin": ["use_pos", "manage_users"],
    "Manager": ["use_pos", "manage_users"],
    "Cashier": ["use_pos"],
}

PERMISSIONS = [
    {"id": "use_pos", "label": "Use the sales register"},
    {"id": "manage_users", "label": "Manage users, roles, and locks"},
]

USERS = []
USERS_BY_NAME = {}


def _load_overrides():
    if not OVERRIDES_PATH.exists():
        return {}
    data = json.loads(OVERRIDES_PATH.read_text())
    return data.get("accounts") or {}


def _save_overrides(accounts):
    OVERRIDES_PATH.write_text(json.dumps({
        "title": "Bookstore Management System",
        "sprint": "Sprint 1 - T1-010",
        "developer": "Alexis Silva",
        "note": "T1-010 overlays only. Does not replace T1-009 user_management.py or users.json.",
        "accounts": accounts,
    }, indent=2) + "\n")


def _display_name(user):
    first = user.get("first_name") or ""
    last = user.get("last_name") or ""
    return (first + " " + last).strip() or user.get("username", "")


def _merge(employee, overlay):
    record = dict(employee)
    role = overlay.get("role") or record.get("role") or "Cashier"
    record["role"] = role
    record["permissions"] = list(overlay.get("permissions") or ROLES.get(role, ROLES["Cashier"]))
    record["locked"] = bool(overlay.get("locked")) or not record.get("active", True)
    record["name"] = _display_name(record)
    return record


def load_users():
    global USERS, USERS_BY_NAME
    overlays = _load_overrides()
    USERS = []
    for employee in load_employee_file():
        key = employee["username"].lower()
        USERS.append(_merge(employee, overlays.get(key) or overlays.get(employee["username"]) or {}))
    USERS_BY_NAME = {u["username"].lower(): u for u in USERS}
    return USERS


def _update_account(username, **changes):
    user = get_user(username)
    if not user:
        return False
    accounts = _load_overrides()
    key = user["username"]
    entry = dict(accounts.get(key) or accounts.get(key.lower()) or {})
    entry.update(changes)
    accounts = {k: v for k, v in accounts.items() if k.lower() != key.lower()}
    accounts[key] = entry
    _save_overrides(accounts)
    load_users()
    return True


def get_user(username):
    load_users()
    if not username:
        return None
    return USERS_BY_NAME.get(username.lower())


def effective_permissions(user):
    if not user or user.get("locked"):
        return []
    return list(user.get("permissions") or [])


def has_permission(user, permission):
    return permission in effective_permissions(user)


def assign_role(username, role):
    """T1-010: assign a role and copy that role's default permissions."""
    if role not in ROLES:
        return False
    return _update_account(username, role=role, permissions=list(ROLES[role]))


def set_permissions(username, permissions):
    """T1-010: override the permission list for one account."""
    allowed = {p["id"] for p in PERMISSIONS}
    return _update_account(username, permissions=[p for p in permissions if p in allowed])


def set_locked(username, locked):
    """T1-010: lock/disable without changing T1-009 users.json."""
    return _update_account(username, locked=bool(locked))


load_users()
