"""
DISCO – DesiHedge Investment Strategy & Capital Opportunities
app.py — Streamlit dashboard
"""
import re
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

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
@st.cache_data(ttl=300, show_spinner=False)
def load_raw(url: str) -> pd.DataFrame:
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
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--bdrh);border-radius:2px}
/* HTML table (theme-aware, replaces st.dataframe) */
.disco-table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:13px;}
.disco-table th{background:var(--sf2)!important;color:var(--txtm)!important;
  font-size:10px!important;font-weight:700!important;letter-spacing:.8px!important;
  text-transform:uppercase!important;padding:9px 12px!important;
  border-bottom:2px solid var(--bdrh)!important;text-align:right!important;}
.disco-table th:first-child{text-align:left!important;}
.disco-table td{padding:10px 12px!important;border-bottom:1px solid var(--bdr)!important;
  color:var(--txth)!important;text-align:right!important;}
.disco-table td:first-child{text-align:left!important;font-weight:600!important;
  color:var(--acc)!important;}
.disco-table tr:hover td{background:var(--sf2)!important;filter:brightness(1.04);}
.disco-table tr.sel-row td{background:var(--sf2)!important;
  border-left:3px solid var(--acc)!important;}
.disco-table tr.pnl-pos td{background:rgba(0,230,118,0.06)!important;}
.disco-table tr.pnl-neg td{background:rgba(255,51,102,0.06)!important;}
.disco-table .pnl-pos-txt{color:#00e676!important;font-weight:700!important;}
.disco-table .pnl-neg-txt{color:#ff3366!important;font-weight:700!important;}
/* Radio (ticker selector) */
div[data-testid="stRadio"]{padding:0!important;}
div[data-testid="stRadio"] label{display:none!important;}
div[data-testid="stRadio"] > div{gap:8px!important;}
div[data-testid="stRadio"] > div > label{
  background:var(--sf2)!important;border:1px solid var(--bdr)!important;
  border-radius:6px!important;padding:6px 14px!important;
  font-family:var(--mono)!important;font-size:12px!important;font-weight:600!important;
  color:var(--txt)!important;cursor:pointer!important;display:inline-flex!important;
  align-items:center!important;gap:6px!important;}
div[data-testid="stRadio"] > div > label:has(input:checked){
  background:var(--acc)!important;color:#000!important;
  border-color:var(--acc)!important;}
div[data-testid="stRadio"] > div > label > div[data-testid="stMarkdownContainer"]{
  color:inherit!important;}
div[data-testid="stRadio"] > div > label input{display:none!important;}
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
    total_pnl = pn(kget(kpis, "TOTAL PROFIT"))
    risk_eq   = pn(kget(kpis, "RISK ON EQUITY"))
    risk_gbp  = pn(kget(kpis, "CURRENT RISK ("))
    port_size = pn(kget(kpis, "PORTFOLIO SIZE"))
    leverage  = pn(kget(kpis, "LEVERAGE"))
    new_pos   = kget(kpis, "NEW POSITION").upper().strip()

    risk_pct  = (risk_eq * 100 if risk_eq and abs(risk_eq) < 2 else risk_eq) if risk_eq else 0
    risk_over = abs(risk_pct) > 33
    lev_over  = (leverage or 0) > 2.5

    winners = sum(1 for p in positions if (p["P&L"] or 0) > 0)
    losers  = sum(1 for p in positions if (p["P&L"] or 0) < 0)

    cards = [
        _card("Total P&L",
              fmt(total_pnl, sign=True) if total_pnl is not None else "—",
              "pos" if (total_pnl or 0) > 0 else "neg" if (total_pnl or 0) < 0 else "",
              f"{winners} winner{'s' if winners!=1 else ''} · {losers} loser{'s' if losers!=1 else ''}"),
        _card("Risk on Equity",
              fmt_pct_abs(risk_eq) if risk_eq else "—",
              "neg" if risk_over else "ok", "max 33%"),
        _card("Current Risk £/$",
              fmt(risk_gbp, 0) if risk_gbp else "—",
              "", "total exposure"),
        _card("Portfolio Size",
              fmt(port_size, 0) if port_size else "—",
              "", "market value"),
        _card("Leverage",
              f"{leverage:.2f}×" if leverage else "—",
              "neg" if lev_over else "ok", "max 2.5×"),
        _card("New Position?",
              new_pos or "—",
              "ok" if new_pos == "YES" else "neg" if "NO" in new_pos else "",
              f"{len(positions)} open position{'s' if len(positions)!=1 else ''}"),
    ]
    grid = "".join(cards)
    st.markdown(
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;padding:16px 20px 12px;">{grid}</div>',
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
# POSITIONS TABLE  (pure HTML — theme-aware, no st.dataframe)
# ══════════════════════════════════════════════════════════════════
def render_table(positions: list, selected_ticker: str | None):
    if not positions:
        st.info("No positions found in the sheet.")
        return None

    def _pnl_fmt(v):
        if v is None: return "—"
        return f"+{v:.2f}" if v > 0 else f"{v:.2f}"

    def _px(v):
        return f"{v:.2f}" if v is not None else "—"

    # Build HTML rows
    rows_html = ""
    for p in positions:
        pnl      = p["P&L"]
        is_sel   = p["Ticker"] == selected_ticker
        row_cls  = "sel-row " if is_sel else ""
        row_cls += "pnl-pos" if (pnl or 0) > 0 else "pnl-neg" if (pnl or 0) < 0 else ""
        pnl_cls  = "pnl-pos-txt" if (pnl or 0) > 0 else "pnl-neg-txt" if (pnl or 0) < 0 else ""
        sel_dot  = ('<span style="color:var(--acc);margin-right:4px;">●</span>' if is_sel
                    else '<span style="color:transparent;margin-right:4px;">●</span>')
        rows_html += (
            f'<tr class="{row_cls.strip()}">' +
            f'<td>{sel_dot}{p["Ticker"]}</td>' +
            f'<td>{int(p["Shares"]) if p["Shares"] else "—"}</td>' +
            f'<td>{_px(p["Entry Px"])}</td>' +
            f'<td>{p["Entry Date"]}</td>' +
            f'<td>{_px(p["Stop Px"])}</td>' +
            f'<td>{_px(p["Curr Px"])}</td>' +
            f'<td class="{pnl_cls}">{_pnl_fmt(pnl)}</td>' +
            f'</tr>'
        )

    table_html = f"""
<div style="margin-bottom:10px;">
  <div style="font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
    color:var(--txtd);padding:10px 2px 10px;">Open Positions — select ticker below to chart ↓</div>
  <table class="disco-table">
    <thead><tr>
      <th>Ticker</th><th>Shares</th><th>Entry Px</th>
      <th>Entry Date</th><th>Stop Px</th><th>Curr Px</th><th>P&amp;L</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>"""
    st.markdown(table_html, unsafe_allow_html=True)

    # Ticker selector
    tickers = [p["Ticker"] for p in positions]
    default_idx = tickers.index(selected_ticker) if selected_ticker in tickers else 0
    chosen = st.radio(
        "Select position",
        tickers,
        index=default_idx,
        horizontal=True,
        key="ticker_radio",
        label_visibility="collapsed",
    )
    # Return full position dict for chosen ticker
    for p in positions:
        if p["Ticker"] == chosen:
            return p
    return positions[0]


# ══════════════════════════════════════════════════════════════════
# TRADINGVIEW CHART
# ══════════════════════════════════════════════════════════════════
def render_chart(ticker, buy_px, stop_px, theme: str, height: int = 700):
    tv_theme   = "dark" if theme == "dark" else "light"
    sma200_col = "#FFFFFF" if theme == "dark" else "#000000"
    d          = theme == "dark"
    bg         = "#0c1018"  if d else "#ffffff"
    hdr_bdr    = "#1a2333"  if d else "#e2e8f0"
    txt_hi     = "#f0f6ff"  if d else "#0f172a"
    txt_dim    = "#7a8fa6"  if d else "#64748b"
    buy_bg     = "rgba(0,230,118,.12)"   if d else "rgba(21,128,61,.10)"
    buy_col    = "#00e676"  if d else "#15803d"
    buy_bdr    = "rgba(0,230,118,.3)"    if d else "rgba(21,128,61,.25)"
    stp_bg     = "rgba(255,51,102,.10)"  if d else "rgba(185,28,28,.08)"
    stp_col    = "#ff3366"  if d else "#b91c1c"
    stp_bdr    = "rgba(255,51,102,.3)"   if d else "rgba(185,28,28,.25)"

    if not ticker:
        ph_bg  = "#0c1018" if d else "#f8fafc"
        ph_col = "#3d4f63" if d else "#94a3b8"
        components.html(
            f'<div style="height:{height}px;display:flex;align-items:center;'
            f'justify-content:center;background:{ph_bg};border-radius:8px;">'
            f'<div style="text-align:center;">'
            f'<div style="font-size:40px;opacity:.18;">📈</div>'
            f'<div style="font-size:14px;color:{ph_col};margin-top:14px;'
            f'font-family:Inter,sans-serif;letter-spacing:.5px;">'
            f'Select a position to view chart</div></div></div>',
            height=height + 4,
        )
        return

    buy_badge = (
        f'<span style="background:{buy_bg};color:{buy_col};border:1px solid {buy_bdr};'
        f'padding:4px 12px;border-radius:5px;font-size:12px;font-weight:600;">'
        f'● BUY &nbsp;{buy_px:.2f}</span>'
        if buy_px else ""
    )
    stop_badge = (
        f'<span style="background:{stp_bg};color:{stp_col};border:1px solid {stp_bdr};'
        f'padding:4px 12px;border-radius:5px;font-size:12px;font-weight:600;">'
        f'● STOP &nbsp;{stop_px:.2f}</span>'
        if stop_px else ""
    )

    html = f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;700&family=JetBrains+Mono:wght@400;600&family=Syne:wght@800&display=swap" rel="stylesheet">
<div style="font-family:'JetBrains Mono',monospace;font-size:13px;
  padding:10px 16px 9px;background:{bg};display:flex;align-items:center;gap:12px;
  border-bottom:1px solid {hdr_bdr};">
  <span style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;
    color:{txt_hi};">{ticker}</span>
  {buy_badge}
  {stop_badge}
  <span style="margin-left:auto;font-size:11px;color:{txt_dim};font-family:'Inter',sans-serif;">
    Daily &nbsp;·&nbsp;
    <span style="color:#1565C0;font-size:14px;">━</span> SMA 50 &nbsp;·&nbsp;
    <span style="color:{sma200_col};font-size:14px;">━</span> SMA 200 &nbsp;·&nbsp;
    <span style="color:rgba(30,144,255,.85);">▲</span> Dodger Blue &nbsp;·&nbsp;
    <span style="color:rgba(255,0,255,.85);">▼</span> Magenta
  </span>
</div>
<div id="tvc" style="width:100%;height:{height - 44}px;"></div>
<script src="https://s3.tradingview.com/tv.js"></script>
<script>
new TradingView.widget({{
  container_id:"tvc", autosize:true,
  symbol:"{ticker}", interval:"D", timezone:"Etc/UTC",
  theme:"{tv_theme}", style:"1", locale:"en",
  enable_publishing:false, allow_symbol_change:false,
  hide_side_toolbar:false, withdateranges:true, save_image:true,
  studies:[
    "Volume@tv-basicstudies",
    {{id:"MASimple@tv-basicstudies",inputs:{{length:50}}}},
    {{id:"MAExp@tv-basicstudies",inputs:{{length:200}}}}
  ],
  overrides:{{
    "mainSeriesProperties.candleStyle.upColor":         "rgba(30,144,255,0.6)",
    "mainSeriesProperties.candleStyle.downColor":       "rgba(255,0,255,0.6)",
    "mainSeriesProperties.candleStyle.borderUpColor":   "rgba(30,144,255,0.85)",
    "mainSeriesProperties.candleStyle.borderDownColor": "rgba(255,0,255,0.85)",
    "mainSeriesProperties.candleStyle.wickUpColor":     "rgba(30,144,255,0.70)",
    "mainSeriesProperties.candleStyle.wickDownColor":   "rgba(255,0,255,0.70)"
  }},
  studies_overrides:{{
    "moving average.plot.color":             "#1565C0",
    "moving average.plot.linewidth":         2,
    "exponential moving average.plot.color": "{sma200_col}",
    "exponential moving average.plot.linewidth": 1.5
  }}
}});
</script>"""
    components.html(html, height=height + 4)


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
            load_raw.clear()
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
        raw       = load_raw(url)
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

    # ── Auto-select first position if nothing yet chosen
    if positions and st.session_state.ticker is None:
        st.session_state.ticker  = positions[0]["Ticker"]
        st.session_state.buy_px  = positions[0]["Entry Px"]
        st.session_state.stop_px = positions[0]["Stop Px"]

    # ── MAIN SPLIT: table left, chart right
    left, right = st.columns([5, 6], gap="small")

    with left:
        st.markdown('<div style="padding:0 4px 0 18px;">', unsafe_allow_html=True)
        selected = render_table(positions, st.session_state.ticker)
        if selected:
            if selected["Ticker"] != st.session_state.ticker:
                st.session_state.ticker  = selected["Ticker"]
                st.session_state.buy_px  = selected["Entry Px"]
                st.session_state.stop_px = selected["Stop Px"]
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        render_chart(
            ticker  = st.session_state.ticker,
            buy_px  = st.session_state.buy_px,
            stop_px = st.session_state.stop_px,
            theme   = theme,
            height  = 700,
        )


main()
