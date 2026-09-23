"""
Bookstore Management System
Sprint 2 - T2-010
Developer: Alexis Silva

BMS-011 Customer management:
  - Search customer records
  - View purchase history
  - Test customer management
"""

from customer_management import load_customers
from database import load_sales


def search_customers(query, customers=None):
    #Return customer rows that match name, email, phone, address, or ID.
    rows = customers if customers is not None else load_customers()
    needle = (query or "").strip().casefold()
    if not needle:
        return list(rows)
    hits = []
    for row in rows:
        haystack = " ".join([
            str(row.get("customer_id") or ""),
            str(row.get("first_name") or ""),
            str(row.get("last_name") or ""),
            (str(row.get("first_name") or "") + " " + str(row.get("last_name") or "")),
            str(row.get("email") or ""),
            str(row.get("phone") or ""),
            str(row.get("address") or ""),
        ]).casefold()
        if needle in haystack:
            hits.append(row)
    return hits


def purchases_for_customer(customer, sales=None):
    #Sales that belong to this customer, newest first.
    if not customer:
        return []
    rows = sales if sales is not None else load_sales()
    customer_id = str(customer.get("customer_id") or "")
    email = str(customer.get("email") or "").casefold()
    matches = []
    for sale in rows:
        if not isinstance(sale, dict):
            continue
        if customer_id and str(sale.get("customer_id") or "") == customer_id:
            matches.append(sale)
        elif email and str(sale.get("customer_email") or "").casefold() == email:
            matches.append(sale)
    matches.sort(key=lambda sale: str(sale.get("timestamp") or ""), reverse=True)
    return matches


def purchase_summary(purchases):
    total = 0.0
    for sale in purchases:
        try:
            total += float(sale.get("total") or 0)
        except (TypeError, ValueError):
            continue
    return {
        "count": len(purchases),
        "total": total,
    }
