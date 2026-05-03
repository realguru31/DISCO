"""
DISCO – DesiHedge Investment Strategy & Capital Opportunities
app.py — Streamlit dashboard
"""
import re
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import warnings
from datetime import datetime

# Suppress Streamlit components deprecation until official migration path is available
warnings.filterwarnings("ignore", message=".*st.components.v1.html.*")

# ══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="DISCO · DesiHedge",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
_DEFAULTS = dict(
    auth=False, user="", theme="dark",
    ticker=None, buy_px=None, stop_px=None,
    refresh_count=0,
    rp_equity=10000.0, rp_win_amt=2400.0, rp_loss_amt=600.0,
    rp_win_rate=60.0, rp_kelly_frac=33.0, rp_max_risk=33.0, rp_max_lev=2.5,
)
for _k, _v in _DEFAULTS.items():
    st.session_state.setdefault(_k, _v)

# ══════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════
def pn(val):
    """Parse float from messy cell value. Returns None for NaN, empty, or non-numeric."""
    if val is None:
        return None
    s = re.sub(r"[%£$,\s]", "", str(val))
    try:
        result = float(s)
        return None if result != result else result  # reject NaN (NaN != NaN by IEEE)
    except ValueError:
        return None


def fmt(v, d=2, sign=False):
    if v is None:
        return "—"
    s = f"{abs(v):,.{d}f}"
    if v < 0:
        s = "−" + s
    elif sign and v > 0:
        s = "+" + s
    return s


def fmt_pct_abs(v):
    """Format as absolute percentage (no leading +)."""
    if v is None:
        return "—"
    p = v * 100 if abs(v) < 2 else v
    return f"{abs(p):.1f}%"


def parse_date(s):
    s = str(s).strip()
    if not s or s in ("", "nan"):
        return "—"
    for f in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d %b %y", "%d %b %Y", "%d-%b-%y"):
        try:
            return datetime.strptime(s, f).strftime("%d %b %Y")
        except ValueError:
            pass
    return s


# ══════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_raw(url: str, bust: int = 0) -> pd.DataFrame:
    return pd.read_csv(url, header=None, dtype=str).fillna("")


def get_positions(raw: pd.DataFrame) -> list:
    out = []
    for i in range(3, len(raw)):
        r = raw.iloc[i].tolist()
        tk = r[2].strip() if len(r) > 2 else ""
        _SKIP = {"", "NAN", "TICKER", "N/A", "#N/A", "COMPANY"}
        if not tk or tk.upper() in _SKIP or not re.match(r"^[A-Z0-9:\.]+$", tk.upper()):
            continue
        pnl = pn(r[19]) if len(r) > 19 else None
        out.append(
            {
                "Ticker":     tk,
                "Shares":     pn(r[4])         if len(r) > 4  else None,
                "Entry Px":   pn(r[5])          if len(r) > 5  else None,
                "Entry Date": parse_date(r[8])  if len(r) > 8  else "—",
                "Stop Px":    pn(r[9])          if len(r) > 9  else None,
                "Curr Px":    pn(r[13])         if len(r) > 13 else None,
                "P&L":        pnl,
            }
        )
    return out


def get_kpis(raw: pd.DataFrame) -> dict:
    LC, VC, V2, V3 = 21, 25, 27, 29
    kpis: dict = {}
    for i in range(len(raw)):
        r = raw.iloc[i].tolist()
        if len(r) <= LC:
            continue
        lbl = r[LC].strip().upper()
        if not lbl:
            continue
        kpis[lbl] = {
            "v":  r[VC].strip()  if len(r) > VC  else "",
            "v2": r[V2].strip()  if len(r) > V2  else "",
            "v3": r[V3].strip()  if len(r) > V3  else "",
        }
    return kpis


def kget(kpis: dict, frag: str, key: str = "v") -> str:
    for k, d in kpis.items():
        if frag.upper() in k:
            return d.get(key, "")
    return ""


# ══════════════════════════════════════════════════════════════════
# CSS INJECTION
# ══════════════════════════════════════════════════════════════════
def inject_css(theme: str):
    d = theme == "dark"
    v = {
        "bg":   "#07090f" if d else "#f4f6f9",
        "sf":   "#0c1018" if d else "#ffffff",
        "sf2":  "#111827" if d else "#eef2f7",
        "bdr":  "#1a2333" if d else "#dde3ec",
        "bdrh": "#243347" if d else "#c4cede",
        "acc":  "#00d4ff" if d else "#0059b3",
        "grn":  "#00e676" if d else "#15803d",
        "grnd": "rgba(0,230,118,.07)" if d else "rgba(21,128,61,.07)",
        "red":  "#ff3366" if d else "#b91c1c",
        "redd": "rgba(255,51,102,.07)" if d else "rgba(185,28,28,.07)",
        "ylw":  "#ffd700" if d else "#b45309",
        "txt":  "#c9d1d9" if d else "#1e293b",
        "txtm": "#8fa3bc" if d else "#475569",
        "txtd": "#526a85" if d else "#94a3b8",
        "txth": "#f0f6ff" if d else "#0f172a",
        "inbg": "#07090f" if d else "#f8fafc",
        "btnc": "#000000" if d else "#ffffff",
    }
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Syne:wght@700;800&display=swap');
:root{{
  --bg:{v["bg"]};--sf:{v["sf"]};--sf2:{v["sf2"]};--bdr:{v["bdr"]};--bdrh:{v["bdrh"]};
  --acc:{v["acc"]};--grn:{v["grn"]};--grnd:{v["grnd"]};
  --red:{v["red"]};--redd:{v["redd"]};--ylw:{v["ylw"]};
  --txt:{v["txt"]};--txtm:{v["txtm"]};--txtd:{v["txtd"]};--txth:{v["txth"]};
  --inbg:{v["inbg"]};--mono:'JetBrains Mono',monospace;
  --sans:'Inter',-apple-system,sans-serif;--disp:'Syne',sans-serif;
}}
#MainMenu,footer{{visibility:hidden}}
.stDeployButton,[data-testid="stToolbar"]{{display:none!important}}
header[data-testid="stHeader"]{{display:none!important}}
.block-container{{padding:0!important;max-width:100%!important}}
section[data-testid="stSidebar"]{{display:none!important}}
html,body,.stApp{{background:var(--bg)!important;color:var(--txt)!important;
  font-family:var(--sans)!important;font-size:15px!important;}}
/* Inputs */
.stTextInput input,.stPasswordInput input{{
  background:var(--inbg)!important;border-color:var(--bdrh)!important;
  color:var(--txth)!important;font-family:var(--mono)!important;
  font-size:15px!important;padding:11px 14px!important;border-radius:7px!important;}}
.stTextInput label,.stPasswordInput label{{color:var(--txtm)!important;
  font-size:11px!important;font-weight:600!important;
  letter-spacing:.5px!important;text-transform:uppercase!important;}}
.stNumberInput input{{background:var(--inbg)!important;border-color:var(--bdrh)!important;
  color:var(--txth)!important;font-family:var(--mono)!important;
  font-size:14px!important;border-radius:7px!important;}}
.stNumberInput label{{color:var(--txtm)!important;font-size:11px!important;
  font-weight:600!important;letter-spacing:.5px!important;text-transform:uppercase!important;}}
/* Buttons */
.stButton>button{{background:var(--acc)!important;color:{v["btnc"]}!important;
  border:none!important;border-radius:7px!important;font-family:var(--sans)!important;
  font-weight:700!important;font-size:13px!important;
  padding:10px 16px!important;letter-spacing:.3px!important;}}
.stButton>button:hover{{opacity:.82!important}}
/* Expander */
details summary{{background:var(--sf2)!important;color:var(--txth)!important;
  font-weight:600!important;font-size:14px!important;
  border:1px solid var(--bdrh)!important;border-radius:8px!important;padding:12px 18px!important;}}
details[open] summary{{border-radius:8px 8px 0 0!important}}
details .streamlit-expanderContent{{
  background:var(--sf)!important;border:1px solid var(--bdrh)!important;
  border-top:none!important;border-radius:0 0 8px 8px!important;padding:22px!important;}}
/* Scrollbar */
::-webkit-scrollbar{{width:4px;height:4px}}
::-webkit-scrollbar-track{{background:var(--bg)}}
::-webkit-scrollbar-thumb{{background:var(--bdrh);border-radius:2px}}
/* HTML table (theme-aware, replaces st.dataframe) */
.disco-table{{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:13px;}}
.disco-table th{{background:var(--sf2)!important;color:var(--txtm)!important;
  font-size:10px!important;font-weight:700!important;letter-spacing:.8px!important;
  text-transform:uppercase!important;padding:9px 12px!important;
  border-bottom:2px solid var(--bdrh)!important;text-align:right!important;}}
.disco-table th:first-child{{text-align:left!important;}}
.disco-table td{{padding:10px 12px!important;border-bottom:1px solid var(--bdr)!important;
  color:var(--txth)!important;text-align:right!important;}}
.disco-table td:first-child{{text-align:left!important;font-weight:600!important;
  color:var(--acc)!important;}}
.disco-table tr:hover td{{background:var(--sf2)!important;filter:brightness(1.04);}}
.disco-table tr.sel-row td{{background:var(--sf2)!important;
  border-left:3px solid var(--acc)!important;}}
.disco-table tr.pnl-pos td{{background:rgba(30,144,255,0.06)!important;}}
.disco-table tr.pnl-neg td{{background:rgba(255,0,255,0.06)!important;}}
.disco-table .pnl-pos-txt{{color:#1E90FF!important;font-weight:700!important;}}
.disco-table .pnl-neg-txt{{color:#FF00FF!important;font-weight:700!important;}}
/* Radio — completely hidden, used only as Streamlit state bridge */
div[data-testid="stRadio"]{{display:none!important;}}
</style>""",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
# AUTH SCREEN
# ══════════════════════════════════════════════════════════════════
def show_login():
    inject_css(st.session_state.theme)
    st.markdown('<div style="height:50px;"></div>', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        st.markdown(
            """
<div style="background:var(--sf);border:1px solid var(--bdrh);border-radius:14px;
  padding:52px 48px;text-align:center;box-shadow:0 8px 48px rgba(0,0,0,.3);">
  <div style="font-family:var(--disp);font-size:36px;font-weight:800;
    letter-spacing:5px;color:var(--txth);">DIS<span style="color:var(--acc)">CO</span></div>
  <div style="font-size:10px;letter-spacing:1.5px;color:var(--txtd);
    text-transform:uppercase;line-height:2.2;margin-top:6px;">
    DesiHedge Investment Strategy<br>&amp; Capital Opportunities</div>
  <div style="width:52px;height:2px;background:var(--acc);
    margin:22px auto 38px;border-radius:1px;"></div>
</div>""",
            unsafe_allow_html=True,
        )
        email    = st.text_input("Email Address", placeholder="you@email.com")
        password = st.text_input("Password", placeholder="••••••••", type="password")
        if st.button("SIGN IN  →", use_container_width=True):
            try:
                users = st.secrets["users"]
                ok = False
                for _, u in users.items():
                    if email.strip().lower() == u["email"].lower() and password == u["password"]:
                        st.session_state.auth = True
                        st.session_state.user = email.strip()
                        ok = True
                        st.rerun()
                if not ok:
                    st.error("Invalid email or password.")
            except Exception as e:
                st.error(f"Auth config error: {e}")


# ══════════════════════════════════════════════════════════════════
# KPI CARDS
# ══════════════════════════════════════════════════════════════════
def _card(lbl, val, cls="", sub=""):
    cols = {"pos": "var(--grn)", "neg": "var(--red)", "ok": "var(--grn)", "warn": "var(--ylw)"}
    col  = cols.get(cls, "var(--txth)")
    sub_html = (
        f'<div style="font-size:11px;color:var(--txtd);margin-top:6px;">{sub}</div>'
        if sub else ""
    )
    return (
        f'<div style="background:var(--sf);border:1px solid var(--bdr);border-radius:10px;'
        f'padding:18px 20px;flex:1;min-width:155px;">'
        f'<div style="font-size:10px;font-weight:600;letter-spacing:.8px;'
        f'text-transform:uppercase;color:var(--txtd);margin-bottom:10px;">{lbl}</div>'
        f'<div style="font-family:var(--disp);font-size:28px;font-weight:800;'
        f'color:{col};line-height:1;">{val}</div>'
        f'{sub_html}</div>'
    )


def render_kpis(kpis: dict, positions: list):
    total_pnl   = pn(kget(kpis, "TOTAL PROFIT"))
    initial_cap = pn(kget(kpis, "INITIAL INVESTMENT")) or pn(kget(kpis, "BROKERAGE")) or 1
    risk_eq     = pn(kget(kpis, "RISK ON EQUITY"))
    new_pos     = kget(kpis, "NEW POSITION").upper().strip()

    # P&L as % of initial capital
    pnl_pct     = (total_pnl / initial_cap * 100) if total_pnl is not None and initial_cap else None
    pnl_sign    = "+" if (pnl_pct or 0) > 0 else ""
    pnl_str     = f"{pnl_sign}{pnl_pct:.2f}%" if pnl_pct is not None else "—"

    # Risk on equity (sheet stores as raw %, e.g. 4.91 means 4.91%)
    risk_pct    = (risk_eq * 100 if risk_eq and abs(risk_eq) < 2 else risk_eq) if risk_eq else 0
    risk_over   = abs(risk_pct) > 33
    risk_str    = f"{abs(risk_pct):.1f}%" if risk_eq else "—"

    winners = sum(1 for p in positions if (p["P&L"] or 0) > 0)
    losers  = sum(1 for p in positions if (p["P&L"] or 0) < 0)

    cards = [
        _card("Total Return",
              pnl_str,
              "pos" if (pnl_pct or 0) > 0 else "neg" if (pnl_pct or 0) < 0 else "",
              f"{winners}W · {losers}L of {len(positions)} positions"),
        _card("Risk on Equity",
              risk_str,
              "neg" if risk_over else "ok",
              "limit 33%"),
        _card("New Position?",
              new_pos or "—",
              "ok" if new_pos == "YES" else "neg" if "NO" in new_pos else "",
              f"{len(positions)} open position{'s' if len(positions)!=1 else ''}"),
    ]
    grid = "".join(cards)
    st.markdown(
        f'<div style="display:flex;gap:12px;flex-wrap:wrap;padding:16px 20px 12px;">{grid}</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════
# RISK MANAGEMENT PARAMETERS
# ══════════════════════════════════════════════════════════════════
def render_risk_params(kpis: dict):
    with st.expander("⚙️  Risk Management Parameters", expanded=False):
        c1, c2, c3 = st.columns([1, 1, 1], gap="large")

        with c1:
            st.markdown(
                '<div style="font-size:11px;font-weight:700;letter-spacing:1px;'
                'text-transform:uppercase;color:var(--txtm);padding-bottom:10px;'
                'border-bottom:1px solid var(--bdr);margin-bottom:14px;">Portfolio Inputs</div>',
                unsafe_allow_html=True,
            )
            equity   = st.number_input("Brokerage Equity Balance (£/$)",
                                        value=st.session_state.rp_equity, step=100.0, format="%.2f")
            win_amt  = st.number_input("Expected Win per Trade (£/$)",
                                        value=st.session_state.rp_win_amt, step=50.0, format="%.0f")
            loss_amt = st.number_input("Expected Loss per Trade (£/$)",
                                        value=st.session_state.rp_loss_amt, step=50.0, format="%.0f")

        with c2:
            st.markdown(
                '<div style="font-size:11px;font-weight:700;letter-spacing:1px;'
                'text-transform:uppercase;color:var(--txtm);padding-bottom:10px;'
                'border-bottom:1px solid var(--bdr);margin-bottom:14px;">Strategy Parameters</div>',
                unsafe_allow_html=True,
            )
            win_rate   = st.number_input("Expected Win Rate (%)", value=st.session_state.rp_win_rate,
                                          min_value=1.0, max_value=99.0, step=1.0, format="%.0f")
            kelly_frac = st.number_input("Fractional Kelly Multiplier (%)", value=st.session_state.rp_kelly_frac,
                                          min_value=1.0, max_value=100.0, step=1.0, format="%.0f")
            max_risk   = st.number_input("Max Portfolio Risk on Equity (%)", value=st.session_state.rp_max_risk,
                                          min_value=1.0, max_value=100.0, step=1.0, format="%.0f")
            max_lev    = st.number_input("Max Leverage", value=st.session_state.rp_max_lev,
                                          min_value=1.0, max_value=10.0, step=0.1, format="%.1f")

        # Persist to session state
        st.session_state.rp_equity     = equity
        st.session_state.rp_win_amt    = win_amt
        st.session_state.rp_loss_amt   = loss_amt
        st.session_state.rp_win_rate   = win_rate
        st.session_state.rp_kelly_frac = kelly_frac
        st.session_state.rp_max_risk   = max_risk
        st.session_state.rp_max_lev    = max_lev

        with c3:
            st.markdown(
                '<div style="font-size:11px;font-weight:700;letter-spacing:1px;'
                'text-transform:uppercase;color:var(--txtm);padding-bottom:10px;'
                'border-bottom:1px solid var(--bdr);margin-bottom:14px;">Calculated Outputs</div>',
                unsafe_allow_html=True,
            )
            # Kelly formula: f* = (b*p - q) / b
            ratio      = win_amt / loss_amt if loss_amt else 0
            loss_rate  = 100.0 - win_rate
            p_w, p_l   = win_rate / 100, loss_rate / 100
            full_kelly = max(0.0, (ratio * p_w - p_l) / ratio * 100) if ratio > 0 else 0.0
            frac_kelly = full_kelly * (kelly_frac / 100)
            next_sz    = equity * (frac_kelly / 100)

            # Pull current risk + leverage from sheet for "New Position Allowed?"
            curr_re  = pn(kget(kpis, "RISK ON EQUITY"))
            curr_rp  = abs(curr_re * 100) if curr_re and abs(curr_re) < 2 else abs(curr_re or 0)
            curr_lev = pn(kget(kpis, "LEVERAGE")) or 0
            new_ok   = curr_rp < max_risk and curr_lev < max_lev

            def _row(lbl, val, flag=None):
                if flag is True:
                    col, fw = "var(--grn)", "700"
                elif flag is False:
                    col, fw = "var(--red)", "700"
                else:
                    col, fw = "var(--txth)", "600"
                return (
                    f'<div style="display:flex;justify-content:space-between;align-items:center;'
                    f'padding:9px 0;border-bottom:1px solid var(--bdr);font-size:14px;">'
                    f'<span style="color:var(--txtm);">{lbl}</span>'
                    f'<span style="font-family:var(--mono);color:{col};font-weight:{fw};">{val}</span>'
                    f'</div>'
                )

            html = (
                _row("Win / Loss Ratio",     f"{ratio:.2f}") +
                _row("Win Rate",             f"{win_rate:.0f}%") +
                _row("Loss Rate",            f"{loss_rate:.0f}%") +
                _row("Full Kelly %",         f"{full_kelly:.1f}%") +
                _row("Fractional Kelly %",   f"{frac_kelly:.1f}%") +
                _row("Next Position Size %", f"{frac_kelly:.1f}%") +
                _row("Next Position £/$",    f"£{next_sz:,.0f}") +
                _row("New Position Allowed?",
                      "YES" if new_ok else "NO",
                      new_ok)
            )
            st.markdown(
                f'<div style="background:var(--sf2);border:1px solid var(--bdr);'
                f'border-radius:8px;padding:2px 16px;">{html}</div>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════
# TABLE + CHART  — single component, Lightweight Charts, no radio hacks
# ══════════════════════════════════════════════════════════════════
def render_panel(positions: list, theme: str = "dark", height: int = 700):
    """
    One components.html block containing:
      - clickable positions table (left pane)
      - Lightweight Charts candlestick chart (right pane)
    Row clicks directly call loadChart() in the same JS scope.
    OHLCV data fetched browser-side from Yahoo Finance (no CORS on HTTPS).
    SMAs and price lines rendered natively by Lightweight Charts.
    """
    import json as _json
    if not positions:
        st.info("No positions found.")
        return

    d          = theme == "dark"
    t_bg       = "#07090f" if d else "#f4f6f9"
    t_surface  = "#0c1018" if d else "#ffffff"
    t_bdr      = "#1a2333" if d else "#dde3ec"
    t_hdr_col  = "#526a85" if d else "#94a3b8"
    t_txt      = "#d0dae6" if d else "#1e293b"
    t_acc      = "#00d4ff" if d else "#0059b3"
    t_sel_bg   = "#111827" if d else "#eef2f7"
    chart_bg   = "#07090f" if d else "#ffffff"
    chart_txt  = "#7a8fa6" if d else "#374151"
    chart_grid = "rgba(26,35,51,.7)" if d else "rgba(220,225,232,.8)"
    chart_bdr  = "#1a2333" if d else "#e5e7eb"
    sma200_col = "#FFFFFF" if d else "#000000"

    pos_js = _json.dumps(positions, default=str)
    tbl_h  = 38 + 44 * len(positions) + 20       # approx px for table
    comp_h = max(height, tbl_h + 60)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@800&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{height:100%;background:{t_bg};color:{t_txt};font-family:'JetBrains Mono',monospace;font-size:13px;overflow:hidden;}}
.wrap{{display:flex;height:{comp_h}px;}}
/* ── TABLE ── */
.tbl-panel{{width:390px;flex-shrink:0;display:flex;flex-direction:column;border-right:1px solid {t_bdr};}}
.tbl-label{{font-size:9px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;
  color:{t_hdr_col};padding:7px 12px;background:{t_surface};border-bottom:1px solid {t_bdr};flex-shrink:0;}}
.tbl-wrap{{overflow-y:auto;flex:1;}}
table{{width:100%;border-collapse:collapse;white-space:nowrap;}}
thead th{{position:sticky;top:0;z-index:5;background:{t_surface};
  font-size:9px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;
  padding:7px 9px;border-bottom:2px solid {t_bdr};text-align:right;color:{t_hdr_col};}}
thead th:first-child{{text-align:left;}}
tbody tr{{border-bottom:1px solid {t_bdr};cursor:pointer;}}
tbody tr:hover td{{background:rgba(0,212,255,.05);}}
tbody tr.sel{{border-left:3px solid {t_acc};}}
tbody tr.sel td{{background:{t_sel_bg};}}
td{{padding:9px 9px;text-align:right;color:{t_txt};}}
td:first-child{{text-align:left;font-weight:600;color:{t_acc};}}
.rp{{color:#1E90FF;font-weight:700;}}
.rn{{color:#FF00FF;font-weight:700;}}
/* ── CHART ── */
.chart-panel{{flex:1;display:flex;flex-direction:column;min-width:0;}}
.chart-hdr{{flex-shrink:0;background:{t_surface};border-bottom:1px solid {t_bdr};
  padding:7px 14px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;min-height:42px;}}
.ct{{font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:{t_txt};}}
.bb{{padding:3px 10px;border-radius:4px;font-size:11px;font-weight:600;display:none;}}
.buy-b{{background:rgba(0,230,118,.10);color:#00e676;border:1px solid rgba(0,230,118,.3);}}
.stp-b{{background:rgba(255,0,255,.08);color:#FF00FF;border:1px solid rgba(255,0,255,.3);}}
.leg{{margin-left:auto;font-size:10px;color:{t_hdr_col};text-align:right;line-height:1.7;}}
#cc{{flex:1;position:relative;min-height:0;}}
#ch{{position:absolute;inset:0;}}
.ph{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:10px;color:{t_hdr_col};font-size:13px;letter-spacing:.3px;opacity:.7;}}
::-webkit-scrollbar{{width:3px;}}.wrap::-webkit-scrollbar{{display:none;}}
::-webkit-scrollbar-thumb{{background:{t_bdr};border-radius:2px;}}
</style>
</head>
<body>
<div class="wrap">
<div class="tbl-panel">
  <div class="tbl-label">Open Positions — click any row to chart →</div>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Ticker</th><th>Shares</th><th>Entry Px</th><th>Entry Date</th><th>Stop Px</th><th>Curr Px</th><th>Return</th></tr></thead>
    <tbody id="tbl"></tbody>
  </table></div>
</div>
<div class="chart-panel">
  <div class="chart-hdr">
    <span class="ct" id="ct">—</span>
    <span class="bb buy-b" id="bb"></span>
    <span class="bb stp-b" id="bs"></span>
    <div class="leg">
      Daily &nbsp;·&nbsp;
      <span style="color:#1565C0;font-size:13px;">━</span> SMA 50 &nbsp;·&nbsp;
      <span style="color:{sma200_col};font-size:13px;">━</span> SMA 200 &nbsp;·&nbsp;
      <span style="color:rgba(30,144,255,.9);">▲</span> Blue &nbsp;·&nbsp;
      <span style="color:rgba(255,0,255,.9);">▼</span> Magenta
    </div>
  </div>
  <div id="cc">
    <div id="ch"></div>
    <div class="ph" id="ph">📈&nbsp;&nbsp;Select a position to view chart</div>
  </div>
</div>
</div>

<script>
// ── Data injected from Python ────────────────────────────────────
const POSITIONS  = {pos_js};
const CHART_BG   = "{chart_bg}";
const CHART_TXT  = "{chart_txt}";
const CHART_GRID = "{chart_grid}";
const CHART_BDR  = "{chart_bdr}";
const SMA200     = "{sma200_col}";

// ── Build table ──────────────────────────────────────────────────
let selIdx = 0;

function retPct(p) {{
  const ep = p["Entry Px"], cp = p["Curr Px"];
  if (!ep || !cp || ep === 0) return ["—", 0];
  const pct = (cp - ep) / ep * 100;
  return [(pct >= 0 ? "+" : "") + pct.toFixed(2) + "%", pct];
}}

function px(v) {{ return v != null ? (+v).toFixed(2) : "—"; }}

function buildTable() {{
  const tbody = document.getElementById("tbl");
  POSITIONS.forEach((p, i) => {{
    const [rs, rv] = retPct(p);
    const tr = document.createElement("tr");
    tr.className = i === 0 ? "sel" : "";
    tr.innerHTML =
      `<td>${{p["Ticker"]}}</td>` +
      `<td>${{p["Shares"] != null ? Math.round(p["Shares"]) : "—"}}</td>` +
      `<td>${{px(p["Entry Px"])}}</td>` +
      `<td>${{p["Entry Date"] || "—"}}</td>` +
      `<td>${{px(p["Stop Px"])}}</td>` +
      `<td>${{px(p["Curr Px"])}}</td>` +
      `<td class="${{rv > 0 ? "rp" : rv < 0 ? "rn" : ""}}">${{rs}}</td>`;
    tr.onclick = () => selectRow(i, tr);
    tbody.appendChild(tr);
  }});
}}

function selectRow(i, tr) {{
  document.querySelectorAll("#tbl tr").forEach(r => r.classList.remove("sel"));
  tr.classList.add("sel");
  selIdx = i;
  const p = POSITIONS[i];
  loadChart(p["Ticker"], p["Entry Px"], p["Stop Px"]);
}}

// ── Lightweight Charts ───────────────────────────────────────────
let chartObj = null, resizeObs = null;

function calcSMA(data, period) {{
  const out = [];
  for (let i = period - 1; i < data.length; i++) {{
    let s = 0;
    for (let j = i - period + 1; j <= i; j++) s += data[j].close;
    out.push({{ time: data[i].time, value: +(s / period).toFixed(4) }});
  }}
  return out;
}}

async function loadChart(ticker, buyPx, stopPx) {{
  // Update header
  document.getElementById("ct").textContent = ticker;
  const bb = document.getElementById("bb"), bs = document.getElementById("bs");
  if (buyPx != null) {{ bb.textContent = "● BUY  " + (+buyPx).toFixed(2); bb.style.display = "inline"; }}
  else bb.style.display = "none";
  if (stopPx != null) {{ bs.textContent = "● STOP  " + (+stopPx).toFixed(2); bs.style.display = "inline"; }}
  else bs.style.display = "none";
  document.getElementById("ph").style.display = "none";

  // Tear down old chart
  const cc = document.getElementById("ch");
  cc.innerHTML = "";
  if (resizeObs) {{ resizeObs.disconnect(); resizeObs = null; }}
  if (chartObj)  {{ try {{ chartObj.remove(); }} catch(e){{}} chartObj = null; }}

  // Create chart
  const container = document.getElementById("cc");
  const chart = LightweightCharts.createChart(cc, {{
    width:  container.clientWidth,
    height: container.clientHeight,
    layout: {{ background: {{ color: CHART_BG }}, textColor: CHART_TXT }},
    grid:   {{ vertLines: {{ color: CHART_GRID }}, horzLines: {{ color: CHART_GRID }} }},
    crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
    rightPriceScale: {{ borderColor: CHART_BDR }},
    timeScale: {{ borderColor: CHART_BDR, timeVisible: true }},
  }});
  chartObj = chart;

  const candles = chart.addCandlestickSeries({{
    upColor: "rgba(30,144,255,0.60)", downColor: "rgba(255,0,255,0.60)",
    borderUpColor: "rgba(30,144,255,0.85)", borderDownColor: "rgba(255,0,255,0.85)",
    wickUpColor: "rgba(30,144,255,0.70)", wickDownColor: "rgba(255,0,255,0.70)",
  }});
  const sma50s = chart.addLineSeries({{
    color: "#1565C0", lineWidth: 1.5, title: "SMA 50",
    priceLineVisible: false, lastValueVisible: true, crosshairMarkerVisible: false,
  }});
  const sma200s = chart.addLineSeries({{
    color: SMA200, lineWidth: 1.5, title: "SMA 200",
    priceLineVisible: false, lastValueVisible: true, crosshairMarkerVisible: false,
  }});

  // Fetch OHLCV — Yahoo Finance direct (no CORS issues on HTTPS)
  try {{
    const sym = ticker.includes(":") ? ticker.split(":")[1] : ticker;
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${{sym}}?interval=1d&range=2y`;
    const res = await fetch(url);
    const js  = await res.json();
    const r   = js.chart.result[0];
    const ts  = r.timestamp;
    const q   = r.indicators.quote[0];

    const ohlcv = ts.map((t, i) => ({{
      time: t,
      open: q.open[i], high: q.high[i], low: q.low[i], close: q.close[i],
    }})).filter(d => d.open != null && d.high != null && d.low != null && d.close != null)
       .sort((a, b) => a.time - b.time);

    candles.setData(ohlcv);
    sma50s.setData(calcSMA(ohlcv, 50));
    sma200s.setData(calcSMA(ohlcv, 200));

    if (buyPx != null)  candles.createPriceLine({{ price: +buyPx,  color: "#00e676", lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true, title: "BUY" }});
    if (stopPx != null) candles.createPriceLine({{ price: +stopPx, color: "#FF00FF", lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true, title: "STOP" }});

    chart.timeScale().fitContent();

  }} catch(e) {{
    cc.innerHTML = `<div class="ph">⚠ Chart unavailable for ${{ticker}}<br><small style="font-size:10px;">${{e.message}}</small></div>`;
  }}

  resizeObs = new ResizeObserver(() => {{
    const c = document.getElementById("cc");
    chart.resize(c.clientWidth, c.clientHeight);
  }});
  resizeObs.observe(container);
}}

// ── Init ─────────────────────────────────────────────────────────
buildTable();
if (POSITIONS.length > 0) {{
  const p = POSITIONS[0];
  loadChart(p["Ticker"], p["Entry Px"], p["Stop Px"]);
}}
</script>
</body></html>"""

    components.html(html, height=comp_h + 4, scrolling=False)


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    if not st.session_state.auth:
        show_login()
        return

    theme = st.session_state.theme
    inject_css(theme)

    # ── HEADER BAR
    hc1, hc2, hc3, hc4, hc5 = st.columns([7, 1.1, 1.1, 1.8, 1.1])
    with hc1:
        acc = "#00d4ff" if theme == "dark" else "#0059b3"
        sf  = "#0c1018" if theme == "dark" else "#ffffff"
        bdr = "#1a2333" if theme == "dark" else "#dde3ec"
        txh = "#f0f6ff" if theme == "dark" else "#0f172a"
        txd = "#3d4f63" if theme == "dark" else "#94a3b8"
        st.markdown(
            f'<div style="padding:14px 20px;background:{sf};'
            f'border-bottom:1px solid {bdr};">'
            f'<span style="font-family:Syne,sans-serif;font-size:22px;font-weight:800;'
            f'letter-spacing:3px;color:{txh};">DIS<span style="color:{acc};">CO</span></span>'
            f'<span style="font-size:10px;letter-spacing:1px;color:{txd};'
            f'text-transform:uppercase;margin-left:16px;">'
            f'DesiHedge Investment Strategy &amp; Capital Opportunities</span></div>',
            unsafe_allow_html=True,
        )
    with hc2:
        st.markdown('<div style="padding:8px 0 0;"></div>', unsafe_allow_html=True)
        if st.button("☀️ Light" if theme == "dark" else "🌙 Dark", use_container_width=True):
            st.session_state.theme = "light" if theme == "dark" else "dark"
            st.rerun()
    with hc3:
        st.markdown('<div style="padding:8px 0 0;"></div>', unsafe_allow_html=True)
        if st.button("↻ Refresh", use_container_width=True):
            st.session_state.refresh_count += 1
            st.rerun()
    with hc4:
        st.markdown(
            f'<div style="padding:18px 4px 0;font-size:11px;color:var(--txtm);'
            f'text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
            f'{st.session_state.user}</div>',
            unsafe_allow_html=True,
        )
    with hc5:
        st.markdown('<div style="padding:8px 0 0;"></div>', unsafe_allow_html=True)
        if st.button("⏻ Sign Out", use_container_width=True):
            st.session_state.auth = False
            st.session_state.user = ""
            st.rerun()

    # ── LOAD DATA
    url = st.secrets.get("SHEET_URL", "")
    if not url:
        st.error("SHEET_URL not set in secrets.")
        return
    try:
        raw       = load_raw(url, bust=st.session_state.refresh_count)
        positions = get_positions(raw)
        kpis      = get_kpis(raw)
    except Exception as e:
        st.error(f"Failed to load sheet data: {e}")
        return

    # ── RISK KPIs
    render_kpis(kpis, positions)

    # ── RISK PARAMETERS (collapsible)
    with st.container():
        st.markdown('<div style="padding:0 20px 8px;">', unsafe_allow_html=True)
        render_risk_params(kpis)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

    # ── TABLE + CHART (single self-contained component)
    render_panel(positions, theme=theme, height=700)


main()
