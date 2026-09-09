"""
Bookstore Management System
Sprint 1 - T1-009
User Management and Employee Accounts

This module manages employee user accounts for the
Bookstore Management System.
"""

import json
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash


USERS_FILE = Path("users.json")


def load_users():
    """
    Loads employee accounts from users.json.
    """

    if not USERS_FILE.exists():
        return []

    try:
        data = json.loads(USERS_FILE.read_text())

        if isinstance(data, list):
            return data

        return []

    except json.JSONDecodeError:
        return []


def save_users(users):
    """
    Saves employee accounts to users.json.
    """

    USERS_FILE.write_text(
        json.dumps(users, indent=4)
    )


def generate_user_id(users):
    """
    Generates the next available employee user ID.
    """

    if not users:
        return 1

    return max(user["user_id"] for user in users) + 1


def hash_password(password):
    """
    Securely hashes an employee password before storage.
    The plain-text password is never saved.
    """

    return generate_password_hash(password)


def username_exists(users, username):
    """
    Checks whether a username already exists.
    """

    for user in users:

        if user["username"].lower() == username.lower():
            return True

    return False

def validate_password(password):
    """
    Validates basic employee password requirements.
    """

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if not any(char.isupper() for char in password):
        return False, "Password must contain an uppercase letter."

    if not any(char.islower() for char in password):
        return False, "Password must contain a lowercase letter."

    if not any(char.isdigit() for char in password):
        return False, "Password must contain a number."

    return True, "Password is valid."

def create_employee_account(
    username,
    password,
    first_name,
    last_name,
    role
):
    """
    Creates a new employee account.
    """

    users = load_users()

    # Validate required fields.
    if not username or not password:
        return False, "Username and password are required."
    password_valid, password_message = validate_password(password)

    if not password_valid:
        return False, password_message
    # Prevent duplicate usernames.
    if username_exists(users, username):
        return False, "Username already exists."

    # Validate role.
    valid_roles = ["Admin", "Manager", "Cashier"]

    if role not in valid_roles:
        return False, "Invalid employee role."

    user_id = generate_user_id(users)

    new_user = {
        "user_id": user_id,
        "username": username,
        "password_hash": hash_password(password),
        "first_name": first_name,
        "last_name": last_name,
        "role": role,
        "active": True
    }

    users.append(new_user)

    save_users(users)

    return True, user_id


def find_user_by_username(username):
    """
    Finds an employee by username.
    """

    users = load_users()

    for user in users:

        if user["username"].lower() == username.lower():
            return user

    return None


def authenticate_user(username, password):
    """
    Authenticates an employee using their username and password.

    Returns the employee record when authentication succeeds.
    Returns None when authentication fails.
    """

    user = find_user_by_username(username)

    # Username does not exist.
    if user is None:
        return None

    # Inactive employees cannot log in.
    if not user["active"]:
        return None

    # Compare the entered password with the stored hash.
    if check_password_hash(user["password_hash"], password):
        return user

    return None


def deactivate_user(user_id):
    """
    Deactivates an employee account.
    """

    users = load_users()

    for user in users:

        if user["user_id"] == user_id:

            user["active"] = False

            save_users(users)

            return True

    return False


def view_users():
    """
    Displays all employee accounts.
    """

    users = load_users()

    if not users:
        print("\nNo employee accounts found.")
        return

    print("\n--- EMPLOYEE ACCOUNTS ---")

    for user in users:

        status = "Active" if user["active"] else "Inactive"

        print(
            f"ID: {user['user_id']} | "
            f"Username: {user['username']} | "
            f"Name: {user['first_name']} {user['last_name']} | "
            f"Role: {user['role']} | "
            f"Status: {status}"
        )