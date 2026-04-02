import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import scipy.stats as stats
import time
import requests
from curl_cffi import requests as curl_requests

pd.options.display.float_format = '{:,.2f}'.format

FMP_API_KEY = "aTxTmpqxyHRTAFEX9kPkSmEBvsEPcvz1"
FMP_BASE    = "https://financialmodelingprep.com/stable"

st.set_page_config(page_title="Financial Analytics Dashboard", layout="wide")

# ── Global styles ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f4f3f8; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #eeecf6; }
.fin-card {
    background: #ffffff; border: 1px solid #e2dff0; border-radius: 12px;
    padding: 18px 20px; margin-bottom: 12px; position: relative; overflow: hidden;
}
.fin-card::before {
    content: ''; position: absolute; top: 0; left: 0;
    width: 4px; height: 100%; border-radius: 4px 0 0 4px;
    background: var(--accent, #7C3AED);
}
.fin-card .label {
    font-size: 11px; font-weight: 600; letter-spacing: 0.06em;
    text-transform: uppercase; color: #9d8ec4; margin-bottom: 6px;
}
.fin-card .value { font-size: 22px; font-weight: 700; color: #1e1b4b; line-height: 1.2; }
.fin-card .sub   { font-size: 11px; color: #b8afd6; margin-top: 4px; }
.fin-card.good .value { color: #15803d; }
.fin-card.warn .value { color: #b45309; }
.fin-card.bad  .value { color: #b91c1c; }
.section-header {
    font-size: 11px; font-weight: 700; letter-spacing: 0.09em;
    text-transform: uppercase; color: #7C3AED;
    border-bottom: 2px solid #e2dff0; padding-bottom: 8px; margin: 28px 0 14px;
}
.company-header {
    background: #ffffff; border: 1px solid #e2dff0; border-top: 4px solid #7C3AED;
    border-radius: 16px; padding: 24px 28px; margin-bottom: 24px;
    display: flex; justify-content: space-between; align-items: flex-start;
    flex-wrap: wrap; gap: 16px;
}
.company-name { font-size: 26px; font-weight: 700; color: #1e1b4b; }
.company-sub  { font-size: 13px; color: #9d8ec4; margin-top: 4px; }
.price-big    { font-size: 32px; font-weight: 700; color: #1e1b4b; text-align: right; }
.price-change { font-size: 14px; font-weight: 600; text-align: right; margin-top: 2px; }
.price-up  { color: #15803d; }
.price-down{ color: #b91c1c; }
.rec-badge {
    display: inline-block; font-size: 11px; font-weight: 700;
    padding: 3px 12px; border-radius: 20px; margin-top: 8px; letter-spacing: 0.06em;
}
.rec-buy  { background: #dcfce7; color: #15803d; }
.rec-hold { background: #fef3c7; color: #b45309; }
.rec-sell { background: #fee2e2; color: #b91c1c; }
.ov-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 4px; }
.ov-item { background: #ffffff; border: 1px solid #e2dff0; border-radius: 10px; padding: 12px 14px; }
.ov-label { font-size: 11px; color: #9d8ec4; margin-bottom: 4px; font-weight: 500; }
.ov-val   { font-size: 14px; font-weight: 700; color: #1e1b4b; }
.val-section {
    background: #ffffff; border: 1px solid #e2dff0;
    border-radius: 12px; padding: 18px 20px; margin-bottom: 12px;
}
.val-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.val-lbl { font-size: 13px; color: #9d8ec4; }
.val-num { font-size: 15px; font-weight: 700; color: #1e1b4b; }
.bar-track { height: 6px; background: #e2dff0; border-radius: 4px; margin-top: 8px; }
.bar-fill  { height: 6px; border-radius: 4px; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

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

def card_html(label, value, sub="", accent="#534AB7", q=""):
    return f"""
    <div class="fin-card {q}" style="--accent:{accent}">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        {"<div class='sub'>" + sub + "</div>" if sub else ""}
    </div>"""

def quality(val, low, high):
    if pd.isna(val): return ""
    return "good" if val >= high else ("warn" if val >= low else "bad")

def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.loc[:, ~df.columns.duplicated()]
    return df

def _make_session():
    return curl_requests.Session(impersonate="chrome")


# ── FMP data fetching ──────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fmp_get(endpoint):
    url = f"{FMP_BASE}/{endpoint}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and "Error Message" in data:
                return []
            return data
        return []
    except Exception:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_profile(sym):
    data = fmp_get(f"profile?symbol={sym}")
    if data and isinstance(data, list):
        return data[0]
    return {}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_financials(sym):
    income   = fmp_get(f"income-statement?symbol={sym}&limit=4")
    balance  = fmp_get(f"balance-sheet-statement?symbol={sym}&limit=4")
    cashflow = fmp_get(f"cash-flow-statement?symbol={sym}&limit=4")
    return income, balance, cashflow

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_price_history(sym):
    try:
        session = _make_session()
        t  = yf.Ticker(sym, session=session)
        h5 = flatten_columns(t.history(period="5y"))
        h1 = flatten_columns(t.history(period="1y"))
        return h5, h1
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_market():
    try:
        session = _make_session()
        market = yf.download("^GSPC", period="10y", auto_adjust=True,
                             progress=False, session=session, multi_level_index=False)
        rf     = yf.download("^TNX",  period="5d",  auto_adjust=True,
                             progress=False, session=session, multi_level_index=False)
        market = flatten_columns(market)
        rf     = flatten_columns(rf)
        return market, rf
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


# ── Extract helpers ────────────────────────────────────────────────────────────

def extract_series(data, key):
    if not data:
        return pd.Series(dtype=float)
    years  = [str(d.get("calendarYear", d.get("date", "")[:4])) for d in data]
    values = [d.get(key, np.nan) for d in data]
    s = pd.Series(values, index=years, dtype=float)
    return s.sort_index()


# ── Analysis ───────────────────────────────────────────────────────────────────

def liquidity_ratios(balance):
    ca  = extract_series(balance, "totalCurrentAssets")
    cl  = extract_series(balance, "totalCurrentLiabilities")
    inv = extract_series(balance, "inventory")
    csh = extract_series(balance, "cashAndCashEquivalents")
    cr  = ca / cl
    qr  = (ca - inv.fillna(0)) / cl
    ar  = csh / cl
    return cr, qr, ar

def profitability_ratios(income, balance):
    rev = extract_series(income,  "revenue")
    gp  = extract_series(income,  "grossProfit")
    oi  = extract_series(income,  "operatingIncome")
    ni  = extract_series(income,  "netIncome")
    ta  = extract_series(balance, "totalAssets")
    eq  = extract_series(balance, "totalStockholdersEquity")
    eps = extract_series(income,  "eps")
    gm  = gp / rev
    om  = oi / rev
    nm  = ni / rev
    roa = ni / ta
    roe = ni / eq
    return gm, om, nm, roa, roe, eps, rev, ni, oi

def additional_ratios(income, balance, cashflow, current_price):
    eq  = extract_series(balance,  "totalStockholdersEquity")
    td  = extract_series(balance,  "totalDebt")
    div = extract_series(cashflow, "dividendsPaid")
    ni  = extract_series(income,   "netIncome")
    eps = extract_series(income,   "eps")
    roe = ni / eq
    pe  = current_price / eps.iloc[-1] if len(eps) and eps.iloc[-1] != 0 else np.nan
    dpr = abs(div) / ni
    dte = td / eq
    sgr = roe * (1 - dpr)
    return pe, \
           float(dpr.iloc[-1]) if len(dpr) else np.nan, \
           float(dte.iloc[-1]) if len(dte) else np.nan, \
           float(sgr.iloc[-1]) if len(sgr) else np.nan

def capm_calc(price_5y):
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
    if market.empty:
        return {"beta": np.nan, "risk_free_rate": np.nan,
                "market_return": np.nan, "expected_return": np.nan,
                "slope": np.nan, "r_squared": np.nan}
    mr  = market["Close"].pct_change().dropna()
    ret = pd.concat([sr, mr], axis=1).dropna()
    ret.columns = ["Stock", "Market"]
    if ret.empty:
        return {"beta": np.nan, "risk_free_rate": np.nan,
                "market_return": np.nan, "expected_return": np.nan,
                "slope": np.nan, "r_squared": np.nan}
    cov  = ret.cov().iloc[0, 1]
    mv   = ret["Market"].var()
    beta = cov / mv if mv != 0 else np.nan
    slope, _, r_val, _, _ = stats.linregress(ret["Market"], ret["Stock"])
    rf   = float(rf_data["Close"].iloc[-1]) / 100 if not rf_data.empty else np.nan
    mr10 = ret["Market"].mean() * 252
    er   = rf + beta * (mr10 - rf) if pd.notna(rf) and pd.notna(beta) else np.nan
    return {"beta": beta, "risk_free_rate": rf, "market_return": mr10,
            "expected_return": er, "slope": slope, "r_squared": r_val**2}

def fcf_calc(cashflow):
    ocf   = extract_series(cashflow, "operatingCashFlow")
    capex = extract_series(cashflow, "capitalExpenditure")
    free  = ocf + capex
    return ocf, capex, free

def wacc_calc(profile, income, balance, cashflow, expected_return):
    mc  = profile.get("mktCap", np.nan)
    td  = extract_series(balance,  "totalDebt")
    ie  = extract_series(income,   "interestExpense")
    itx = extract_series(income,   "incomeTaxExpense")
    pti = extract_series(income,   "incomeBeforeTax")
    tdm = float(td.iloc[-1])  if len(td)  else np.nan
    iem = float(ie.iloc[-1])  if len(ie)  else np.nan
    itm = float(itx.iloc[-1]) if len(itx) else np.nan
    ptm = float(pti.iloc[-1]) if len(pti) else np.nan
    cod = abs(iem) / tdm if pd.notna(tdm) and tdm != 0 else np.nan
    tr  = abs(itm) / abs(ptm) if pd.notna(ptm) and ptm != 0 else np.nan
    E = mc; D = tdm
    V = E + D if pd.notna(E) and pd.notna(D) else np.nan
    w = ((E/V)*expected_return + (D/V)*cod*(1-tr)
         if all(pd.notna(x) for x in [E,D,V,cod,tr,expected_return]) and V != 0 else np.nan)
    return {"market_cap": mc, "total_debt": tdm, "cost_of_debt": cod, "tax_rate": tr, "wacc": w}

def dcf_calc(profile, free_cf, wacc_val, current_price):
    fc = free_cf.dropna()
    if fc.empty or pd.isna(wacc_val) or wacc_val <= 0:
        return {"fcf_latest": np.nan, "firm_value": np.nan,
                "intrinsic_price": np.nan, "current_price": current_price}
    fl  = float(fc.iloc[-1])
    mc  = profile.get("mktCap", np.nan)
    sh  = mc / current_price if pd.notna(mc) and current_price and current_price != 0 else np.nan
    g   = 0.03; yrs = 5; tg = 0.02
    pf  = [fl*(1+g)**y for y in range(1, yrs+1)]
    df_ = [pf[i]/(1+wacc_val)**(i+1) for i in range(yrs)]
    tv  = pf[-1]*(1+tg)/(wacc_val-tg) if wacc_val > tg else np.nan
    dtv = tv/(1+wacc_val)**yrs if pd.notna(tv) else np.nan
    fv  = sum(df_) + dtv if pd.notna(dtv) else np.nan
    ip  = fv/sh if pd.notna(fv) and pd.notna(sh) and sh != 0 else np.nan
    return {"fcf_latest": fl, "firm_value": fv,
            "intrinsic_price": ip, "current_price": current_price}


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
            profile                   = fetch_profile(ticker_symbol)
            income, balance, cashflow = fetch_financials(ticker_symbol)
            price_5y, price_1y        = fetch_price_history(ticker_symbol)

        if not profile:
            st.error(f"Could not find ticker **{ticker_symbol}**. Please check the symbol and try again.")
            st.stop()

        # current price
        cp = float(profile.get("price", np.nan) or np.nan)
        if pd.isna(cp) and not price_5y.empty:
            cp = float(price_5y["Close"].dropna().iloc[-1])

        # ETF / no financials check
        is_etf = bool(profile.get("isEtf", False)) or not income

        if is_etf:
            prev_row = price_5y["Close"].dropna() if not price_5y.empty else pd.Series()
            change   = float(prev_row.iloc[-1] - prev_row.iloc[-2]) if len(prev_row) >= 2 else 0
            chg_pct  = (change / float(prev_row.iloc[-2])) * 100 if len(prev_row) >= 2 else 0
            chg_cls  = "price-up" if change >= 0 else "price-down"
            chg_sign = "+" if change >= 0 else ""
            name     = profile.get("companyName", ticker_symbol)

            st.markdown(f"""
            <div class="company-header">
              <div>
                <div class="company-name">{name}
                  <span style='font-size:15px;font-weight:400;color:#9d8ec4;'>{ticker_symbol}</span>
                </div>
                <div class="company-sub">{profile.get('exchangeShortName','N/A')}</div>
                <span class="rec-badge" style="background:#ede9fe;color:#5b21b6;font-size:11px;font-weight:700;padding:3px 12px;border-radius:20px;margin-top:8px;display:inline-block;">ETF</span>
              </div>
              <div>
                <div class="price-big">${cp:,.2f}</div>
                <div class="price-change {chg_cls}">{chg_sign}{change:.2f} ({chg_sign}{chg_pct:.2f}%)</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            capm_etf = capm_calc(price_5y)
            st.markdown('<div class="section-header">1-year price</div>', unsafe_allow_html=True)
            if not price_1y.empty:
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

            st.markdown('<div class="section-header">CAPM & risk</div>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            beta_q = "good" if pd.notna(capm_etf['beta']) and capm_etf['beta'] < 0.8 else \
                     "warn" if pd.notna(capm_etf['beta']) and capm_etf['beta'] < 1.5 else "bad"
            with c1: st.markdown(card_html("Beta", fmt_num(capm_etf['beta']), "vs S&P 500", "#534AB7", beta_q), unsafe_allow_html=True)
            with c2: st.markdown(card_html("Risk-free rate", fmt_pct(capm_etf['risk_free_rate']), "10Y Treasury", "#185FA5"), unsafe_allow_html=True)
            with c3: st.markdown(card_html("Market return", fmt_pct(capm_etf['market_return']), "S&P 500 10Y avg", "#1D9E75"), unsafe_allow_html=True)
            with c4: st.markdown(card_html("Expected return", fmt_pct(capm_etf['expected_return']), "Re = Rf + β(Rm−Rf)", "#D85A30"), unsafe_allow_html=True)
            st.info(f"**{ticker_symbol} is an ETF.** Financial statements are not available for funds.")
            st.stop()

        # ── Stock branch ──────────────────────────────────────────────────────
        gm, om, nm, roa, roe, eps_s, rev_s, ni_s, oi_s = profitability_ratios(income, balance)
        cr, qr, ar = liquidity_ratios(balance)
        pe, dpr, dte, sgr = additional_ratios(income, balance, cashflow, cp)
        capm_d = capm_calc(price_5y)
        ocf_s, capex_s, free_cf = fcf_calc(cashflow)
        wacc_d = wacc_calc(profile, income, balance, cashflow, capm_d["expected_return"])
        dcf_d  = dcf_calc(profile, free_cf, wacc_d["wacc"], cp)

        ip     = dcf_d["intrinsic_price"]
        upside = ((ip - cp)/cp)*100 if pd.notna(ip) and pd.notna(cp) and cp != 0 else None
        if upside is not None:
            rec, rec_cls = ("BUY","rec-buy") if upside >= 15 else \
                           ("SELL","rec-sell") if upside < -15 else ("HOLD","rec-hold")
        else:
            rec, rec_cls = "HOLD", "rec-hold"

        # Company header
        name     = profile.get("companyName", ticker_symbol)
        sector   = profile.get("sector", "N/A")
        industry = profile.get("industry", "N/A")
        prev_row = price_5y["Close"].dropna() if not price_5y.empty else pd.Series()
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
            <span class="rec-badge {rec_cls}">{rec}</span>
          </div>
          <div>
            <div class="price-big">${cp:,.2f}</div>
            <div class="price-change {chg_cls}">{chg_sign}{change:.2f} ({chg_sign}{chg_pct:.2f}%)</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Company overview
        st.markdown('<div class="section-header">Company overview</div>', unsafe_allow_html=True)
        mc_val  = profile.get("mktCap", np.nan)
        emp     = profile.get("fullTimeEmployees", "N/A")
        country = profile.get("country", "N/A")
        rev_val = float(rev_s.iloc[-1]) if len(rev_s) else np.nan
        ni_val  = float(ni_s.iloc[-1])  if len(ni_s)  else np.nan
        ocf_val = float(ocf_s.iloc[-1]) if len(ocf_s) else np.nan
        emp_str = f"{emp:,}" if isinstance(emp, int) else str(emp)

        st.markdown(f"""
        <div class="ov-grid">
          <div class="ov-item"><div class="ov-label">Market cap</div><div class="ov-val">{fmt_big(mc_val)}</div></div>
          <div class="ov-item"><div class="ov-label">Revenue (TTM)</div><div class="ov-val">{fmt_big(rev_val)}</div></div>
          <div class="ov-item"><div class="ov-label">Net income</div><div class="ov-val">{fmt_big(ni_val)}</div></div>
          <div class="ov-item"><div class="ov-label">Operating CF</div><div class="ov-val">{fmt_big(ocf_val)}</div></div>
          <div class="ov-item"><div class="ov-label">Employees</div><div class="ov-val">{emp_str}</div></div>
          <div class="ov-item"><div class="ov-label">Country</div><div class="ov-val">{country}</div></div>
        </div>
        """, unsafe_allow_html=True)

        # 1-year price chart
        st.markdown('<div class="section-header">1-year stock price</div>', unsafe_allow_html=True)
        if not price_1y.empty:
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

        # Profitability ratios
        st.markdown('<div class="section-header">Profitability ratios</div>', unsafe_allow_html=True)
        gm_v  = float(gm.iloc[-1])  if len(gm)  else np.nan
        om_v  = float(om.iloc[-1])  if len(om)  else np.nan
        nm_v  = float(nm.iloc[-1])  if len(nm)  else np.nan
        roa_v = float(roa.iloc[-1]) if len(roa) else np.nan
        roe_v = float(roe.iloc[-1]) if len(roe) else np.nan
        eps_v = float(eps_s.iloc[-1]) if len(eps_s) else np.nan

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(card_html("Gross margin",     fmt_pct(gm_v),  "Gross profit / revenue",   "#1D9E75", quality(gm_v,  0.2, 0.4)), unsafe_allow_html=True)
            st.markdown(card_html("Return on assets", fmt_pct(roa_v), "Net income / total assets", "#D85A30", quality(roa_v, 0.03,0.1)), unsafe_allow_html=True)
        with c2:
            st.markdown(card_html("Operating margin", fmt_pct(om_v),  "EBIT / revenue",            "#185FA5", quality(om_v,  0.1, 0.25)), unsafe_allow_html=True)
            st.markdown(card_html("Return on equity", fmt_pct(roe_v), "Net income / equity",        "#D4537E", quality(roe_v, 0.1, 0.2)),  unsafe_allow_html=True)
        with c3:
            st.markdown(card_html("Net margin",       fmt_pct(nm_v),  "Net income / revenue",      "#534AB7", quality(nm_v,  0.05,0.15)), unsafe_allow_html=True)
            st.markdown(card_html("EPS", f"${fmt_num(eps_v)}" if pd.notna(eps_v) else "N/A",
                                  "Diluted earnings per share", "#BA7517"), unsafe_allow_html=True)

        # Liquidity ratios
        st.markdown('<div class="section-header">Liquidity ratios</div>', unsafe_allow_html=True)
        cr_v = float(cr.iloc[-1]) if len(cr) else np.nan
        qr_v = float(qr.iloc[-1]) if len(qr) else np.nan
        ar_v = float(ar.iloc[-1]) if len(ar) else np.nan

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(card_html("Current ratio", fmt_num(cr_v), "Current assets / liabilities", "#1D9E75", quality(cr_v, 1.0, 2.0)), unsafe_allow_html=True)
        with c2: st.markdown(card_html("Quick ratio",   fmt_num(qr_v), "(Assets − inventory) / liab",  "#185FA5", quality(qr_v, 0.8, 1.5)), unsafe_allow_html=True)
        with c3: st.markdown(card_html("Cash ratio",    fmt_num(ar_v), "Cash / current liabilities",   "#534AB7", quality(ar_v, 0.2, 0.5)), unsafe_allow_html=True)

        # Additional ratios
        st.markdown('<div class="section-header">Additional ratios</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(card_html("P/E ratio",         fmt_num(pe),  "Price / earnings",       "#BA7517"), unsafe_allow_html=True)
        with c2: st.markdown(card_html("Div payout ratio",  fmt_pct(dpr), "Dividends / net income", "#D4537E"), unsafe_allow_html=True)
        with c3: st.markdown(card_html("Debt-to-equity",    fmt_num(dte), "Total debt / equity",    "#D85A30",
                             quality(2-dte if pd.notna(dte) else np.nan, 0, 1)), unsafe_allow_html=True)
        with c4: st.markdown(card_html("Sust. growth rate", fmt_pct(sgr), "ROE × retention ratio",  "#1D9E75",
                             quality(sgr, 0.05, 0.12)), unsafe_allow_html=True)

        # CAPM
        st.markdown('<div class="section-header">CAPM & cost of equity</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        beta_q = "good" if pd.notna(capm_d['beta']) and capm_d['beta'] < 0.8 else \
                 "warn" if pd.notna(capm_d['beta']) and capm_d['beta'] < 1.5 else "bad"
        with c1: st.markdown(card_html("Beta",            fmt_num(capm_d['beta']),           "Market sensitivity",    "#534AB7", beta_q), unsafe_allow_html=True)
        with c2: st.markdown(card_html("Risk-free rate",  fmt_pct(capm_d['risk_free_rate']), "10Y US Treasury",       "#185FA5"), unsafe_allow_html=True)
        with c3: st.markdown(card_html("Market return",   fmt_pct(capm_d['market_return']),  "S&P 500 10Y avg",       "#1D9E75"), unsafe_allow_html=True)
        with c4: st.markdown(card_html("Expected return", fmt_pct(capm_d['expected_return']),"Re = Rf + β(Rm − Rf)", "#D85A30"), unsafe_allow_html=True)

        with st.expander("Show beta regression plot"):
            ret_df = pd.DataFrame()
            try:
                sr = price_5y["Close"].pct_change().dropna()
                sr.index = sr.index.tz_localize(None)
                mkt, _ = fetch_market()
                if not mkt.empty:
                    mr = mkt["Close"].pct_change().dropna()
                    ret_df = pd.concat([sr, mr], axis=1).dropna()
                    ret_df.columns = ["Stock", "Market"]
            except Exception:
                pass
            if not ret_df.empty:
                fig2, ax2 = plt.subplots(figsize=(7, 4))
                fig2.patch.set_facecolor("#ffffff"); ax2.set_facecolor("#ffffff")
                ax2.scatter(ret_df["Market"], ret_df["Stock"], alpha=0.25, s=6, color="#a78bfa")
                xs = np.linspace(ret_df["Market"].min(), ret_df["Market"].max(), 100)
                ax2.plot(xs, capm_d["slope"]*xs, color="#7C3AED", linewidth=2,
                         label=f"β={capm_d['slope']:.3f}  R²={capm_d['r_squared']:.3f}")
                ax2.set_xlabel("S&P 500 daily return", color="#9d8ec4", fontsize=10)
                ax2.set_ylabel(f"{ticker_symbol} daily return", color="#9d8ec4", fontsize=10)
                ax2.tick_params(colors="#9d8ec4")
                for sp in ax2.spines.values(): sp.set_edgecolor("#e2dff0")
                ax2.grid(color="#e2dff0", linewidth=0.5)
                ax2.legend(fontsize=9, facecolor="#ffffff", labelcolor="#1e1b4b")
                plt.tight_layout(); st.pyplot(fig2); plt.close()

        # FCF
        st.markdown('<div class="section-header">Free cash flow</div>', unsafe_allow_html=True)
        if len(free_cf):
            fig3, ax3 = plt.subplots(figsize=(8, 3))
            fig3.patch.set_facecolor("#ffffff"); ax3.set_facecolor("#ffffff")
            colors = ["#7C3AED" if v >= 0 else "#b91c1c" for v in free_cf.values]
            ax3.bar(free_cf.index, free_cf.values / 1e9, color=colors, width=0.5, edgecolor="#e2dff0")
            ax3.set_ylabel("USD (Billions)", color="#9d8ec4", fontsize=10)
            ax3.tick_params(colors="#9d8ec4")
            ax3.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:.0f}B"))
            for sp in ax3.spines.values(): sp.set_edgecolor("#e2dff0")
            ax3.grid(axis="y", color="#e2dff0", linewidth=0.5)
            plt.tight_layout(); st.pyplot(fig3); plt.close()

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(card_html("Latest FCF",   fmt_big(dcf_d["fcf_latest"]), "Most recent annual FCF", "#1D9E75"), unsafe_allow_html=True)
        with c2: st.markdown(card_html("Operating CF", fmt_big(float(ocf_s.iloc[-1]) if len(ocf_s) else np.nan), "Cash from operations", "#185FA5"), unsafe_allow_html=True)
        with c3: st.markdown(card_html("CapEx", fmt_big(float(capex_s.iloc[-1]) if len(capex_s) else np.nan), "Capital expenditures", "#D85A30"), unsafe_allow_html=True)

        # WACC & DCF
        st.markdown('<div class="section-header">WACC & DCF valuation</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(card_html("WACC",         fmt_pct(wacc_d['wacc']),         "Weighted avg cost of capital", "#534AB7"), unsafe_allow_html=True)
        with c2: st.markdown(card_html("Cost of debt", fmt_pct(wacc_d['cost_of_debt']), "Interest / total debt",        "#D85A30"), unsafe_allow_html=True)
        with c3: st.markdown(card_html("Tax rate",     fmt_pct(wacc_d['tax_rate']),     "Effective tax rate",           "#BA7517"), unsafe_allow_html=True)
        with c4: st.markdown(card_html("Firm value",   fmt_big(dcf_d['firm_value']),    "Sum of discounted FCFs",       "#1D9E75"), unsafe_allow_html=True)

        if pd.notna(ip) and pd.notna(cp):
            bar_w      = min(max((upside + 50) / 100 * 100, 2), 100)
            bar_col    = "#15803d" if upside >= 0 else "#b91c1c"
            upside_str = f"{'+' if upside>=0 else ''}{upside:.1f}%"
            st.markdown(f"""
            <div class="val-section">
              <div class="val-row"><span class="val-lbl">Current market price</span><span class="val-num">${cp:,.2f}</span></div>
              <div class="val-row"><span class="val-lbl">Intrinsic price (DCF)</span><span class="val-num">${ip:,.2f}</span></div>
              <div class="val-row"><span class="val-lbl">Upside / downside</span>
                <span class="val-num" style="color:{bar_col}">{upside_str}</span></div>
              <div class="bar-track">
                <div class="bar-fill" style="width:{bar_w:.1f}%;background:{bar_col}"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Could not analyse {ticker_symbol}: {e}")