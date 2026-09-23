"""
Bookstore Management System
Sprint 2 - T2-007 / T2-011

Financial Dashboard Integration Tests

Original Financial Dashboard:
Gregory Krautkremer

Flask Integration and Testing:
Ashley Lindamood
"""

from sales_app import app


# ---------------------------------------------------------
# Test reporting helper
# ---------------------------------------------------------

failures = []


def report(condition, message):

    if condition:
        print("PASS:", message)

    else:
        print("FAIL:", message)
        failures.append(message)


# ---------------------------------------------------------
# Create Flask test client
# ---------------------------------------------------------

app.config["TESTING"] = True

client = app.test_client()


print()
print("FINANCIAL DASHBOARD INTEGRATION TESTS")


# =========================================================
# TEST 1
# User must be logged in to view dashboard.
# =========================================================

response = client.get(
    "/financial-dashboard",
    follow_redirects=False,
)

report(
    response.status_code in (301, 302),
    "Unauthenticated user is redirected from "
    "the financial dashboard.",
)


# =========================================================
# TEST 2
# Admin can view financial dashboard.
# =========================================================

with client.session_transaction() as session:

    session["username"] = "admin1"
    session["role"] = "Admin"


response = client.get(
    "/financial-dashboard",
)

report(
    response.status_code == 200,
    "Admin can open the financial dashboard.",
)


# =========================================================
# TEST 3
# Dashboard contains financial overview.
# =========================================================

page = response.get_data(
    as_text=True
)

report(
    "Financial Overview" in page
    and "Total Revenue" in page
    and "Total Expenses" in page
    and "Total Profit" in page,
    "Financial dashboard displays "
    "revenue, expenses, and profit.",
)


# =========================================================
# TEST 4
# Dashboard displays completed sales.
# =========================================================

report(
    "Completed Sales" in page,
    "Financial dashboard displays "
    "completed sales.",
)


# =========================================================
# TEST 5
# Financial performance chart endpoint works.
# =========================================================

response = client.get(
    "/financial-dashboard/chart",
)

report(
    response.status_code == 200
    and response.content_type == "image/png",
    "Revenue, expenses, and profit chart "
    "is generated successfully.",
)


# =========================================================
# TEST 6
# Profit by Sale chart endpoint works.
# =========================================================

response = client.get(
    "/financial-dashboard/profit-chart",
)

report(
    response.status_code == 200
    and response.content_type == "image/png",
    "Profit by Sale chart is generated "
    "successfully.",
)


# =========================================================
# TEST 7
# CSV export endpoint works.
# =========================================================

response = client.get(
    "/financial-dashboard/export",
)

csv_data = response.get_data(
    as_text=True
)

report(
    response.status_code == 200
    and "text/csv" in response.content_type
    and "Date" in csv_data
    and "Transaction ID" in csv_data
    and "Revenue" in csv_data
    and "Expenses" in csv_data
    and "Profit" in csv_data,
    "Financial data can be exported "
    "as a CSV file.",
)


# =========================================================
# TEST 8
# CSV response provides download filename.
# =========================================================

content_disposition = response.headers.get(
    "Content-Disposition",
    "",
)

report(
    "financial_data.csv"
    in content_disposition,
    "CSV export uses the correct "
    "financial_data.csv filename.",
)


# =========================================================
# TEST 9
# Cashier cannot access financial dashboard.
# =========================================================

with client.session_transaction() as session:

    session.clear()
    session["username"] = "cashier1"
    session["role"] = "Cashier"


response = client.get(
    "/financial-dashboard",
    follow_redirects=False,
)

report(
    response.status_code in (301, 302),
    "Cashier is blocked from the "
    "financial dashboard.",
)


# =========================================================
# TEST 10
# Cashier cannot access financial chart.
# =========================================================

response = client.get(
    "/financial-dashboard/chart",
    follow_redirects=False,
)

report(
    response.status_code in (301, 302),
    "Cashier is blocked from the "
    "financial performance chart.",
)


# =========================================================
# TEST 11
# Cashier cannot access Profit by Sale chart.
# =========================================================

response = client.get(
    "/financial-dashboard/profit-chart",
    follow_redirects=False,
)

report(
    response.status_code in (301, 302),
    "Cashier is blocked from the "
    "Profit by Sale chart.",
)


# =========================================================
# TEST 12
# Cashier cannot export financial data.
# =========================================================

response = client.get(
    "/financial-dashboard/export",
    follow_redirects=False,
)

report(
    response.status_code in (301, 302),
    "Cashier is blocked from exporting "
    "financial data.",
)


# =========================================================
# Final Results
# =========================================================

print()

if failures:

    print(
        "T2-007 financial dashboard "
        "integration tests failed."
    )

    print()

    for failure in failures:
        print("-", failure)

    raise SystemExit(1)

else:

    print(
        "T2-007 financial dashboard "
        "integration tests passed."
    )