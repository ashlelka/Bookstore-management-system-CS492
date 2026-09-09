"""
Bookstore Management System
Sprint 1 - T1-006
Sprint 1 - T1-007
Developer: Alexis Silva
"""

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for, Response

from tax_rates import STATES, STATES_BY_CODE, load_tax_rates, state_rate
from inventory import decrement_quantities, load_books, save_books

APP_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.secret_key = "bookstore-pos-dev"

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


def item_count():
    return sum(int(qty) for qty in cart().values())


# T1-006: sales tax (state lookup in tax_rates.json; rate is not typed in)

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


def update_inventory(sale_items):
    # T1-007: after checkout, decrement stock through Ashley's inventory module (T1-003).
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
            "low": available is not None and 0 < available <= 3,
        })
    totals = calc_totals(tax_rate())
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
        can_checkout=bool(cart_lines()) and bool(selected_state()),
    )


@app.post("/add/<pid>")
def add(pid):
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
    sale = build_sale()
    if not sale:
        return redirect_home()
    session["cart"] = {}
    session["last_receipt"] = sale["receipt"]
    session["last_sale_id"] = sale["id"]
    session["banner"] = {"id": sale["id"], "total": money(sale["total"])}
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


# T1-007: test a sample sale (python app.py --sample)

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


if __name__ == "__main__":
    import sys
    if "--sample" in sys.argv:
        run_sample_sales()
    else:
        app.run(debug=True)
