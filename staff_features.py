"""T2-001 / T2-009: management screens integrated with existing staff accounts."""
from datetime import date
from datetime import datetime
from secrets import token_urlsafe
from hmac import compare_digest
from flask import Blueprint, abort, redirect, render_template, request, session, url_for, Response
from users import get_user, has_permission
from customer_management import (load_customers, get_customer, save_customer, delete_customer,
                                 CustomerStoreError, CustomerConflictError)
from customer_history import search_customers, purchases_for_customer, purchase_summary
from sales_reports import generate_report, csv_report, pdf_report, ReportDataError

staff_bp = Blueprint("staff", __name__)


@staff_bp.before_request
def authorize():
    # TT: Reuse live staff permissions and lock state on every page and export.
    user = get_user(session.get("username"))
    if not user:
        return redirect(url_for("auth.login"))
    if user.get("role") not in ("Admin", "Manager") or not has_permission(user, "manage_users"):
        abort(403)
    session.setdefault("customer_csrf", token_urlsafe(32))
    # TT: Compare bytes so malformed non-ASCII tokens are rejected rather than crashing.
    if request.method == "POST" and not compare_digest(
            session["customer_csrf"].encode(), request.form.get("csrf_token", "").encode()):
        abort(400, "Invalid form token. Reload the form and try again.")


@staff_bp.after_request
def prevent_private_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@staff_bp.errorhandler(CustomerStoreError)
def customer_store_error(error):
    return render_template("staff_error.html", message=str(error)), 503
def format_timestamp(timestamp):
    """Format an ISO timestamp for display in the sales report."""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%m/%d/%Y %I:%M %p")
    except (ValueError, TypeError):
        return timestamp

@staff_bp.get("/reports")
def reports():
    period = request.args.get("period", "daily")
    anchor = request.args.get("date", date.today().isoformat())
    try:
        report = generate_report(period, anchor)
    except ReportDataError as exc:
        return render_template("reports.html", report=None, period=period, anchor=anchor, format_timestamp=format_timestamp,
                               error=str(exc)), 503
    except (ValueError, KeyError, TypeError, ArithmeticError):
        return render_template("reports.html", report=None, period=period, anchor=anchor, format_timestamp=format_timestamp,
                               error="Cannot generate report. Check the date, period, and sales records."), 400
    output = request.args.get("format", "html")
    if output in ("csv", "pdf"):
        content = csv_report(report) if output == "csv" else pdf_report(report)
        return Response(content, mimetype="text/csv" if output == "csv" else "application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=sales-{period}-{report['start']}.{output}"})
    if output != "html":
        abort(400)
    return render_template("reports.html", report=report, period=period, anchor=anchor, format_timestamp=format_timestamp)


@staff_bp.get("/customers")
def customers():
    # T2-010: search customer records (Alexis)
    query = request.args.get("q", "")
    return render_template("customers.html", customers=search_customers(query), query=query)


@staff_bp.route("/customers/new", methods=["GET", "POST"])
@staff_bp.route("/customers/<customer_id>/edit", methods=["GET", "POST"])
def customer_form(customer_id=None):
    customer = get_customer(customer_id) if customer_id else {}
    if customer_id and customer is None:
        abort(404)
    error = None
    status = 200
    if request.method == "POST":
        try:
            saved = save_customer(request.form, customer_id,
                                  request.form.get("updated_at", "") if customer_id else None)
            return redirect(url_for("staff.customer_profile", customer_id=saved["customer_id"]))
        except LookupError:
            abort(404)
        except CustomerConflictError as exc:
            error = str(exc)
            customer = request.form
            status = 409
        except ValueError as exc:
            error = str(exc)
            customer = request.form
            status = 400
    return render_template("customer_form.html", customer=customer, error=error), status


@staff_bp.get("/customers/<customer_id>")
def customer_profile(customer_id):
    customer = get_customer(customer_id)
    if customer is None:
        abort(404)
    # T2-010: purchase history joined from sales.json
    purchases = purchases_for_customer(customer)
    return render_template(
        "customer_profile.html",
        customer=customer,
        purchases=purchases,
        purchase_summary=purchase_summary(purchases),
    )

@staff_bp.post("/customers/<customer_id>/delete")
def customer_delete(customer_id):
    try:
        delete_customer(customer_id)
    except LookupError:
        abort(404)

    return redirect(url_for("staff.customers"))
