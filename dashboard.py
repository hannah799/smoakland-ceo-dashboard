import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smoakland CEO Dashboard",
    page_icon="🌿",
    layout="wide",
)

# ── Brand palette ─────────────────────────────────────────────────────────────
PURPLE = "#7B5EA7"
PURPLE_LIGHT = "#C8A4E8"
GOLD   = "#D4A017"
GOLD_LIGHT = "#F5D87E"
TEAL   = "#00897B"
TEAL_LIGHT = "#4DB6AC"
BLACK  = "#1A1A1A"
WHITE  = "#FFFFFF"
GRAY   = "#F5F5F5"
GRAY2  = "#E0E0E0"

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  /* Page background */
  .stApp {{ background-color: {WHITE}; }}
  [data-testid="stSidebar"] {{ background-color: {GRAY}; }}

  /* Remove default padding */
  .block-container {{ padding-top: 1.5rem; padding-bottom: 1rem; }}

  /* KPI card */
  .kpi-card {{
    background: {WHITE};
    border: 1.5px solid {GRAY2};
    border-radius: 10px;
    padding: 16px 18px 12px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  }}
  .kpi-label {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #666;
    margin-bottom: 4px;
  }}
  .kpi-value {{
    font-size: 28px;
    font-weight: 800;
    color: {BLACK};
    line-height: 1.1;
  }}
  .kpi-sub {{
    font-size: 12px;
    color: #888;
    margin-top: 3px;
  }}
  .kpi-pos {{ color: {TEAL}; }}
  .kpi-neg {{ color: #E02020; }}

  /* Section headers */
  .section-head {{
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: {PURPLE};
    border-left: 4px solid {GOLD};
    padding-left: 10px;
    margin: 18px 0 10px;
  }}

  /* Dashboard title */
  .dash-title {{
    font-size: 26px;
    font-weight: 900;
    color: {BLACK};
    letter-spacing: -0.5px;
  }}
  .dash-sub {{
    font-size: 13px;
    color: #777;
    margin-top: 2px;
  }}
</style>
""", unsafe_allow_html=True)

# ── Mock data generation ──────────────────────────────────────────────────────
@st.cache_data
def generate_data():
    rng = np.random.default_rng(42)
    start = date(2026, 1, 1)
    end   = date(2026, 5, 27)
    days  = (end - start).days + 1
    dates = [start + timedelta(d) for d in range(days)]

    # Seasonal + day-of-week trend
    trend = np.linspace(0.75, 1.0, days)
    dow   = np.array([(0.85 if d.weekday() < 4 else 1.2) for d in dates])

    # Deliveries: 20-55/day
    base_del = 35
    deliveries = np.clip(
        (base_del * trend * dow * rng.normal(1.0, 0.12, days)).astype(int), 10, 80
    )

    # AOV: $68-$110
    aov = rng.normal(84, 9, days).clip(60, 115)

    revenue = (deliveries * aov).round(2)

    # Web sessions: 300-900/day
    sessions = np.clip(
        (550 * trend * dow * rng.normal(1.0, 0.15, days)).astype(int), 150, 1200
    )

    # Abandon carts: 62-78%
    abandon_rate = rng.normal(0.69, 0.04, days).clip(0.55, 0.82)
    abandon_carts = (sessions * 0.28 * abandon_rate).astype(int)

    # Customer service chats: 4-22/day
    cs_chats = np.clip(
        (11 * trend * rng.normal(1.0, 0.25, days)).astype(int), 2, 30
    )

    # Google reviews: cumulative, 2-5 new/day
    new_reviews = rng.integers(1, 6, days)
    total_reviews = np.cumsum(new_reviews) + 380
    review_scores = rng.normal(4.62, 0.22, days).clip(1, 5)

    df = pd.DataFrame({
        "date":         dates,
        "deliveries":   deliveries,
        "aov":          aov,
        "revenue":      revenue,
        "sessions":     sessions,
        "abandon_carts": abandon_carts,
        "abandon_rate": abandon_rate,
        "cs_chats":     cs_chats,
        "new_reviews":  new_reviews,
        "total_reviews": total_reviews,
        "review_score": review_scores,
    })

    # Product sales (daily by product)
    products = [
        "Blue Dream Pre-Roll 1g",
        "Mango Kush Vape Cart",
        "OG Edible Gummies 100mg",
        "Gelato Flower 3.5g",
        "Purple Punch Concentrate",
        "Sour Diesel Pre-Roll 2pk",
        "Watermelon Zkittlez Vape",
        "CBN Sleep Tincture",
    ]
    prod_weights = np.array([0.22, 0.18, 0.17, 0.14, 0.10, 0.08, 0.07, 0.04])
    prod_rows = []
    for i, d in enumerate(dates):
        for j, p in enumerate(products):
            qty = int(deliveries[i] * prod_weights[j] * rng.normal(1.0, 0.18))
            qty = max(0, qty)
            prod_rows.append({"date": d, "product": p, "qty": qty})
    prod_df = pd.DataFrame(prod_rows)

    # City data
    cities = ["Oakland", "San Francisco", "Berkeley", "Sacramento", "San Jose", "Long Beach"]
    city_weights = np.array([0.32, 0.25, 0.17, 0.12, 0.09, 0.05])
    city_rows = []
    for i, d in enumerate(dates):
        for j, c in enumerate(cities):
            qty = int(deliveries[i] * city_weights[j] * rng.normal(1.0, 0.15))
            qty = max(0, qty)
            rev = qty * aov[i] * rng.normal(1.0, 0.05)
            city_rows.append({"date": d, "city": c, "deliveries": qty, "revenue": rev})
    city_df = pd.DataFrame(city_rows)

    # Traffic sources (daily)
    sources = ["Organic Search", "Direct", "Social Media", "Referral"]
    src_weights_base = np.array([0.40, 0.24, 0.21, 0.15])
    src_rows = []
    for i, d in enumerate(dates):
        w = src_weights_base * rng.normal(1.0, 0.05, 4)
        w = w / w.sum()
        for j, s in enumerate(sources):
            src_rows.append({"date": d, "source": s, "sessions": int(sessions[i] * w[j])})
    src_df = pd.DataFrame(src_rows)

    # Top search terms (static mock)
    search_terms = pd.DataFrame({
        "term":    ["delivery near me", "pre-rolls", "edibles", "vape carts", "dispensary oakland"],
        "searches": [2840, 1990, 1620, 1380, 1050],
    })

    return df, prod_df, city_df, src_df, search_terms


df_all, prod_all, city_all, src_all, search_terms = generate_data()

# ── Header ────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 11])
with col_title:
    st.markdown('<div class="dash-title">🌿 Smoakland</div>', unsafe_allow_html=True)
    st.markdown('<div class="dash-sub">CEO Dashboard &nbsp;·&nbsp; Mock Data</div>', unsafe_allow_html=True)

st.markdown("---")

# ── Date filter ───────────────────────────────────────────────────────────────
min_date = df_all["date"].min()
max_date = df_all["date"].max()

with st.sidebar:
    st.markdown("### Filters")
    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        d_start, d_end = date_range
    else:
        d_start, d_end = min_date, max_date

    st.markdown("---")
    selected_cities = st.multiselect(
        "Cities",
        options=city_all["city"].unique().tolist(),
        default=city_all["city"].unique().tolist(),
    )

# Filter data
df = df_all[(df_all["date"] >= d_start) & (df_all["date"] <= d_end)].copy()
prod_df = prod_all[(prod_all["date"] >= d_start) & (prod_all["date"] <= d_end)].copy()
city_df = city_all[
    (city_all["date"] >= d_start) & (city_all["date"] <= d_end) &
    (city_all["city"].isin(selected_cities if selected_cities else city_all["city"].unique()))
].copy()
src_df = src_all[(src_all["date"] >= d_start) & (src_all["date"] <= d_end)].copy()

# Filtered search terms (static — not date-dependent in mock)
n_days = max(1, (d_end - d_start).days + 1)
full_days = (max_date - min_date).days + 1
scale = n_days / full_days
search_scaled = search_terms.copy()
search_scaled["searches"] = (search_scaled["searches"] * scale).round(0).astype(int)

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_rev    = df["revenue"].sum()
total_del    = int(df["deliveries"].sum())
avg_aov      = df["revenue"].sum() / df["deliveries"].sum() if df["deliveries"].sum() > 0 else 0
avg_abandon  = df["abandon_rate"].mean() * 100
avg_g_score  = df["review_score"].mean()
total_reviews = int(df["new_reviews"].sum())
total_chats  = int(df["cs_chats"].sum())
total_sessions = int(df["sessions"].sum())

def kpi(col, label, value, sub=""):
    col.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-sub">{sub}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
kpi(k1, "Total Revenue",     f"${total_rev:,.0f}",     "YTD")
kpi(k2, "Total Deliveries",  f"{total_del:,}",         "orders delivered")
kpi(k3, "Avg Order Value",   f"${avg_aov:.2f}",        "per delivery")
kpi(k4, "Web Sessions",      f"{total_sessions:,}",    "total visits")
kpi(k5, "Abandon Cart Rate", f"{avg_abandon:.1f}%",    "avg rate")
kpi(k6, "Google Rating",     f"{avg_g_score:.2f} ★",   f"{total_reviews} new reviews")
kpi(k7, "CS Chats",          f"{total_chats:,}",       "support conversations")

st.markdown("<br>", unsafe_allow_html=True)

# ── Revenue & Deliveries over time ───────────────────────────────────────────
st.markdown('<div class="section-head">Revenue & Deliveries Over Time</div>', unsafe_allow_html=True)

fig_rev = go.Figure()
fig_rev.add_trace(go.Bar(
    x=df["date"], y=df["revenue"],
    name="Revenue ($)",
    marker_color=PURPLE_LIGHT,
    yaxis="y1",
))
fig_rev.add_trace(go.Scatter(
    x=df["date"], y=df["deliveries"].rolling(7, min_periods=1).mean(),
    name="Deliveries (7-day avg)",
    line=dict(color=GOLD, width=2.5),
    yaxis="y2",
))
fig_rev.update_layout(
    height=280,
    margin=dict(t=20, b=20, l=10, r=10),
    paper_bgcolor=WHITE, plot_bgcolor=WHITE,
    legend=dict(orientation="h", y=1.12, x=0),
    xaxis=dict(showgrid=False),
    yaxis=dict(title="Revenue ($)", showgrid=True, gridcolor=GRAY2,
               tickformat="$,.0f"),
    yaxis2=dict(title="Deliveries", overlaying="y", side="right",
                showgrid=False),
    hovermode="x unified",
)
st.plotly_chart(fig_rev, use_container_width=True)

# ── Top products + Cities ─────────────────────────────────────────────────────
col_prod, col_city = st.columns([1, 1])

with col_prod:
    st.markdown('<div class="section-head">Top 5 Best-Selling Products</div>', unsafe_allow_html=True)
    top5 = (
        prod_df.groupby("product")["qty"].sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )
    colors_prod = [PURPLE, PURPLE_LIGHT, TEAL, TEAL_LIGHT, GOLD]
    fig_prod = go.Figure(go.Bar(
        x=top5["qty"],
        y=top5["product"],
        orientation="h",
        marker_color=colors_prod[:len(top5)],
        text=top5["qty"].apply(lambda v: f"{v:,}"),
        textposition="outside",
        cliponaxis=False,
    ))
    fig_prod.update_layout(
        height=240,
        margin=dict(t=10, b=10, l=10, r=60),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(autorange="reversed", showgrid=False),
    )
    st.plotly_chart(fig_prod, use_container_width=True)

with col_city:
    st.markdown('<div class="section-head">Top Cities by Deliveries</div>', unsafe_allow_html=True)
    top_cities = (
        city_df.groupby("city")[["deliveries", "revenue"]].sum()
        .sort_values("deliveries", ascending=False)
        .head(3)
        .reset_index()
    )
    city_colors = [TEAL, PURPLE, GOLD]
    fig_city = go.Figure()
    for i, row in top_cities.iterrows():
        fig_city.add_trace(go.Bar(
            name=row["city"],
            x=[row["city"]],
            y=[row["deliveries"]],
            marker_color=city_colors[i % 3],
            text=f'{int(row["deliveries"]):,}',
            textposition="outside",
            cliponaxis=False,
        ))
    fig_city.update_layout(
        height=240,
        margin=dict(t=10, b=10, l=10, r=20),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        showlegend=False,
        yaxis=dict(showgrid=True, gridcolor=GRAY2),
        xaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig_city, use_container_width=True)

# ── Web traffic ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">Web Traffic</div>', unsafe_allow_html=True)
col_traffic, col_sources, col_search = st.columns([2, 1, 1])

with col_traffic:
    fig_traffic = go.Figure()
    fig_traffic.add_trace(go.Scatter(
        x=df["date"], y=df["sessions"].rolling(7, min_periods=1).mean(),
        name="Sessions (7-day avg)",
        fill="tozeroy",
        fillcolor=f"rgba(0,137,123,0.15)",
        line=dict(color=TEAL, width=2),
    ))
    fig_traffic.update_layout(
        height=220,
        margin=dict(t=10, b=20, l=10, r=10),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=GRAY2, title="Sessions"),
    )
    st.plotly_chart(fig_traffic, use_container_width=True)

with col_sources:
    st.markdown("**Top 3 Traffic Sources**")
    src_agg = (
        src_df.groupby("source")["sessions"].sum()
        .sort_values(ascending=False)
        .head(3)
        .reset_index()
    )
    fig_src = go.Figure(go.Pie(
        labels=src_agg["source"],
        values=src_agg["sessions"],
        hole=0.45,
        marker=dict(colors=[PURPLE, TEAL, GOLD]),
        textinfo="label+percent",
        textfont_size=11,
    ))
    fig_src.update_layout(
        height=220,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor=WHITE,
        showlegend=False,
    )
    st.plotly_chart(fig_src, use_container_width=True)

with col_search:
    st.markdown("**Top Search Terms**")
    st.dataframe(
        search_scaled.rename(columns={"term": "Term", "searches": "Searches"}),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Searches": st.column_config.NumberColumn(format="%d"),
        },
        height=220,
    )

# ── Abandon carts + Customer service + Google reviews ─────────────────────────
st.markdown('<div class="section-head">Operations & Customer Experience</div>', unsafe_allow_html=True)
col_ab, col_cs, col_gr = st.columns(3)

with col_ab:
    st.markdown("**Abandon Carts**")
    fig_ab = go.Figure(go.Bar(
        x=df["date"], y=df["abandon_carts"],
        marker_color=GOLD_LIGHT,
        name="Abandon Carts",
    ))
    fig_ab.add_trace(go.Scatter(
        x=df["date"], y=df["abandon_carts"].rolling(7, min_periods=1).mean(),
        line=dict(color=GOLD, width=2),
        name="7-day avg",
    ))
    fig_ab.update_layout(
        height=220,
        margin=dict(t=10, b=20, l=10, r=10),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=GRAY2),
    )
    st.plotly_chart(fig_ab, use_container_width=True)

with col_cs:
    st.markdown("**Customer Service Chats**")
    fig_cs = go.Figure(go.Bar(
        x=df["date"], y=df["cs_chats"],
        marker_color=PURPLE_LIGHT,
        name="CS Chats",
    ))
    fig_cs.add_trace(go.Scatter(
        x=df["date"], y=df["cs_chats"].rolling(7, min_periods=1).mean(),
        line=dict(color=PURPLE, width=2),
        name="7-day avg",
    ))
    fig_cs.update_layout(
        height=220,
        margin=dict(t=10, b=20, l=10, r=10),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=GRAY2),
    )
    st.plotly_chart(fig_cs, use_container_width=True)

with col_gr:
    st.markdown("**Google Reviews**")
    fig_gr = go.Figure()
    fig_gr.add_trace(go.Scatter(
        x=df["date"], y=df_all[
            (df_all["date"] >= d_start) & (df_all["date"] <= d_end)
        ]["total_reviews"],
        fill="tozeroy",
        fillcolor=f"rgba(212,160,23,0.15)",
        line=dict(color=GOLD, width=2),
        name="Total Reviews",
        yaxis="y1",
    ))
    fig_gr.add_trace(go.Scatter(
        x=df["date"], y=df["review_score"].rolling(14, min_periods=1).mean(),
        line=dict(color=TEAL, width=2, dash="dot"),
        name="Avg Score",
        yaxis="y2",
    ))
    fig_gr.update_layout(
        height=220,
        margin=dict(t=10, b=20, l=10, r=10),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        legend=dict(orientation="h", y=1.18, font_size=10),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=GRAY2, title="Total Reviews"),
        yaxis2=dict(overlaying="y", side="right", title="Score",
                    range=[4.0, 5.0], showgrid=False),
    )
    st.plotly_chart(fig_gr, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f'<div style="font-size:11px;color:#aaa;text-align:center;">Smoakland CEO Dashboard &nbsp;·&nbsp; '
    f'Mock data for demo purposes &nbsp;·&nbsp; '
    f'Showing {d_start.strftime("%b %d")} – {d_end.strftime("%b %d, %Y")}</div>',
    unsafe_allow_html=True,
)
