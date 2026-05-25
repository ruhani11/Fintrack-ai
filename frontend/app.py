import streamlit as st
import pandas as pd
import requests
from datetime import date
from dotenv import load_dotenv
import os
import re

load_dotenv()


def get_api_url():
    """
    First priority: Streamlit secrets
    Second priority: .env file
    Default: localhost for local development
    """
    try:
        api_url = st.secrets.get("PROJECT_URL", None)
    except Exception:
        api_url = None

    if not api_url:
        api_url = os.getenv("PROJECT_URL", "http://localhost:5000")

    return api_url.rstrip("/")


def clean_ai_tip(tip):
    """
    Cleans AI tip and formats numbered tips line-by-line.
    """
    if not tip:
        return "No tip generated."

    tip = str(tip).strip()

    prefixes = [
        "💡 AI Tip:",
        "AI Tip:",
        "💡"
    ]

    for prefix in prefixes:
        if tip.startswith(prefix):
            tip = tip.replace(prefix, "", 1).strip()

    # Put each numbered tip on a new line
    tip = re.sub(r"\s*(\d+\.)\s+", r"\n\1 ", tip).strip()

    return tip


def is_ai_error_message(tip):
    """
    Detects backend AI failure messages so frontend does not show fake success.
    """
    if not tip:
        return True

    error_keywords = [
        "could not",
        "not be extracted",
        "temporarily busy",
        "rate-limited",
        "unavailable",
        "missing",
        "invalid",
        "try again",
        "error generating",
        "failed"
    ]

    tip_lower = tip.lower()

    return any(keyword in tip_lower for keyword in error_keywords)


def convert_df_to_csv(df):
    """
    Converts dataframe to CSV for download.
    utf-8-sig helps Excel open the file properly.
    """
    return df.to_csv(index=False).encode("utf-8-sig")


API_URL = get_api_url()

st.set_page_config(
    page_title="Fintrack AI",
    page_icon="💰",
    layout="centered"
)

st.title("💰 Fintrack AI – Budget Dashboard")
st.caption("Track your income, expenses and get AI-powered budgeting tips.")

# ---------------- Backend Status ----------------
with st.expander("🔗 Backend Connection Status"):
    st.write(f"Backend URL: `{API_URL}`")

    try:
        health_res = requests.get(f"{API_URL}/", timeout=10)

        if health_res.status_code == 200:
            st.success("Backend connected successfully.")
        else:
            st.warning("Backend is reachable, but returned an unexpected response.")

    except Exception as e:
        st.error(f"Backend not connected: {e}")

st.divider()

# ---------------- Add New Transaction ----------------
st.subheader("➕ Add a Transaction")

amount = st.number_input(
    "Amount",
    min_value=0.0,
    format="%.2f"
)

category = st.selectbox(
    "Category",
    [
        "Income",
        "Food",
        "Transport",
        "Shopping",
        "Utilities",
        "Health",
        "Entertainment",
        "Rent",
        "Savings",
        "Education",
        "Others"
    ]
)

date_input = st.date_input(
    "Date",
    value=date.today()
)

month = date_input.strftime("%B")
year = date_input.year

if st.button("Add Transaction", width="stretch"):
    if amount > 0 and category and date_input:
        payload = {
            "amount": float(amount),
            "category": category,
            "date": date_input.strftime("%Y-%m-%d"),
            "month": month,
            "year": year
        }

        try:
            res = requests.post(
                f"{API_URL}/api/transactions",
                json=payload,
                timeout=20
            )

            if res.status_code in [200, 201]:
                st.success("✅ Transaction added successfully!")
                st.rerun()
            else:
                try:
                    error_data = res.json()
                    st.error(f"❌ Failed to add: {error_data.get('error', res.text)}")
                except Exception:
                    st.error(f"❌ Failed to add: {res.text}")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
    else:
        st.warning("⚠️ Please enter an amount greater than 0.")

st.divider()

# ---------------- View Transactions ----------------
st.subheader("📋 Transaction History")

try:
    res = requests.get(
        f"{API_URL}/api/transactions",
        timeout=20
    )

    if res.status_code == 200:
        response_data = res.json()

        if isinstance(response_data, dict):
            data = response_data.get("transactions", [])
        else:
            data = response_data

        if data:
            df = pd.DataFrame(data)

            df["amount"] = df["amount"].astype(float)
            df["year"] = df["year"].astype(int)
            df = df.sort_values(by="date", ascending=False)

            preferred_columns = ["id", "amount", "category", "date", "month", "year"]
            available_columns = [col for col in preferred_columns if col in df.columns]
            df_display = df[available_columns]

            st.dataframe(
                df_display,
                width="stretch",
                hide_index=True
            )

            # ---------------- Full Data Download ----------------
            st.markdown("#### ⬇️ Download Full Transaction Data")

            full_csv = convert_df_to_csv(df_display)

            st.download_button(
                label="Download All Transactions CSV",
                data=full_csv,
                file_name="fintrack_all_transactions.csv",
                mime="text/csv",
                width="stretch"
            )

            # ---------------- Monthly Financial Overview ----------------
            st.markdown("### 📅 Monthly Financial Overview")

            overview_col1, overview_col2 = st.columns(2)

            with overview_col1:
                overview_month = st.selectbox(
                    "Select Month for Overview",
                    [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December"
                    ],
                    index=date.today().month - 1,
                    key="overview_month"
                )

            with overview_col2:
                available_years = sorted(df["year"].dropna().unique().tolist())

                if date.today().year not in available_years:
                    available_years.append(date.today().year)

                available_years = sorted(available_years)

                overview_year = st.selectbox(
                    "Select Year for Overview",
                    available_years,
                    index=available_years.index(date.today().year),
                    key="overview_year"
                )

            monthly_df = df[
                (df["month"] == overview_month) &
                (df["year"] == overview_year)
            ]

            if not monthly_df.empty:
                monthly_income = monthly_df[monthly_df["category"] == "Income"]["amount"].sum()
                monthly_expense = monthly_df[monthly_df["category"] != "Income"]["amount"].sum()
                monthly_savings = monthly_income - monthly_expense

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        f"Income - {overview_month} {overview_year}",
                        f"₹{monthly_income:,.2f}"
                    )

                with col2:
                    st.metric(
                        f"Expenses - {overview_month} {overview_year}",
                        f"₹{monthly_expense:,.2f}"
                    )

                with col3:
                    st.metric(
                        f"Savings - {overview_month} {overview_year}",
                        f"₹{monthly_savings:,.2f}"
                    )

                # ---------------- Selected Month Download ----------------
                st.markdown("#### ⬇️ Download Selected Month Data")

                monthly_display_columns = [
                    col for col in preferred_columns if col in monthly_df.columns
                ]

                monthly_df_display = monthly_df[monthly_display_columns].sort_values(
                    by="date",
                    ascending=False
                )

                monthly_csv = convert_df_to_csv(monthly_df_display)

                st.download_button(
                    label=f"Download {overview_month} {overview_year} Transactions CSV",
                    data=monthly_csv,
                    file_name=f"fintrack_transactions_{overview_month}_{overview_year}.csv",
                    mime="text/csv",
                    width="stretch"
                )

            else:
                st.info(f"ℹ️ No transactions found for {overview_month} {overview_year}.")

            # ---------------- Month-wise Summary Table ----------------
            st.markdown("### 📊 Month-wise Summary")

            summary_df = df.copy()

            month_order = {
                "January": 1,
                "February": 2,
                "March": 3,
                "April": 4,
                "May": 5,
                "June": 6,
                "July": 7,
                "August": 8,
                "September": 9,
                "October": 10,
                "November": 11,
                "December": 12
            }

            summary_df["month_no"] = summary_df["month"].map(month_order)

            income_df = (
                summary_df[summary_df["category"] == "Income"]
                .groupby(["year", "month", "month_no"])["amount"]
                .sum()
                .reset_index(name="Income")
            )

            expense_df = (
                summary_df[summary_df["category"] != "Income"]
                .groupby(["year", "month", "month_no"])["amount"]
                .sum()
                .reset_index(name="Expenses")
            )

            monthly_summary = pd.merge(
                income_df,
                expense_df,
                on=["year", "month", "month_no"],
                how="outer"
            ).fillna(0)

            monthly_summary["Savings"] = (
                monthly_summary["Income"] - monthly_summary["Expenses"]
            )

            monthly_summary = monthly_summary.sort_values(
                by=["year", "month_no"],
                ascending=[False, False]
            )

            monthly_summary = monthly_summary[
                ["month", "year", "Income", "Expenses", "Savings"]
            ]

            st.dataframe(
                monthly_summary,
                width="stretch",
                hide_index=True
            )

            # ---------------- Month-wise Summary Download ----------------
            st.markdown("#### ⬇️ Download Month-wise Summary")

            monthly_summary_csv = convert_df_to_csv(monthly_summary)

            st.download_button(
                label="Download Month-wise Summary CSV",
                data=monthly_summary_csv,
                file_name="fintrack_month_wise_summary.csv",
                mime="text/csv",
                width="stretch"
            )

        else:
            st.info("ℹ️ No transactions yet.")

    else:
        st.error("❌ Failed to load transactions.")

except Exception as e:
    st.error(f"⚠️ Error: {e}")

st.divider()

# ---------------- Monthly Summary & AI Tip ----------------
st.subheader("📊 Monthly Summary & AI Budget Tip")

month_col, year_col = st.columns(2)

with month_col:
    selected_month = st.selectbox(
        "📅 Select Month",
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ],
        index=date.today().month - 1
    )

with year_col:
    current_year = date.today().year
    year_options = list(range(2020, current_year + 6))

    selected_year = st.selectbox(
        "📅 Select Year",
        year_options,
        index=year_options.index(current_year)
    )

if st.button("Generate Summary", width="stretch"):
    try:
        summary_res = requests.post(
            f"{API_URL}/api/summary",
            json={
                "month": selected_month,
                "year": selected_year
            },
            timeout=20
        )

        if summary_res.status_code == 200:
            response_data = summary_res.json()

            if isinstance(response_data, dict):
                summary = response_data.get("summary", {})
            else:
                summary = response_data

            if summary:
                st.write(f"📊 Category-wise Breakdown for {selected_month} {selected_year}")

                summary_series = pd.Series(summary)
                st.bar_chart(summary_series)

                income_amount = float(summary.get("Income", 0))

                expense_summary = {
                    category: amount
                    for category, amount in summary.items()
                    if category != "Income"
                }

                if income_amount <= 0:
                    st.warning("⚠️ Please add income for this month and year to generate better AI tips.")

                elif not expense_summary:
                    st.info("ℹ️ No expenses found for this month and year.")

                else:
                    tip_res = requests.post(
                        f"{API_URL}/api/tip",
                        json={
                            "summary": expense_summary,
                            "income": income_amount
                        },
                        timeout=60
                    )

                    if tip_res.status_code == 200:
                        tip_data = tip_res.json()
                        tip = clean_ai_tip(tip_data.get("tip", "No tip generated."))

                        if is_ai_error_message(tip):
                            st.warning(f"⚠️ {tip}")
                        else:
                            st.success("💡 AI Tip generated successfully!")

                            st.markdown(
                                f"""
<div style="
    background-color:#f0fff4;
    padding:14px 18px;
    border-radius:10px;
    border-left:5px solid #22c55e;
    line-height:1.8;
    font-size:16px;
">
{tip.replace(chr(10), "<br>")}
</div>
""",
                                unsafe_allow_html=True
                            )

                    else:
                        try:
                            error_data = tip_res.json()
                            st.warning(
                                f"⚠️ Failed to load AI tip: {error_data.get('tip', tip_res.text)}"
                            )
                        except Exception:
                            st.warning(f"⚠️ Failed to load AI tip: {tip_res.text}")

            else:
                st.info(f"ℹ️ No data for {selected_month} {selected_year}.")

        else:
            try:
                error_data = summary_res.json()
                st.error(
                    f"❌ Error loading summary: {error_data.get('error', summary_res.text)}"
                )
            except Exception:
                st.error(f"❌ Error loading summary: {summary_res.text}")

    except Exception as e:
        st.error(f"⚠️ Error: {e}")