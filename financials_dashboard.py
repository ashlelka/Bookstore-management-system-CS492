# T2-007, BMS-009

# get required packages and libraries
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# connect to existing BMS sales database
from database import load_sales


# load completed sales from existing BMS database
sales = load_sales()

# create list for financial dashboard records
financial_records = []

for sale in sales:

    # get sale date from existing sales record
    sale_date = sale.get(
        "date",
        sale.get("datetime", sale.get("timestamp", "Unknown"))
    )

    # get total revenue from completed sale
    revenue = sale.get("total", 0)

    try:
        revenue = float(revenue)
    except (TypeError, ValueError):
        revenue = 0.0

    financial_records.append({
        "Date": sale_date,
        "Sale ID": sale.get(
            "sale_id",
            sale.get("id", "")
        ),
        "Revenue": round(revenue, 2),
    })


# create dataframe from actual BMS sales
df = pd.DataFrame(financial_records)
# format sale date for easier reading
if not df.empty:

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    df["Date"] = df["Date"].dt.strftime(
        "%b %d, %I:%M %p"
    )
# expenses are not currently stored in the BMS database
# use zero until expense tracking is implemented
if not df.empty:
    df["Expenses"] = 0.0
    df["Profit"] = df["Revenue"] - df["Expenses"]

else:
    df = pd.DataFrame(
        columns=[
            "Date",
            "Sale ID",
            "Revenue",
            "Expenses",
            "Profit"
        ]
    )


# create Streamlit financial dashboard
st.title("Financial Dashboard for Ana's Anomalous Anthologies")

st.subheader("Financial Overview")

# display financial data
st.write(df)


# display financial totals
if not df.empty:

    total_revenue = df["Revenue"].sum()
    total_expenses = df["Expenses"].sum()
    total_profit = df["Profit"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Revenue",
        f"${total_revenue:,.2f}"
    )

    col2.metric(
        "Total Expenses",
        f"${total_expenses:,.2f}"
    )

    col3.metric(
        "Total Profit",
        f"${total_profit:,.2f}"
    )


# create line chart for revenue, expenses, and profit
st.subheader("Revenue, Expenses, and Profit Over Time")

if not df.empty:

    fig, ax = plt.subplots()

    ax.plot(
        df["Date"],
        df["Revenue"],
        label="Revenue",
        marker="o"
    )

    ax.plot(
        df["Date"],
        df["Expenses"],
        label="Expenses",
        marker="s"
    )

    ax.plot(
        df["Date"],
        df["Profit"],
        label="Profit",
        marker="^"
    )

    ax.set_xlabel("Sale Date")
    ax.set_ylabel("Amount ($)")
    ax.set_title("Financial Performance Over Time")
    ax.legend()

    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)

else:
    st.info(
        "No completed sales are currently available."
    )


# create bar chart for profit
st.subheader("Profit by Sale")

if not df.empty:

    st.bar_chart(
        df.set_index("Sale ID")["Profit"]
    )


# export function to download financial data as CSV file
def export_data():

    csv = df.to_csv(
        index=False,
        encoding="utf-8"
    )

    st.download_button(
        label="Download Financial Data as CSV",
        data=csv,
        file_name="financial_data.csv",
        mime="text/csv",
    )


# call export function
export_data()