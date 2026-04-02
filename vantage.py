import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import scipy.stats as stats

pd.options.display.float_format = '{:,.2f}'.format

st.set_page_config(page_title="Vantage Finance", layout="wide")

# ── Global styles — Soft Purple & Slate fintech theme ─────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f4f3f8; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #eeecf6; }

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

.ov-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 4px; }
.ov-item { background: #ffffff; border: 1px solid #e2dff0; border-radius: 10px; padding: 12px 14px; }
.ov-label { font-size: 11px; color: #9d8ec4; margin-bottom: 4px; font-weight: 500; }
.ov-val   { font-size: 14px; font-weight: 700; color: #1e1b4b; }

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

.sector-row {
    display: flex;
    align-items: center;
    background: #ffffff;
    border: 1px solid #e2dff0;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 6px;
    gap: 12px;
}
.sector-rank { font-size: 12px; color: #9d8ec4; font-weight: 700; width: 24px; }
.sector-sym  { font-size: 14px; font-weight: 700; color: #1e1b4b; flex: 1; }
.sector-mc   { font-size: 13px; color: #534AB7; font-weight: 600; flex: 1; text-align: right; }
.sector-px   { font-size: 13px; color: #1e1b4b; flex: 1; text-align: right; }

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Sector data ────────────────────────────────────────────────────────────────

SECTOR_TICKERS = {
    "Technology":            ["AAPL","MSFT","NVDA","AVGO","ORCL","AMD","QCOM","INTC","IBM","TXN"],
    "Healthcare":            ["LLY","UNH","JNJ","ABBV","MRK","ABT","TMO","DHR","AMGN","PFE"],
    "Financials":            ["BRK-B","JPM","V","MA","BAC","WFC","GS","MS","BLK","AXP"],
    "Consumer Discretionary":["AMZN","TSLA","HD","MCD","NKE","LOW","SBUX","TJX","BKNG","ABNB"],
    "Communication Services":["GOOGL","META","NFLX","DIS","CMCSA","T","VZ","TMUS","EA","PARA"],
    "Industrials":           ["GE","CAT","RTX","HON","UPS","DE","LMT","BA","MMM","CSX"],
    "Energy":                ["XOM","CVX","COP","EOG","SLB","MPC","PSX","VLO","OXY","KMI"],
    "Consumer Staples":      ["WMT","PG","KO","PEP","COST","PM","MO","CL","MDLZ","KHC"],
    "Real Estate":           ["PLD","AMT","EQIX","CCI","SPG","PSA","O","WELL","AVB","DLR"],
    "Utilities":             ["NEE","SO","DUK","AEP","SRE","D","XEL","EXC","PCG","AWK"],
    "Materials":             ["LIN","APD","SHW","ECL","NEM","FCX","NUE","VMC","MLM","ALB"],
}

ASSET_TYPES = {
    "Stock / ETF": "stock",
    "Cryptocurrency": "crypto",
    "Forex": "forex",
    "Futures": "futures",
    "Index": "index",
}

CRYPTO_EXAMPLES  = ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD"]
FOREX_EXAMPLES   = ["EURUSD=X","GBPUSD=X","JPYUSD=X","AUDUSD=X","CADUSD=X"]
FUTURES_EXAMPLES = ["CL=F","GC=F","SI=F","NG=F","ZC=F"]
INDEX_EXAMPLES   = ["^GSPC","^DJI","^IXIC","^RUT","^VIX"]


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


# ── Data fetching ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_data(sym):
    t = yf.Ticker(sym)
    return t.balance_sheet, t.financials, t.cashflow, t.history(period="5y"), t.history(period="1y")


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_meta(sym):
    t = yf.Ticker(sym)
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
    market = yf.download("^GSPC", period="10y", auto_adjust=True, progress=False)
    rf     = yf.download("^TNX",  period="5d",  auto_adjust=True, progress=False)
    return market, rf


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_sector_snapshot(tickers: tuple):
    rows = []
    for sym in tickers:
        try:
            info = yf.Ticker(sym).fast_info
            rows.append({
                "Ticker":     sym,
                "Market Cap": info.get("market_cap", np.nan),
                "Price":      info.get("last_price",  np.nan),
            })
        except Exception:
            rows.append({"Ticker": sym, "Market Cap": np.nan, "Price": np.nan})
    df = pd.DataFrame(rows).set_index("Ticker")
    df = df.sort_values("Market Cap", ascending=False)
    return df


@st.cache_data(ttl=900, show_spinner=False)
def fetch_simple_history(sym, period="1y"):
    return yf.Ticker(sym).history(period=period)


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
    cov  = ret.cov().iloc[0, 1]
    mv   = ret["Market"].var()
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


# ── Price chart helper ─────────────────────────────────────────────────────────

def draw_price_chart(price_1y, ticker_symbol):
    fig, ax = plt.subplots(figsize=(12, 3.5))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")
    closes = price_1y["Close"]
    ax.plot(closes.index, closes.values, color="#7C3AED", linewidth=2)
    ax.fill_between(closes.index, closes.values, closes.min(), alpha=0.08, color="#7C3AED")
    ax.set_xlabel("Date", color="#9d8ec4", fontsize=10)
    ax.set_ylabel("Price (USD)", color="#9d8ec4", fontsize=10)
    ax.tick_params(colors="#9d8ec4")
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.2f}"))
    for spine in ax.spines.values():
        spine.set_edgecolor("#e2dff0")
    ax.grid(axis="y", color="#e2dff0", linewidth=0.5)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style='padding: 0.5rem 0 1rem;'>
      <span style='font-size:20px; font-weight:800; color:#1e1b4b;'>Vantage Finance</span><br>
      <span style='font-size:11px; color:#9d8ec4;'>Professional financial analytics</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🏭 Sector Explorer")
    st.caption("Live top 10 by market cap — click any ticker to analyse it.")

    chosen_sector = st.selectbox("Sector", list(SECTOR_TICKERS.keys()))

    if st.button("Load Top 10 →", use_container_width=True):
        st.session_state["show_sector"] = chosen_sector

    st.markdown("---")
    st.markdown("### 🌐 Asset Types")
    st.caption("Vantage supports stocks, ETFs, crypto, forex, futures & indices.")
    with st.expander("See example tickers"):
        st.markdown("**Crypto:** " + " · ".join(CRYPTO_EXAMPLES))
        st.markdown("**Forex:** " + " · ".join(FOREX_EXAMPLES))
        st.markdown("**Futures:** " + " · ".join(FUTURES_EXAMPLES))
        st.markdown("**Indices:** " + " · ".join(INDEX_EXAMPLES))


# ── Sector Explorer Panel ──────────────────────────────────────────────────────

if "show_sector" in st.session_state:
    sector_name = st.session_state["show_sector"]
    tickers     = SECTOR_TICKERS[sector_name]

    st.markdown(f"""
    <div style='padding: 0.5rem 0 0.2rem;'>
      <span style='font-size:22px; font-weight:800; color:#1e1b4b;'>🏭 {sector_name} — Top 10</span><br>
      <span style='font-size:12px; color:#9d8ec4;'>Ranked by live market capitalisation. Click Analyse → to deep-dive any company.</span>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Fetching live market data…"):
        snap = fetch_sector_snapshot(tuple(tickers))

    header_cols = st.columns([0.4, 1.2, 1.8, 1.2, 1.2])
    header_cols[0].markdown("**#**")
    header_cols[1].markdown("**Ticker**")
    header_cols[2].markdown("**Market Cap**")
    header_cols[3].markdown("**Price**")
    header_cols[4].markdown("")

    for i, (sym, row) in enumerate(snap.iterrows(), 1):
        mc_str  = fmt_big(row["Market Cap"])
        px_str  = f"${row['Price']:,.2f}" if pd.notna(row["Price"]) else "N/A"
        c1, c2, c3, c4, c5 = st.columns([0.4, 1.2, 1.8, 1.2, 1.2])
        c1.markdown(f"**#{i}**")
        c2.markdown(f"**{sym}**")
        c3.markdown(mc_str)
        c4.markdown(px_str)
        if c5.button("Analyse →", key=f"sec_{sym}_{i}"):
            st.session_state["ticker_prefill"] = sym
            del st.session_state["show_sector"]
            st.rerun()

    if st.button("✕ Close Sector View", use_container_width=True):
        del st.session_state["show_sector"]
        st.rerun()

    st.stop()


# ── Main header & search ───────────────────────────────────────────────────────

st.markdown("""
<div style='padding: 1rem 0 0.5rem;'>
  <span style='font-size:28px; font-weight:700; color:#1e1b4b;'>⚡ Vantage Finance</span><br>
  <span style='font-size:13px; color:#9d8ec4;'>Search any stock, ETF, crypto, forex pair, futures contract or index.</span>
</div>
""", unsafe_allow_html=True)

default_ticker = st.session_state.pop("ticker_prefill", "AAPL")

col_input, col_btn = st.columns([5, 1])
with col_input:
    ticker_symbol = st.text_input(
        "", value=default_ticker,
        placeholder="e.g. AAPL · BTC-USD · EURUSD=X · GC=F · ^GSPC",
        label_visibility="collapsed"
    ).strip().upper()
with col_btn:
    st.markdown("<div style='padding-top:4px'>", unsafe_allow_html=True)
    analyse = st.button("Analyse →", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ── Asset-type detection helpers ───────────────────────────────────────────────

def detect_asset_type(sym: str) -> str:
    s = sym.upper()
    if s.endswith("-USD") or s.endswith("-USDT") or s.endswith("-BTC"):
        return "crypto"
    if s.endswith("=X"):
        return "forex"
    if s.endswith("=F"):
        return "futures"
    if s.startswith("^"):
        return "index"
    return "stock_etf"


def render_simple_asset(sym, asset_type, label_str):
    """Shared renderer for crypto / forex / futures / indices."""
    with st.spinner(f"Fetching {label_str} data…"):
        hist_1y = fetch_simple_history(sym, "1y")
        hist_5y = fetch_simple_history(sym, "5y")

    if hist_1y.empty:
        st.error(f"No data found for **{sym}**. Check the ticker and try again.")
        return

    cp       = float(hist_1y["Close"].dropna().iloc[-1])
    prev_row = hist_1y["Close"].dropna()
    change   = float(prev_row.iloc[-1] - prev_row.iloc[-2]) if len(prev_row) >= 2 else 0
    chg_pct  = (change / float(prev_row.iloc[-2])) * 100 if len(prev_row) >= 2 else 0
    chg_cls  = "price-up" if change >= 0 else "price-down"
    chg_sign = "+" if change >= 0 else ""

    hi_1y = float(hist_1y["High"].max())
    lo_1y = float(hist_1y["Low"].min())
    vol   = float(hist_1y["Volume"].mean()) if "Volume" in hist_1y else np.nan

    badge_colors = {
        "crypto":  ("#fef3c7", "#b45309", "CRYPTO"),
        "forex":   ("#e0f2fe", "#0369a1", "FOREX"),
        "futures": ("#fce7f3", "#9d174d", "FUTURES"),
        "index":   ("#ede9fe", "#5b21b6", "INDEX"),
    }
    bg, fg, badge_label = badge_colors.get(asset_type, ("#f3f4f6","#374151","ASSET"))

    try:
        info = yf.Ticker(sym).info
        full_name = info.get("longName", info.get("shortName", sym))
    except Exception:
        full_name = sym

    st.markdown(f"""
    <div class="company-header">
      <div>
        <div class="company-name">{full_name}
          <span style='font-size:15px;font-weight:400;color:#9d8ec4;'>{sym}</span>
        </div>
        <div class="company-sub">{label_str}</div>
        <span class="rec-badge" style="background:{bg};color:{fg};">{badge_label}</span>
      </div>
      <div>
        <div class="price-big">{cp:,.4f}</div>
        <div class="price-change {chg_cls}">{chg_sign}{change:.4f} ({chg_sign}{chg_pct:.2f}%)</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Key stats
    st.markdown('<div class="section-header">Key statistics</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ov-grid">
      <div class="ov-item"><div class="ov-label">Current price</div><div class="ov-val">{cp:,.4f}</div></div>
      <div class="ov-item"><div class="ov-label">52W High</div><div class="ov-val">{hi_1y:,.4f}</div></div>
      <div class="ov-item"><div class="ov-label">52W Low</div><div class="ov-val">{lo_1y:,.4f}</div></div>
      <div class="ov-item"><div class="ov-label">Avg daily volume</div><div class="ov-val">{vol:,.0f if pd.notna(vol) else 'N/A'}</div></div>
      <div class="ov-item"><div class="ov-label">1Y change</div>
        <div class="ov-val" style="color:{'#15803d' if hist_1y['Close'].iloc[-1] >= hist_1y['Close'].iloc[0] else '#b91c1c'}">
          {((hist_1y['Close'].iloc[-1]/hist_1y['Close'].iloc[0])-1)*100:.2f}%
        </div>
      </div>
      <div class="ov-item"><div class="ov-label">Data points (1Y)</div><div class="ov-val">{len(hist_1y):,}</div></div>
    </div>
    """, unsafe_allow_html=True)

    # 1Y chart
    st.markdown('<div class="section-header">1-year price chart</div>', unsafe_allow_html=True)
    draw_price_chart(hist_1y, sym)

    # CAPM / risk if 5y data available
    if not hist_5y.empty:
        capm_res = capm_analysis(hist_5y)
        st.markdown('<div class="section-header">CAPM & risk (vs S&P 500)</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        beta_q = "good" if pd.notna(capm_res['beta']) and capm_res['beta'] < 0.8 else \
                 "warn" if pd.notna(capm_res['beta']) and capm_res['beta'] < 1.5 else "bad"
        with c1:
            st.markdown(card_html("Beta (5Y)", fmt_num(capm_res['beta']), "vs S&P 500", "#534AB7", beta_q), unsafe_allow_html=True)
        with c2:
            st.markdown(card_html("Risk-free rate", fmt_pct(capm_res['risk_free_rate']), "10Y US Treasury", "#185FA5"), unsafe_allow_html=True)
        with c3:
            st.markdown(card_html("Market return", fmt_pct(capm_res['market_return']), "S&P 500 10Y avg", "#1D9E75"), unsafe_allow_html=True)
        with c4:
            st.markdown(card_html("Expected return", fmt_pct(capm_res['expected_return']), "Re = Rf + β(Rm − Rf)", "#D85A30"), unsafe_allow_html=True)

    st.info(f"**{sym}** is a {label_str}. Full financial statement analysis (WACC, DCF, ratios) is only available for individual stocks.")


# ── Main analysis ──────────────────────────────────────────────────────────────

if analyse:
    asset_type = detect_asset_type(ticker_symbol)

    # ── Non-stock assets ───────────────────────────────────────────────────────
    if asset_type == "crypto":
        render_simple_asset(ticker_symbol, "crypto", "Cryptocurrency")
        st.stop()
    elif asset_type == "forex":
        render_simple_asset(ticker_symbol, "forex", "Forex / Currency Pair")
        st.stop()
    elif asset_type == "futures":
        render_simple_asset(ticker_symbol, "futures", "Futures Contract")
        st.stop()
    elif asset_type == "index":
        render_simple_asset(ticker_symbol, "index", "Market Index")
        st.stop()

    # ── Stock / ETF ────────────────────────────────────────────────────────────
    try:
        with st.spinner("Fetching financial data…"):
            balance, income, cashflow, price_5y, price_1y = fetch_data(ticker_symbol)
            meta = fetch_meta(ticker_symbol)

        is_etf = meta.get("is_etf", False)

        # ── ETF branch ─────────────────────────────────────────────────────────
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
                <span class="rec-badge" style="background:#ede9fe;color:#5b21b6;">ETF</span>
              </div>
              <div>
                <div class="price-big">${cp:,.2f}</div>
                <div class="price-change {chg_cls}">{chg_sign}{change:.2f} ({chg_sign}{chg_pct:.2f}%)</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="section-header">Fund overview</div>', unsafe_allow_html=True)
            aum_v = ex.get('aum', np.nan)
            nav_v = ex.get('nav', np.nan)
            exp_v = ex.get('expense_ratio', np.nan)
            ytd_v = ex.get('ytd_return', np.nan)
            t3_v  = ex.get('three_year', np.nan)
            t5_v  = ex.get('five_year', np.nan)
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
            draw_price_chart(price_1y, ticker_symbol)

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

        # ── Stock branch ───────────────────────────────────────────────────────
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
            <span class="rec-badge rec-{rec.lower()}">{rec}</span>
            <span class="rec-badge" style="background:#ede9fe;color:#5b21b6;margin-left:6px;">STOCK</span>
          </div>
          <div>
            <div class="price-big">${cp:,.2f}</div>
            <div class="price-change {chg_cls}">{chg_sign}{change:.2f} ({chg_sign}{chg_pct:.2f}%)</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Company overview
        st.markdown('<div class="section-header">Company overview</div>', unsafe_allow_html=True)
        rev_val = get_row(income, ["Total Revenue", "Revenue"]).dropna()
        ni_val  = get_row(income, ["Net Income"]).dropna()
        ocf_val = get_row(cashflow, ["Operating Cash Flow","Total Cash From Operating Activities"]).dropna()
        employees = meta.get("employees")
        emp_str   = f"{employees:,}" if employees else "N/A"

        st.markdown(f"""
        <div class="ov-grid">
          <div class="ov-item"><div class="ov-label">Market cap</div><div class="ov-val">{fmt_big(meta.get('market_cap'))}</div></div>
          <div class="ov-item"><div class="ov-label">Revenue (TTM)</div><div class="ov-val">{fmt_big(float(rev_val.iloc[-1]) if not rev_val.empty else np.nan)}</div></div>
          <div class="ov-item"><div class="ov-label">Net income</div><div class="ov-val">{fmt_big(float(ni_val.iloc[-1]) if not ni_val.empty else np.nan)}</div></div>
          <div class="ov-item"><div class="ov-label">Operating CF</div><div class="ov-val">{fmt_big(float(ocf_val.iloc[-1]) if not ocf_val.empty else np.nan)}</div></div>
          <div class="ov-item"><div class="ov-label">Employees</div><div class="ov-val">{emp_str}</div></div>
          <div class="ov-item"><div class="ov-label">Country</div><div class="ov-val">{meta.get('country','N/A')}</div></div>
        </div>
        """, unsafe_allow_html=True)

        # 1-year chart
        st.markdown('<div class="section-header">1-year stock price</div>', unsafe_allow_html=True)
        draw_price_chart(price_1y, ticker_symbol)

        # Profitability ratios
        st.markdown('<div class="section-header">Profitability ratios</div>', unsafe_allow_html=True)
        ly = prof_df.columns[-1]

        def pv(df, row, yr):
            try: return float(df.loc[row, yr])
            except: return np.nan

        gm  = pv(prof_df, "Gross Margin",     ly)
        om  = pv(prof_df, "Operating Margin",  ly)
        nm  = pv(prof_df, "Net Margin",        ly)
        roa = pv(prof_df, "Return On Assets",  ly)
        roe = pv(prof_df, "Return On Equity",  ly)
        eps = pv(prof_df, "Earnings Per Share", ly)

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

        # Liquidity ratios
        st.markdown('<div class="section-header">Liquidity ratios</div>', unsafe_allow_html=True)
        lly = liq_ratios.columns[-1]
        cr = float(liq_ratios.loc["Current Ratio", lly]) if "Current Ratio" in liq_ratios.index else np.nan
        qr = float(liq_ratios.loc["Quick Ratio",   lly]) if "Quick Ratio"   in liq_ratios.index else np.nan
        ar = float(liq_ratios.loc["Cash Ratio",    lly]) if "Cash Ratio"    in liq_ratios.index else np.nan

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(card_html("Current ratio", fmt_num(cr), "Current assets / liabilities", "#1D9E75", quality(cr, 1.0, 2.0)), unsafe_allow_html=True)
        with c2:
            st.markdown(card_html("Quick ratio",   fmt_num(qr), "(Assets − inventory) / liab",  "#185FA5", quality(qr, 0.8, 1.5)), unsafe_allow_html=True)
        with c3:
            st.markdown(card_html("Cash ratio",    fmt_num(ar), "Cash / current liabilities",   "#534AB7", quality(ar, 0.2, 0.5)), unsafe_allow_html=True)

        # Additional ratios
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
            st.markdown(card_html("P/E ratio",        fmt_num(pe),  "Price / earnings",        "#BA7517"), unsafe_allow_html=True)
        with c2:
            st.markdown(card_html("Div payout ratio", fmt_pct(dpr), "Dividends / net income",  "#D4537E"), unsafe_allow_html=True)
        with c3:
            st.markdown(card_html("Debt-to-equity",   fmt_num(dte), "Total debt / equity",     "#D85A30",
                                  quality(2-dte if pd.notna(dte) else np.nan, 0, 1)), unsafe_allow_html=True)
        with c4:
            st.markdown(card_html("Sust. growth rate",fmt_pct(sgr), "ROE × retention ratio",   "#1D9E75",
                                  quality(sgr, 0.05, 0.12)), unsafe_allow_html=True)

        # CAPM
        st.markdown('<div class="section-header">CAPM & cost of equity</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        beta_q = "good" if pd.notna(capm['beta']) and capm['beta'] < 0.8 else \
                 "warn" if pd.notna(capm['beta']) and capm['beta'] < 1.5 else "bad"
        with c1:
            st.markdown(card_html("Beta",            fmt_num(capm['beta']),           "Market sensitivity",    "#534AB7", beta_q), unsafe_allow_html=True)
        with c2:
            st.markdown(card_html("Risk-free rate",  fmt_pct(capm['risk_free_rate']), "10Y US Treasury",       "#185FA5"), unsafe_allow_html=True)
        with c3:
            st.markdown(card_html("Market return",   fmt_pct(capm['market_return']),  "S&P 500 10Y avg",       "#1D9E75"), unsafe_allow_html=True)
        with c4:
            st.markdown(card_html("Expected return", fmt_pct(capm['expected_return']),"Re = Rf + β(Rm − Rf)", "#D85A30"), unsafe_allow_html=True)

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

        # FCF
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

        # WACC & DCF
        st.markdown('<div class="section-header">WACC & DCF valuation</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(card_html("WACC",         fmt_pct(wacc_d['wacc']),         "Weighted avg cost of capital", "#534AB7"), unsafe_allow_html=True)
        with c2:
            st.markdown(card_html("Cost of debt", fmt_pct(wacc_d['cost_of_debt']), "Interest / total debt",        "#D85A30"), unsafe_allow_html=True)
        with c3:
            st.markdown(card_html("Tax rate",     fmt_pct(wacc_d['tax_rate']),     "Effective tax rate",           "#BA7517"), unsafe_allow_html=True)
        with c4:
            st.markdown(card_html("Firm value",   fmt_big(dcf_d['firm_value']),    "Sum of discounted FCFs",       "#1D9E75"), unsafe_allow_html=True)

        if pd.notna(ip) and pd.notna(cp):
            bar_w   = min(max((upside + 50) / 100 * 100, 2), 100)
            bar_col = "#15803d" if upside >= 0 else "#b91c1c"
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
        if "Too Many Requests" in str(e) or "Rate limited" in str(e):
            st.error("Yahoo Finance is rate-limiting the app. Wait a moment and try again.")
        else:
            st.error(f"Could not analyse {ticker_symbol}: {e}")