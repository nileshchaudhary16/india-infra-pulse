import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from nl_query import answer_query
from data_fetcher import load_infrastructure_data, LAST_UPDATED

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="India Infrastructure Pulse",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main-header {
    background: linear-gradient(135deg, #FF9933 0%, #f0f0f0 50%, #138808 100%);
    padding: 3px; border-radius: 14px; margin-bottom: 1.5rem;
}
.main-header-inner {
    background: #0f1117; border-radius: 12px;
    padding: 1.4rem 2rem; text-align: center;
}
.main-title {
    font-size: 2rem; font-weight: 700;
    background: linear-gradient(90deg, #FF9933 20%, #ffffff 50%, #138808 80%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0;
}
.main-subtitle { color: #9ca3af; font-size: 0.88rem; margin-top: 0.35rem; }

.kpi-card {
    background: #1c1f26; border: 1px solid #2d3748;
    border-radius: 12px; padding: 1.1rem 1.4rem;
}
.kpi-label {
    color: #9ca3af; font-size: 0.72rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.07em;
}
.kpi-value {
    color: #f9fafb; font-size: 1.7rem; font-weight: 700;
    line-height: 1.1; margin: 0.25rem 0 0.2rem;
}
.kpi-pos { color: #34d399; font-size: 0.78rem; }
.kpi-neg { color: #f87171; font-size: 0.78rem; }

.section-title {
    font-size: 1rem; font-weight: 600; color: #f3f4f6;
    padding-bottom: 0.4rem; border-bottom: 2px solid #FF9933;
    display: inline-block; margin-bottom: 1rem;
}
.answer-box {
    background: #0d1117; border-left: 4px solid #138808;
    border-radius: 8px; padding: 1rem 1.2rem;
    color: #d1fae5; font-size: 0.9rem;
    white-space: pre-wrap; margin-top: 0.8rem; line-height: 1.8;
}
.badge {
    background: #1a2035; border: 1px solid #2d3748;
    border-radius: 6px; padding: 0.25rem 0.75rem;
    color: #9ca3af; font-size: 0.72rem; display: inline-block;
}
div[data-testid="stSidebar"] { background: #0f1117; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_data():
    return load_infrastructure_data()

df = get_data()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header"><div class="main-header-inner">
  <p class="main-title">🇮🇳 India Infrastructure Pulse</p>
  <p class="main-subtitle">
    National Highways · PMGSY Rural Roads · State Infra Spend · AI Query Engine
  </p>
</div></div>
<span class="badge">📡 data.gov.in · NHAI · MoRTH</span>
&nbsp;<span class="badge">🕒 Updated: {LAST_UPDATED}</span><br><br>
""", unsafe_allow_html=True)

# ── Sidebar Filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Filters")
    st.markdown("---")

    regions = {
        "All India":  None,
        "🏔️ North":   ["Jammu & Kashmir", "Himachal Pradesh", "Punjab", "Haryana", "Uttarakhand", "Uttar Pradesh"],
        "🌊 South":   ["Andhra Pradesh", "Telangana", "Tamil Nadu", "Kerala", "Karnataka", "Goa"],
        "🌿 East":    ["West Bengal", "Odisha", "Bihar", "Jharkhand", "Assam", "Tripura",
                       "Meghalaya", "Manipur", "Nagaland", "Arunachal Pradesh", "Mizoram", "Sikkim"],
        "🏜️ West":    ["Gujarat", "Maharashtra", "Rajasthan"],
        "🌾 Central": ["Madhya Pradesh", "Chhattisgarh"],
    }

    region      = st.selectbox("Region", list(regions.keys()))
    metric      = st.selectbox("Map Metric", [
        "Completion Rate (%)", "NH Length (km)",
        "Budget Spent (Rs Cr)", "PMGSY Roads (km)", "Active Projects"
    ])
    min_comp    = st.slider("Min Completion %", 0, 100, 0)

    st.markdown("---")
    st.markdown("**Stack:** Streamlit · Plotly · Gemini 2.0 Flash · data.gov.in")

# Apply filters
fdf = df.copy()
if regions[region]:
    fdf = fdf[fdf["state"].isin(regions[region])]
fdf = fdf[fdf["completion_pct"] >= min_comp]

col_map = {
    "Completion Rate (%)": "completion_pct",
    "NH Length (km)":      "nh_length_km",
    "Budget Spent (Rs Cr)":"spend_crore",
    "PMGSY Roads (km)":    "pmgsy_km",
    "Active Projects":     "active_projects"
}
map_col = col_map[metric]

# ── KPI Row ────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-title">📊 National Overview</p>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
kpis = [
    (c1, "Total NH Length",  f"{df['nh_length_km'].sum():,.0f} km",       "↑ 3,842 km vs last year", True),
    (c2, "Completed FY25",   f"{df['km_completed_fy25'].sum():,.0f} km",  "↑ 18% vs FY24",           True),
    (c3, "Avg Completion",   f"{df['completion_pct'].mean():.1f}%",       "↑ 4.2% vs last year",     True),
    (c4, "Total Spend",      f"Rs {df['spend_crore'].sum()/100000:.2f}L Cr","↑ 12% utilisation",     True),
    (c5, "Active Projects",  f"{df['active_projects'].sum():,}",           "↓ 234 completed",         False),
]
for col, lbl, val, delta, pos in kpis:
    dcls = "kpi-pos" if pos else "kpi-neg"
    col.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{lbl}</div>'
        f'<div class="kpi-value">{val}</div>'
        f'<div class="{dcls}">{delta}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ India Map", "📊 State Analysis", "💰 Budget Tracker", "🤖 Ask AI"
])

GEOJSON = (
    "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112"
    "/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
)

# ── TAB 1: Choropleth Map ──────────────────────────────────────────────────────
with tab1:
    st.markdown('<p class="section-title">State-wise Heatmap</p>', unsafe_allow_html=True)

    cscales = {
        "Completion Rate (%)": "RdYlGn",
        "NH Length (km)":      "Blues",
        "Budget Spent (Rs Cr)":"Oranges",
        "PMGSY Roads (km)":    "Greens",
        "Active Projects":     "Purples"
    }

    fig_map = px.choropleth(
        fdf, geojson=GEOJSON, featureidkey="properties.ST_NM",
        locations="state", color=map_col,
        color_continuous_scale=cscales[metric],
        hover_name="state",
        hover_data={
            "completion_pct": ":.1f", "nh_length_km": ":,",
            "km_completed_fy25": ":,", "spend_crore": ":,", "active_projects": True
        },
        labels={
            "completion_pct": "Completion %", "nh_length_km": "NH km",
            "km_completed_fy25": "FY25 km", "spend_crore": "Spend Rs Cr",
            "active_projects": "Projects"
        },
        title=f"{metric} — State-wise"
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(
    margin={"r":0,"t":40,"l":0,"b":0}, height=580,
    paper_bgcolor="#0f1117", font_color="#f9fafb",
    coloraxis_colorbar=dict(
        tickfont=dict(color="#9ca3af"),
        title=dict(font=dict(color="#9ca3af"))   # ← Fixed
    )
)
    st.plotly_chart(fig_map, use_container_width=True)

    cl, cr = st.columns(2)
    with cl:
        st.markdown("#### 🏆 Top 5 States")
        t5 = fdf.nlargest(5, "completion_pct")[["state", "completion_pct", "km_completed_fy25"]]
        t5.columns = ["State", "Completion %", "FY25 km"]
        st.dataframe(t5.reset_index(drop=True), use_container_width=True, hide_index=True)
    with cr:
        st.markdown("#### ⚠️ Needs Attention")
        b5 = fdf.nsmallest(5, "completion_pct")[["state", "completion_pct", "active_projects"]]
        b5.columns = ["State", "Completion %", "Active Projects"]
        st.dataframe(b5.reset_index(drop=True), use_container_width=True, hide_index=True)

# ── TAB 2: State Analysis ──────────────────────────────────────────────────────
with tab2:
    st.markdown('<p class="section-title">Performance Deep-Dive</p>', unsafe_allow_html=True)

    ca, cb = st.columns([1.2, 1])

    with ca:
        fig_sc = px.scatter(
            fdf, x="nh_length_km", y="completion_pct",
            size="spend_crore", color="completion_pct",
            color_continuous_scale="RdYlGn", hover_name="state",
            labels={"nh_length_km": "NH Length (km)", "completion_pct": "Completion %"},
            title="NH Length vs Completion (bubble size = spend)",
            size_max=40
        )
        fig_sc.update_layout(
            paper_bgcolor="#0f1117", plot_bgcolor="#1c1f26",
            font_color="#f9fafb", height=400, showlegend=False,
            xaxis=dict(gridcolor="#2d3748"), yaxis=dict(gridcolor="#2d3748")
        )
        st.plotly_chart(fig_sc, use_container_width=True)

    with cb:
        top12 = fdf.nlargest(12, "completion_pct").sort_values("completion_pct")
        fig_bar = go.Figure(go.Bar(
            x=top12["completion_pct"], y=top12["state"], orientation="h",
            marker=dict(color=top12["completion_pct"], colorscale="RdYlGn", showscale=False),
            text=top12["completion_pct"].apply(lambda x: f"{x:.1f}%"),
            textposition="outside"
        ))
        fig_bar.update_layout(
            title="Top 12 by Completion %",
            paper_bgcolor="#0f1117", plot_bgcolor="#1c1f26",
            font_color="#f9fafb", height=400,
            xaxis=dict(range=[0, 110], gridcolor="#2d3748"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            margin=dict(l=0, r=50, t=40, b=0)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Trend chart
    trend = pd.DataFrame({
        "Year": ["FY20", "FY21", "FY22", "FY23", "FY24", "FY25"],
        "NH km Completed": [10457, 13327, 10457, 10993, 12349, 14000],
        "PMGSY km":        [19000, 17000, 14000, 17500, 21000, 22500]
    })
    fig_line = px.line(
        trend.melt("Year", var_name="Category", value_name="km"),
        x="Year", y="km", color="Category", markers=True,
        color_discrete_map={"NH km Completed": "#FF9933", "PMGSY km": "#138808"},
        title="National Highway & PMGSY Construction Trend FY20–FY25"
    )
    fig_line.update_layout(
        paper_bgcolor="#0f1117", plot_bgcolor="#1c1f26",
        font_color="#f9fafb", height=320,
        xaxis=dict(gridcolor="#2d3748"), yaxis=dict(gridcolor="#2d3748"),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    fig_line.update_traces(line_width=2.5, marker_size=8)
    st.plotly_chart(fig_line, use_container_width=True)

# ── TAB 3: Budget Tracker ──────────────────────────────────────────────────────
with tab3:
    st.markdown('<p class="section-title">Budget Allocation vs Actual Spend</p>', unsafe_allow_html=True)

    bdf = fdf.copy()
    bdf["util"] = (bdf["spend_crore"] / bdf["budget_crore"] * 100).round(1)
    bdf = bdf.sort_values("budget_crore", ascending=False).head(20)

    fig_bud = go.Figure()
    fig_bud.add_trace(go.Bar(
        name="Allocated (Rs Cr)", x=bdf["state"], y=bdf["budget_crore"],
        marker_color="#374151", opacity=0.8
    ))
    fig_bud.add_trace(go.Bar(
        name="Spent (Rs Cr)", x=bdf["state"], y=bdf["spend_crore"],
        marker=dict(
            color=bdf["util"],
            colorscale=[[0, "#ef4444"], [0.6, "#f59e0b"], [1, "#22c55e"]],
            showscale=True,
            colorbar=dict(title="Util %", len=0.6, tickfont=dict(color="#9ca3af"))
        ),
        text=bdf["util"].apply(lambda x: f"{x}%"),
        textposition="outside",
        textfont=dict(size=9, color="#d1d5db")
    ))
    fig_bud.update_layout(
        barmode="overlay", title="Budget Utilisation — Top 20 States",
        paper_bgcolor="#0f1117", plot_bgcolor="#1c1f26",
        font_color="#f9fafb", height=480,
        xaxis=dict(tickangle=-35, gridcolor="#2d3748"),
        yaxis=dict(gridcolor="#2d3748"),
        legend=dict(bgcolor="rgba(0,0,0,0)")
    )
    st.plotly_chart(fig_bud, use_container_width=True)

    st.markdown("#### 📋 Efficiency Ranking")
    eff = fdf[["state", "budget_crore", "spend_crore", "km_completed_fy25"]].copy()
    eff["Util %"]       = (eff["spend_crore"] / eff["budget_crore"] * 100).round(1)
    eff["Cost/km (Rs)"] = (eff["spend_crore"] / eff["km_completed_fy25"].replace(0, 1)).round(1)
    eff = eff.sort_values("Util %", ascending=False).reset_index(drop=True)
    eff.columns = ["State", "Allocated (Rs Cr)", "Spent (Rs Cr)", "FY25 km", "Util %", "Cost/km (Rs Cr)"]
    st.dataframe(eff, use_container_width=True, hide_index=True)

# ── TAB 4: Ask AI ──────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<p class="section-title">🤖 Natural Language Query Engine</p>', unsafe_allow_html=True)
    st.markdown(
        "Ask any question in plain English. "
        "Gemini reads the live dataset and answers with real numbers."
    )

    st.markdown("**💡 Example questions:**")
    examples = [
        "Which state has the fastest highway completion rate?",
        "Top 3 states by budget utilisation",
        "Which states have completion rate below 50%?",
        "Average cost per km across all states",
        "Compare Gujarat and Maharashtra",
        "States with high budget but low completion",
    ]
    cols = st.columns(3)
    selected = None
    for i, ex in enumerate(examples):
        if cols[i % 3].button(ex, key=f"ex{i}", use_container_width=True):
            selected = ex

    st.markdown("<br>", unsafe_allow_html=True)
    query = st.text_input(
        "Your question:",
        value=selected or "",
        placeholder="Which state has the highest highway completion rate?"
    )

    if st.button("🔍 Ask Gemini", type="primary") and query:
        with st.spinner("🧠 Gemini is analysing the data..."):
            answer, code_used = answer_query(query, df)
        st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)
        with st.expander("🔧 Generated Python code"):
            st.code(code_used, language="python")
        st.markdown("#### 📄 Full Dataset")
        st.dataframe(
            df.sort_values("completion_pct", ascending=False),
            use_container_width=True,
            hide_index=True
        )

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#6b7280;font-size:0.78rem">'
    '🇮🇳 India Infrastructure Pulse &nbsp;|&nbsp; '
    'Data: data.gov.in · NHAI · MoRTH Annual Report 2024–25 &nbsp;|&nbsp; '
    'Built with Streamlit + Gemini 2.0 Flash + Plotly'
    '</div>',
    unsafe_allow_html=True
)