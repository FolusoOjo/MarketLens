import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import scipy.stats as stats
import time
import requests

pd.options.display.float_format = '{:,.2f}'.format

# ── Spoof browser User-Agent to avoid Yahoo Finance rate limiting on cloud ─────
_YF_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def _make_session():
    s = requests.Session()
    s.headers.update(_YF_HEADERS)
    return s

st.set_page_config(page_title="Financial Analytics Dashboard", layout="wide")

# ── Global styles — Soft Purple & Slate fintech theme ─────────────────────────
st.markdown("""
<style>
/* Page background — light warm slate */
[data-testid="stAppViewContainer"] { background: #f4f3f8; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #eeecf6; }

/* Metric card */
.fin-card {
    background: #ffffff;
    border: 1px solid #e2dff0;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 12px;
    position: relative;
    overflow: hidden;
}
.fin-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    border-radius: 4px 0 0 4px;
    background: var(--accent, #7C3AED);
}
.fin-card .label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #9d8ec4;
    margin-bottom: 6px;
}
.fin-card .value {
    font-size: 22px;
    font-weight: 700;
    color: #1e1b4b;
    line-height: 1.2;
}
.fin-card .sub {
    font-size: 11px;
    color: #b8afd6;
    margin-top: 4px;
}
.fin-card.good  .value { color: #15803d; }
.fin-card.warn  .value { color: #b45309; }
.fin-card.bad   .value { color: #b91c1c; }

/* Section header */
.section-header {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #7C3AED;
    border-bottom: 2px solid #e2dff0;
    padding-bottom: 8px;
    margin: 28px 0 14px;
}

/* Company header */
.company-header {
    background: #ffffff;
    border: 1px solid #e2dff0;
    border-top: 4px solid #7C3AED;
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 16px;
}
.company-name { font-size: 26px; font-weight: 700; color: #1e1b4b; }
.company-sub  { font-size: 13px; color: #9d8ec4; margin-top: 4px; }
.price-big    { font-size: 32px; font-weight: 700; color: #1e1b4b; text-align: right; }
.price-change { font-size: 14px; font-weight: 600; text-align: right; margin-top: 2px; }
.price-up     { color: #15803d; }
.price-down   { color: #b91c1c; }
.rec-badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 12px;
    border-radius: 20px;
    margin-top: 8px;
    letter-spacing: 0.06em;
}
.rec-buy  { background: #dcfce7; color: #15803d; }
.rec-hold { background: #fef3c7; color: #b45309; }
.rec-sell { background: #fee2e2; color: #b91c1c; }

/* Overview grid */
.ov-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 4px; }
.ov-item { background: #ffffff; border: 1px solid #e2dff0; border-radius: 10px; padding: 12px 14px; }
.ov-label { font-size: 11px; color: #9d8ec4; margin-bottom: 4px; font-weight: 500; }
.ov-val   { font-size: 14px; font-weight: 700; color: #1e1b4b; }

/* Valuation bar */
.val-section {
    background: #ffffff;
    border: 1px solid #e2dff0;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 12px;
}
.val-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.val-lbl { font-size: 13px; color: #9d8ec4; }
.val-num { font-size: 15px; font-weight: 700; color: #1e1b4b; }
.bar-track { height: 6px; background: #e2dff0; border-radius: 4px; margin-top: 8px; }
.bar-fill  { height: 6px; border-radius: 4px; }

/* Hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Helper utilities ───────────────────────────────────────────────────────────

def get_row(df: pd.DataFrame, possible_labels: list) -> pd.Series:
    for label in possible_labels:
        if label in df.index:
            return df.loc[label]
    return pd.Series([np.nan] * len(df.columns), index=df.columns)


def clean_yearly_table(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(axis=1, how="all").copy()
    new_cols = []
    for col in df.columns:
        try:
            new_cols.append(str(pd.to_datetime(col).year))
        except Exception:
            new_cols.append(str(col))
    df.columns = new_cols
    df = df.T.groupby(level=0).first().T
    try:
        df = df.reindex(sorted(df.columns, key=int), axis=1)
    except Exception:
        pass
    return df


def fmt_big(n):
    if pd.isna(n): return "N/A"
    if abs(n) >= 1e12: return f"${n/1e12:.2f}T"
    if abs(n) >= 1e9:  return f"${n/1e9:.2f}B"
    if abs(n) >= 1e6:  return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"


def fmt_pct(n):
    if pd.isna(n): return "N/A"
    return f"{n*100:.2f}%"


def fmt_num(n, dec=2):
    if pd.isna(n): return "N/A"
    return f"{n:.{dec}f}"


def card_html(label, value, sub="", accent="#534AB7", quality=""):
    return f"""
    <div class="fin-card {quality}" style="--accent:{accent}">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        {"<div class='sub'>" + sub + "</div>" if sub else ""}
    </div>"""


def quality(val, low, high):
    if pd.isna(val): return ""
    return "good" if val >= high else ("warn" if val >= low else "bad")


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten MultiIndex columns produced by newer yfinance versions."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.loc[:, ~df.columns.duplicated()]
    for col in df.columns:
        if isinstance(df[col], pd.DataFrame):
            df[col] = df[col].iloc[:, 0]
    return df


# ── Data fetching (cached) ─────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_data(sym):
    for attempt in range(3):
        try:
            session = _make_session()
            t = yf.Ticker(sym, session=session)
            h5 = t.history(period="5y")
            h1 = t.history(period="1y")
            h5 = flatten_columns(h5)
            h1 = flatten_columns(h1)
            return t.balance_sheet, t.financials, t.cashflow, h5, h1
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                raise e


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_meta(sym):
    session = _make_session()
    t = yf.Ticker(sym, session=session)
    mc, sh, name, sector, industry, country, employees = np.nan, np.nan, sym, "", "", "", None
    is_etf = False
    etf_extra = {}
    try:
        f = t.fast_info
        mc = f.get("market_cap", np.nan)
        sh = f.get("shares", np.nan)
    except Exception:
        pass
    try:
        info = t.info
        mc       = info.get("marketCap", mc)
        sh       = info.get("sharesOutstanding", sh)
        name     = info.get("longName", info.get("shortName", sym))
        sector   = info.get("sector", "")
        industry = info.get("industry", "")
        country  = info.get("country", "")
        employees= info.get("fullTimeEmployees", None)
        if info.get("quoteType", "") in ("ETF", "MUTUALFUND") or \
           (not sector and info.get("fundFamily")):
            is_etf = True
            etf_extra = {
                "fund_family":   info.get("fundFamily", "N/A"),
                "category":      info.get("category", "N/A"),
                "expense_ratio": info.get("annualReportExpenseRatio",
                                 info.get("totalExpenseRatio", np.nan)),
                "nav":           info.get("navPrice", np.nan),
                "aum":           info.get("totalAssets", np.nan),
                "ytd_return":    info.get("ytdReturn", np.nan),
                "three_year":    info.get("threeYearAverageReturn", np.nan),
                "five_year":     info.get("fiveYearAverageReturn", np.nan),
                "beta_3y":       info.get("beta3Year", np.nan),
            }
    except Exception:
        pass
    return {"market_cap": mc, "shares_outstanding": sh, "name": name,
            "sector": sector, "industry": industry, "country": country,
            "employees": employees, "is_etf": is_etf, "etf_extra": etf_extra}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_market():
    session = _make_session()
    market = yf.download("^GSPC", period="10y", auto_adjust=True, progress=False,
                         session=session, multi_level_index=False)
    rf     = yf.download("^TNX",  period="5d",  auto_adjust=True, progress=False,
                         session=session, multi_level_index=False)
    market = flatten_columns(market)
    rf     = flatten_columns(rf)
    if isinstance(market.get("Close"), pd.DataFrame):
        market["Close"] = market["Close"].iloc[:, 0]
    if isinstance(rf.get("Close"), pd.DataFrame):
        rf["Close"] = rf["Close"].iloc[:, 0]
    return market, rf


# ── Analysis functions ─────────────────────────────────────────────────────────

def liquidity_analysis(balance):
    ca  = get_row(balance, ["Current Assets", "Total Current Assets"])
    cl  = get_row(balance, ["Current Liabilities", "Total Current Liabilities"])
    inv = get_row(balance, ["Inventory", "Inventories"])
    csh = get_row(balance, ["Cash And Cash Equivalents", "Cash",
                             "Cash Cash Equivalents And Short Term Investments"])
    df = pd.DataFrame({
        "Current Assets": ca, "Current Liabilities": cl,
        "Inventory": inv, "Cash": csh,
        "Current Ratio": ca / cl,
        "Quick Ratio": (ca - inv.fillna(0)) / cl,
        "Cash Ratio": csh / cl,
    }).T
    df = clean_yearly_table(df)
    return df, df.loc[["Current Ratio", "Quick Ratio", "Cash Ratio"]]


def profitability_analysis(balance, income):
    rev = get_row(income,  ["Total Revenue", "Revenue"])
    gp  = get_row(income,  ["Gross Profit"])
    oi  = get_row(income,  ["Operating Income"])
    ni  = get_row(income,  ["Net Income"])
    ta  = get_row(balance, ["Total Assets"])
    eq  = get_row(balance, ["Total Stockholder Equity", "Stockholders Equity"])
    eps = get_row(income,  ["Diluted EPS", "Basic EPS"])
    df = pd.DataFrame({
        "Revenue": rev, "Gross Profit": gp, "Operating Income": oi, "Net Income": ni,
        "Gross Margin": gp/rev, "Operating Margin": oi/rev, "Net Margin": ni/rev,
        "Return On Assets": ni/ta, "Return On Equity": ni/eq, "Earnings Per Share": eps,
    }).T
    df = clean_yearly_table(df)
    return df, df.loc[["Gross Margin","Operating Margin","Net Margin",
                        "Return On Assets","Return On Equity","Earnings Per Share"]]


def additional_ratios(balance, income, cashflow, price_5y, profitability_df):
    eq   = get_row(balance,  ["Total Stockholder Equity", "Stockholders Equity"])
    td   = get_row(balance,  ["Total Debt", "Long Term Debt"])
    div  = get_row(cashflow, ["Cash Dividends Paid", "Dividends Paid", "Common Stock Dividend Paid"])
    ni   = get_row(income,   ["Net Income"])
    roe  = profitability_df.loc["Return On Equity"]

    cp   = float(price_5y["Close"].dropna().iloc[-1]) if not price_5y.empty else np.nan
    ly   = profitability_df.columns[-1]
    eps  = profitability_df.loc["Earnings Per Share", ly]
    pe   = cp / eps if pd.notna(eps) and eps != 0 else np.nan
    pe_s = pd.Series(np.nan, index=profitability_df.columns)
    pe_s.loc[ly] = pe

    dpr  = abs(div) / ni
    dte  = td / eq
    sgr  = roe * (1 - dpr)

    df = pd.DataFrame({"P/E Ratio": pe_s, "Dividend Payout Ratio": dpr,
                        "Debt to Equity": dte, "Sustainable Growth Rate": sgr}).T
    return clean_yearly_table(df)


def capm_analysis(price_5y):
    sr = price_5y["Close"].pct_change().dropna()
    if sr.empty:
        return {"beta": np.nan, "risk_free_rate": np.nan,
                "market_return": np.nan, "expected_return": np.nan,
                "slope": np.nan, "r_squared": np.nan}
    try:
        sr.index = sr.index.tz_localize(None)
    except Exception:
        pass
    market, rf_data = fetch_market()
    mr = market["Close"].pct_change().dropna()
    ret = pd.concat([sr, mr], axis=1).dropna()
    ret.columns = ["Stock", "Market"]
    if ret.empty:
        return {"beta": np.nan, "risk_free_rate": np.nan,
                "market_return": np.nan, "expected_return": np.nan,
                "slope": np.nan, "r_squared": np.nan}
    cov = ret.cov().iloc[0, 1]
    mv  = ret["Market"].var()
    beta = cov / mv if mv != 0 else np.nan
    slope, intercept, r_val, p_val, se = stats.linregress(ret["Market"], ret["Stock"])
    rf   = float(rf_data["Close"].iloc[-1]) / 100 if not rf_data.empty else np.nan
    mr10 = ret["Market"].mean() * 252
    er   = rf + beta * (mr10 - rf) if pd.notna(rf) and pd.notna(beta) else np.nan
    return {"beta": beta, "risk_free_rate": rf, "market_return": mr10,
            "expected_return": er, "slope": slope, "r_squared": r_val**2}


def fcf_analysis(cashflow):
    ocf   = get_row(cashflow, ["Operating Cash Flow", "Total Cash From Operating Activities"])
    capex = get_row(cashflow, ["Capital Expenditure", "Capital Expenditures"])
    fcf   = ocf + capex
    df    = pd.DataFrame({"Operating Cash Flow": ocf,
                           "Capital Expenditures": capex, "Free Cash Flow": fcf}).T
    return clean_yearly_table(df), fcf


def wacc_analysis(meta, balance, income, expected_return):
    mc  = meta.get("market_cap", np.nan)
    td  = get_row(balance, ["Total Debt", "Long Term Debt"])
    ie  = get_row(income, ["Interest Expense","Interest Expense Non Operating",
                            "Net Non Operating Interest Income Expense"])
    itx = get_row(income, ["Tax Provision"])
    pti = get_row(income, ["Pretax Income"])
    ds  = td.dropna(); ies = ie.dropna()
    ity = itx.dropna(); pts = pti.dropna()
    cdy = ds.index.intersection(ies.index)
    if len(cdy):
        dy = cdy[0]; tdm = ds.loc[dy]; iem = ies.loc[dy]
        cod = abs(iem)/tdm if tdm != 0 else np.nan
    else:
        tdm = cod = np.nan
    cty = ity.index.intersection(pts.index)
    if len(cty):
        ty = cty[0]; itm = ity.loc[ty]; ptm = pts.loc[ty]
        tr = abs(itm)/abs(ptm) if ptm != 0 else np.nan
    else:
        tr = np.nan
    E = mc; D = tdm; V = E + D
    w = ((E/V)*expected_return + (D/V)*cod*(1-tr)
         if all(pd.notna(x) for x in [D,cod,tr,expected_return]) and V != 0 else np.nan)
    return {"market_cap": mc, "total_debt": tdm, "cost_of_debt": cod,
            "tax_rate": tr, "wacc": w}


def dcf_analysis(meta, fcf_series, wacc, price_5y):
    fc = fcf_series.dropna()
    if fc.empty or pd.isna(wacc) or wacc <= 0:
        return {"fcf_latest": np.nan, "firm_value": np.nan,
                "intrinsic_price": np.nan, "current_price": np.nan}
    fl   = float(fc.iloc[-1])
    sh   = meta.get("shares_outstanding", np.nan)
    g    = 0.03; yrs = 5; tg = 0.02
    pf   = [fl*(1+g)**y for y in range(1, yrs+1)]
    df_  = [pf[i]/(1+wacc)**(i+1) for i in range(yrs)]
    tv   = pf[-1]*(1+tg)/(wacc-tg) if wacc > tg else np.nan
    dtv  = tv/(1+wacc)**yrs if pd.notna(tv) else np.nan
    fv   = sum(df_) + dtv if pd.notna(dtv) else np.nan
    ip   = fv/sh if pd.notna(fv) and pd.notna(sh) and sh != 0 else np.nan
    cp   = float(price_5y["Close"].dropna().iloc[-1]) if not price_5y.empty else np.nan
    return {"fcf_latest": fl, "firm_value": fv, "intrinsic_price": ip, "current_price": cp}


# ── UI ─────────────────────────────────────────────────────────────────────────

st.markdown("""
<div style='padding: 1rem 0 0.5rem;'>
  <span style='font-size:28px; font-weight:700; color:#1e1b4b;'>MarketLens</span><br>
  <span style='font-size:13px; color:#9d8ec4;'>Data-Driven Stock Valuation & Forecasting Platform.</span>
</div>
""", unsafe_allow_html=True)

col_input, col_btn = st.columns([5, 1])
with col_input:
    ticker_symbol = st.text_input("", value="AAPL", placeholder="e.g. AAPL, MSFT, TSLA",
                                   label_visibility="collapsed").strip().upper()
with col_btn:
    st.markdown("<div style='padding-top:4px'>", unsafe_allow_html=True)
    analyse = st.button("Analyse →", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

if analyse:
    try:
        with st.spinner("Fetching financial data…"):
            balance, income, cashflow, price_5y, price_1y = fetch_data(ticker_symbol)
            meta = fetch_meta(ticker_symbol)

        is_etf = meta.get("is_etf", False)

        # ── ETF branch ────────────────────────────────────────────────────────
        if is_etf or (balance.empty and income.empty):
            ex = meta.get("etf_extra", {})
            cp = float(price_5y["Close"].dropna().iloc[-1]) if not price_5y.empty else np.nan
            prev_row = price_5y["Close"].dropna()
            change   = float(prev_row.iloc[-1] - prev_row.iloc[-2]) if len(prev_row) >= 2 else 0
            chg_pct  = (change / float(prev_row.iloc[-2])) * 100 if len(prev_row) >= 2 else 0
            chg_cls  = "price-up" if change >= 0 else "price-down"
            chg_sign = "+" if change >= 0 else ""
            name     = meta.get("name", ticker_symbol)

            st.markdown(f"""
            <div class="company-header">
              <div>
                <div class="company-name">{name}
                  <span style='font-size:15px;font-weight:400;color:#9d8ec4;'>{ticker_symbol}</span>
                </div>
                <div class="company-sub">{ex.get('fund_family','N/A')} · {ex.get('category','N/A')}</div>
                <span class="rec-badge" style="background:#ede9fe;color:#5b21b6;font-size:11px;font-weight:700;padding:3px 12px;border-radius:20px;margin-top:8px;display:inline-block;">ETF</span>
              </div>
              <div>
                <div class="price-big">${cp:,.2f}</div>
                <div class="price-change {chg_cls}">{chg_sign}{change:.2f} ({chg_sign}{chg_pct:.2f}%)</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="section-header">Fund overview</div>', unsafe_allow_html=True)
            aum_v  = ex.get('aum', np.nan)
            nav_v  = ex.get('nav', np.nan)
            exp_v  = ex.get('expense_ratio', np.nan)
            ytd_v  = ex.get('ytd_return', np.nan)
            t3_v   = ex.get('three_year', np.nan)
            t5_v   = ex.get('five_year', np.nan)
            st.markdown(f"""
            <div class="ov-grid">
              <div class="ov-item"><div class="ov-label">AUM</div><div class="ov-val">{fmt_big(aum_v)}</div></div>
              <div class="ov-item"><div class="ov-label">NAV</div><div class="ov-val">{fmt_big(nav_v) if pd.notna(nav_v) else 'N/A'}</div></div>
              <div class="ov-item"><div class="ov-label">Expense ratio</div><div class="ov-val">{fmt_pct(exp_v) if pd.notna(exp_v) else 'N/A'}</div></div>
              <div class="ov-item"><div class="ov-label">YTD return</div><div class="ov-val">{fmt_pct(ytd_v) if pd.notna(ytd_v) else 'N/A'}</div></div>
              <div class="ov-item"><div class="ov-label">3-year avg return</div><div class="ov-val">{fmt_pct(t3_v) if pd.notna(t3_v) else 'N/A'}</div></div>
              <div class="ov-item"><div class="ov-label">5-year avg return</div><div class="ov-val">{fmt_pct(t5_v) if pd.notna(t5_v) else 'N/A'}</div></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="section-header">1-year price</div>', unsafe_allow_html=True)
            fig, ax = plt.subplots(figsize=(12, 3.5))
            fig.patch.set_facecolor("#ffffff"); ax.set_facecolor("#ffffff")
            closes = price_1y["Close"]
            ax.plot(closes.index, closes.values, color="#7C3AED", linewidth=2)
            ax.fill_between(closes.index, closes.values, closes.min(), alpha=0.08, color="#7C3AED")
            ax.set_xlabel("Date", color="#9d8ec4", fontsize=10)
            ax.set_ylabel("Price (USD)", color="#9d8ec4", fontsize=10)
            ax.tick_params(colors="#9d8ec4")
            ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
            for spine in ax.spines.values(): spine.set_edgecolor("#e2dff0")
            ax.grid(axis="y", color="#e2dff0", linewidth=0.5)
            plt.tight_layout(); st.pyplot(fig); plt.close()

            capm_etf = capm_analysis(price_5y)
            st.markdown('<div class="section-header">CAPM & risk</div>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            beta_3y = ex.get('beta_3y', np.nan)
            beta_q  = "good" if pd.notna(capm_etf['beta']) and capm_etf['beta'] < 0.8 else \
                      "warn" if pd.notna(capm_etf['beta']) and capm_etf['beta'] < 1.5 else "bad"
            with c1:
                st.markdown(card_html("Beta (3Y fund)", fmt_num(beta_3y), "Reported by fund", "#534AB7", beta_q), unsafe_allow_html=True)
            with c2:
                st.markdown(card_html("Beta (calc)", fmt_num(capm_etf['beta']), "Regression vs S&P 500", "#7C3AED", beta_q), unsafe_allow_html=True)
            with c3:
                st.markdown(card_html("Risk-free rate", fmt_pct(capm_etf['risk_free_rate']), "10Y US Treasury", "#185FA5"), unsafe_allow_html=True)
            with c4:
                st.markdown(card_html("Expected return", fmt_pct(capm_etf['expected_return']), "Re = Rf + β(Rm − Rf)", "#D85A30"), unsafe_allow_html=True)

            st.info(f"**{ticker_symbol} is an ETF.** Financial statements are not available for funds — showing fund-specific metrics above instead.")
            st.stop()

        # ── Stock branch ──────────────────────────────────────────────────────
        if price_5y.empty:
            st.error("No price data found for this ticker.")
            st.stop()

        liq_df,  liq_ratios  = liquidity_analysis(balance)
        prof_df, prof_ratios = profitability_analysis(balance, income)
        add_df               = additional_ratios(balance, income, cashflow, price_5y, prof_df)
        capm                 = capm_analysis(price_5y)
        fcf_df, free_cf      = fcf_analysis(cashflow)
        wacc_d               = wacc_analysis(meta, balance, income, capm["expected_return"])
        dcf_d                = dcf_analysis(meta, free_cf, wacc_d["wacc"], price_5y)

        cp = dcf_d["current_price"]
        ip = dcf_d["intrinsic_price"]
        upside = ((ip - cp)/cp)*100 if pd.notna(ip) and pd.notna(cp) and cp != 0 else None

        if upside is not None:
            rec, rec_cls = ("BUY", "rec-buy") if upside >= 15 else \
                           ("SELL", "rec-sell") if upside < -15 else \
                           ("HOLD", "rec-hold")
        else:
            rec, rec_cls = "HOLD", "rec-hold"

        # ── Company header ────────────────────────────────────────────────────
        name     = meta.get("name", ticker_symbol)
        sector   = meta.get("sector", "")
        industry = meta.get("industry", "")
        prev_row = price_5y["Close"].dropna()
        change   = float(prev_row.iloc[-1] - prev_row.iloc[-2]) if len(prev_row) >= 2 else 0
        chg_pct  = (change / float(prev_row.iloc[-2])) * 100 if len(prev_row) >= 2 else 0
        chg_cls  = "price-up" if change >= 0 else "price-down"
        chg_sign = "+" if change >= 0 else ""

        st.markdown(f"""
        <div class="company-header">
          <div>
            <div class="company-name">{name}
              <span style='font-size:15px;font-weight:400;color:#6b7280;'>{ticker_symbol}</span>
            </div>
            <div class="company-sub">{sector} · {industry}</div>
            <span class="rec-badge" style="background:#ede9fe;color:#5b21b6;">STOCK</span>
          </div>
          <div>
            <div class="price-big">${cp:,.2f}</div>
            <div class="price-change {chg_cls}">{chg_sign}{change:.2f} ({chg_sign}{chg_pct:.2f}%)</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Company overview ──────────────────────────────────────────────────
        st.markdown('<div class="section-header">Company overview</div>', unsafe_allow_html=True)
        rev_val = get_row(income, ["Total Revenue", "Revenue"]).dropna().iloc[-1] \
                  if not get_row(income, ["Total Revenue","Revenue"]).dropna().empty else np.nan
        ni_val  = get_row(income, ["Net Income"]).dropna().iloc[-1] \
                  if not get_row(income, ["Net Income"]).dropna().empty else np.nan
        ocf_val = get_row(cashflow, ["Operating Cash Flow","Total Cash From Operating Activities"]).dropna().iloc[-1] \
                  if not get_row(cashflow, ["Operating Cash Flow","Total Cash From Operating Activities"]).dropna().empty else np.nan
        employees = meta.get("employees")
        emp_str   = f"{employees:,}" if employees else "N/A"

        st.markdown(f"""
        <div class="ov-grid">
          <div class="ov-item"><div class="ov-label">Market cap</div><div class="ov-val">{fmt_big(meta.get('market_cap'))}</div></div>
          <div class="ov-item"><div class="ov-label">Revenue (TTM)</div><div class="ov-val">{fmt_big(rev_val)}</div></div>
          <div class="ov-item"><div class="ov-label">Net income</div><div class="ov-val">{fmt_big(ni_val)}</div></div>
          <div class="ov-item"><div class="ov-label">Operating CF</div><div class="ov-val">{fmt_big(ocf_val)}</div></div>
          <div class="ov-item"><div class="ov-label">Employees</div><div class="ov-val">{emp_str}</div></div>
          <div class="ov-item"><div class="ov-label">Country</div><div class="ov-val">{meta.get('country','N/A')}</div></div>
        </div>
        """, unsafe_allow_html=True)

        # ── 1-Year stock price chart ──────────────────────────────────────────
        st.markdown('<div class="section-header">1-year stock price</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(12, 3.5))
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#ffffff")
        closes = price_1y["Close"]
        ax.plot(closes.index, closes.values, color="#7C3AED", linewidth=2)
        ax.fill_between(closes.index, closes.values, closes.min(), alpha=0.08, color="#7C3AED")
        ax.set_xlabel("Date", color="#9d8ec4", fontsize=10)
        ax.set_ylabel("Price (USD)", color="#9d8ec4", fontsize=10)
        ax.tick_params(colors="#9d8ec4")
        ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
        for spine in ax.spines.values(): spine.set_edgecolor("#e2dff0")
        ax.grid(axis="y", color="#e2dff0", linewidth=0.5)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        # ── Profitability ratios ───────────────────────────────────────────────
        st.markdown('<div class="section-header">Profitability ratios</div>', unsafe_allow_html=True)
        ly = prof_df.columns[-1]

        def pv(df, row, yr):
            try: return float(df.loc[row, yr])
            except: return np.nan

        gm  = pv(prof_df, "Gross Margin",      ly)
        om  = pv(prof_df, "Operating Margin",   ly)
        nm  = pv(prof_df, "Net Margin",         ly)
        roa = pv(prof_df, "Return On Assets",   ly)
        roe = pv(prof_df, "Return On Equity",   ly)
        eps = pv(prof_df, "Earnings Per Share",  ly)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(card_html("Gross margin",     fmt_pct(gm),  "Gross profit / revenue",   "#1D9E75", quality(gm,  0.2, 0.4)), unsafe_allow_html=True)
            st.markdown(card_html("Return on assets", fmt_pct(roa), "Net income / total assets", "#D85A30", quality(roa, 0.03,0.1)), unsafe_allow_html=True)
        with c2:
            st.markdown(card_html("Operating margin", fmt_pct(om),  "EBIT / revenue",            "#185FA5", quality(om,  0.1, 0.25)), unsafe_allow_html=True)
            st.markdown(card_html("Return on equity", fmt_pct(roe), "Net income / equity",        "#D4537E", quality(roe, 0.1, 0.2)),  unsafe_allow_html=True)
        with c3:
            st.markdown(card_html("Net margin",       fmt_pct(nm),  "Net income / revenue",      "#534AB7", quality(nm,  0.05,0.15)), unsafe_allow_html=True)
            st.markdown(card_html("EPS",              f"${fmt_num(eps)}" if pd.notna(eps) else "N/A",
                                  "Diluted earnings per share",   "#BA7517"), unsafe_allow_html=True)

        # ── Liquidity ratios ───────────────────────────────────────────────────
        st.markdown('<div class="section-header">Liquidity ratios</div>', unsafe_allow_html=True)
        lly = liq_ratios.columns[-1]
        cr = float(liq_ratios.loc["Current Ratio", lly]) if "Current Ratio" in liq_ratios.index else np.nan
        qr = float(liq_ratios.loc["Quick Ratio",   lly]) if "Quick Ratio"   in liq_ratios.index else np.nan
        ar = float(liq_ratios.loc["Cash Ratio",    lly]) if "Cash Ratio"    in liq_ratios.index else np.nan

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(card_html("Current ratio", fmt_num(cr), "Current assets / liabilities", "#1D9E75", quality(cr, 1.0, 2.0)), unsafe_allow_html=True)
        with c2:
            st.markdown(card_html("Quick ratio",   fmt_num(qr), "(Assets − inventory) / liab", "#185FA5", quality(qr, 0.8, 1.5)), unsafe_allow_html=True)
        with c3:
            st.markdown(card_html("Cash ratio",    fmt_num(ar), "Cash / current liabilities",  "#534AB7", quality(ar, 0.2, 0.5)), unsafe_allow_html=True)

        # ── Additional ratios ─────────────────────────────────────────────────
        st.markdown('<div class="section-header">Additional ratios</div>', unsafe_allow_html=True)
        aly = add_df.columns[-1]
        def av(row):
            try: return float(add_df.loc[row, aly])
            except: return np.nan
        pe  = av("P/E Ratio")
        dpr = av("Dividend Payout Ratio")
        dte = av("Debt to Equity")
        sgr = av("Sustainable Growth Rate")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(card_html("P/E ratio",          fmt_num(pe),  "Price / earnings",        "#BA7517"), unsafe_allow_html=True)
        with c2:
            st.markdown(card_html("Div payout ratio",   fmt_pct(dpr), "Dividends / net income",  "#D4537E"), unsafe_allow_html=True)
        with c3:
            st.markdown(card_html("Debt-to-equity",     fmt_num(dte), "Total debt / equity",     "#D85A30",
                                  quality(2-dte if pd.notna(dte) else np.nan, 0, 1)), unsafe_allow_html=True)
        with c4:
            st.markdown(card_html("Sust. growth rate",  fmt_pct(sgr), "ROE × retention ratio",   "#1D9E75",
                                  quality(sgr, 0.05, 0.12)), unsafe_allow_html=True)

        # ── CAPM ──────────────────────────────────────────────────────────────
        st.markdown('<div class="section-header">CAPM & cost of equity</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        beta_q = "good" if pd.notna(capm['beta']) and capm['beta'] < 0.8 else \
                 "warn" if pd.notna(capm['beta']) and capm['beta'] < 1.5 else "bad"
        with c1:
            st.markdown(card_html("Beta",            fmt_num(capm['beta']),          "Market sensitivity",         "#534AB7", beta_q), unsafe_allow_html=True)
        with c2:
            st.markdown(card_html("Risk-free rate",  fmt_pct(capm['risk_free_rate']),"10Y US Treasury",            "#185FA5"), unsafe_allow_html=True)
        with c3:
            st.markdown(card_html("Market return",   fmt_pct(capm['market_return']), "S&P 500 10Y avg",            "#1D9E75"), unsafe_allow_html=True)
        with c4:
            st.markdown(card_html("Expected return", fmt_pct(capm['expected_return']),"Re = Rf + β(Rm − Rf)",      "#D85A30"), unsafe_allow_html=True)

        # Regression scatter
        with st.expander("Show beta regression plot"):
            ret_df = pd.DataFrame()
            try:
                sr = price_5y["Close"].pct_change().dropna()
                sr.index = sr.index.tz_localize(None)
                mkt, _ = fetch_market()
                mr = mkt["Close"].pct_change().dropna()
                ret_df = pd.concat([sr, mr], axis=1).dropna()
                ret_df.columns = ["Stock", "Market"]
            except Exception:
                pass
            if not ret_df.empty:
                fig2, ax2 = plt.subplots(figsize=(7, 4))
                fig2.patch.set_facecolor("#ffffff")
                ax2.set_facecolor("#ffffff")
                ax2.scatter(ret_df["Market"], ret_df["Stock"], alpha=0.25, s=6, color="#a78bfa")
                xs = np.linspace(ret_df["Market"].min(), ret_df["Market"].max(), 100)
                ax2.plot(xs, capm["slope"]*xs, color="#7C3AED", linewidth=2,
                         label=f"β={capm['slope']:.3f}  R²={capm['r_squared']:.3f}")
                ax2.set_xlabel("S&P 500 daily return", color="#9d8ec4", fontsize=10)
                ax2.set_ylabel(f"{ticker_symbol} daily return", color="#9d8ec4", fontsize=10)
                ax2.tick_params(colors="#9d8ec4")
                for sp in ax2.spines.values(): sp.set_edgecolor("#e2dff0")
                ax2.grid(color="#e2dff0", linewidth=0.5)
                ax2.legend(fontsize=9, facecolor="#ffffff", labelcolor="#1e1b4b")
                plt.tight_layout()
                st.pyplot(fig2)
                plt.close()

        # ── FCF ───────────────────────────────────────────────────────────────
        st.markdown('<div class="section-header">Free cash flow</div>', unsafe_allow_html=True)
        fcf_row = fcf_df.loc["Free Cash Flow"] if "Free Cash Flow" in fcf_df.index else pd.Series()
        if not fcf_row.empty:
            fig3, ax3 = plt.subplots(figsize=(8, 3))
            fig3.patch.set_facecolor("#ffffff")
            ax3.set_facecolor("#ffffff")
            colors = ["#7C3AED" if v >= 0 else "#b91c1c" for v in fcf_row.values]
            ax3.bar(fcf_row.index, fcf_row.values / 1e9, color=colors, width=0.5, edgecolor="#e2dff0")
            ax3.set_ylabel("USD (Billions)", color="#9d8ec4", fontsize=10)
            ax3.tick_params(colors="#9d8ec4")
            ax3.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:.0f}B"))
            for sp in ax3.spines.values(): sp.set_edgecolor("#e2dff0")
            ax3.grid(axis="y", color="#e2dff0", linewidth=0.5)
            plt.tight_layout()
            st.pyplot(fig3)
            plt.close()

        fcf_latest = dcf_d["fcf_latest"]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(card_html("Latest FCF", fmt_big(fcf_latest), "Most recent annual FCF", "#1D9E75"), unsafe_allow_html=True)
        with c2:
            ocf_latest = get_row(cashflow, ["Operating Cash Flow","Total Cash From Operating Activities"]).dropna()
            st.markdown(card_html("Operating CF", fmt_big(float(ocf_latest.iloc[-1]) if not ocf_latest.empty else np.nan), "Cash from operations", "#185FA5"), unsafe_allow_html=True)
        with c3:
            capex_latest = get_row(cashflow, ["Capital Expenditure","Capital Expenditures"]).dropna()
            st.markdown(card_html("CapEx", fmt_big(float(capex_latest.iloc[-1]) if not capex_latest.empty else np.nan), "Capital expenditures", "#D85A30"), unsafe_allow_html=True)

        # ── WACC & DCF ────────────────────────────────────────────────────────
        st.markdown('<div class="section-header">WACC & DCF valuation</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(card_html("WACC",          fmt_pct(wacc_d['wacc']),         "Weighted avg cost of capital", "#534AB7"), unsafe_allow_html=True)
        with c2:
            st.markdown(card_html("Cost of debt",  fmt_pct(wacc_d['cost_of_debt']), "Interest / total debt",        "#D85A30"), unsafe_allow_html=True)
        with c3:
            st.markdown(card_html("Tax rate",      fmt_pct(wacc_d['tax_rate']),     "Effective tax rate",           "#BA7517"), unsafe_allow_html=True)
        with c4:
            st.markdown(card_html("Firm value",    fmt_big(dcf_d['firm_value']),    "Sum of discounted FCFs",       "#1D9E75"), unsafe_allow_html=True)

        # Valuation bar
        if pd.notna(ip) and pd.notna(cp):
            bar_w    = min(max((upside + 50) / 100 * 100, 2), 100)
            bar_col  = "#15803d" if upside >= 0 else "#b91c1c"
            upside_str = f"{'+' if upside>=0 else ''}{upside:.1f}%"
            st.markdown(f"""
            <div class="val-section">
              <div class="val-row"><span class="val-lbl">Current market price</span><span class="val-num">${cp:,.2f}</span></div>
              <div class="val-row"><span class="val-lbl">Intrinsic price (DCF)</span><span class="val-num">${ip:,.2f}</span></div>
              <div class="val-row"><span class="val-lbl">Upside / downside</span>
                <span class="val-num" style="color:{bar_col}">{upside_str}</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" style="width:{bar_w:.1f}%;background:{bar_col}"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        if "Too Many Requests" in str(e) or "Rate limited" in str(e) or "429" in str(e):
            st.warning("⚠️ Yahoo Finance is rate-limiting this server. Retrying in 5 seconds...")
            time.sleep(5)
            try:
                st.cache_data.clear()
                st.rerun()
            except Exception:
                st.error("Still rate-limited. Please wait 30 seconds and click Analyse again.")
        else:
            st.error(f"Could not analyse {ticker_symbol}: {e}")