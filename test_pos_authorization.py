"""
Bookstore Management System
POS Authorization Tests

Tests the POS authorization controls without modifying
real employee roles or permissions.
"""

from unittest.mock import patch

from sales_app import app


print("\n--- POS AUTHORIZATION TESTS ---")

app.config["TESTING"] = True

client = app.test_client()


# ---------------------------------------------------------
# TEST 1: Restricted employee sees POS warning
# ---------------------------------------------------------

with patch(
    "sales_app.can_use_pos",
    return_value=False
):

    with client.session_transaction() as test_session:
        test_session["username"] = "testcashier"

    response = client.get(
        "/",
        follow_redirects=True
    )

    page = response.get_data(
        as_text=True
    )

    if (
        response.status_code == 200
        and
        "This account cannot use the register."
        in page
    ):
        print(
            "PASS: Restricted employee sees POS warning."
        )
    else:
        print(
            "FAIL: POS restriction warning was not displayed."
        )


# ---------------------------------------------------------
# TEST 2: Product buttons are disabled
# ---------------------------------------------------------

with patch(
    "sales_app.can_use_pos",
    return_value=False
):

    with client.session_transaction() as test_session:
        test_session["username"] = "testcashier"

    response = client.get(
        "/",
        follow_redirects=True
    )

    page = response.get_data(
        as_text=True
    )

    if (
        'class="tile"' in page
        and
        "disabled" in page
    ):
        print(
            "PASS: Product buttons are disabled "
            "without POS permission."
        )
    else:
        print(
            "FAIL: Product buttons were not disabled."
        )


# ---------------------------------------------------------
# TEST 3: Restricted employee cannot add a book
# ---------------------------------------------------------

with patch(
    "sales_app.can_use_pos",
    return_value=False
):

    with client.session_transaction() as test_session:
        test_session["username"] = "testcashier"
        test_session["cart"] = {}

    response = client.post(
        "/add/1",
        follow_redirects=False
    )

    with client.session_transaction() as test_session:
        test_cart = test_session.get(
            "cart",
            {}
        )

    if (
        response.status_code in (302, 303)
        and
        not test_cart
    ):
        print(
            "PASS: Restricted employee cannot add books."
        )
    else:
        print(
            "FAIL: Restricted employee added a book."
        )


# ---------------------------------------------------------
# TEST 4: Restricted employee cannot checkout
# ---------------------------------------------------------

with patch(
    "sales_app.can_use_pos",
    return_value=False
):

    with client.session_transaction() as test_session:
        test_session["username"] = "testcashier"

    response = client.post(
        "/checkout",
        follow_redirects=False
    )

    redirect_location = response.headers.get(
        "Location",
        ""
    )

    if (
        response.status_code in (302, 303)
        and
        (
            redirect_location == "/"
            or
            redirect_location.startswith("/?")
        )
    ):
        print(
            "PASS: Restricted employee is blocked "
            "from checkout."
        )
    else:
        print(
            "FAIL: Restricted employee was not "
            "blocked from checkout."
        )

        print(
            "Redirect location:",
            redirect_location
        )


# ---------------------------------------------------------
# TEST 5: Authorized Cashier still has POS permission
# ---------------------------------------------------------

with patch(
    "sales_app.can_use_pos",
    return_value=True
):

    with client.session_transaction() as test_session:
        test_session["username"] = "testcashier"

    response = client.get(
        "/",
        follow_redirects=True
    )

    page = response.get_data(
        as_text=True
    )

    if (
        response.status_code == 200
        and
        "This account cannot use the register."
        not in page
    ):
        print(
            "PASS: Authorized employee does not "
            "see POS restriction warning."
        )
    else:
        print(
            "FAIL: Authorized employee incorrectly "
            "sees POS restriction warning."
        )


print("\n--- POS AUTHORIZATION TESTING COMPLETE ---")