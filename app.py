import altair as alt
import pandas as pd
import streamlit as st


st.title("Visual3.1: TB treatment coverage dashboard")


path = "data/visual3.csv"
tb_cov_df = pd.read_csv(path)


cols = tb_cov_df.columns

def find_col(target: str) -> str:
    return next(c for c in cols if c.upper() == target)

year_col     = find_col("YEAR")
country_col  = find_col("COUNTRY")
value_col    = find_col("VALUE")
value_lo_col = find_col("VALUE_LO")
value_hi_col = find_col("VALUE_HI")


for c in [year_col, value_col, value_lo_col, value_hi_col]:
    tb_cov_df[c] = pd.to_numeric(tb_cov_df[c], errors="coerce")

tb_cov_df = tb_cov_df.dropna(subset=[year_col, country_col, value_col])

#country drop down
country_list = sorted(tb_cov_df[country_col].unique().tolist())
selected_country = st.selectbox("Select Country:", options=country_list)

#up panel
cov_country = tb_cov_df[tb_cov_df[country_col] == selected_country]

band = alt.Chart(cov_country).mark_area(opacity=0.2).encode(
    x=alt.X(f"{year_col}:Q", title="Year"),
    y=alt.Y(f"{value_lo_col}:Q", title="Treatment coverage (%)"),
    y2=f"{value_hi_col}:Q"
)

line = alt.Chart(cov_country).mark_line(point=True).encode(
    x=f"{year_col}:Q",
    y=f"{value_col}:Q",
    tooltip=[
        alt.Tooltip(f"{year_col}:O", title="Year"),
        alt.Tooltip(f"{value_col}:Q", title="Coverage (%)", format=".1f"),
        alt.Tooltip(f"{value_lo_col}:Q", title="Lower bound", format=".1f"),
        alt.Tooltip(f"{value_hi_col}:Q", title="Upper bound", format=".1f")
    ]
)

top_chart = (band + line).properties(
    width=700,
    height=250,
    title=f"TB treatment coverage over time in {selected_country} (with uncertainty)"
)

st.altair_chart(top_chart, use_container_width=True)

#year slider
year_min = int(tb_cov_df[year_col].min())
year_max = int(tb_cov_df[year_col].max())

selected_year = st.slider(
    "Select Year:",
    min_value=year_min,
    max_value=year_max,
    value=year_max,
    step=1
)

#down panel
this_year = tb_cov_df[tb_cov_df[year_col] == selected_year].copy()
this_year["rank"] = this_year[value_col].rank(method="first", ascending=False)
top10_year = this_year[this_year["rank"] <= 10]

bars = alt.Chart(top10_year).mark_bar().encode(
    x=alt.X(f"{value_col}:Q", title="Treatment coverage (%)"),
    y=alt.Y(f"{country_col}:N", sort="-x", title="Country"),
    color=alt.condition(
        f"datum.{country_col} == '{selected_country}'",
        alt.value("#d62728"),
        alt.value("#1f77b4")
    ),
    tooltip=[
        alt.Tooltip(f"{country_col}:N", title="Country"),
        alt.Tooltip(f"{value_col}:Q", title="Coverage (%)", format=".1f"),
    ]
).properties(
    width=700,
    height=280,
    title=f"Top 10 countries by TB treatment coverage in {selected_year}"
)

st.altair_chart(bars, use_container_width=True)
