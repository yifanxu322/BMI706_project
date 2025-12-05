import altair as alt
import pandas as pd
import streamlit as st

# ================================
# GLOBAL PAGE SETUP
# ================================
st.set_page_config(layout="wide")

# ================================
# LOAD DATA
# ================================
@st.cache_data
def load_tb_cov_data():
    return pd.read_csv("data/visual3.csv")

tb_cov_df = load_tb_cov_data()

# Detect correct columns (robust to case)
def find_col(target: str) -> str:
    target = target.upper()
    for c in tb_cov_df.columns:
        if c.upper() == target:
            return c
    raise KeyError(target)

year_col     = find_col("YEAR")
country_col  = find_col("COUNTRY")
value_col    = find_col("VALUE")
value_lo_col = find_col("VALUE_LO")
value_hi_col = find_col("VALUE_HI")

# Make numeric
for c in [year_col, value_col, value_lo_col, value_hi_col]:
    tb_cov_df[c] = pd.to_numeric(tb_cov_df[c], errors="coerce")

tb_cov_df = tb_cov_df.dropna(subset=[value_col])

# ============================================================
# VISUAL 3.1 — PANEL A + PANEL B (SIDE BY SIDE)
# ============================================================
st.title("Visual 3.1: TB Treatment Coverage Dashboard")

# ----------------- PANEL A: Multi-country trend -----------------
colA, colB = st.columns([1, 1])  # Side-by-side layout

with colA:
    st.subheader("Panel A: Coverage over time")

    all_countries = sorted(tb_cov_df[country_col].unique().tolist())
    selected_countries = st.multiselect(
        "Select up to 8 countries:",
        options=all_countries,
        default=["Algeria"],
        max_selections=8,
        key="countries_multi"
    )

    if len(selected_countries) == 0:
        st.warning("Please select at least one country.")
    else:
        selected_countries = selected_countries[:8]
        multi_df = tb_cov_df[tb_cov_df[country_col].isin(selected_countries)]

        band_multi = (
            alt.Chart(multi_df)
            .mark_area(opacity=0.18)
            .encode(
                x=alt.X(f"{year_col}:Q", title="Year"),
                y=alt.Y(f"{value_lo_col}:Q", title="Coverage (%)"),
                y2=f"{value_hi_col}:Q",
                color=alt.Color(f"{country_col}:N", legend=None),
            )
        )

        line_multi = (
            alt.Chart(multi_df)
            .mark_line(point=True, strokeWidth=2)
            .encode(
                x=f"{year_col}:Q",
                y=f"{value_col}:Q",
                color=alt.Color(f"{country_col}:N", scale=alt.Scale(scheme="category10")),
                tooltip=[
                    alt.Tooltip(f"{country_col}:N", title="Country"),
                    alt.Tooltip(f"{year_col}:O", title="Year"),
                    alt.Tooltip(f"{value_col}:Q", title="Coverage (%)", format=".1f"),
                ],
            )
        )

        panelA_chart = (band_multi + line_multi).properties(
            width=390,  # <-- SHRUNK WIDTH
            height=260,
        )

        st.altair_chart(panelA_chart, use_container_width=False)

# ----------------- PANEL B: Top 10 countries -----------------
with colB:
    st.subheader("Panel B: Top 10 in selected year")

    year_min = int(tb_cov_df[year_col].min())
    year_max = int(tb_cov_df[year_col].max())

    selected_year = st.slider(
        "Select year:",
        min_value=year_min,
        max_value=year_max,
        value=year_max,
        step=1,
        key="year_top5"
    )

    this_year = tb_cov_df[tb_cov_df[year_col] == selected_year].copy()
    this_year["rank"] = this_year[value_col].rank(method="first", ascending=False)
    top5 = this_year[this_year["rank"] <= 5]

    top5_chart = (
        alt.Chart(top5)
        .mark_bar()
        .encode(
            x=alt.X(f"{value_col}:Q", title="Coverage (%)"),
            y=alt.Y(f"{country_col}:N", sort="-x", title=""),
            tooltip=[
                alt.Tooltip(f"{country_col}:N"),
                alt.Tooltip(f"{value_col}:Q", title="Coverage (%)", format=".1f"),
            ],
            color=alt.value("#1f77b4"),
        )
        .properties(width=390, height=260)  
    )

    st.altair_chart(top5_chart, use_container_width=False)

# ========= Visual 3.2 below ===========
st.markdown("---")
st.title("Visual 3.2: Compact Coverage Comparison")

#  Developed 
developed_set = {
    "Australia","Austria","Belgium","Canada","Denmark","Finland","France","Germany","Iceland",
    "Ireland","Israel","Italy","Japan","Luxembourg","Netherlands (Kingdom of the)","New Zealand",
    "Norway","Portugal","Singapore","Spain","Sweden","Switzerland",
    "United Kingdom of Great Britain and Northern Ireland","United States of America",
    "Republic of Korea","Cyprus","Czechia","Estonia","Greece","Hungary","Latvia","Lithuania",
    "Poland","Slovakia","Slovenia","Malta",
}

tb_cov_df["DEV_STATUS"] = tb_cov_df[country_col].apply(
    lambda x: "Developed" if x in developed_set else "Developing"
)

# Ordering by mean
mean_df = (
    tb_cov_df.groupby([country_col, "DEV_STATUS"], as_index=False)[value_col]
    .mean()
    .rename(columns={value_col: "MEAN_COV"})
)

tb_cov_df = tb_cov_df.merge(mean_df, on=[country_col, "DEV_STATUS"], how="left")

# Equal number sample
devN = len(mean_df[mean_df["DEV_STATUS"] == "Developed"])
worstDeveloping = (
    mean_df[mean_df["DEV_STATUS"] == "Developing"]
    .sort_values("MEAN_COV", ascending=True)
    .head(devN)[country_col]
    .tolist()
)

compact = lambda data, title: (
    alt.Chart(data)
    .mark_rect()
    .encode(
        x=alt.X(f"{year_col}:O", title=""),
        y=alt.Y(f"{country_col}:N", axis=None, sort=alt.SortField("MEAN_COV", order="descending")),
        color=alt.Color(f"{value_col}:Q", title="", scale=alt.Scale(domain=[0, 100], scheme="blues")),
        tooltip=[
            alt.Tooltip(f"{country_col}:N", title="Country"),
            alt.Tooltip(f"{year_col}:O", title="Year"),
            alt.Tooltip(f"{value_col}:Q", format=".1f", title="Coverage (%)"),
        ],
    )
    .properties(width=140, height=alt.Step(9), title=title)
)

heat_dev = compact(
    tb_cov_df[tb_cov_df["DEV_STATUS"] == "Developed"],
    "Developed"
)

heat_developing = compact(
    tb_cov_df[(tb_cov_df["DEV_STATUS"] == "Developing") & (tb_cov_df[country_col].isin(worstDeveloping))],
    "Developing (lowest)"
)

center = st.columns([1, 3, 1])[1]
with center:
    st.altair_chart(alt.hconcat(heat_dev, heat_developing).resolve_scale(color="shared"), use_container_width=False)
