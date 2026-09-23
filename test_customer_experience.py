"""
Bookstore Management System
Sprint 2 - T2-005

Customer Experience Testing:
- Improved book search
- Improved catalog navigation
"""

from sales_app import app


print("\n--- CUSTOMER EXPERIENCE TESTS (T2-005) ---")

failed = False


def report(ok, label):
    """Print the result of each T2-005 test."""
    global failed

    if ok:
        print("PASS:", label)
    else:
        failed = True
        print("FAIL:", label)


# ---------------------------------------------------------
# Create test client and log in as an authorized POS user
# ---------------------------------------------------------

app.config["TESTING"] = True

client = app.test_client()

with client.session_transaction() as session:
    session["username"] = "admin1"


# ---------------------------------------------------------
# Test 1 - POS catalog is available
# ---------------------------------------------------------

page = client.get("/")

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "The Great Gatsby" in html,
    "POS catalog displays available books.",
)


# ---------------------------------------------------------
# Test 2 - Search by book title
# ---------------------------------------------------------

page = client.get(
    "/?search=Gatsby"
)

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "The Great Gatsby" in html
    and "The Hobbit" not in html,
    "Search finds a book by title.",
)


# ---------------------------------------------------------
# Test 3 - Search by author
# ---------------------------------------------------------

page = client.get(
    "/?search=Harper+Lee"
)

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "To Kill a Mockingbird" in html,
    "Search finds a book by author.",
)


# ---------------------------------------------------------
# Test 4 - Search by ISBN
# ---------------------------------------------------------

page = client.get(
    "/?search=9780547928227"
)

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "The Hobbit" in html,
    "Search finds a book by ISBN.",
)


# ---------------------------------------------------------
# Test 5 - Search is case insensitive
# ---------------------------------------------------------

page = client.get(
    "/?search=gatsby"
)

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "The Great Gatsby" in html,
    "Book search is case insensitive.",
)


# ---------------------------------------------------------
# Test 6 - Partial search works
# ---------------------------------------------------------

page = client.get(
    "/?search=Guthix"
)

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "The Gift of Guthix" in html,
    "Partial book title search works.",
)


# ---------------------------------------------------------
# Test 7 - Author search can return multiple books
# ---------------------------------------------------------

page = client.get(
    "/?search=T.S.+Church"
)

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "Betrayal at Falador" in html
    and "Return to Canifis" in html
    and "Legacy of Blood" in html,
    "Author search returns multiple matching books.",
)


# ---------------------------------------------------------
# Test 8 - Unknown search gives customer feedback
# ---------------------------------------------------------

page = client.get(
    "/?search=zzzzzzzz"
)

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "No books found matching" in html,
    "Unknown search displays a no-results message.",
)


# ---------------------------------------------------------
# Test 9 - Category navigation filters catalog
# ---------------------------------------------------------

page = client.get(
    "/?cat=Fantasy"
)

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "The Hobbit" in html
    and "Betrayal at Falador" in html
    and "Return to Canifis" in html,
    "Category navigation filters the book catalog.",
)

# ---------------------------------------------------------
# Test 10 - Search and category work together
# ---------------------------------------------------------

page = client.get(
    "/?cat=Fantasy&search=Church"
)

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "Betrayal at Falador" in html
    and "Return to Canifis" in html
    and "Legacy of Blood" in html
    and "The Hobbit" not in html,
    "Search works together with category navigation.",
)


# ---------------------------------------------------------
# Test 11 - Improved navigation is displayed
# ---------------------------------------------------------

page = client.get("/")

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "All Books" in html
    and "Fiction" in html
    and "Fantasy" in html
    and "Technology" in html,
    "Improved category navigation is displayed.",
)


# ---------------------------------------------------------
# Test 12 - Search controls are displayed
# ---------------------------------------------------------

report(
    page.status_code == 200
    and "Search Books" in html
    and 'name="search"' in html
    and "Title, author, or ISBN" in html,
    "Improved book search controls are displayed.",
)


# ---------------------------------------------------------
# Test 13 - Clear Search is available during a search
# ---------------------------------------------------------

page = client.get(
    "/?cat=Fantasy&search=Church"
)

html = page.get_data(as_text=True)

report(
    page.status_code == 200
    and "Clear Search" in html,
    "Clear Search navigation is available during a search.",
)


# ---------------------------------------------------------
# Final Test Result
# ---------------------------------------------------------

if failed:
    raise SystemExit(1)

print("T2-005 customer experience tests passed.")