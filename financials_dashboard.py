# T2-007, BMS-009

# get required packages and libraries
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Ensure requirements.txt file has been updated to include pandas, streamlit, and matplotlib

# create sample data for financial dashboard testing
# for actual application, import data from bookstore sales reports or database
data = {
    'Month': ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'],
    'Revenue': [12000, 15000, 13000, 17000, 16000, 18000, 20000, 22000, 21000, 23000, 25000, 27000],
    'Expenses': [8000, 9000, 8500, 9500, 9000, 10000, 11000, 12000, 11500, 12500, 13000, 14000]
}

# create simple dataframe for financial dashboard showing profit, revenue, and expenses
df = pd.DataFrame(data)
df['Profit'] = df['Revenue'] - df['Expenses']

# create streamlit app function to display financial dashboard
st.title("Financial Dashboard for Ana's Anomalous Anthologies")

st.subheader("Monthly Financial Overview")
st.write(df)

# create line chart for revenue, expenses, and profit
st.subheader("Revenue, Expenses, and Profit Over Time")
fig, ax = plt.subplots()
ax.plot(df['Month'], df['Revenue'], label='Revenue', marker='o')
ax.plot(df['Month'], df['Expenses'], label='Expenses', marker='s')
ax.plot(df['Month'], df['Profit'], label='Profit', marker='^')
ax.set_xlabel('Month')
ax.set_ylabel('Amount ($)')
ax.set_title('Financial Performance Over Time')
ax.legend()
st.pyplot(fig)

# create bar chart for monthly profit
st.subheader("Monthly Profit Comparison")
st.bar_chart(df.set_index('Month')['Profit'])

# export function to download the financial data as a CSV file
def export_data():
    csv = df.to_csv(index=False, encoding='utf-8')
    st.download_button(
        label="Download Financial Data as CSV",
        data=csv,
        file_name='financial_data.csv',
        mime='text/csv',
    )

# call export function to provide download option
export_data()
