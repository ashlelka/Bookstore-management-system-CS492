from user_management import (
    authenticate_user,
    create_employee_account,
    find_user_by_username,
    load_users
)


print("\n--- USER MANAGEMENT TESTS ---")


# ---------------------------------------------------------
# TEST 1: Employee accounts exist
# ---------------------------------------------------------

users = load_users()

if len(users) >= 3:
    print("PASS: Employee accounts exist.")
else:
    print("FAIL: Employee accounts were not created.")


# ---------------------------------------------------------
# TEST 2: Find employee by username
# ---------------------------------------------------------

user = find_user_by_username("admin1")

if user is not None:
    print("PASS: Employee found by username.")
else:
    print("FAIL: Employee could not be found.")


# ---------------------------------------------------------
# TEST 3: Correct password
# ---------------------------------------------------------

user = authenticate_user("admin1", "Admin123!")

if user is not None:
    print("PASS: Correct password authenticated.")
else:
    print("FAIL: Correct password was rejected.")


# ---------------------------------------------------------
# TEST 4: Incorrect password
# ---------------------------------------------------------

user = authenticate_user(
    "admin1",
    "WrongPassword123"
)

if user is None:
    print("PASS: Incorrect password rejected.")
else:
    print("FAIL: Incorrect password was accepted.")


# ---------------------------------------------------------
# TEST 5: Unknown employee
# ---------------------------------------------------------

user = authenticate_user(
    "doesnotexist",
    "Password123"
)

if user is None:
    print("PASS: Unknown employee rejected.")
else:
    print("FAIL: Unknown employee was authenticated.")


# ---------------------------------------------------------
# TEST 6: Create Cashier employee account
# ---------------------------------------------------------

existing_user = find_user_by_username("testcashier")

if existing_user is None:

    success, message = create_employee_account(
        "testcashier",
        "Password123",
        "Test",
        "Employee",
        "Cashier"
    )

    if success:
        print("PASS: Cashier employee account created.")
    else:
        print(
            "FAIL: Cashier account was not created.",
            message
        )

else:
    print(
        "PASS: Test Cashier account already exists."
    )


# ---------------------------------------------------------
# TEST 7: Authenticate newly created Cashier
# ---------------------------------------------------------

user = authenticate_user(
    "testcashier",
    "Password123"
)

if user is not None:
    print(
        "PASS: Newly created Cashier authenticated."
    )
else:
    print(
        "FAIL: Newly created Cashier could not log in."
    )


# ---------------------------------------------------------
# TEST 8: Verify Cashier role
# ---------------------------------------------------------

user = find_user_by_username("testcashier")

if user is not None and user["role"] == "Cashier":
    print("PASS: New employee has Cashier role.")
else:
    print("FAIL: New employee role is incorrect.")


print("\n--- TESTING COMPLETE ---")