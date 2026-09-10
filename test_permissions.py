from users import (
    assign_role,
    get_user,
    has_permission,
    load_users
)


print("\n--- PERMISSION TESTS ---")


# ---------------------------------------------------------
# TEST 1: Load users
# ---------------------------------------------------------

users = load_users()

if len(users) > 0:
    print("PASS: Users loaded into permission system.")
else:
    print("FAIL: No users were loaded.")


# ---------------------------------------------------------
# TEST 2: Find Admin account
# ---------------------------------------------------------

admin_user = get_user("admin1")

if admin_user is not None:
    print("PASS: Admin account found.")
else:
    print("FAIL: Admin account was not found.")


# ---------------------------------------------------------
# TEST 3: Admin can use POS
# ---------------------------------------------------------

if admin_user is not None and has_permission(
    admin_user,
    "use_pos"
):
    print("PASS: Admin has POS permission.")
else:
    print("FAIL: Admin does not have POS permission.")


# ---------------------------------------------------------
# TEST 4: Admin can manage users
# ---------------------------------------------------------

if admin_user is not None and has_permission(
    admin_user,
    "manage_users"
):
    print("PASS: Admin can manage users.")
else:
    print("FAIL: Admin cannot manage users.")


# ---------------------------------------------------------
# TEST 5: Find Cashier account
# ---------------------------------------------------------

cashier_user = get_user("testcashier")

if cashier_user is not None:
    print("PASS: Cashier account found.")
else:
    print("FAIL: Cashier account was not found.")


# ---------------------------------------------------------
# TEST 6: Cashier can use POS
# ---------------------------------------------------------

if cashier_user is not None and has_permission(
    cashier_user,
    "use_pos"
):
    print("PASS: Cashier has POS permission.")
else:
    print("FAIL: Cashier does not have POS permission.")


# ---------------------------------------------------------
# TEST 7: Cashier cannot manage users
# ---------------------------------------------------------

if cashier_user is not None and not has_permission(
    cashier_user,
    "manage_users"
):
    print("PASS: Cashier is correctly blocked from user management.")
else:
    print("FAIL: Cashier incorrectly has user-management permission.")


# ---------------------------------------------------------
# TEST 8: Verify Cashier role
# ---------------------------------------------------------

if (
    cashier_user is not None
    and cashier_user.get("role") == "Cashier"
):
    print("PASS: Test employee has Cashier role.")
else:
    print("FAIL: Test employee does not have Cashier role.")


# ---------------------------------------------------------
# TEST 9: Temporarily assign Manager role
# ---------------------------------------------------------

if cashier_user is not None:

    assign_role(
        "testcashier",
        "Manager"
    )

    load_users()

    manager_user = get_user("testcashier")

    if (
        manager_user is not None
        and manager_user.get("role") == "Manager"
    ):
        print("PASS: Employee role changed to Manager.")
    else:
        print("FAIL: Employee role was not changed to Manager.")


# ---------------------------------------------------------
# TEST 10: Manager can manage users
# ---------------------------------------------------------

manager_user = get_user("testcashier")

if (
    manager_user is not None
    and has_permission(
        manager_user,
        "manage_users"
    )
):
    print("PASS: Manager has user-management permission.")
else:
    print("FAIL: Manager does not have user-management permission.")


# ---------------------------------------------------------
# RESTORE TEST USER TO CASHIER
# ---------------------------------------------------------

assign_role(
    "testcashier",
    "Cashier"
)

load_users()

cashier_user = get_user("testcashier")

if (
    cashier_user is not None
    and cashier_user.get("role") == "Cashier"
):
    print("PASS: Test employee restored to Cashier role.")
else:
    print("FAIL: Test employee was not restored to Cashier.")


print("\n--- PERMISSION TESTING COMPLETE ---")