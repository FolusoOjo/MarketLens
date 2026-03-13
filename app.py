import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pd.options.display.float_format = '{:,.2f}'.format

st.set_page_config(page_title="Financial Analytics Dashboard", layout="wide")


def get_row(df: pd.DataFrame, possible_labels: list[str]) -> pd.Series:
    for label in possible_labels:
        if label in df.index:
            return df.loc[label]
    return pd.Series([np.nan] * len(df.columns), index=df.columns)


def clean_yearly_table(df):
    df = df.dropna(axis=1, how="all").copy()
    new_cols = []
    for col in df.columns:
        try:
            new_cols.append(str(pd.to_datetime(col).year))
        except:
            new_cols.append(str(col))
    df.columns = new_cols

    df= df.T.groupby(level= 0).first().T

    try:
        df= df.reindex(sorted(df.columns, key=int), axis = 1)
    except:
        pass
    return df


def fetch_data(ticker_symbol: str):
    ticker = yf.Ticker(ticker_symbol)
    balance = ticker.balance_sheet
    income = ticker.financials
    cashflow = ticker.cashflow
    price_5y = ticker.history(period="5y")
    info = ticker.info
    return ticker, balance, income, cashflow, price_5y, info


def liquidity_analysis(balance: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    current_assets = get_row(balance, ["Current Assets", "Total Current Assets"])
    current_liabilities = get_row(balance, ["Current Liabilities", "Total Current Liabilities"])
    inventory = get_row(balance, ["Inventory", "Inventories"])
    cash = get_row(balance, ["Cash And Cash Equivalents", "Cash", "Cash Cash Equivalents And Short Term Investments"])

    current_ratio = current_assets / current_liabilities
    quick_ratio = (current_assets - inventory.fillna(0)) / current_liabilities
    cash_ratio = cash / current_liabilities

    liquidity_df = pd.DataFrame({
        "Current Assets": current_assets,
        "Current Liabilities": current_liabilities,
        "Inventory": inventory,
        "Cash": cash,
        "Current Ratio": current_ratio,
        "Quick Ratio": quick_ratio,
        "Cash Ratio": cash_ratio,
    }).T

    liquidity_df = clean_yearly_table(liquidity_df)
    liquidity_ratios_df = liquidity_df.loc[["Current Ratio", "Quick Ratio", "Cash Ratio"]]
    return liquidity_df, liquidity_ratios_df


def profitability_analysis(balance: pd.DataFrame, income: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    revenue = get_row(income, ["Total Revenue", "Revenue"])
    gross_profit = get_row(income, ["Gross Profit"])
    operating_income = get_row(income, ["Operating Income"])
    net_income = get_row(income, ["Net Income"])

    total_assets = get_row(balance, ["Total Assets"])
    total_equity = get_row(balance, ["Total Stockholder Equity", "Stockholders Equity"])
    eps = get_row(income, ["Diluted EPS", "Basic EPS"])

    gross_margin = gross_profit / revenue
    operating_margin = operating_income / revenue
    net_margin = net_income / revenue
    roa = net_income / total_assets
    roe = net_income / total_equity

    profitability_df = pd.DataFrame({
        "Revenue": revenue,
        "Gross Profit": gross_profit,
        "Operating Income": operating_income,
        "Net Income": net_income,
        "Gross Margin": gross_margin,
        "Operating Margin": operating_margin,
        "Net Margin": net_margin,
        "Return On Assets": roa,
        "Return On Equity": roe,
        "Earnings Per Share": eps,
    }).T

    profitability_df = clean_yearly_table(profitability_df)
    profitability_ratios_df = profitability_df.loc[[
        "Gross Margin", "Operating Margin", "Net Margin",
        "Return On Assets", "Return On Equity", "Earnings Per Share"
    ]]
    return profitability_df, profitability_ratios_df


def additional_ratios(balance: pd.DataFrame, income: pd.DataFrame, cashflow: pd.DataFrame, price_5y: pd.DataFrame, profitability_df: pd.DataFrame) -> pd.DataFrame:
    total_equity = get_row(balance, ["Total Stockholder Equity", "Stockholders Equity"])
    total_debt = get_row(balance, ["Total Debt", "Long Term Debt"])
    dividends_paid = get_row(cashflow, ["Cash Dividends Paid", "Dividends Paid"])
    net_income = get_row(income, ["Net Income"])
    roe = profitability_df.loc["Return On Equity"]

    current_price = float(price_5y["Close"].dropna().iloc[-1]) if not price_5y.empty else np.nan
    latest_year = profitability_df.columns[-1]
    latest_eps = profitability_df.loc["Earnings Per Share", latest_year]
    pe_ratio = current_price / latest_eps if pd.notna(latest_eps) and latest_eps != 0 else np.nan

    pe_ratio_series = pd.Series(np.nan, index=profitability_df.columns)
    pe_ratio_series.loc[latest_year] = pe_ratio

    dividend_payout_ratio = abs(dividends_paid) / net_income
    debt_to_equity = total_debt / total_equity
    retention_ratio = 1 - dividend_payout_ratio
    sustainable_growth_rate = roe * retention_ratio

    add_df = pd.DataFrame({
        "P/E Ratio": pe_ratio_series,
        "Dividend Payout Ratio": dividend_payout_ratio,
        "Debt to Equity": debt_to_equity,
        "Sustainable Growth Rate": sustainable_growth_rate,
    }).T

    add_df = clean_yearly_table(add_df)
    return add_df


def capm_analysis(price_5y: pd.DataFrame):
    stock_returns = price_5y["Close"].pct_change().dropna()
    if stock_returns.empty:
        return {"beta": np.nan, "risk_free_rate": np.nan, "market_return": np.nan, "expected_return": np.nan, "returns_df": pd.DataFrame()}

    stock_returns.index = stock_returns.index.tz_localize(None)

    market = yf.download("^GSPC", period="5y", auto_adjust=True, progress=False)
    market_returns = market["Close"].pct_change().dropna()

    returns_df = pd.concat([stock_returns, market_returns], axis=1)
    returns_df.columns = ["Stock", "Market"]
    returns_df = returns_df.dropna()

    covariance = returns_df.cov().iloc[0, 1]
    market_variance = returns_df["Market"].var()
    beta = covariance / market_variance if market_variance != 0 else np.nan

    rf_data = yf.download("^TNX", period="1d", auto_adjust=True, progress=False)
    risk_free_rate = float(rf_data["Close"].iloc[-1]) / 100 if not rf_data.empty else np.nan

    market_return = returns_df["Market"].mean() * 252
    expected_return = risk_free_rate + beta * (market_return - risk_free_rate)

    return {
        "beta": beta,
        "risk_free_rate": risk_free_rate,
        "market_return": market_return,
        "expected_return": expected_return,
        "returns_df": returns_df,
    }


def fcf_analysis(cashflow: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    operating_cash_flow = get_row(cashflow, ["Operating Cash Flow", "Total Cash From Operating Activities"])
    capex = get_row(cashflow, ["Capital Expenditure", "Capital Expenditures"])
    free_cash_flow = operating_cash_flow + capex

    fcf_df = pd.DataFrame({
        "Operating Cash Flow": operating_cash_flow,
        "Capital Expenditures": capex,
        "Free Cash Flow": free_cash_flow,
    }).T

    fcf_df = clean_yearly_table(fcf_df)
    return fcf_df, free_cash_flow


def wacc_analysis(ticker, balance: pd.DataFrame, income: pd.DataFrame, expected_return: float):
    market_cap = ticker.info.get("marketCap", np.nan)
    total_debt = get_row(balance, ["Total Debt", "Long Term Debt"])
    interest_expense = get_row(income, [
        "Interest Expense",
        "Interest Expense Non Operating",
        "Net Non Operating Interest Income Expense",
    ])
    income_tax = get_row(income, ["Tax Provision"])
    pretax_income = get_row(income, ["Pretax Income"])

    debt_series = total_debt.dropna()
    interest_series = interest_expense.dropna()
    income_tax_series = income_tax.dropna()
    pretax_income_series = pretax_income.dropna()

    common_debt_years = debt_series.index.intersection(interest_series.index)
    if len(common_debt_years) > 0:
        debt_year = common_debt_years[0]
        total_debt_matched = debt_series.loc[debt_year]
        interest_expense_matched = interest_series.loc[debt_year]
        cost_of_debt = abs(interest_expense_matched) / total_debt_matched if total_debt_matched != 0 else np.nan
    else:
        debt_year = None
        total_debt_matched = np.nan
        cost_of_debt = np.nan

    common_tax_years = income_tax_series.index.intersection(pretax_income_series.index)
    if len(common_tax_years) > 0:
        tax_year = common_tax_years[0]
        income_tax_matched = income_tax_series.loc[tax_year]
        pretax_income_matched = pretax_income_series.loc[tax_year]
        tax_rate = abs(income_tax_matched) / abs(pretax_income_matched) if pretax_income_matched != 0 else np.nan
    else:
        tax_year = None
        tax_rate = np.nan

    E = market_cap
    D = total_debt_matched
    V = E + D

    wacc = (E / V) * expected_return + (D / V) * cost_of_debt * (1 - tax_rate) if pd.notna(D) and pd.notna(cost_of_debt) and pd.notna(tax_rate) and V != 0 else np.nan

    return {
        "market_cap": market_cap,
        "debt_year": debt_year,
        "tax_year": tax_year,
        "total_debt_matched": total_debt_matched,
        "cost_of_debt": cost_of_debt,
        "tax_rate": tax_rate,
        "wacc": wacc,
    }


def dcf_analysis(ticker, free_cash_flow: pd.Series, wacc: float, price_5y: pd.DataFrame):
    fcf_clean = free_cash_flow.dropna()
    if fcf_clean.empty or pd.isna(wacc) or wacc <= 0:
        return {"fcf_latest": np.nan, "firm_value": np.nan, "intrinsic_price": np.nan, "current_price": np.nan}

    fcf_latest = float(fcf_clean.iloc[-1])
    shares_outstanding = ticker.info.get("sharesOutstanding", np.nan)

    growth_rate = 0.03
    projection_years = 5
    terminal_growth_rate = 0.02

    projected_fcfs = []
    discounted_fcfs = []

    for year in range(1, projection_years + 1):
        projected_fcf = fcf_latest * (1 + growth_rate) ** year
        discounted_fcf = projected_fcf / (1 + wacc) ** year
        projected_fcfs.append(projected_fcf)
        discounted_fcfs.append(discounted_fcf)

    terminal_fcf = projected_fcfs[-1] * (1 + terminal_growth_rate)
    terminal_value = terminal_fcf / (wacc - terminal_growth_rate) if wacc > terminal_growth_rate else np.nan
    discounted_terminal_value = terminal_value / (1 + wacc) ** projection_years if pd.notna(terminal_value) else np.nan

    firm_value = sum(discounted_fcfs) + discounted_terminal_value if pd.notna(discounted_terminal_value) else np.nan
    intrinsic_price = firm_value / shares_outstanding if pd.notna(firm_value) and pd.notna(shares_outstanding) and shares_outstanding != 0 else np.nan
    current_price = float(price_5y["Close"].dropna().iloc[-1]) if not price_5y.empty else np.nan

    return {
        "fcf_latest": fcf_latest,
        "firm_value": firm_value,
        "intrinsic_price": intrinsic_price,
        "current_price": current_price,
    }


st.title("Financial Analytics Dashboard")
st.caption("Search a stock ticker to view ratios, CAPM, FCF, WACC, and DCF valuation.")

ticker_symbol = st.text_input("Enter stock ticker", value="AAPL").strip().upper()

if st.button("Analyze"):
    try:
        ticker, balance, income, cashflow, price_5y, info = fetch_data(ticker_symbol)

        if balance.empty or income.empty or cashflow.empty or price_5y.empty:
            st.error("Some data is missing for this ticker. Try another company.")
        else:
            liquidity_df, liquidity_ratios_df = liquidity_analysis(balance)
            profitability_df, profitability_ratios_df = profitability_analysis(balance, income)
            add_df = additional_ratios(balance, income, cashflow, price_5y, profitability_df)
            capm = capm_analysis(price_5y)
            fcf_df, free_cash_flow = fcf_analysis(cashflow)
            wacc_data = wacc_analysis(ticker, balance, income, capm["expected_return"])
            dcf_data = dcf_analysis(ticker, free_cash_flow, wacc_data["wacc"], price_5y)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current Price", f"${dcf_data['current_price']:,.2f}" if pd.notna(dcf_data['current_price']) else "N/A")
            col2.metric("Beta", f"{capm['beta']:.2f}" if pd.notna(capm['beta']) else "N/A")
            col3.metric("WACC", f"{wacc_data['wacc']:.2%}" if pd.notna(wacc_data['wacc']) else "N/A")
            col4.metric("Intrinsic Price", f"${dcf_data['intrinsic_price']:,.2f}" if pd.notna(dcf_data['intrinsic_price']) else "N/A")

            st.subheader(f"{ticker_symbol} 5-Year Stock Price")
            fig, ax = plt.subplots(figsize=(10, 4))
            price_5y["Close"].plot(ax=ax)
            ax.set_xlabel("Date")
            ax.set_ylabel("Price")
            st.pyplot(fig)

            st.subheader("Liquidity Ratios")
            st.dataframe(liquidity_ratios_df)

            st.subheader("Profitability Ratios")
            st.dataframe(profitability_ratios_df)

            st.subheader("Additional Ratios")
            st.dataframe(add_df)

            st.subheader("Free Cash Flow")
            st.dataframe(fcf_df)

            st.subheader("CAPM Summary")
            st.write(f"Risk-Free Rate: {capm['risk_free_rate']:.2%}" if pd.notna(capm['risk_free_rate']) else "Risk-Free Rate: N/A")
            st.write(f"Market Return: {capm['market_return']:.2%}" if pd.notna(capm['market_return']) else "Market Return: N/A")
            st.write(f"Expected Return: {capm['expected_return']:.2%}" if pd.notna(capm['expected_return']) else "Expected Return: N/A")

            st.subheader("WACC Summary")
            st.write(f"Cost of Debt: {wacc_data['cost_of_debt']:.2%}" if pd.notna(wacc_data['cost_of_debt']) else "Cost of Debt: N/A")
            st.write(f"Tax Rate: {wacc_data['tax_rate']:.2%}" if pd.notna(wacc_data['tax_rate']) else "Tax Rate: N/A")
            st.write(f"WACC: {wacc_data['wacc']:.2%}" if pd.notna(wacc_data['wacc']) else "WACC: N/A")

            st.subheader("DCF Valuation")
            st.write(f"Latest FCF: ${dcf_data['fcf_latest']:,.2f}" if pd.notna(dcf_data['fcf_latest']) else "Latest FCF: N/A")
            st.write(f"Firm Value: ${dcf_data['firm_value']:,.2f}" if pd.notna(dcf_data['firm_value']) else "Firm Value: N/A")
            st.write(f"Intrinsic Stock Price: ${dcf_data['intrinsic_price']:,.2f}" if pd.notna(dcf_data['intrinsic_price']) else "Intrinsic Stock Price: N/A")

    except Exception as e:
        st.error(f"Could not analyze {ticker_symbol}: {e}")