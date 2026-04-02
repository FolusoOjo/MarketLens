import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import scipy.stats as stats
import requests
from curl_cffi import requests as curl_requests

pd.options.display.float_format = '{:,.2f}'.format

FMP_API_KEY = "aTxTmpqxyHRTAFEX9kPkSmEBvsEPcvz1"
FMP_BASE    = "https://financialmodelingprep.com/stable"

st.set_page_config(page_title="MarketLens", layout="wide", initial_sidebar_state="collapsed")

# ── Fonts ──────────────────────────────────────────────────────────────────────
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">',
    unsafe_allow_html=True
)

# ── Global styles ──────────────────────────────────────────────────────────────
# ── Theme state ───────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# Theme variables
if st.session_state.theme == "dark":
    T = {
        "bg":          "#0a0d16",
        "bg_grad":     "radial-gradient(ellipse 70% 40% at 50% 0%, rgba(139,92,246,0.12) 0%, transparent 65%), radial-gradient(ellipse 40% 30% at 90% 90%, rgba(20,184,166,0.07) 0%, transparent 60%)",
        "card_bg":     "rgba(255,255,255,0.025)",
        "card_border": "rgba(255,255,255,0.07)",
        "card_hover":  "rgba(255,255,255,0.04)",
        "text_primary":"#f1f0ff",
        "text_sec":    "#e2e8f0",
        "text_muted":  "#64748b",
        "text_dim":    "#475569",
        "input_bg":    "#111827",
        "input_bg_f":  "#141a2e",
        "input_border":"rgba(255,255,255,0.12)",
        "ac_bg":       "#13172a",
        "ac_border":   "rgba(255,255,255,0.1)",
        "ac_item_b":   "rgba(255,255,255,0.04)",
        "val_bar_bg":  "rgba(255,255,255,0.07)",
        "peers_border":"rgba(255,255,255,0.06)",
        "peers_td_b":  "rgba(255,255,255,0.04)",
        "peers_hover": "rgba(255,255,255,0.02)",
        "peers_cur":   "rgba(129,140,248,0.07)",
        "hero_color":  "#f1f0ff",
        "toggle_bg":   "rgba(255,255,255,0.06)",
        "toggle_icon": "🌙",
        "toggle_lbl":  "Dark",
    }
else:
    T = {
        "bg":          "#f8f7ff",
        "bg_grad":     "radial-gradient(ellipse 70% 40% at 50% 0%, rgba(139,92,246,0.07) 0%, transparent 65%), radial-gradient(ellipse 40% 30% at 90% 90%, rgba(20,184,166,0.04) 0%, transparent 60%)",
        "card_bg":     "rgba(255,255,255,0.85)",
        "card_border": "rgba(0,0,0,0.08)",
        "card_hover":  "rgba(255,255,255,1)",
        "text_primary":"#1e1b4b",
        "text_sec":    "#1e293b",
        "text_muted":  "#64748b",
        "text_dim":    "#94a3b8",
        "input_bg":    "#ffffff",
        "input_bg_f":  "#f5f3ff",
        "input_border":"rgba(0,0,0,0.15)",
        "ac_bg":       "#ffffff",
        "ac_border":   "rgba(0,0,0,0.1)",
        "ac_item_b":   "rgba(0,0,0,0.04)",
        "val_bar_bg":  "rgba(0,0,0,0.06)",
        "peers_border":"rgba(0,0,0,0.06)",
        "peers_td_b":  "rgba(0,0,0,0.04)",
        "peers_hover": "rgba(124,58,237,0.03)",
        "peers_cur":   "rgba(129,140,248,0.1)",
        "hero_color":  "#1e1b4b",
        "toggle_bg":   "rgba(0,0,0,0.06)",
        "toggle_icon": "☀️",
        "toggle_lbl":  "Light",
    }

input_color = "#f1f0ff" if st.session_state.theme == "dark" else "#1e1b4b"
placeholder_color = "#4b5563" if st.session_state.theme == "dark" else "#94a3b8"

st.markdown(f"""
<style>
* {{ font-family: 'Outfit', sans-serif; box-sizing: border-box; }}

[data-testid="stAppViewContainer"] {{
    background: {T["bg"]};
    background-image: {T["bg_grad"]};
}}
[data-testid="stHeader"]            {{ background: transparent; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 1.5rem; max-width: 1100px; }}

/* ── Hero ── */
.hero {{ text-align: center; padding: 2rem 0 1.8rem; }}
.hero-title {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 64px; font-weight: 700; letter-spacing: -1px;
    color: {T["hero_color"]}; line-height: 1; margin-bottom: 10px;
}}
.hero-title span {{
    background: linear-gradient(135deg, #c4b5fd 0%, #818cf8 60%, #34d399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}}
.hero-sub {{ font-size: 14px; color: {T["text_muted"]}; font-weight: 300; letter-spacing: 0.12em; text-transform: uppercase; }}

/* ── Input ── */
input,
[data-testid="stTextInput"] input,
[data-testid="stTextInput"] > div > div > input {{
    background: {T["input_bg"]} !important;
    border: 1px solid {T["input_border"]} !important;
    border-radius: 14px !important;
    color: {input_color} !important;
    caret-color: #a78bfa !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 15px !important; font-weight: 400 !important;
    padding: 14px 18px !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
}}
input:focus,
[data-testid="stTextInput"] input:focus {{
    border-color: rgba(139,92,246,0.6) !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.12) !important;
    background: {T["input_bg_f"]} !important;
    outline: none !important;
}}
input::placeholder,
[data-testid="stTextInput"] input::placeholder {{ color: {placeholder_color} !important; }}

/* ── Button ── */
[data-testid="stButton"] > button {{
    background: linear-gradient(135deg, #7c3aed, #6366f1) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 14px !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    padding: 0 28px !important;
    height: 52px !important;
    transition: opacity 0.2s, transform 0.2s, box-shadow 0.2s !important;
}}
[data-testid="stButton"] > button:hover {{
    opacity: 0.92 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(124,58,237,0.35) !important;
}}

/* ── Autocomplete dropdown ── */
.ac-drop {{
    background: {T["ac_bg"]}; border: 1px solid {T["ac_border"]};
    border-radius: 14px; overflow: hidden; margin-top: -8px; margin-bottom: 16px;
    box-shadow: 0 16px 40px rgba(0,0,0,0.2);
}}
.ac-item {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 11px 18px; cursor: pointer;
    border-bottom: 1px solid {T["ac_item_b"]}; transition: background 0.15s;
}}
.ac-item:last-child {{ border-bottom: none; }}
.ac-item:hover {{ background: rgba(139,92,246,0.1); }}
.ac-sym  {{ font-weight: 600; font-size: 14px; color: #818cf8; }}
.ac-name {{ font-size: 13px; color: {T["text_muted"]}; font-weight: 300; }}
.ac-type {{ font-size: 11px; color: {T["text_dim"]}; background: {T["card_bg"]}; padding: 2px 8px; border-radius: 6px; }}

/* ── Company card ── */
.co-card {{
    background: {T["card_bg"]}; border: 1px solid {T["card_border"]};
    border-radius: 20px; padding: 28px 32px; margin-bottom: 28px;
    display: flex; justify-content: space-between; align-items: flex-start;
    flex-wrap: wrap; gap: 20px; position: relative; overflow: hidden;
    box-shadow: 0 2px 20px rgba(0,0,0,0.08);
}}
.co-card::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(139,92,246,0.6), rgba(52,211,153,0.4), transparent);
}}
.co-name {{ font-family: 'Cormorant Garamond', serif; font-size: 30px; font-weight: 700; color: {T["text_primary"]}; letter-spacing: -0.3px; }}
.co-sym {{ font-size: 12px; font-weight: 500; color: #818cf8; background: rgba(129,140,248,0.12); padding: 3px 10px; border-radius: 6px; margin-left: 10px; vertical-align: middle; letter-spacing: 0.06em; }}
.co-meta {{ font-size: 13px; color: {T["text_muted"]}; margin-top: 6px; font-weight: 300; }}
.price-val {{ font-family: 'Cormorant Garamond', serif; font-size: 40px; font-weight: 700; color: {T["text_primary"]}; text-align: right; letter-spacing: -1px; }}
.price-chg {{ font-size: 14px; font-weight: 400; text-align: right; margin-top: 4px; }}
.up   {{ color: #34d399; }}
.down {{ color: #f87171; }}

/* ── Badges ── */
.bdg {{
    display: inline-block; font-size: 10px; font-weight: 600;
    letter-spacing: 0.12em; padding: 4px 12px; border-radius: 20px;
    margin-top: 10px; text-transform: uppercase;
}}
.bdg-buy  {{ background: rgba(52,211,153,0.12);  color: #34d399; border: 1px solid rgba(52,211,153,0.25); }}
.bdg-hold {{ background: rgba(251,191,36,0.12);  color: #fbbf24; border: 1px solid rgba(251,191,36,0.25); }}
.bdg-sell {{ background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.25); }}
.bdg-etf  {{ background: rgba(129,140,248,0.12); color: #a5b4fc; border: 1px solid rgba(129,140,248,0.25); }}
.bdg-stock{{ background: rgba(52,211,153,0.08);  color: #6ee7b7; border: 1px solid rgba(52,211,153,0.18); }}

/* ── Section title ── */
.sec-ttl {{
    font-family: 'Outfit', sans-serif;
    font-size: 10px; font-weight: 600; letter-spacing: 0.18em;
    text-transform: uppercase; color: #7c3aed;
    margin: 32px 0 14px;
    display: flex; align-items: center; gap: 12px;
}}
.sec-ttl::after {{
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(124,58,237,0.25), transparent);
}}

/* ── Metric cards ── */
.mc {{ background: {T["card_bg"]}; border: 1px solid {T["card_border"]}; border-radius: 16px; padding: 18px 20px; margin-bottom: 12px; position: relative; transition: border-color 0.2s, background 0.2s; }}
.mc:hover {{ border-color: rgba(124,58,237,0.25); background: {T["card_hover"]}; }}
.mc-bar {{ position: absolute; left: 0; top: 22%; bottom: 22%; width: 3px; border-radius: 0 3px 3px 0; }}
.mc-lbl {{ font-size: 10px; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: {T["text_muted"]}; margin-bottom: 8px; padding-left: 14px; }}
.mc-val {{ font-family: 'Cormorant Garamond', serif; font-size: 26px; font-weight: 600; color: {T["text_sec"]}; padding-left: 14px; line-height: 1; }}
.mc-sub {{ font-size: 11px; color: {T["text_dim"]}; padding-left: 14px; margin-top: 5px; font-weight: 300; }}
.mc.good .mc-val {{ color: #34d399; }}
.mc.warn .mc-val {{ color: #fbbf24; }}
.mc.bad  .mc-val {{ color: #f87171; }}

/* ── Overview grid ── */
.ov {{ display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; margin-bottom: 6px; }}
.ov-i {{ background: {T["card_bg"]}; border: 1px solid {T["card_border"]}; border-radius: 14px; padding: 16px 18px; transition: border-color 0.2s; }}
.ov-i:hover {{ border-color: rgba(124,58,237,0.2); }}
.ov-l {{ font-size: 10px; color: {T["text_muted"]}; margin-bottom: 6px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; }}
.ov-v {{ font-family: 'Cormorant Garamond', serif; font-size: 18px; font-weight: 600; color: {T["text_sec"]}; }}

/* ── Valuation card ── */
.val-c {{ background: {T["card_bg"]}; border: 1px solid {T["card_border"]}; border-radius: 16px; padding: 24px 28px; margin-top: 6px; }}
.val-r {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }}
.val-l {{ font-size: 13px; color: {T["text_muted"]}; font-weight: 300; }}
.val-n {{ font-family: 'Cormorant Garamond', serif; font-size: 20px; font-weight: 600; color: {T["text_primary"]}; }}
.bar-bg {{ height: 6px; background: {T["val_bar_bg"]}; border-radius: 6px; margin-top: 4px; }}
.bar-fg {{ height: 6px; border-radius: 6px; }}

/* ── News cards ── */
.news-card {{ background: {T["card_bg"]}; border: 1px solid {T["card_border"]}; border-radius: 14px; padding: 16px 20px; margin-bottom: 10px; display: flex; gap: 16px; align-items: flex-start; transition: border-color 0.2s, background 0.2s; text-decoration: none; }}
.news-card:hover {{ border-color: rgba(129,140,248,0.3); background: {T["card_hover"]}; }}
.news-dot {{ width: 8px; height: 8px; border-radius: 50%; background: #818cf8; margin-top: 6px; flex-shrink: 0; }}
.news-title {{ font-size: 14px; font-weight: 400; color: {T["text_sec"]}; line-height: 1.5; margin-bottom: 4px; }}
.news-meta  {{ font-size: 11px; color: {T["text_muted"]}; font-weight: 300; }}
.news-src   {{ color: #818cf8; font-weight: 500; }}

/* ── Peers table ── */
.peers-table {{ width: 100%; border-collapse: collapse; margin-top: 4px; }}
.peers-table th {{ font-size: 10px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: {T["text_muted"]}; padding: 10px 14px; text-align: left; border-bottom: 1px solid {T["peers_border"]}; }}
.peers-table td {{ font-size: 13px; color: {T["text_sec"]}; padding: 12px 14px; border-bottom: 1px solid {T["peers_td_b"]}; font-family: 'Outfit', sans-serif; }}
.peers-table tr:last-child td {{ border-bottom: none; }}
.peers-table tr:hover td {{ background: {T["peers_hover"]}; }}
.peers-table .cur-row td {{ background: {T["peers_cur"]}; color: #818cf8; font-weight: 500; }}
.peers-table .num {{ font-family: 'Cormorant Garamond', serif; font-size: 16px; }}

/* ── Landing page cards ── */
.idx-card {{ background: {T["card_bg"]}; border: 1px solid {T["card_border"]}; border-radius: 16px; padding: 22px 20px 18px; text-align: center; transition: border-color 0.2s, box-shadow 0.2s; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
.idx-card:hover {{ border-color: rgba(129,140,248,0.3); box-shadow: 0 4px 20px rgba(124,58,237,0.1); }}
.idx-name  {{ font-size: 10px; color: {T["text_muted"]}; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 10px; font-weight: 600; }}
.idx-price {{ font-family: 'Cormorant Garamond', serif; font-size: 28px; font-weight: 700; color: {T["text_primary"]}; }}
.idx-chg   {{ font-size: 13px; font-weight: 500; margin-top: 6px; }}
.idx-desc  {{ font-size: 12px; color: {T["text_muted"]}; margin-top: 12px; line-height: 1.6; font-weight: 300; text-align: left; }}
.mover-card {{ background: {T["card_bg"]}; border: 1px solid {T["card_border"]}; border-radius: 12px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; transition: border-color 0.15s; }}
.mover-card:hover {{ border-color: rgba(129,140,248,0.2); }}
.mover-sym  {{ font-weight: 600; font-size: 14px; color: {T["text_sec"]}; }}
.mover-name {{ font-size: 11px; color: {T["text_muted"]}; margin-top: 2px; font-weight: 300; }}
.mover-chg  {{ font-size: 14px; font-weight: 500; }}

/* ── Custom loading spinner ── */
.ml-loader {{
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 60px 0;
}}
.ml-chart {{
    display: flex; align-items: flex-end; gap: 5px; height: 60px; margin-bottom: 20px;
}}
.ml-bar {{
    width: 8px; border-radius: 4px 4px 0 0;
    background: linear-gradient(180deg, #818cf8, #6366f1);
    animation: mlrise 1.2s ease-in-out infinite;
}}
.ml-bar:nth-child(1) {{ animation-delay: 0s;    height: 20px; }}
.ml-bar:nth-child(2) {{ animation-delay: 0.1s;  height: 35px; }}
.ml-bar:nth-child(3) {{ animation-delay: 0.2s;  height: 50px; }}
.ml-bar:nth-child(4) {{ animation-delay: 0.3s;  height: 40px; }}
.ml-bar:nth-child(5) {{ animation-delay: 0.4s;  height: 55px; }}
.ml-bar:nth-child(6) {{ animation-delay: 0.5s;  height: 30px; }}
.ml-bar:nth-child(7) {{ animation-delay: 0.6s;  height: 45px; }}
.ml-line {{
    position: absolute; top: 10px; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #34d399, transparent);
    animation: mlsweep 1.2s ease-in-out infinite;
}}
@keyframes mlrise {{
    0%, 100% {{ transform: scaleY(0.4); opacity: 0.4; }}
    50%       {{ transform: scaleY(1);   opacity: 1;   }}
}}
@keyframes mlsweep {{
    0%   {{ transform: translateX(-100%); opacity: 0; }}
    50%  {{ opacity: 1; }}
    100% {{ transform: translateX(100%);  opacity: 0; }}
}}
.ml-txt {{
    font-size: 13px; color: #64748b; letter-spacing: 0.12em;
    text-transform: uppercase; font-weight: 400;
    animation: mlfade 1.5s ease-in-out infinite;
}}
@keyframes mlfade {{
    0%, 100% {{ opacity: 0.4; }}
    50%       {{ opacity: 1;   }}
}}
/* Hide default streamlit spinner */
[data-testid="stSpinner"] {{ display: none !important; }}

/* ── Spinner ── */
[data-testid="stSpinner"] {{ display: none !important; }}

/* ── Toggle button ── */
.theme-toggle {{
    position: fixed; top: 14px; right: 20px; z-index: 9999;
    background: {T["toggle_bg"]}; border: 1px solid {T["card_border"]};
    border-radius: 20px; padding: 6px 14px;
    font-size: 12px; color: {T["text_muted"]}; cursor: pointer;
    backdrop-filter: blur(10px); transition: all 0.2s;
    display: flex; align-items: center; gap: 6px;
}}

#MainMenu, footer, header {{ visibility: hidden; }}
div[data-testid="column"] {{ padding: 0 5px; }}
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

def mcard(label, value, sub="", accent="#7c3aed", q=""):
    return f"""<div class="mc {q}">
    <div class="mc-bar" style="background:{accent}"></div>
    <div class="mc-lbl">{label}</div>
    <div class="mc-val">{value}</div>
    {"<div class='mc-sub'>" + sub + "</div>" if sub else ""}
</div>"""

def qual(val, low, high):
    if pd.isna(val): return ""
    return "good" if val >= high else ("warn" if val >= low else "bad")

def section(t):
    st.markdown(f'<div class="sec-ttl">{t}</div>', unsafe_allow_html=True)

def flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.loc[:, ~df.columns.duplicated()]

def _session():
    return curl_requests.Session(impersonate="chrome")

# ── Plotly theme ───────────────────────────────────────────────────────────────
_PL = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Outfit", color="#94a3b8", size=12),
    margin=dict(l=10, r=10, t=10, b=40),
    xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11, color="#64748b")),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)",
               showline=False, tickfont=dict(size=11, color="#64748b")),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#1e2235", bordercolor="#334155",
                    font=dict(family="Outfit", color="#f1f0ff", size=12)),
)

def chart_price(df, sym):
    c = df["Close"].dropna()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=c.index, y=c.values, mode="lines",
        line=dict(color="#818cf8", width=2.5),
        fill="tozeroy", fillcolor="rgba(129,140,248,0.06)",
        hovertemplate="<b>$%{y:,.2f}</b><extra></extra>", name=sym,
    ))
    l = {**_PL}; l["height"] = 260; l["yaxis"] = {**_PL["yaxis"], "tickprefix": "$"}
    fig.update_layout(**l)
    return fig

def chart_fcf(free_cf):
    cols = ["#34d399" if v >= 0 else "#f87171" for v in free_cf.values]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=free_cf.index, y=free_cf.values/1e9,
        marker_color=cols, marker_line_width=0,
        hovertemplate="<b>$%{y:.2f}B</b><extra></extra>",
    ))
    l = {**_PL}; l["height"] = 220
    l["yaxis"] = {**_PL["yaxis"], "tickprefix":"$", "ticksuffix":"B"}
    fig.update_layout(**l)
    return fig

def chart_scatter(ret_df, slope, r2, sym):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ret_df["Market"], y=ret_df["Stock"], mode="markers",
        marker=dict(color="#818cf8", size=4, opacity=0.3),
        hovertemplate="Market: %{x:.3f}<br>Stock: %{y:.3f}<extra></extra>",
    ))
    xs = np.linspace(ret_df["Market"].min(), ret_df["Market"].max(), 100)
    fig.add_trace(go.Scatter(
        x=xs, y=slope*xs, mode="lines",
        line=dict(color="#34d399", width=2),
        name=f"β fit  R²={r2:.3f}",
    ))
    l = {**_PL}; l["height"] = 300
    l["xaxis"] = {**_PL["xaxis"], "title": "S&P 500 daily return"}
    l["yaxis"] = {**_PL["yaxis"], "title": f"{sym} daily return"}
    l["legend"] = dict(font=dict(color="#94a3b8", size=11), bgcolor="rgba(0,0,0,0)")
    fig.update_layout(**l)
    return fig


def chart_revenue_earnings(income):
    """Bar chart showing revenue and net income trends."""
    rev = []
    ni  = []
    yrs = []
    for d in reversed(income):
        yr = str(d.get("calendarYear", d.get("date","")[:4]))
        yrs.append(yr)
        rev.append(d.get("revenue", 0) / 1e9)
        ni.append(d.get("netIncome", 0) / 1e9)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=yrs, y=rev, name="Revenue",
        marker_color="#818cf8", marker_line_width=0,
        hovertemplate="Revenue: <b>$%{y:.2f}B</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=yrs, y=ni, name="Net Income",
        marker_color="#34d399", marker_line_width=0,
        hovertemplate="Net Income: <b>$%{y:.2f}B</b><extra></extra>",
    ))
    l = {**_PL}; l["height"] = 260; l["barmode"] = "group"
    l["yaxis"] = {**_PL["yaxis"], "tickprefix":"$", "ticksuffix":"B"}
    l["legend"] = dict(font=dict(color="#94a3b8", size=12), bgcolor="rgba(0,0,0,0)",
                       orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    fig.update_layout(**l)
    return fig

def chart_peers(peers_data, current_sym):
    """Horizontal bar chart comparing peers on key metrics."""
    syms = [d["symbol"] for d in peers_data]
    gms  = [d.get("grossMargin", 0)*100 for d in peers_data]
    pes  = [min(d.get("pe", 0) or 0, 80) for d in peers_data]  # cap at 80 for display

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=syms, x=gms, orientation="h", name="Gross Margin %",
        marker_color=["#818cf8" if s == current_sym else "#334155" for s in syms],
        marker_line_width=0,
        hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
    ))
    l = {**_PL}; l["height"] = 200
    l["xaxis"] = {**_PL["xaxis"], "ticksuffix":"%"}
    l["yaxis"] = {**_PL["yaxis"], "showgrid": False}
    l["margin"] = dict(l=60, r=10, t=10, b=30)
    fig.update_layout(**l)
    return fig


# ── FMP API ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fmp_get(endpoint):
    url = f"{FMP_BASE}/{endpoint}&apikey={FMP_API_KEY}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            d = r.json()
            return [] if isinstance(d, dict) and "Error Message" in d else d
    except Exception:
        pass
    return []

@st.cache_data(ttl=60, show_spinner=False)
def fmp_search(q):
    """Search tickers by name or symbol - tries multiple endpoints."""
    endpoints = [
        f"{FMP_BASE}/search?query={q}&limit=6&apikey={FMP_API_KEY}",
        f"https://financialmodelingprep.com/api/v3/search?query={q}&limit=6&apikey={FMP_API_KEY}",
        f"https://financialmodelingprep.com/api/v3/search-ticker?query={q}&limit=6&apikey={FMP_API_KEY}",
    ]
    for url in endpoints:
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass
    return []

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_profile(sym):
    d = fmp_get(f"profile?symbol={sym}")
    return d[0] if d and isinstance(d, list) else {}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_financials(sym):
    return (fmp_get(f"income-statement?symbol={sym}&limit=4"),
            fmp_get(f"balance-sheet-statement?symbol={sym}&limit=4"),
            fmp_get(f"cash-flow-statement?symbol={sym}&limit=4"))

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices(sym):
    try:
        s = _session(); t = yf.Ticker(sym, session=s)
        return flatten(t.history(period="5y")), flatten(t.history(period="1y"))
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_news(sym):
    """Fetch latest news via Yahoo Finance RSS — no API key needed."""
    import xml.etree.ElementTree as ET
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={sym}&region=US&lang=en-US"
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            news = []
            for item in items[:5]:
                title   = item.findtext("title", "")
                link    = item.findtext("link", "#")
                pubdate = item.findtext("pubDate", "")[:16] if item.findtext("pubDate") else ""
                source  = item.findtext("source", "Yahoo Finance")
                news.append({
                    "title": title, "url": link,
                    "publishedDate": pubdate, "site": source
                })
            if news:
                return news
    except Exception:
        pass
    # Fallback to FMP
    try:
        r = requests.get(
            f"https://financialmodelingprep.com/api/v3/stock_news?tickers={sym}&limit=5&apikey={FMP_API_KEY}",
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and data:
                return data[:5]
    except Exception:
        pass
    return []

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_peers(sym):
    """Fetch stock peers — tries API first, then builds from sector/industry."""
    # Try FMP peers API
    urls = [
        f"https://financialmodelingprep.com/api/v4/stock_peers?symbol={sym}&apikey={FMP_API_KEY}",
        f"https://financialmodelingprep.com/stable/peers?symbol={sym}&apikey={FMP_API_KEY}",
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if not data:
                    continue
                if isinstance(data, list) and len(data) > 0:
                    first = data[0]
                    if isinstance(first, dict):
                        peers = first.get("peersList", first.get("peers", []))
                    elif isinstance(first, str):
                        peers = data
                    else:
                        peers = []
                    peers = [p for p in peers if p != sym]
                    if peers:
                        return peers[:4]
        except Exception:
            pass

    # If API fails — use FMP screener to find companies in same sector/industry
    try:
        prof = fetch_profile(sym)
        sector   = prof.get("sector", "")
        industry = prof.get("industry", "")
        exchange = prof.get("exchangeShortName", "NASDAQ")
        if sector:
            screen_url = (
                f"https://financialmodelingprep.com/api/v3/stock-screener"
                f"?sector={requests.utils.quote(sector)}"
                f"&exchange={exchange}&limit=10&apikey={FMP_API_KEY}"
            )
            r = requests.get(screen_url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    peers = [d.get("symbol") for d in data
                             if d.get("symbol") and d.get("symbol") != sym]
                    if peers:
                        return peers[:4]
    except Exception:
        pass
    # Fallback: hardcoded peers for common tickers
    fallbacks = {
        # Tech
        "AAPL": ["MSFT","GOOGL","META","AMZN"],
        "MSFT": ["AAPL","GOOGL","META","ORCL"],
        "GOOGL": ["MSFT","META","AAPL","AMZN"],
        "GOOG": ["MSFT","META","AAPL","AMZN"],
        "AMZN": ["MSFT","GOOGL","AAPL","WMT"],
        "META": ["GOOGL","SNAP","PINS","TWTR"],
        "NVDA": ["AMD","INTC","QCOM","AVGO"],
        "AMD":  ["NVDA","INTC","QCOM","AVGO"],
        "INTC": ["NVDA","AMD","QCOM","TXN"],
        "ORCL": ["MSFT","SAP","CRM","NOW"],
        "CRM":  ["ORCL","SAP","NOW","WDAY"],
        "NFLX": ["DIS","PARA","WBD","SPOT"],
        # EV / Auto
        "TSLA": ["F","GM","NIO","RIVN"],
        "F":    ["GM","TSLA","STLA","TM"],
        "GM":   ["F","TSLA","STLA","TM"],
        # Retail
        "WMT":  ["COST","TGT","AMZN","KR"],
        "COST": ["WMT","TGT","BJ","AMZN"],
        "TGT":  ["WMT","COST","KR","AMZN"],
        "AMZN": ["WMT","COST","GOOGL","MSFT"],
        "KR":   ["WMT","TGT","SFM","ACI"],
        # Finance
        "JPM":  ["BAC","WFC","GS","C"],
        "BAC":  ["JPM","WFC","C","GS"],
        "WFC":  ["JPM","BAC","C","USB"],
        "GS":   ["MS","JPM","BAC","C"],
        "MS":   ["GS","JPM","BAC","C"],
        "V":    ["MA","AXP","PYPL","SQ"],
        "MA":   ["V","AXP","PYPL","SQ"],
        # Healthcare
        "JNJ":  ["PFE","MRK","ABT","BMY"],
        "PFE":  ["JNJ","MRK","ABBV","BMY"],
        "MRK":  ["PFE","JNJ","ABBV","LLY"],
        "UNH":  ["CVS","CI","HUM","CNC"],
        # Energy
        "XOM":  ["CVX","COP","BP","SHEL"],
        "CVX":  ["XOM","COP","BP","SHEL"],
        # Consumer
        "KO":   ["PEP","MNST","KDRN","TAP"],
        "PEP":  ["KO","MNST","TAP","BUD"],
        "MCD":  ["YUM","QSR","SBUX","DPZ"],
        "SBUX": ["MCD","DNKN","QSR","CMG"],
        # Telecom
        "T":    ["VZ","TMUS","CMCSA","CHTR"],
        "VZ":   ["T","TMUS","CMCSA","CHTR"],
    }
    result = fallbacks.get(sym, [])
    if not result:
        # Last resort: get sector peers from FMP profile-based search
        try:
            prof = fetch_profile(sym)
            sector = prof.get("sector","")
            if sector:
                sector_map = {
                    "Technology": ["AAPL","MSFT","GOOGL","META","NVDA"],
                    "Consumer Cyclical": ["AMZN","TSLA","HD","NKE","MCD"],
                    "Consumer Defensive": ["WMT","COST","PG","KO","PEP"],
                    "Financial Services": ["JPM","BAC","WFC","GS","MS"],
                    "Healthcare": ["JNJ","UNH","PFE","MRK","ABT"],
                    "Energy": ["XOM","CVX","COP","SLB","EOG"],
                    "Industrials": ["HON","GE","MMM","CAT","BA"],
                    "Communication Services": ["GOOGL","META","NFLX","DIS","T"],
                    "Real Estate": ["AMT","PLD","EQIX","CCI","SPG"],
                    "Utilities": ["NEE","DUK","SO","D","AEP"],
                    "Basic Materials": ["LIN","APD","SHW","FCX","NEM"],
                }
                sector_peers = sector_map.get(sector, [])
                result = [p for p in sector_peers if p != sym][:4]
        except Exception:
            pass
    return result

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_market():
    try:
        s = _session()
        mkt = flatten(yf.download("^GSPC", period="10y", auto_adjust=True, progress=False, session=s, multi_level_index=False))
        rf  = flatten(yf.download("^TNX",  period="5d",  auto_adjust=True, progress=False, session=s, multi_level_index=False))
        return mkt, rf
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def fetch_market_indices():
    """Fetch major market indices."""
    indices = {
        "S&P 500": "^GSPC",
        "NASDAQ":  "^IXIC",
        "Dow Jones": "^DJI",
        "VIX": "^VIX",
    }
    results = []
    try:
        s = _session()
        for name_idx, sym_idx in indices.items():
            try:
                t = yf.Ticker(sym_idx, session=s)
                h = flatten(t.history(period="2d"))
                if not h.empty and len(h) >= 2:
                    cur = float(h["Close"].iloc[-1])
                    prev_c = float(h["Close"].iloc[-2])
                    chg = cur - prev_c
                    chgp = (chg / prev_c) * 100
                    results.append({"name": name_idx, "price": cur, "change": chg, "changePct": chgp})
            except Exception:
                pass
    except Exception:
        pass
    return results

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_general_news():
    """Fetch general market news via Yahoo Finance RSS."""
    import xml.etree.ElementTree as ET
    # Use multiple market-related RSS feeds
    feeds = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^DJI&region=US&lang=en-US",
    ]
    news = []
    seen = set()
    for url in feeds:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                for item in root.findall(".//item"):
                    title   = item.findtext("title", "")
                    link    = item.findtext("link", "#")
                    pubdate = item.findtext("pubDate", "")[:16] if item.findtext("pubDate") else ""
                    source  = item.findtext("source", "Yahoo Finance")
                    if title and title not in seen:
                        seen.add(title)
                        news.append({"title": title, "url": link,
                                     "publishedDate": pubdate, "site": source})
        except Exception:
            pass
    return news[:8]

@st.cache_data(ttl=600, show_spinner=False)
def fetch_top_movers():
    """Fetch top gaining and losing stocks."""
    gainers_url = f"https://financialmodelingprep.com/api/v3/gainers?apikey={FMP_API_KEY}"
    losers_url  = f"https://financialmodelingprep.com/api/v3/losers?apikey={FMP_API_KEY}"
    gainers, losers = [], []
    try:
        r = requests.get(gainers_url, timeout=8)
        if r.status_code == 200:
            gainers = r.json()[:4] if isinstance(r.json(), list) else []
    except Exception:
        pass
    try:
        r = requests.get(losers_url, timeout=8)
        if r.status_code == 200:
            losers = r.json()[:4] if isinstance(r.json(), list) else []
    except Exception:
        pass
    return gainers, losers


# ── Analysis ───────────────────────────────────────────────────────────────────

def exs(data, key):
    if not data: return pd.Series(dtype=float)
    yrs = [str(d.get("calendarYear", d.get("date","")[:4])) for d in data]
    return pd.Series([d.get(key, np.nan) for d in data], index=yrs, dtype=float).sort_index()

def liq(bal):
    ca=exs(bal,"totalCurrentAssets"); cl=exs(bal,"totalCurrentLiabilities")
    inv=exs(bal,"inventory"); csh=exs(bal,"cashAndCashEquivalents")
    return ca/cl, (ca-inv.fillna(0))/cl, csh/cl

def prof(inc, bal):
    rev=exs(inc,"revenue"); gp=exs(inc,"grossProfit"); oi=exs(inc,"operatingIncome")
    ni=exs(inc,"netIncome"); ta=exs(bal,"totalAssets"); eq=exs(bal,"totalStockholdersEquity")
    eps=exs(inc,"eps")
    return gp/rev, oi/rev, ni/rev, ni/ta, ni/eq, eps, rev, ni, oi

def addl(inc, bal, cf, cp):
    eq=exs(bal,"totalStockholdersEquity"); td=exs(bal,"totalDebt")
    div=exs(cf,"dividendsPaid"); ni=exs(inc,"netIncome"); eps=exs(inc,"eps")
    roe=ni/eq; pe=cp/eps.iloc[-1] if len(eps) and eps.iloc[-1] else np.nan
    dpr=abs(div)/ni; dte=td/eq; sgr=roe*(1-dpr)
    return pe, float(dpr.iloc[-1]) if len(dpr) else np.nan, \
               float(dte.iloc[-1]) if len(dte) else np.nan, \
               float(sgr.iloc[-1]) if len(sgr) else np.nan

def capm(p5):
    E={"beta":np.nan,"risk_free_rate":np.nan,"market_return":np.nan,
       "expected_return":np.nan,"slope":np.nan,"r_squared":np.nan}
    sr=p5["Close"].pct_change().dropna()
    if sr.empty: return E
    try: sr.index=sr.index.tz_localize(None)
    except: pass
    mkt,rf=fetch_market()
    if mkt.empty: return E
    mr=mkt["Close"].pct_change().dropna()
    ret=pd.concat([sr,mr],axis=1).dropna(); ret.columns=["S","M"]
    if ret.empty: return E
    cov=ret.cov().iloc[0,1]; mv=ret["M"].var()
    beta=cov/mv if mv else np.nan
    slope,_,rv,_,_=stats.linregress(ret["M"],ret["S"])
    rfv=float(rf["Close"].iloc[-1])/100 if not rf.empty else np.nan
    mr10=ret["M"].mean()*252
    er=rfv+beta*(mr10-rfv) if pd.notna(rfv) and pd.notna(beta) else np.nan
    return {"beta":beta,"risk_free_rate":rfv,"market_return":mr10,
            "expected_return":er,"slope":slope,"r_squared":rv**2}

def fcf(cf):
    ocf = exs(cf,"operatingCashFlow")
    cap = exs(cf,"capitalExpenditure")
    # FMP returns capex as negative already — free cash flow = ocf + capex (both signs correct)
    # But if capex comes back positive, make it negative
    cap_adj = cap.apply(lambda x: -abs(x) if pd.notna(x) else x)
    free = ocf + cap_adj
    return ocf, cap_adj, free

def wacc(profile, inc, bal, cf, er):
    mc=profile.get("mktCap",np.nan)
    td=exs(bal,"totalDebt"); ie=exs(inc,"interestExpense")
    itx=exs(inc,"incomeTaxExpense"); pti=exs(inc,"incomeBeforeTax")
    tdm=float(td.iloc[-1]) if len(td) else np.nan
    iem=float(ie.iloc[-1]) if len(ie) else np.nan
    itm=float(itx.iloc[-1]) if len(itx) else np.nan
    ptm=float(pti.iloc[-1]) if len(pti) else np.nan
    cod=abs(iem)/tdm if pd.notna(tdm) and tdm else np.nan
    tr=abs(itm)/abs(ptm) if pd.notna(ptm) and ptm else np.nan
    E=mc; D=tdm; V=E+D if pd.notna(E) and pd.notna(D) else np.nan
    w=((E/V)*er+(D/V)*cod*(1-tr)
       if all(pd.notna(x) for x in [E,D,V,cod,tr,er]) and V else np.nan)
    return {"market_cap":mc,"total_debt":tdm,"cost_of_debt":cod,"tax_rate":tr,"wacc":w}

def dcf(profile, free_cf, wv, cp):
    fc=free_cf.dropna()
    if fc.empty or pd.isna(wv) or wv<=0:
        return {"fcf_latest":np.nan,"firm_value":np.nan,"intrinsic_price":np.nan,"current_price":cp}
    fl=float(fc.iloc[-1]); mc=profile.get("mktCap",np.nan)
    sh=mc/cp if pd.notna(mc) and cp else np.nan
    g=0.03; yrs=5; tg=0.02
    pf=[fl*(1+g)**y for y in range(1,yrs+1)]
    df_=[pf[i]/(1+wv)**(i+1) for i in range(yrs)]
    tv=pf[-1]*(1+tg)/(wv-tg) if wv>tg else np.nan
    dtv=tv/(1+wv)**yrs if pd.notna(tv) else np.nan
    fv=sum(df_)+dtv if pd.notna(dtv) else np.nan
    ip=fv/sh if pd.notna(fv) and pd.notna(sh) and sh else np.nan
    return {"fcf_latest":fl,"firm_value":fv,"intrinsic_price":ip,"current_price":cp}


# ── UI ─────────────────────────────────────────────────────────────────────────

# Theme toggle button
t_col1, t_col2, t_col3 = st.columns([6, 1, 1])
with t_col3:
    icon = "🌙 Dark" if st.session_state.theme == "light" else "☀️ Light"
    if st.button(icon, key="theme_toggle"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

st.markdown("""
<div class="hero">
  <div class="hero-title">Market<span>Lens</span></div>
  <div class="hero-sub">Data-Driven Stock Valuation &amp; Forecasting</div>
</div>
""", unsafe_allow_html=True)

# ── Ticker search with autocomplete ───────────────────────────────────────────
col_in, col_btn = st.columns([5, 1])
with col_in:
    query = st.text_input(
        label="search",
        value="",
        placeholder="Enter a ticker symbol — e.g. AAPL, MSFT, TSLA, WMT",
        label_visibility="collapsed",
        key="search_input",
    )
with col_btn:
    analyse = st.button("Analyse →", use_container_width=True)

# Show autocomplete suggestions
selected_ticker = None
if query and len(query) >= 1 and not analyse:
    results = fmp_search(query)
    if results:
        st.markdown('<div class="ac-drop">', unsafe_allow_html=True)
        for r in results[:6]:
            sym  = r.get("symbol","")
            name = r.get("name","")
            typ  = r.get("type","equity").upper()
            exch = r.get("exchangeShortName","")
            btn_key = f"ac_{sym}"
            col_a, col_b = st.columns([6,1])
            with col_a:
                st.markdown(f"""
                <div class="ac-item">
                  <div>
                    <span class="ac-sym">{sym}</span>
                    <span class="ac-name" style="margin-left:10px">{name}</span>
                  </div>
                  <span class="ac-type">{typ} · {exch}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                if st.button("→", key=btn_key):
                    selected_ticker = sym
        st.markdown('</div>', unsafe_allow_html=True)

# Determine which ticker to use
ticker_symbol = (selected_ticker or query).strip().upper()

if not analyse and not selected_ticker and not query:
    # ── Landing page ─────────────────────────────────────────────────────────

    # About section
    st.markdown("""
    <div style="background:rgba(129,140,248,0.06);border:1px solid rgba(129,140,248,0.15);
                border-radius:16px;padding:24px 28px;margin-bottom:8px;">
      <div style="font-family:'Cormorant Garamond',serif;font-size:22px;font-weight:600;
                  color:#c4b5fd;margin-bottom:12px;">What is MarketLens?</div>
      <div style="font-size:13px;color:#94a3b8;line-height:1.9;font-weight:300;">
        MarketLens is a data-driven stock analysis platform that helps you evaluate any publicly
        traded company in seconds. Simply enter a ticker symbol (e.g. <b style="color:#e2e8f0">AAPL</b> for Apple,
        <b style="color:#e2e8f0">MSFT</b> for Microsoft) and get a full financial breakdown including:
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px;">
        <div style="background:rgba(255,255,255,0.03);border-radius:10px;padding:12px 14px;">
          <div style="font-size:11px;color:#818cf8;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">📊 Valuation</div>
          <div style="font-size:12px;color:#64748b;font-weight:300;line-height:1.7;">DCF intrinsic value, WACC, and Buy/Hold/Sell recommendation based on upside potential.</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:10px;padding:12px 14px;">
          <div style="font-size:11px;color:#34d399;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">📈 Financials</div>
          <div style="font-size:12px;color:#64748b;font-weight:300;line-height:1.7;">Profitability, liquidity, and growth ratios pulled from the latest annual filings.</div>
        </div>
        <div style="background:rgba(255,255,255,0.03);border-radius:10px;padding:12px 14px;">
          <div style="font-size:11px;color:#f59e0b;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">🏆 Competition</div>
          <div style="font-size:12px;color:#64748b;font-weight:300;line-height:1.7;">Side-by-side comparison with industry peers on margins, ROE, and P/E ratio.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    indices  = fetch_market_indices()
    gen_news = fetch_general_news()
    gainers, losers = fetch_top_movers()

    # Market indices
    def idx_desc(name, chg):
        direction = "up" if chg >= 0 else "down"
        descs = {
            "S&P 500":   "Tracks 500 large US companies — the broadest health check of the US stock market. It is " + direction + " today.",
            "NASDAQ":    "Tracks tech-heavy stocks like Apple, Google & Microsoft. It is " + direction + " today, reflecting " + ("positive" if chg >= 0 else "negative") + " momentum in tech.",
            "Dow Jones": "Tracks 30 major blue-chip US companies like Boeing & Goldman Sachs. It is " + direction + " today.",
            "VIX":       ("Higher" if chg >= 0 else "Lower") + " means investors are feeling " + ("more nervous" if chg >= 0 else "more confident") + " about the market right now.",
        }
        return descs.get(name, "It is " + direction + " today.")

    if indices:
        section("Market Overview")
        cols = st.columns(len(indices))
        for i, idx in enumerate(indices):
            c = idx["changePct"]
            col = "#34d399" if c >= 0 else "#f87171"
            sign = "+" if c >= 0 else ""
            desc = idx_desc(idx["name"], c)
            with cols[i]:
                st.markdown(
                    '<div class="idx-card">'
                    '<div class="idx-name">' + idx["name"] + '</div>'
                    '<div class="idx-price">' + f'{idx["price"]:,.2f}' + '</div>'
                    '<div class="idx-chg" style="color:' + col + '">' + sign + f'{c:.2f}%' + '</div>'
                    '<div class="idx-desc">' + desc + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

    # Top movers
    if gainers or losers:
        section("Top Movers Today")
        col_g, col_l = st.columns(2)
        with col_g:
            st.markdown('<div style="font-size:11px;color:#34d399;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;">Top Gainers</div>', unsafe_allow_html=True)
            for g in gainers:
                sym  = g.get("ticker", g.get("symbol",""))
                nm   = g.get("companyName", g.get("name",""))[:25]
                chgp = g.get("changesPercentage", g.get("change",0))
                pr   = g.get("price", 0)
                chgp_val = float(str(chgp).replace("%","").replace("+","")) if chgp else 0
                st.markdown(
                    '<div class="mover-card">'
                    '<div><div class="mover-sym">' + sym + '</div>'
                    '<div class="mover-name">' + nm + '</div></div>'
                    '<div><div class="mover-chg" style="color:#34d399">+'
                    + f'{chgp_val:.2f}%' + '</div>'
                    '<div style="font-size:11px;color:#64748b;text-align:right">$' + f'{float(pr):,.2f}' + '</div>'
                    '</div></div>',
                    unsafe_allow_html=True
                )
        with col_l:
            st.markdown('<div style="font-size:11px;color:#f87171;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;">Top Losers</div>', unsafe_allow_html=True)
            for l in losers:
                sym  = l.get("ticker", l.get("symbol",""))
                nm   = l.get("companyName", l.get("name",""))[:25]
                chgp = l.get("changesPercentage", l.get("change",0))
                pr   = l.get("price", 0)
                chgp_val = float(str(chgp).replace("%","").replace("+","").replace("-","")) if chgp else 0
                st.markdown(
                    '<div class="mover-card">'
                    '<div><div class="mover-sym">' + sym + '</div>'
                    '<div class="mover-name">' + nm + '</div></div>'
                    '<div><div class="mover-chg" style="color:#f87171">-'
                    + f'{chgp_val:.2f}%' + '</div>'
                    '<div style="font-size:11px;color:#64748b;text-align:right">$' + f'{float(pr):,.2f}' + '</div>'
                    '</div></div>',
                    unsafe_allow_html=True
                )

    # General market news
    if gen_news:
        section("Market News")
        for article in gen_news:
            title    = article.get("title", article.get("headline", ""))
            url_link = article.get("url", article.get("link", "#"))
            source   = article.get("site", article.get("source", ""))
            pub_raw  = article.get("publishedDate", article.get("datetime", "")) or ""
            pub_date = pub_raw[:10] if pub_raw else ""
            if not title: continue
            st.markdown(
                '<a href="' + url_link + '" target="_blank" style="text-decoration:none;">'
                '<div class="news-card">'
                '<div class="news-dot"></div>'
                '<div><div class="news-title">' + title + '</div>'
                '<div class="news-meta"><span class="news-src">' + source + '</span>'
                + (' · ' + pub_date if pub_date else '') +
                '</div></div></div></a>',
                unsafe_allow_html=True
            )

if analyse or selected_ticker:
    if not ticker_symbol:
        st.warning("Please enter a company name or ticker symbol.")
        st.stop()
    try:
        loader = st.empty()
        loader.markdown('''
        <div class="ml-loader">
          <div class="ml-chart">
            <div class="ml-bar"></div><div class="ml-bar"></div>
            <div class="ml-bar"></div><div class="ml-bar"></div>
            <div class="ml-bar"></div><div class="ml-bar"></div>
            <div class="ml-bar"></div>
          </div>
          <div class="ml-txt">Fetching market data</div>
        </div>''', unsafe_allow_html=True)
        profile                   = fetch_profile(ticker_symbol)
        income, balance, cashflow = fetch_financials(ticker_symbol)
        price_5y, price_1y        = fetch_prices(ticker_symbol)
        loader.empty()

        if not profile:
            st.error(f"Could not find **{ticker_symbol}**. Please enter a valid ticker e.g. AAPL, WMT, TSLA.")
            st.stop()

        cp = float(profile.get("price", np.nan) or np.nan)
        if pd.isna(cp) and not price_5y.empty:
            cp = float(price_5y["Close"].dropna().iloc[-1])

        is_etf = bool(profile.get("isEtf", False)) or not income

        prev = price_5y["Close"].dropna() if not price_5y.empty else pd.Series()
        chg  = float(prev.iloc[-1]-prev.iloc[-2]) if len(prev)>=2 else 0
        chgp = (chg/float(prev.iloc[-2]))*100 if len(prev)>=2 else 0
        ccls = "up" if chg>=0 else "down"
        csn  = "+" if chg>=0 else ""
        name = profile.get("companyName", ticker_symbol)

        if is_etf:
            st.markdown(f"""
            <div class="co-card">
              <div>
                <div class="co-name">{name}<span class="co-sym">{ticker_symbol}</span></div>
                <div class="co-meta">{profile.get('exchangeShortName','')}</div>
                <span class="bdg bdg-etf">ETF</span>
              </div>
              <div>
                <div class="price-val">${cp:,.2f}</div>
                <div class="price-chg {ccls}">{csn}{chg:.2f} ({csn}{chgp:.2f}%)</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            cd = capm(price_5y)
            section("1-Year Price")
            if not price_1y.empty: st.plotly_chart(chart_price(price_1y, ticker_symbol), use_container_width=True)
            section("CAPM & Risk")
            c1,c2,c3,c4 = st.columns(4)
            with c1: st.markdown(mcard("Beta",fmt_num(cd['beta']),"vs S&P 500","#818cf8"), unsafe_allow_html=True)
            with c2: st.markdown(mcard("Risk-Free Rate",fmt_pct(cd['risk_free_rate']),"10Y Treasury","#3b82f6"), unsafe_allow_html=True)
            with c3: st.markdown(mcard("Market Return",fmt_pct(cd['market_return']),"S&P 500 10Y avg","#34d399"), unsafe_allow_html=True)
            with c4: st.markdown(mcard("Expected Return",fmt_pct(cd['expected_return']),"Re = Rf + β(Rm−Rf)","#f59e0b"), unsafe_allow_html=True)
            st.info(f"**{ticker_symbol}** is an ETF — financial statements are not available for funds.")
            st.stop()

        # ── Stock branch ──────────────────────────────────────────────────────
        gm,om,nm,roa,roe,eps_s,rev_s,ni_s,oi_s = prof(income, balance)
        cr,qr,ar     = liq(balance)
        pe,dpr,dte,sgr = addl(income, balance, cashflow, cp)
        cd  = capm(price_5y)
        ocf_s,cap_s,free_cf = fcf(cashflow)
        wd  = wacc(profile, income, balance, cashflow, cd["expected_return"])
        dd  = dcf(profile, free_cf, wd["wacc"], cp)

        ip     = dd["intrinsic_price"]
        upside = ((ip-cp)/cp)*100 if pd.notna(ip) and pd.notna(cp) and cp else None
        if upside is not None:
            rec,rcls = ("BUY","bdg-buy") if upside>=15 else ("SELL","bdg-sell") if upside<-15 else ("HOLD","bdg-hold")
        else:
            rec,rcls = "HOLD","bdg-hold"

        sec = profile.get("sector","N/A"); ind = profile.get("industry","N/A")

        st.markdown(f"""
        <div class="co-card">
          <div>
            <div class="co-name">{name}<span class="co-sym">{ticker_symbol}</span></div>
            <div class="co-meta">{sec} · {ind}</div>
            <span class="bdg bdg-stock">STOCK</span>
            <span class="bdg {rcls}" style="margin-left:8px">{rec}</span>
          </div>
          <div>
            <div class="price-val">${cp:,.2f}</div>
            <div class="price-chg {ccls}">{csn}{chg:.2f} ({csn}{chgp:.2f}%)</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        section("Company Overview")
        mc_v = profile.get("mktCap",np.nan)
        emp  = profile.get("fullTimeEmployees","N/A")
        cty  = profile.get("country","N/A")
        # Country full name mapping
        country_names = {
            "US":"United States","GB":"United Kingdom","CA":"Canada","AU":"Australia",
            "DE":"Germany","FR":"France","JP":"Japan","CN":"China","IN":"India",
            "BR":"Brazil","MX":"Mexico","KR":"South Korea","SG":"Singapore",
            "HK":"Hong Kong","NL":"Netherlands","SE":"Sweden","CH":"Switzerland",
            "IL":"Israel","TW":"Taiwan","IE":"Ireland",
        }
        cty_display = country_names.get(cty, cty)
        rv   = float(rev_s.iloc[-1]) if len(rev_s) else np.nan
        niv  = float(ni_s.iloc[-1])  if len(ni_s)  else np.nan
        ocfv = float(ocf_s.iloc[-1]) if len(ocf_s) else np.nan
        emps = f"{emp:,}" if isinstance(emp,int) else str(emp)

        st.markdown(f"""
        <div class="ov">
          <div class="ov-i"><div class="ov-l">Market Cap</div><div class="ov-v">{fmt_big(mc_v)}</div></div>
          <div class="ov-i"><div class="ov-l">Revenue (TTM)</div><div class="ov-v">{fmt_big(rv)}</div></div>
          <div class="ov-i"><div class="ov-l">Net Income</div><div class="ov-v">{fmt_big(niv)}</div></div>
          <div class="ov-i"><div class="ov-l">Operating CF</div><div class="ov-v">{fmt_big(ocfv)}</div></div>
          <div class="ov-i"><div class="ov-l">Employees</div><div class="ov-v">{emps}</div></div>
          <div class="ov-i"><div class="ov-l">Headquarters</div><div class="ov-v">{cty_display}</div></div>
        </div>
        """, unsafe_allow_html=True)

        section("1-Year Stock Price")
        if not price_1y.empty: st.plotly_chart(chart_price(price_1y, ticker_symbol), use_container_width=True)

        section("Profitability Ratios")
        gv=float(gm.iloc[-1]) if len(gm) else np.nan
        ov=float(om.iloc[-1]) if len(om) else np.nan
        nv=float(nm.iloc[-1]) if len(nm) else np.nan
        rav=float(roa.iloc[-1]) if len(roa) else np.nan
        rev=float(roe.iloc[-1]) if len(roe) else np.nan
        ev=float(eps_s.iloc[-1]) if len(eps_s) else np.nan

        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown(mcard("Gross Margin",    fmt_pct(gv),  "Gross profit / revenue",   "#34d399", qual(gv,  0.2, 0.4)), unsafe_allow_html=True)
            st.markdown(mcard("Return on Assets",fmt_pct(rav), "Net income / total assets", "#f59e0b", qual(rav, 0.03,0.1)), unsafe_allow_html=True)
        with c2:
            st.markdown(mcard("Operating Margin",fmt_pct(ov),  "EBIT / revenue",            "#3b82f6", qual(ov,  0.1, 0.25)), unsafe_allow_html=True)
            st.markdown(mcard("Return on Equity",fmt_pct(rev), "Net income / equity",        "#ec4899", qual(rev, 0.1, 0.2)),  unsafe_allow_html=True)
        with c3:
            st.markdown(mcard("Net Margin",      fmt_pct(nv),  "Net income / revenue",      "#818cf8", qual(nv,  0.05,0.15)), unsafe_allow_html=True)
            st.markdown(mcard("EPS", f"${fmt_num(ev)}" if pd.notna(ev) else "N/A",
                              "Diluted earnings per share", "#a78bfa"), unsafe_allow_html=True)

        section("Liquidity Ratios")
        crv=float(cr.iloc[-1]) if len(cr) else np.nan
        qrv=float(qr.iloc[-1]) if len(qr) else np.nan
        arv=float(ar.iloc[-1]) if len(ar) else np.nan
        c1,c2,c3 = st.columns(3)
        with c1: st.markdown(mcard("Current Ratio",fmt_num(crv),"Current assets / liabilities","#34d399",qual(crv,1.0,2.0)), unsafe_allow_html=True)
        with c2: st.markdown(mcard("Quick Ratio",  fmt_num(qrv),"(Assets − inventory) / liab", "#3b82f6",qual(qrv,0.8,1.5)), unsafe_allow_html=True)
        with c3: st.markdown(mcard("Cash Ratio",   fmt_num(arv),"Cash / current liabilities",  "#818cf8",qual(arv,0.2,0.5)), unsafe_allow_html=True)

        section("Additional Ratios")
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.markdown(mcard("P/E Ratio",        fmt_num(pe), "Price / earnings",       "#f59e0b"), unsafe_allow_html=True)
        with c2: st.markdown(mcard("Div Payout Ratio", fmt_pct(dpr),"Dividends / net income", "#ec4899"), unsafe_allow_html=True)
        with c3: st.markdown(mcard("Debt-to-Equity",   fmt_num(dte),"Total debt / equity",    "#f87171",
                             qual(2-dte if pd.notna(dte) else np.nan,0,1)), unsafe_allow_html=True)
        with c4: st.markdown(mcard("Sust. Growth Rate",fmt_pct(sgr),"ROE × retention ratio",  "#34d399",
                             qual(sgr,0.05,0.12)), unsafe_allow_html=True)

        section("CAPM & Cost of Equity")
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.markdown(mcard("Beta",           fmt_num(cd['beta']),          "Market sensitivity",   "#818cf8"), unsafe_allow_html=True)
        with c2: st.markdown(mcard("Risk-Free Rate", fmt_pct(cd['risk_free_rate']),"10Y US Treasury",      "#3b82f6"), unsafe_allow_html=True)
        with c3: st.markdown(mcard("Market Return",  fmt_pct(cd['market_return']), "S&P 500 10Y avg",      "#34d399"), unsafe_allow_html=True)
        with c4: st.markdown(mcard("Expected Return",fmt_pct(cd['expected_return']),"Re = Rf + β(Rm−Rf)", "#f59e0b"), unsafe_allow_html=True)

        with st.expander("Show Beta Regression Plot"):
            rdf = pd.DataFrame()
            try:
                sr=price_5y["Close"].pct_change().dropna()
                sr.index=sr.index.tz_localize(None)
                mk,_=fetch_market()
                if not mk.empty:
                    mr=mk["Close"].pct_change().dropna()
                    rdf=pd.concat([sr,mr],axis=1).dropna(); rdf.columns=["Stock","Market"]
            except: pass
            if not rdf.empty:
                st.plotly_chart(chart_scatter(rdf,cd["slope"],cd["r_squared"],ticker_symbol), use_container_width=True)

        section("Free Cash Flow")
        if len(free_cf): st.plotly_chart(chart_fcf(free_cf), use_container_width=True)
        c1,c2,c3 = st.columns(3)
        with c1: st.markdown(mcard("Latest FCF",  fmt_big(dd["fcf_latest"]), "Most recent annual FCF","#34d399"), unsafe_allow_html=True)
        with c2: st.markdown(mcard("Operating CF",fmt_big(float(ocf_s.iloc[-1]) if len(ocf_s) else np.nan),"Cash from operations","#3b82f6"), unsafe_allow_html=True)
        with c3: st.markdown(mcard("CapEx",       fmt_big(float(cap_s.iloc[-1]) if len(cap_s) else np.nan),"Capital expenditures","#f87171"), unsafe_allow_html=True)

        section("WACC & DCF Valuation")
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.markdown(mcard("WACC",        fmt_pct(wd['wacc']),        "Weighted avg cost of capital","#818cf8"), unsafe_allow_html=True)
        with c2: st.markdown(mcard("Cost of Debt",fmt_pct(wd['cost_of_debt']),"Interest / total debt",       "#f87171"), unsafe_allow_html=True)
        with c3: st.markdown(mcard("Tax Rate",    fmt_pct(wd['tax_rate']),    "Effective tax rate",          "#f59e0b"), unsafe_allow_html=True)
        with c4: st.markdown(mcard("Firm Value",  fmt_big(dd['firm_value']),  "Sum of discounted FCFs",      "#34d399"), unsafe_allow_html=True)

        if pd.notna(ip) and pd.notna(cp):
            bw     = min(max((upside+50)/100*100,2),100)
            bc     = "#34d399" if upside>=0 else "#f87171"
            us_str = f"{'+' if upside>=0 else ''}{upside:.1f}%"
            st.markdown(f"""
            <div class="val-c">
              <div class="val-r"><span class="val-l">Current Market Price</span><span class="val-n">${cp:,.2f}</span></div>
              <div class="val-r"><span class="val-l">Intrinsic Price (DCF)</span><span class="val-n">${ip:,.2f}</span></div>
              <div class="val-r"><span class="val-l">Upside / Downside</span>
                <span class="val-n" style="color:{bc}">{us_str}</span></div>
              <div class="bar-bg"><div class="bar-fg" style="width:{bw:.1f}%;background:{bc}"></div></div>
            </div>
            """, unsafe_allow_html=True)


        # ── Revenue & Earnings Trend ─────────────────────────────────────────
        section("Revenue & Earnings Trend")
        if income:
            st.plotly_chart(chart_revenue_earnings(income), use_container_width=True)

        # ── Competitors Comparison ───────────────────────────────────────────
        section("Competitors Comparison")
        peer_syms = fetch_peers(ticker_symbol)
        if peer_syms:
            all_syms = [ticker_symbol] + [p for p in peer_syms if p != ticker_symbol][:4]
            peers_data = []
            for ps in all_syms:
                pp = fetch_profile(ps)
                if not pp: continue
                inc_p, bal_p, _ = fetch_financials(ps)
                gm_p = np.nan; nm_p = np.nan; pe_p = np.nan; roe_p = np.nan
                if inc_p and bal_p:
                    rev_p = inc_p[0].get("revenue", 0) or 1
                    gm_p  = (inc_p[0].get("grossProfit", 0) or 0) / rev_p
                    nm_p  = (inc_p[0].get("netIncome",   0) or 0) / rev_p
                    eq_p  = bal_p[0].get("totalStockholdersEquity", 1) or 1
                    roe_p = (inc_p[0].get("netIncome", 0) or 0) / eq_p
                    eps_p = inc_p[0].get("eps", np.nan)
                    pr_p  = float(pp.get("price", np.nan) or np.nan)
                    pe_p  = pr_p / eps_p if pd.notna(eps_p) and eps_p else np.nan
                peers_data.append({
                    "symbol": ps, "name": pp.get("companyName", ps)[:22],
                    "price": float(pp.get("price", np.nan) or np.nan),
                    "mktCap": pp.get("mktCap", np.nan),
                    "grossMargin": gm_p, "netMargin": nm_p,
                    "roe": roe_p, "pe": pe_p,
                })

            if peers_data:
                rows = ""
                for pd_ in peers_data:
                    is_cur  = pd_["symbol"] == ticker_symbol
                    rc      = "cur-row" if is_cur else ""
                    sl      = "<b>" + pd_["symbol"] + "</b>" if is_cur else pd_["symbol"]
                    gms     = f'{pd_["grossMargin"]*100:.1f}%' if pd.notna(pd_["grossMargin"]) else "N/A"
                    nms     = f'{pd_["netMargin"]*100:.1f}%'   if pd.notna(pd_["netMargin"])   else "N/A"
                    roes    = f'{pd_["roe"]*100:.1f}%'         if pd.notna(pd_["roe"])          else "N/A"
                    pes     = f'{pd_["pe"]:.1f}x'              if pd.notna(pd_["pe"])           else "N/A"
                    mcs     = fmt_big(pd_["mktCap"])
                    prs     = f'${pd_["price"]:,.2f}' if pd.notna(pd_["price"]) else "N/A"
                    rows   += (
                        '<tr class="' + rc + '"><td>' + sl +
                        '<br><span style="font-size:11px;color:#64748b">' + pd_["name"] + '</span></td>' +
                        '<td class="num">' + prs + '</td>' +
                        '<td class="num">' + mcs + '</td>' +
                        '<td class="num">' + gms + '</td>' +
                        '<td class="num">' + nms + '</td>' +
                        '<td class="num">' + roes + '</td>' +
                        '<td class="num">' + pes + '</td></tr>'
                    )
                table_html = (
                    '<div style="background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.07);'
                    'border-radius:16px;overflow:hidden;padding:4px 0;">'
                    '<table class="peers-table"><thead><tr>'
                    '<th>Company</th><th>Price</th><th>Mkt Cap</th>'
                    '<th>Gross Margin</th><th>Net Margin</th><th>ROE</th><th>P/E</th>'
                    '</tr></thead><tbody>' + rows + '</tbody></table></div>'
                )
                st.markdown(table_html, unsafe_allow_html=True)
                st.plotly_chart(chart_peers(peers_data, ticker_symbol), use_container_width=True)
        else:
            st.caption("Peer data not available for this ticker.")

        # ── Latest News ──────────────────────────────────────────────────────
        section("Latest News")
        news = fetch_news(ticker_symbol)
        if news:
            for article in news:
                title    = article.get("title", article.get("headline", "No title"))
                url_link = article.get("url", article.get("link", "#"))
                source   = article.get("site", article.get("source", ""))
                pub_raw  = article.get("publishedDate", article.get("datetime", "")) or ""
                pub_date = pub_raw[:10] if pub_raw else ""
                meta     = source + (" · " + pub_date if pub_date else "")
                st.markdown(
                    '<a href="' + url_link + '" target="_blank" style="text-decoration:none;">'
                    '<div class="news-card">'
                    '<div class="news-dot"></div>'
                    '<div><div class="news-title">' + title + '</div>'
                    '<div class="news-meta"><span class="news-src">' + source + '</span>'
                    + (' · ' + pub_date if pub_date else '') +
                    '</div></div></div></a>',
                    unsafe_allow_html=True
                )
        else:
            st.caption("News not available for this ticker.")

    except Exception as e:
        st.error(f"Could not analyse {ticker_symbol}: {e}")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:60px;padding:28px 0 20px;border-top:1px solid rgba(255,255,255,0.06);text-align:center;">
  <div style="font-family:'Cormorant Garamond',serif;font-size:20px;font-weight:600;color:#818cf8;margin-bottom:8px;">MarketLens</div>
  <div style="font-size:12px;color:#475569;font-weight:300;line-height:1.8;max-width:600px;margin:0 auto;">
    Built for educational purposes only. All data sourced from public financial APIs.<br>
    <span style="color:#f87171;font-weight:500;">⚠ Not financial advice.</span>
    Do not make investment decisions based solely on this tool.<br>
    Always consult a qualified financial advisor before investing.
  </div>
  <div style="margin-top:16px;font-size:11px;color:#334155;letter-spacing:0.08em;">
    DATA · Financial Modeling Prep &amp; Yahoo Finance &nbsp;|&nbsp; BUILT WITH · Python &amp; Streamlit
  </div>
</div>
""", unsafe_allow_html=True)