"""
Bookstore Management System
Sprint 2 - Security Testing

Developer: Ashley Lindamood

Description:
Tests security controls used by the Bookstore Management
System, including authentication, authorization, RBAC,
session security, account locking, password security,
and protected Flask routes.
"""

from datetime import datetime, timedelta, timezone

from sales_app import app
from user_management import (
    authenticate_user,
    load_users as load_employee_users,
    validate_password,
)
from users import (
    get_user,
    has_permission,
    ROLES,
)


print("\n--- SECURITY TESTING ---")

failed = False


def report(ok, label):
    """
    Display the result of a security test.
    """

    global failed

    if ok:
        print("PASS:", label)
    else:
        failed = True
        print("FAIL:", label)


# ---------------------------------------------------------
# FLASK TEST CLIENT
# ---------------------------------------------------------

app.config["TESTING"] = True

client = app.test_client()


def clear_session():
    """
    Remove all authentication and application
    information from the test session.
    """

    with client.session_transaction() as session:
        session.clear()


def login_as(username):
    """
    Create an authenticated test session.

    Used for authorization testing without requiring
    or modifying the employee's real password.
    """

    with client.session_transaction() as session:

        session.clear()

        session["username"] = username

        session["last_activity"] = datetime.now(
            timezone.utc
        ).isoformat()

        session["cart"] = {}


# =========================================================
# TEST 1
# Unauthenticated user cannot access POS
# =========================================================

clear_session()

response = client.get(
    "/",
    follow_redirects=False,
)

report(
    response.status_code in (302, 303),
    "Unauthenticated user is blocked from the POS.",
)


# =========================================================
# TEST 2
# Unauthenticated user is redirected to secure login
# =========================================================

location = response.headers.get(
    "Location",
    ""
)

report(
    "/login" in location,
    "Unauthenticated user is redirected to login.",
)


# =========================================================
# TEST 3
# Login page is publicly accessible
# =========================================================

response = client.get("/login")

report(
    response.status_code == 200,
    "Secure login page is publicly accessible.",
)


# =========================================================
# TEST 4
# Invalid login credentials are rejected
# =========================================================

clear_session()

response = client.post(
    "/login",
    data={
        "username": "invalid_security_user",
        "password": "WrongPassword123",
    },
    follow_redirects=True,
)

html = response.get_data(
    as_text=True
)

with client.session_transaction() as session:
    authenticated = (
        "username" in session
    )

report(
    response.status_code == 200
    and not authenticated
    and "Invalid login credentials" in html,
    "Invalid login credentials are rejected.",
)


# =========================================================
# TEST 5
# Unknown employee cannot authenticate
# =========================================================

user = authenticate_user(
    "employee_that_does_not_exist",
    "Password123"
)

report(
    user is None,
    "Unknown employee cannot authenticate.",
)


# =========================================================
# TEST 6
# Passwords are stored as hashes
# =========================================================

employee_users = load_employee_users()

hashed_passwords = True

for user in employee_users:

    password_hash = user.get(
        "password_hash",
        ""
    )

    if not password_hash:
        hashed_passwords = False
        break

report(
    hashed_passwords,
    "Employee passwords are stored as hashes.",
)


# =========================================================
# TEST 7
# Plain-text password field is not stored
# =========================================================

plain_password_found = False

for user in employee_users:

    if "password" in user:
        plain_password_found = True
        break

report(
    not plain_password_found,
    "Plain-text passwords are not stored in employee records.",
)


# =========================================================
# TEST 8
# Password minimum length is enforced
# =========================================================

valid, message = validate_password(
    "Abc123"
)

report(
    valid is False
    and "8 characters" in message,
    "Password minimum length is enforced.",
)


# =========================================================
# TEST 9
# Password uppercase requirement is enforced
# =========================================================

valid, message = validate_password(
    "password123"
)

report(
    valid is False
    and "uppercase" in message.lower(),
    "Password uppercase requirement is enforced.",
)


# =========================================================
# TEST 10
# Password lowercase requirement is enforced
# =========================================================

valid, message = validate_password(
    "PASSWORD123"
)

report(
    valid is False
    and "lowercase" in message.lower(),
    "Password lowercase requirement is enforced.",
)


# =========================================================
# TEST 11
# Password number requirement is enforced
# =========================================================

valid, message = validate_password(
    "PasswordOnly"
)

report(
    valid is False
    and "number" in message.lower(),
    "Password number requirement is enforced.",
)


# =========================================================
# TEST 12
# Valid password passes password policy
# =========================================================

valid, message = validate_password(
    "Password123"
)

report(
    valid is True,
    "Valid password passes password policy.",
)


# =========================================================
# TEST 13
# Cashier receives only POS permission
# =========================================================

cashier_permissions = ROLES.get(
    "Cashier",
    []
)

report(
    "use_pos" in cashier_permissions
    and "manage_users" not in cashier_permissions
    and "manage_suppliers" not in cashier_permissions,
    "Cashier role follows least-privilege access.",
)


# =========================================================
# TEST 14
# Cashier can use POS
# =========================================================

cashier = get_user(
    "cashier1"
)

report(
    cashier is not None
    and has_permission(
        cashier,
        "use_pos"
    ),
    "Cashier has permission to use the POS.",
)


# =========================================================
# TEST 15
# Cashier cannot manage users
# =========================================================

report(
    cashier is not None
    and not has_permission(
        cashier,
        "manage_users"
    ),
    "Cashier cannot manage employee accounts.",
)


# =========================================================
# TEST 16
# Cashier cannot manage suppliers
# =========================================================

report(
    cashier is not None
    and not has_permission(
        cashier,
        "manage_suppliers"
    ),
    "Cashier cannot manage suppliers.",
)


# =========================================================
# TEST 17
# Direct URL access to customer management is blocked
# =========================================================

login_as("cashier1")

response = client.get(
    "/customers",
    follow_redirects=False,
)

report(
    response.status_code == 403,
    "Cashier cannot bypass customer security using a direct URL.",
)


# =========================================================
# TEST 18
# Direct URL access to financial dashboard is blocked
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
    "Cashier cannot access the financial dashboard.",
)


# =========================================================
# TEST 19
# Direct URL access to user management is blocked
# =========================================================

response = client.get(
    "/users",
    follow_redirects=False,
)

report(
    response.status_code in (
        302,
        303,
        403,
    ),
    "Cashier cannot access user management.",
)


# =========================================================
# TEST 20
# Direct URL access to supplier management is blocked
# =========================================================

response = client.get(
    "/suppliers",
    follow_redirects=False,
)

report(
    response.status_code in (
        302,
        303,
        403,
    ),
    "Cashier cannot access supplier management.",
)


# =========================================================
# TEST 21
# Admin can access user management
# =========================================================

login_as("admin1")

response = client.get(
    "/users",
    follow_redirects=False,
)

report(
    response.status_code == 200,
    "Admin can access authorized user management.",
)


# =========================================================
# TEST 22
# Admin can access supplier management
# =========================================================

response = client.get(
    "/suppliers",
    follow_redirects=False,
)

report(
    response.status_code == 200,
    "Admin can access authorized supplier management.",
)


# =========================================================
# TEST 23
# Admin can access financial dashboard
# =========================================================

response = client.get(
    "/financial-dashboard",
    follow_redirects=False,
)

report(
    response.status_code == 200,
    "Admin can access authorized financial information.",
)


# =========================================================
# TEST 24
# Session cookie uses HttpOnly
# =========================================================

report(
    app.config.get(
        "SESSION_COOKIE_HTTPONLY"
    ) is True,
    "Session cookie is configured as HttpOnly.",
)


# =========================================================
# TEST 25
# Session cookie uses SameSite protection
# =========================================================

report(
    app.config.get(
        "SESSION_COOKIE_SAMESITE"
    ) == "Lax",
    "Session cookie uses SameSite=Lax protection.",
)


# =========================================================
# TEST 26
# Session lifetime is limited
# =========================================================

expected_timeout = timedelta(
    minutes=5
)

report(
    app.config.get(
        "PERMANENT_SESSION_LIFETIME"
    ) == expected_timeout,
    "Authenticated session lifetime is limited to five minutes.",
)


# =========================================================
# TEST 27
# Inactive session is terminated
# =========================================================

login_as("cashier1")

old_activity = (
    datetime.now(timezone.utc)
    - timedelta(minutes=6)
)

with client.session_transaction() as session:

    session["last_activity"] = (
        old_activity.isoformat()
    )


response = client.get(
    "/",
    follow_redirects=False,
)

with client.session_transaction() as session:

    still_authenticated = (
        "username" in session
    )


report(
    response.status_code in (
        302,
        303,
    )
    and not still_authenticated,
    "Inactive employee session is terminated after timeout.",
)


# =========================================================
# TEST 28
# Logout clears authenticated session
# =========================================================

login_as("cashier1")

response = client.get(
    "/logout",
    follow_redirects=False,
)

with client.session_transaction() as session:

    still_authenticated = (
        "username" in session
    )


report(
    response.status_code in (
        302,
        303,
    )
    and not still_authenticated,
    "Logout clears the authenticated employee session.",
)


# =========================================================
# TEST 29
# Locked user has no effective permissions
# =========================================================

locked_test_user = {
    "username": "security_test_locked",
    "role": "Admin",
    "permissions": [
        "use_pos",
        "manage_users",
        "manage_suppliers",
    ],
    "locked": True,
}

report(
    not has_permission(
        locked_test_user,
        "use_pos"
    )
    and not has_permission(
        locked_test_user,
        "manage_users"
    ),
    "Locked accounts receive no effective permissions.",
)


# =========================================================
# TEST 30
# Unknown permission is denied
# =========================================================

admin = get_user(
    "admin1"
)

report(
    admin is not None
    and not has_permission(
        admin,
        "security_permission_that_does_not_exist"
    ),
    "Undefined permissions are denied.",
)


# =========================================================
# TEST 31
# Login response does not expose password hash
# =========================================================

clear_session()

response = client.get(
    "/login"
)

html = response.get_data(
    as_text=True
)

hash_exposed = False

for user in employee_users:

    password_hash = user.get(
        "password_hash"
    )

    if (
        password_hash
        and password_hash in html
    ):
        hash_exposed = True
        break


report(
    not hash_exposed,
    "Login page does not expose employee password hashes.",
)


# =========================================================
# TEST 32
# Application remains protected after security tests
# =========================================================

clear_session()

response = client.get(
    "/",
    follow_redirects=False,
)

report(
    response.status_code in (
        302,
        303,
    ),
    "Application remains protected after security testing.",
)


# =========================================================
# CLEAN TEST SESSION
# =========================================================

clear_session()


# =========================================================
# FINAL RESULT
# =========================================================

print()

if failed:

    print(
        "Security testing completed "
        "with failures."
    )

    raise SystemExit(1)


print(
    "All security tests passed."
)