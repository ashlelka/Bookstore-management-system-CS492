from copy import deepcopy
from datetime import datetime
from http import server

from email.message import EmailMessage
import os
import io
import csv
import matplotlib 
matplotlib.use("Agg")
from matplotlib import dates
import matplotlib.pyplot as plt

import smtplib
from pathlib import Path
from securelogin import auth_bp
from flask import Flask, redirect, render_template, request, session, url_for, Response, send_file
from datetime import datetime, timedelta, timezone
from tax_rates import STATES, STATES_BY_CODE, load_tax_rates, state_rate

from inventory import (
    decrement_quantities,
    load_books,
    save_books,
    get_reorder_threshold,
    get_low_stock_books
)
from user_management import authenticate_user
from database import (
    record_sale,
    load_sales,
    connection_status
)
from suppliers import add_supplier, load_suppliers
from purchase_orders import (
    create_purchase_order,
    find_purchase_order,
    load_purchase_orders,
    update_purchase_order_status,
)
from users import (
    PERMISSIONS,
    ROLES,
    USERS,
    assign_role,
    get_user,
    has_permission,
    load_users,
    set_locked,
    set_permissions,
)
app = Flask(__name__, static_folder="Static")
app.secret_key = "bookstore-pos-dev"
# T1-008 Session Security
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.register_blueprint(auth_bp)

APP_DIR = Path(__file__).resolve().parent

products = []
sale_counter = 1042


def as_product(book):
    """Map Ashley's inventory record (T1-001 / T1-003) onto the POS tile/cart shape."""
    return {
        "id": str(book["book_id"]),
        "name": book["title"],
        "author": book.get("author", ""),
        "isbn": book.get("isbn", ""),
        "location": book.get("location", ""),
        "price": book["price"],
        "category": book.get("category") or "Uncategorized",
        "stock": book.get("quantity"),
        "exempt": bool(book.get("exempt")),
    }

def as_product(book):
    """Map inventory records onto the POS tile/cart shape."""

    return {
        "id": str(book["book_id"]),
        "name": book["title"],
        "author": book.get("author", ""),
        "isbn": book.get("isbn", ""),
        "location": book.get("location", ""),
        "price": book["price"],
        "category": book.get("category") or "Uncategorized",
        "stock": book.get("quantity"),
        "reorder_threshold": get_reorder_threshold(book),
        "exempt": bool(book.get("exempt")),
    }

def load_products():
    global products
    products = [as_product(book) for book in load_books()]


def money(n):
    return f"${n:,.2f}"


def cart():
    return session.setdefault("cart", {})


def product_by_id(pid):
    pid = str(pid)
    return next((p for p in products if str(p["id"]) == pid), None)


def qty_in_cart(pid):
    entry = cart().get(str(pid))
    return int(entry) if entry else 0


def stock_left(product):
    if not isinstance(product.get("stock"), (int, float)):
        return None
    return product["stock"] - qty_in_cart(product["id"])


def cart_lines():
    lines = []
    for pid, qty in cart().items():
        product = product_by_id(pid)
        if not product:
            continue
        qty = int(qty)
        lines.append({
            "id": pid,
            "product": product,
            "qty": qty,
            "line_total": product["price"] * qty,
        })
    return lines
def format_receipt_date(timestamp):
    """Format a stored sale timestamp for receipt history."""

    if not timestamp:
        return ""

    try:
        sale_date = datetime.fromisoformat(timestamp)

        return sale_date.strftime(
            "%b %d, %Y %I:%M %p"
        )

    except (ValueError, TypeError):
        return timestamp

def item_count():
    return sum(int(qty) for qty in cart().values())


# T1-006: sales tax (state lookup in tax_rates.json)

def calc_totals(tax_rate):
    subtotal = exempt_amt = taxable_amt = 0
    for line in cart_lines():
        if line["product"].get("exempt"):
            exempt_amt += line["line_total"]
        else:
            taxable_amt += line["line_total"]
        subtotal += line["line_total"]
    tax = taxable_amt * (tax_rate / 100)
    return {
        "subtotal": subtotal,
        "exemptAmt": exempt_amt,
        "taxableAmt": taxable_amt,
        "tax": tax,
        "total": subtotal + tax,
        "taxRate": tax_rate,
    }


def selected_state():
    code = session.get("tax_state")
    return STATES_BY_CODE.get(code)


def tax_rate():
    state = selected_state()
    return state["rate"] if state else 0.0


def format_rate(rate):
    return f"{rate:g}"


# T1-007: receipt text

def generate_receipt(sale):
    lines = [
        "BOOKSTORE MANAGEMENT SYSTEM",
        sale["id"],
        datetime.fromisoformat(sale["timestamp"]).strftime("%c"),
        "-" * 40,
    ]
    for item in sale["items"]:
        extra = "  (tax-exempt)" if item["exempt"] else ""
        lines.append(f"{item['qty']} x {item['name']}")
        lines.append(f"    {money(item['unitPrice'])} each{extra}   {money(item['lineTotal'])}")
    lines += [
        "-" * 40,
        f"{'Subtotal':<24}{money(sale['subtotal'])}",
        f"{sale.get('taxLabel', 'Sales tax'):<24}{money(sale['tax'])}",
        f"{'TOTAL':<24}{money(sale['total'])}",
        "-" * 40,
        "Thank you for shopping with us.",
    ]
    return "\n".join(lines)

# T2-008 - Generate receipt from stored sales history
def generate_historical_receipt(sale):

    sale_id = sale.get(
        "sale_id",
        sale.get("id", "Receipt")
    )

    timestamp = sale.get(
        "date",
        sale.get(
            "datetime",
            sale.get("timestamp", "")
        )
    )

    lines = [
        "BOOKSTORE MANAGEMENT SYSTEM",
        str(sale_id),
        format_receipt_date(timestamp),
        "-" * 40,
    ]
    
    # Display stored sale items when available.
    items = sale.get("items", [])

    for item in items:

        name = item.get(
            "name",
            item.get("title", "Book")
        )

        qty = item.get(
            "qty",
            item.get("quantity", 1)
        )

        unit_price = item.get(
            "unitPrice",
            item.get("unit_price", item.get("price", 0))
        )

        line_total = item.get(
            "lineTotal",
            item.get("line_total", unit_price * qty)
        )

        lines.append(
            f"{qty} x {name}"
        )

        lines.append(
            f"    {money(float(unit_price))} each"
            f"   {money(float(line_total))}"
        )

    lines.append("-" * 40)

    subtotal = float(
        sale.get("subtotal", 0)
    )

    tax = float(
        sale.get("tax", 0)
    )

    total = float(
        sale.get("total", 0)
    )

    lines.extend([
        f"{'Subtotal':<24}{money(subtotal)}",
        f"{'Sales tax':<24}{money(tax)}",
        f"{'TOTAL':<24}{money(total)}",
        "-" * 40,
        "Thank you for shopping with us.",
    ])
    return "\n".join(lines)
    # T2-008 - Email Receipt
def send_receipt_email(customer_email, receipt_text, sale_id):
    """
    Email a completed bookstore receipt to the customer.
    Email credentials are loaded from environment variables
    so passwords are not stored in the source code.
    """

    sender_email = os.environ.get("BMS_EMAIL")
    sender_password = os.environ.get("BMS_EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        return False, "Email service is not configured."

    message = EmailMessage()

    message["Subject"] = (
        f"Ana's Anomalous Anthologies Receipt - {sale_id}"
    )

    message["From"] = sender_email
    message["To"] = customer_email

    message.set_content(
        "Thank you for shopping with "
        "Ana's Anomalous Anthologies!\n\n"
        + receipt_text
    )

    try:
        with smtplib.SMTP_SSL(
        "smtp.mail.yahoo.com",
            465,
                timeout=20
        ) as server:
            
            server.login(
                sender_email,
                sender_password
            )

            server.send_message(message)

        return True, "Receipt emailed successfully."

    except Exception as error:
        print("Receipt email error:", error)

        return False, "Unable to send receipt."
    return "\n".join(lines)
def update_inventory(sale_items):
    # T1-007: after checkout, decrement stock through inventory module (T1-003).
    results = decrement_quantities(sale_items)
    load_products()
    return results


def build_sale():
    global sale_counter
    lines = cart_lines()
    if not lines:
        return None
    state = selected_state()
    if not state:
        return None
    totals = calc_totals(state["rate"])
    sale = {
        "id": f"SALE-{sale_counter}",
        "items": [
            {
                "productId": line["id"],
                "name": line["product"]["name"],
                "qty": line["qty"],
                "unitPrice": line["product"]["price"],
                "lineTotal": line["line_total"],
                "exempt": bool(line["product"].get("exempt")),
            }
            for line in lines
        ],
        **totals,
        "taxState": state["code"],
        "taxStateName": state["name"],
        "taxLabel": f"{state['code']} tax ({format_rate(state['rate'])}%)",
        "timestamp": datetime.now().isoformat(),
    }
    sale_counter += 1
    sale["inventoryResults"] = update_inventory(sale["items"])
    sale["receipt"] = generate_receipt(sale)
    return sale


def categories():
    seen = []
    for product in products:
        cat = product.get("category") or "Uncategorized"
        if cat not in seen:
            seen.append(cat)
    return ["All"] + seen


def visible_products(active):
    if active == "All":
        return products
    return [p for p in products if p.get("category") == active]


def redirect_home():
    cat = request.form.get("cat") or request.args.get("cat") or "All"
    return redirect(url_for("index", cat=cat))


# T1-010: current staff member

def current_user():
    return get_user(session.get("username"))


def can_use_pos():
    return has_permission(current_user(), "use_pos")


def can_manage_users():
    return has_permission(current_user(), "manage_users")


def can_manage_suppliers():
    return has_permission(current_user(), "manage_suppliers")

# T1-008 - Employee inactivity timeout
SESSION_TIMEOUT_MINUTES = 5


@app.before_request
def session_timeout():
    """
    Log out an authenticated employee after
    five minutes without activity.
    """

    if "username" not in session:
        return

    now = datetime.now(timezone.utc)

    last_activity = session.get("last_activity")

    if last_activity:
        last_activity = datetime.fromisoformat(last_activity)

        inactive_time = now - last_activity

        if inactive_time > timedelta(
            minutes=SESSION_TIMEOUT_MINUTES
        ):
            session.clear()

            return redirect(url_for("auth.login"))

    # Update activity time for the current request.
    session["last_activity"] = now.isoformat()
@app.context_processor
def inject_staff():
    user = current_user()
    return {
        "current_user": user,
        "can_use_pos": can_use_pos(),
        "can_manage_users": can_manage_users(),
        "can_manage_suppliers": can_manage_suppliers(),
    }


@app.before_request
def require_staff():
    # Allow Greg's authentication Blueprint pages to open without
    # already being signed in.
    public_endpoints = {
        None,
        "static",
        "signin",          # Keep Alexis's original sign-in route available
        "auth.login",
        "auth.register",
        "auth.dashboard",
        "auth.logout",
    }

    if request.endpoint in public_endpoints:
        return

    load_users()

    # If the visitor is not signed in, send them to Greg's secure login page.
    if not current_user():
        return redirect(url_for("auth.login"))

# =========================================================
# T2-007 - Financial Dashboard
# Developer: Gregory Krautkremer
# Flask Integration
# =========================================================

@app.get("/financial-dashboard")
def financial_dashboard():

    # user must be logged in
    if "username" not in session:
        return redirect(url_for("auth.login"))

    # only Admin and Manager can view financial information
    if not can_manage_users():
        return redirect(url_for("index"))

    # load completed sales from existing BMS database
    sales = load_sales()

    financial_records = []

    for sale in sales:

        sale_date = sale.get(
            "date",
            sale.get(
                "datetime",
                sale.get(
                    "timestamp",
                    "Unknown"
                )
            )
        )

        revenue = sale.get("total", 0)

        try:
            revenue = float(revenue)
        except (TypeError, ValueError):
            revenue = 0.0

        # expenses are not currently stored in BMS
        expenses = 0.0
        profit = revenue - expenses

        financial_records.append({
            "date": sale_date,
            "sale_id": sale.get(
                "sale_id",
                sale.get("id", "")
            ),
            "revenue": round(revenue, 2),
            "expenses": round(expenses, 2),
            "profit": round(profit, 2),
        })

    total_revenue = sum(
        record["revenue"]
        for record in financial_records
    )

    total_expenses = sum(
        record["expenses"]
        for record in financial_records
    )

    total_profit = sum(
        record["profit"]
        for record in financial_records
    )

    return render_template(
        "financial_dashboard.html",
        records=financial_records,
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        total_profit=total_profit,
    )
# =========================================================
# T2-007 - Financial Dashboard Chart
# Developer: Gregory Krautkremer
# Integrated into Flask by Ashley Lindamood
# =========================================================

@app.get("/financial-dashboard/chart")
def financial_dashboard_chart():

    # user must be logged in
    if "username" not in session:
        return redirect(url_for("auth.login"))

    # only Admin and Manager can view financial information
    if not can_manage_users():
        return redirect(url_for("index"))

    sales = load_sales()

    dates = []
    revenues = []
    expenses = []
    profits = []

    for sale in sales:

        # Get sale date from existing sales record
        sale_date = sale.get(
            "date",
            sale.get(
                "datetime",
                sale.get(
                    "timestamp",
                    "Unknown"
                )
            )
        )

        # Get sale revenue
        revenue = sale.get("total", 0)

        try:
            revenue = float(revenue)
        except (TypeError, ValueError):
            revenue = 0.0

        expense = 0.0
        profit = revenue - expense

        # Format date for chart display
        try:
            parsed_date = datetime.fromisoformat(
                str(sale_date)
            )

            formatted_date = parsed_date.strftime(
                "%b %d, %I:%M %p"
            )

        except (ValueError, TypeError):
            formatted_date = str(sale_date)

        # IMPORTANT:
        # These must stay INSIDE the for-sale loop.
        dates.append(formatted_date)
        revenues.append(revenue)
        expenses.append(expense)
        profits.append(profit)

    # Create Greg's financial performance chart
    fig, ax = plt.subplots(
        figsize=(10, 5)
    )

    ax.plot(
        dates,
        revenues,
        label="Revenue",
        marker="o"
    )

    ax.plot(
        dates,
        expenses,
        label="Expenses",
        marker="s"
    )

    ax.plot(
        dates,
        profits,
        label="Profit",
        marker="^"
    )

    ax.set_xlabel("Sale Date")
    ax.set_ylabel("Amount ($)")

    ax.set_title(
        "Financial Performance Over Time"
    )

    ax.legend()

    plt.xticks(
        rotation=20,
        ha="right"
    )

    plt.tight_layout()

    # Save chart to memory for Flask
    image = io.BytesIO()

    fig.savefig(
        image,
        format="png"
    )

    plt.close(fig)

    image.seek(0)

    return send_file(
        image,
        mimetype="image/png"
    )
# =========================================================
# T2-007 - Profit by Sale Chart
# Developer: Gregory Krautkremer
# Integrated into Flask by Ashley Lindamood
# =========================================================

@app.get("/financial-dashboard/profit-chart")
def financial_profit_chart():

    # user must be logged in
    if "username" not in session:
        return redirect(url_for("auth.login"))

    # only Admin and Manager can view financial information
    if not can_manage_users():
        return redirect(url_for("index"))

    sales = load_sales()

    sale_labels = []
    profits = []

    for sale in sales:

        # Get sale ID
        sale_id = sale.get(
            "sale_id",
            sale.get("id", "Unknown")
        )

        # Get sale date
        sale_date = sale.get(
            "date",
            sale.get(
                "datetime",
                sale.get(
                    "timestamp",
                    "Unknown"
                )
            )
        )

        # Format sale date
        try:
            parsed_date = datetime.fromisoformat(
                str(sale_date)
            )

            formatted_date = parsed_date.strftime(
                "%b %d, %I:%M %p"
            )

        except (ValueError, TypeError):
            formatted_date = str(sale_date)

        # Get revenue
        revenue = sale.get("total", 0)

        try:
            revenue = float(revenue)
        except (TypeError, ValueError):
            revenue = 0.0

        # Expenses are not currently stored
        expenses = 0.0
        profit = revenue - expenses

        # Sale ID + date keeps duplicate IDs distinguishable
        sale_labels.append(
            str(sale_id)
            + "\n"
            + formatted_date
        )

        profits.append(profit)

    # Create Profit by Sale chart
    fig, ax = plt.subplots(
        figsize=(10, 5)
    )

    ax.bar(
        sale_labels,
        profits
    )

    ax.set_xlabel("Sale")
    ax.set_ylabel("Profit ($)")
    ax.set_title("Profit by Sale")

    # Display dollar amount above each bar
    for index, profit in enumerate(profits):

        ax.text(
            index,
            profit,
            f"${profit:.2f}",
            ha="center",
            va="bottom"
        )

    plt.xticks(
        rotation=15,
        ha="right"
    )

    plt.tight_layout()

    # Save chart to memory
    image = io.BytesIO()

    fig.savefig(
        image,
        format="png"
    )

    plt.close(fig)

    image.seek(0)

    return send_file(
        image,
        mimetype="image/png"
    )
# =========================================================
# T2-007 - Financial CSV Export
# Developer: Gregory Krautkremer
# Integrated into Flask by Ashley Lindamood
# =========================================================

@app.get("/financial-dashboard/export")
def export_financial_data():

    # user must be logged in
    if "username" not in session:
        return redirect(url_for("auth.login"))

    # only Admin and Manager can export financial data
    if not can_manage_users():
        return redirect(url_for("index"))

    sales = load_sales()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Date",
        "Sale ID",
        "Revenue",
        "Expenses",
        "Profit",
    ])

    for sale in sales:

        sale_date = sale.get(
            "date",
            sale.get(
                "datetime",
                sale.get("timestamp", "Unknown")
            )
        )

        sale_id = sale.get(
            "sale_id",
            sale.get("id", "")
        )

        revenue = sale.get("total", 0)

        try:
            revenue = float(revenue)
        except (TypeError, ValueError):
            revenue = 0.0

        expenses = 0.0
        profit = revenue - expenses

        writer.writerow([
            sale_date,
            sale_id,
            f"{revenue:.2f}",
            f"{expenses:.2f}",
            f"{profit:.2f}",
        ])

    csv_data = output.getvalue()

    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; "
                "filename=financial_data.csv"
        },
    )
# T1-006: sales screen (catalog + ticket)

@app.route("/")
def index():
    load_tax_rates()
    load_products()
    active = request.args.get("cat", "All")
    tiles = []
    for product in visible_products(active):
        available = stock_left(product)
        tiles.append({
            **product,
            "available": available,
            "out_of_stock": available is not None and available <= 0,
            "low": available is not None and 0 < available <= product["reorder_threshold"],
    })
    totals = calc_totals(tax_rate())
    low_stock_books = get_low_stock_books()
    return render_template(
        "pos.html",
        categories=categories(),
        active=active,
        tiles=tiles,
        lines=cart_lines(),
        item_count=item_count(),
        totals=totals,
        tax_rate=tax_rate(),
        states=STATES,
        selected_state=selected_state(),
        format_rate=format_rate,
        money=money,
        banner=session.get("banner"),
        low_stock_books=low_stock_books,
        can_checkout=bool(cart_lines()) and bool(selected_state()) and can_use_pos(),
    )


@app.post("/add/<pid>")
def add(pid):
    if not can_use_pos():
        return redirect_home()
    product = product_by_id(pid)
    available = stock_left(product) if product else 0
    if product and (available is None or available > 0):
        c = cart()
        c[str(pid)] = qty_in_cart(pid) + 1
        session.modified = True
        session.pop("banner", None)
    return redirect_home()


@app.post("/qty/<pid>/<int:delta>")
def change_qty(pid, delta):
    if not can_use_pos():
        return redirect_home()
    product = product_by_id(pid)
    if not product or str(pid) not in cart():
        return redirect_home()
    if delta > 0:
        available = stock_left(product)
        if available is not None and available <= 0:
            return redirect_home()
    new_qty = qty_in_cart(pid) + (1 if delta > 0 else -1)
    c = cart()
    if new_qty <= 0:
        c.pop(str(pid), None)
    else:
        c[str(pid)] = new_qty
    session.modified = True
    session.pop("banner", None)
    return redirect_home()


@app.post("/remove/<pid>")
def remove_item(pid):
    cart().pop(str(pid), None)
    session.modified = True
    session.pop("banner", None)
    return redirect_home()


@app.post("/clear")
def clear_cart():
    session["cart"] = {}
    session.pop("banner", None)
    return redirect_home()


@app.post("/tax")
def set_tax():
    # T1-006: cashier picks a state; tax_rates.json supplies the percentage.
    session.pop("tax_rate", None)
    code = (request.form.get("state") or "").upper()
    if code in STATES_BY_CODE:
        session["tax_state"] = code
    else:
        session.pop("tax_state", None)
    return redirect_home()


# T1-006 checkout, then T1-007 inventory + receipt

@app.post("/checkout")
def checkout():
    if not can_use_pos():
        return redirect_home()

    sale = build_sale()

    if not sale:
        return redirect_home()

    # Save the completed sale to sales.json.
    cashier = current_user()

    record_sale(
        sale,
        cashier
    )

    session["cart"] = {}
    session["last_receipt"] = sale["receipt"]
    session["last_sale_id"] = sale["id"]

    session["banner"] = {
        "id": sale["id"],
        "total": money(sale["total"])
    }

    return redirect(url_for("receipt"))


# T1-007: show / download receipt

@app.get("/receipt")
def receipt():
    text = session.get("last_receipt")
    if not text:
        return redirect(url_for("index"))
    return render_template(
        "receipt.html",
        receipt_text=text,
        sale_id=session.get("last_sale_id", "receipt"),
        banner=session.get("banner"),
        email_message=request.args.get("email_message"),
        email_success=request.args.get("email_success")
    )


@app.get("/receipt.txt")
def download_receipt():
    text = session.get("last_receipt", "")
    sale_id = session.get("last_sale_id", "receipt")
    return Response(
        text,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={sale_id}.txt"},
    )
# T2-008 - Receipt History
@app.get("/receipts")
def receipt_history():

    sales = load_sales()

    # Keep the original database index so each
    # stored transaction can be opened individually.
    receipt_records = list(enumerate(sales))

    # Newest receipts appear first.
    receipt_records.reverse()

    return render_template(
        "receipt_history.html",
        receipt_records=receipt_records,
        money=money,
        format_receipt_date=format_receipt_date
    )
# T2-008 - View a stored receipt
@app.get("/receipts/<int:receipt_index>")
def view_receipt(receipt_index):

    sales = load_sales()

    if receipt_index < 0 or receipt_index >= len(sales):
        return redirect(url_for("receipt_history"))

    sale = sales[receipt_index]

    # Use the stored receipt when available.
    # Use the original receipt if it was stored.
    receipt_text = sale.get("receipt")

# Older stored sales may not contain the original
# receipt text, so rebuild it from sales history.
    if not receipt_text:
        receipt_text = generate_historical_receipt(sale)

    sale_id = sale.get(
        "sale_id",
        sale.get("id", "Receipt")
    )
    

    return render_template(
        "receipt.html",
        receipt_text=receipt_text,
        sale_id=sale_id,
        banner=None
    )
    # T2-008 - Email Receipt
@app.post("/receipt/email")
def email_receipt():

    customer_email = (
        request.form.get("customer_email", "")
        .strip()
    )

    receipt_text = session.get("last_receipt", "")
    sale_id = session.get(
        "last_sale_id",
        "receipt"
    )

    if not customer_email:
        return redirect(
            url_for(
                "receipt",
                email_message="Enter a customer email address."
            )
        )

    if not receipt_text:
        return redirect(url_for("index"))

    success, message = send_receipt_email(
        customer_email,
        receipt_text,
        sale_id
    )

    return redirect(
        url_for(
            "receipt",
            email_message=message,
            email_success=int(success)
        )
    )

# T1-010: sign in, roles, permissions, lock/disable

@app.route("/signin", methods=["GET", "POST"])
def signin():
    load_users()
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password") or ""
        user = authenticate_user(username, password)
        merged = get_user(username)
        if merged and merged.get("locked"):
            error = merged["name"] + " is locked and cannot sign in."
        elif not user:
            error = "Username or password is incorrect."
        else:
            session["username"] = user["username"]
            session.pop("cart", None)
            return redirect(url_for("index"))
    return render_template("signin.html", users=USERS, error=error)


@app.post("/signout")
def signout():
    session.clear()
    return redirect(url_for("signin"))


@app.get("/users")
def user_admin():
    if not can_manage_users():
        return redirect(url_for("index"))
    load_users()
    return render_template(
        "user.html",
        users=USERS,
        roles=list(ROLES.keys()),
        permission_defs=PERMISSIONS,
        notice=request.args.get("notice"),
    )


@app.post("/users/<username>/role")
def set_role(username):
    if not can_manage_users():
        return redirect(url_for("index"))
    assign_role(username, request.form.get("role"))
    return redirect(url_for("user_admin", notice="Role updated for " + username + "."))


@app.post("/users/<username>/permissions")
def set_user_permissions(username):
    if not can_manage_users():
        return redirect(url_for("index"))
    set_permissions(username, request.form.getlist("permissions"))
    return redirect(url_for("user_admin", notice="Permissions updated for " + username + "."))


@app.post("/users/<username>/lock")
def lock_user(username):
    if not can_manage_users():
        return redirect(url_for("index"))
    set_locked(username, True)
    if session.get("username") == username:
        session.clear()
        return redirect(url_for("signin"))
    return redirect(url_for("user_admin", notice=username + " is locked."))


@app.post("/users/<username>/unlock")
def unlock_user(username):
    if not can_manage_users():
        return redirect(url_for("index"))
    set_locked(username, False)
    return redirect(url_for("user_admin", notice=username + " is unlocked."))
#R route for database page
@app.get("/database")
def database_page():

    if not can_manage_users():
        return redirect(url_for("index"))

    status = connection_status()

    return render_template(
        "database.html",
        status=status,
        money=money
    )


# T2-002: supplier table, maintenance screen, add records

def supplier_form_values():
    return {field: request.form.get(field, "") for field in (
        "name", "contact_name", "email", "phone", "city", "state", "categories", "notes",
    )}


@app.get("/suppliers")
def supplier_admin():
    if not can_manage_suppliers():
        return redirect(url_for("index"))
    return render_template(
        "suppliers.html",
        suppliers=load_suppliers(),
        states=STATES,
        form={
            "name": "", "contact_name": "", "email": "", "phone": "",
            "city": "", "state": "", "categories": "", "notes": "",
        },
        notice=request.args.get("notice"),
        error=None,
    )


@app.post("/suppliers")
def create_supplier():
    if not can_manage_suppliers():
        return redirect(url_for("index"))
    form = supplier_form_values()
    ok, result = add_supplier(form)
    if not ok:
        return render_template(
            "suppliers.html",
            suppliers=load_suppliers(),
            states=STATES,
            form=form,
            notice=None,
            error=result,
        )
    
    return redirect(url_for("supplier_admin", notice="Added supplier " + str(result) + "."))
# =========================================================
# Sprint 2 - T2-004
# Developer: Ashley Lindamood
# Purchase Order Management
# =========================================================


@app.get("/purchase-orders")
def purchase_order_admin():
    """Display the purchase order management screen."""

    if not can_manage_suppliers():
        return redirect(url_for("index"))

    return render_template(
        "purchase_orders.html",
        suppliers=load_suppliers(),
        books=load_books(),
        purchase_orders=load_purchase_orders(),
        notice=request.args.get("notice"),
        error=None,
    )


@app.post("/purchase-orders")
def create_purchase_order_route():
    """Create a purchase order from the management screen."""

    if not can_manage_suppliers():
        return redirect(url_for("index"))

    supplier_id = request.form.get("supplier_id", "").strip()
    book_id = request.form.get("book_id", "").strip()
    quantity = request.form.get("quantity", "").strip()
    notes = request.form.get("notes", "").strip()

    # Find the selected book in Ashley's inventory.
    selected_book = None

    for book in load_books():
        if str(book.get("book_id")) == str(book_id):
            selected_book = book
            break

    if selected_book is None:
        return render_template(
            "purchase_orders.html",
            suppliers=load_suppliers(),
            books=load_books(),
            purchase_orders=load_purchase_orders(),
            notice=None,
            error="Please select a valid book.",
        )

    # Get the employee who created the purchase order.
    created_by = session.get("username", "Unknown")

    items = [
        {
            "book_id": selected_book.get("book_id"),
            "title": selected_book.get("title"),
            "quantity": quantity,
        }
    ]

    ok, result = create_purchase_order(
        supplier_id=supplier_id,
        items=items,
        created_by=created_by,
        notes=notes,
    )

    if not ok:
        return render_template(
            "purchase_orders.html",
            suppliers=load_suppliers(),
            books=load_books(),
            purchase_orders=load_purchase_orders(),
            notice=None,
            error=result,
        )

    return redirect(
        url_for(
            "purchase_order_admin",
            notice="Created purchase order "
            + str(result)
            + ".",
        )
    )


@app.post("/purchase-orders/<int:purchase_order_id>/status")
def change_purchase_order_status(purchase_order_id):
    """Update the status of an existing purchase order."""

    if not can_manage_suppliers():
        return redirect(url_for("index"))

    new_status = request.form.get("status", "").strip()

    ok, message = update_purchase_order_status(
        purchase_order_id,
        new_status,
    )

    if not ok:
        return redirect(
            url_for(
                "purchase_order_admin",
                notice=message,
            )
        )

    return redirect(
        url_for(
            "purchase_order_admin",
            notice="Purchase order "
            + str(purchase_order_id)
            + " updated to "
            + new_status
            + ".",
        )
    )

# T1-007: test a sample sale

def run_sample_sales():
    load_products()
    snapshot = deepcopy(load_books())
    print("--- Running sample sales ---")
    before = [{"id": p["id"], "stock": p["stock"]} for p in products[:2]]
    print("Stock before:", before)

    session_cart = {str(products[0]["id"]): 2, str(products[1]["id"]): 1}
    items = []
    for pid, qty in session_cart.items():
        p = product_by_id(pid)
        items.append({
            "productId": pid,
            "name": p["name"],
            "qty": qty,
            "unitPrice": p["price"],
            "lineTotal": p["price"] * qty,
            "exempt": bool(p.get("exempt")),
        })
    subtotal = sum(i["lineTotal"] for i in items)
    taxable = sum(i["lineTotal"] for i in items if not i["exempt"])
    tax_pct = state_rate("TX")
    tax = taxable * (tax_pct / 100)
    sale = {
        "id": "SALE-DEMO",
        "items": items,
        "subtotal": subtotal,
        "taxRate": tax_pct,
        "taxLabel": f"TX tax ({format_rate(tax_pct)}%)",
        "tax": tax,
        "total": subtotal + tax,
        "timestamp": datetime.now().isoformat(),
    }
    sale["inventoryResults"] = update_inventory(sale["items"])
    print("Sale result:", sale)
    after = [{"id": e["id"], "stock": product_by_id(e["id"])["stock"]} for e in before]
    print("Stock after:", after)
    print("Expected: first product stock down by 2, second product stock down by 1.")
    print(generate_receipt(sale))
    save_books(snapshot)
    load_products()


load_products()
load_tax_rates()
load_users()


if __name__ == "__main__":
    app.run(debug=True)
