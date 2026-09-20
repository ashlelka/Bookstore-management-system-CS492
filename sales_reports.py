"""T2-001 — repeatable reports over persisted sales, Timur Tyulin."""
import csv
import json
from xml.sax.saxutils import escape
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO, StringIO
import database


class ReportDataError(Exception):
    """Report totals cannot be trusted until the source data is repaired."""
def format_timestamp(timestamp):
    """Format an ISO timestamp for display in sales reports."""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%m/%d/%Y %I:%M %p")
    except (ValueError, TypeError):
        return timestamp

def report_sales():
    # TT: Read the existing sales store without changing it or hiding corrupt JSON.
    if not database.SALES_PATH.exists():
        return []
    try:
        data = json.loads(database.SALES_PATH.read_text(encoding="utf-8"))
        rows = data if isinstance(data, list) else data["sales"]
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError("Invalid sales list")
        return rows
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise ReportDataError("Sales records could not be read. No report was generated.") from exc


def period_bounds(period, anchor):
    day = date.fromisoformat(anchor)
    if period == "daily":
        return day, day
    if period == "weekly":
        start = day - timedelta(days=day.weekday())
        return start, start + timedelta(days=6)
    if period == "monthly":
        start = day.replace(day=1)
        following = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start, following - timedelta(days=1)
    raise ValueError("Choose daily, weekly, or monthly.")


def amount(value):
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError("Invalid sale amount.")
    return number.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_report(period, anchor):
    start, end = period_bounds(period, anchor)
    rows = []
    for sale in report_sales():
        # Sales use the bookstore server's local timestamp; include both boundary dates.
        try:
            sold_on = datetime.fromisoformat(sale["timestamp"]).date()
        except (ValueError, KeyError, TypeError) as exc:
            raise ReportDataError("A sale has an invalid timestamp. No report was generated.") from exc
        if start <= sold_on <= end:
            try:
                row = {"sale_id": str(sale["sale_id"]), "timestamp": sale["timestamp"],
                       **{key: amount(sale[key]) for key in ("subtotal", "tax", "total")}}
            except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
                raise ReportDataError("A sale has invalid amounts. No report was generated.") from exc
            rows.append(row)
    rows.sort(key=lambda row: (row["timestamp"], row["sale_id"]))
    # TT: Keep every transaction, including legacy records with duplicate IDs.
    return {"period": period, "start": start, "end": end, "rows": rows,
            "count": len(rows), **{key: sum((row[key] for row in rows), Decimal("0.00"))
                                    for key in ("subtotal", "tax", "total")}}

def format_report_timestamp(timestamp):
    """Format an ISO timestamp for CSV report exports."""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%m/%d/%Y %I:%M %p")
    except (ValueError, TypeError):
        return timestamp
def csv_report(report):

    # TT: Neutralize spreadsheet formulas in imported text fields.

    stream = StringIO(newline="")

    writer = csv.writer(stream)

    writer.writerow([
        "Period",
        report["period"],
        "Start",
        report["start"],
        "End",
        report["end"]
    ])

    writer.writerow([
        "Sale ID",
        "Timestamp",
        "Subtotal",
        "Tax",
        "Total"
    ])

    for row in report["rows"]:

        values = [
            row["sale_id"],
            format_report_timestamp(row["timestamp"]),
            row["subtotal"],
            row["tax"],
            row["total"]
        ]

        writer.writerow([
            "'" + v
            if isinstance(v, str)
            and v.lstrip().startswith(("=", "+", "-", "@"))
            else v
            for v in values
        ])

    writer.writerow([
        "TOTAL",
        report["count"],
        report["subtotal"],
        report["tax"],
        report["total"]
    ])

    return stream.getvalue()

def pdf_report(report):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    story = [Paragraph("Bookstore Sales Report", styles["Title"]),
             Paragraph(f"{report['period'].title()}: {report['start']} through {report['end']}", styles["Normal"]),
             Paragraph(f"Transactions: {report['count']} | Subtotal: ${report['subtotal']} | Tax: ${report['tax']} | Total: ${report['total']}", styles["Normal"]),
             Spacer(1, 18)]
    data = [["Sale ID", "Date", "Subtotal", "Tax", "Total"]]
    # TT: Wrap full IDs and repeat column headings when the table spans pages.
    data += [[Paragraph(escape(r["sale_id"]), styles["BodyText"]), r["timestamp"][:10], str(r["subtotal"]), str(r["tax"]), str(r["total"])]
             for r in report["rows"]]
    if not report["rows"]:
        story.append(Paragraph("No sales in this period.", styles["Normal"]))
    table = Table(data, repeatRows=1, colWidths=[150, 85, 80, 65, 80])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                              ("GRID", (0, 0), (-1, -1), .3, colors.grey),
                              ("ALIGN", (2, 0), (-1, -1), "RIGHT")]))
    story.append(table)
    SimpleDocTemplate(buffer).build(story)
    return buffer.getvalue()
