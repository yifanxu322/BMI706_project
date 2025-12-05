import altair as alt
import pandas as pd
import streamlit as st

### Visual3.2
st.set_page_config(layout="wide")


@st.cache_data
def load_tb_cov_data():
    return pd.read_csv("data/visual3.csv")

tb_cov_df = load_tb_cov_data()

# Detect correct columns
def find_col(target):
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

#3.1
st.title("Visual 3.1: TB Treatment Coverage Dashboard")

# Controls
colA, colB = st.columns(2)
with colA:
    selected_country = st.selectbox("Select Country:",
                                    sorted(tb_cov_df[country_col].unique()))
with colB:
    selected_year = st.slider("Select Year:",
                              int(tb_cov_df[year_col].min()),
                              int(tb_cov_df[year_col].max()),
                              int(tb_cov_df[year_col].max()),
                              step=1)

#panelA
cov_country = tb_cov_df[tb_cov_df[country_col] == selected_country]

band = alt.Chart(cov_country).mark_area(opacity=0.2).encode(
    x=alt.X(f"{year_col}:Q", title="Year"),
    y=alt.Y(f"{value_lo_col}:Q", title="Coverage (%)"),
    y2=f"{value_hi_col}:Q",
)

line = alt.Chart(cov_country).mark_line(point=True).encode(
    x=f"{year_col}:Q",
    y=f"{value_col}:Q",
    tooltip=[
        f"{year_col}:O",
        alt.Tooltip(f"{value_col}:Q", format=".1f"),
    ],
)

panelA = (band + line).properties(width=380, height=240,
        title=f"{selected_country}: Trend with CI")

# PanelB
this_year = tb_cov_df[tb_cov_df[year_col] == selected_year].copy()
this_year["rank"] = this_year[value_col].rank(method="first", ascending=False)
top10 = this_year[this_year["rank"] <= 10]

panelB = alt.Chart(top10).mark_circle(size=140).encode(
    x=alt.X(f"{value_col}:Q", title="Coverage (%)"),
    y=alt.Y(f"{country_col}:N", sort="-x", title=""),
    color=alt.condition(
        f"datum.{country_col} == '{selected_country}'",
        alt.value("#d62728"), alt.value("#1f77b4")
    ),
    tooltip=[f"{country_col}:N", alt.Tooltip(f"{value_col}:Q", format=".1f")]
).properties(width=380, height=240,
             title=f"Top 10 countries in {selected_year}")

st.altair_chart(alt.hconcat(panelA, panelB), use_container_width=True)

#3.2
st.title("Visual 3.2: Compact TB Coverage Comparison")

# Developed list
developed_set = {
    "Australia","Austria","Belgium","Canada","Denmark","Finland","France","Germany",
    "Iceland","Ireland","Israel","Italy","Japan","Luxembourg",
    "Netherlands (Kingdom of the)","New Zealand","Norway","Portugal","Singapore",
    "Spain","Sweden","Switzerland",
    "United Kingdom of Great Britain and Northern Ireland",
    "United States of America","Republic of Korea","Cyprus","Czechia","Estonia",
    "Greece","Hungary","Latvia","Lithuania","Poland","Slovakia","Slovenia","Malta"
}

tb_cov_df["DEV_STATUS"] = tb_cov_df[country_col].apply(
    lambda x: "Developed" if x in developed_set else "Developing"
)

# Mean ordering
mean_df = (
    tb_cov_df.groupby([country_col, "DEV_STATUS"], as_index=False)[value_col]
    .mean().rename(columns={value_col: "MEAN_COV"})
)
tb_cov_df = tb_cov_df.merge(mean_df, on=[country_col, "DEV_STATUS"], how="left")


n_dev = len(mean_df[mean_df["DEV_STATUS"] == "Developed"])

# Select same number of developing
worst_developing = (
    mean_df[mean_df["DEV_STATUS"] == "Developing"]
    .sort_values("MEAN_COV", ascending=True)
    .head(n_dev)[country_col].tolist()
)
dev_subset_equal = tb_cov_df[(tb_cov_df["DEV_STATUS"] == "Developing") &
                             (tb_cov_df[country_col].isin(worst_developing))]


def compact_heatmap(data, title):
    return (
        alt.Chart(data)
        .mark_rect()
        .encode(
            x=alt.X(f"{year_col}:O", title="Year", axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{country_col}:N",
                    sort=alt.SortField("MEAN_COV", order="descending"),
                    axis=None  # <<<<<< REMOVE NAMES
            ),
            color=alt.Color(
                f"{value_col}:Q", title="Coverage (%)",
                scale=alt.Scale(domain=[0, 100], scheme="blues")
            ),
            tooltip=[
                alt.Tooltip(f"{country_col}:N", title="Country"),
                alt.Tooltip(f"{year_col}:O", title="Year"),
                alt.Tooltip(f"{value_col}:Q", format=".1f", title="Coverage (%)"),
            ],
        )
        .properties(
            width=240,         # << shrink width
            height=alt.Step(12),  # << tighten height (more compact rows)
            title=title,
        )
    )

heat_dev_chart = compact_heatmap(
    tb_cov_df[tb_cov_df["DEV_STATUS"] == "Developed"],
    f"{n_dev} Developed"
)

heat_dev_equal_chart = compact_heatmap(
    dev_subset_equal,
    f"{n_dev} Developing (Lowest Coverage)"
)

st.altair_chart(
    alt.hconcat(heat_dev_chart, heat_dev_equal_chart).resolve_scale(color="shared"),
    use_container_width=True
)
