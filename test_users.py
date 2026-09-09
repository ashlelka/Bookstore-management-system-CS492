from user_management import (
    authenticate_user,
    find_user_by_username,
    load_users
)


print("\n--- USER MANAGEMENT TESTS ---")


# TEST 1: Employee accounts were created.
users = load_users()

if len(users) >= 3:
    print("PASS: Employee accounts exist.")
else:
    print("FAIL: Employee accounts were not created.")


# TEST 2: Find employee by username.
user = find_user_by_username("admin1")

if user is not None:
    print("PASS: Employee found by username.")
else:
    print("FAIL: Employee could not be found.")


# TEST 3: Correct password.
user = authenticate_user("admin1", "Admin123!")

if user is not None:
    print("PASS: Correct password authenticated.")
else:
    print("FAIL: Correct password was rejected.")


# TEST 4: Incorrect password.
user = authenticate_user("admin1", "WrongPassword123")

if user is None:
    print("PASS: Incorrect password rejected.")
else:
    print("FAIL: Incorrect password was accepted.")


# TEST 5: Unknown employee.
user = authenticate_user("doesnotexist", "Password123")

if user is None:
    print("PASS: Unknown employee rejected.")
else:
    print("FAIL: Unknown employee was authenticated.")


print("\n--- TESTING COMPLETE ---")