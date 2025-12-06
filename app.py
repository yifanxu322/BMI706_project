import altair as alt
import pandas as pd
import streamlit as st
import plotly.express as px
from vega_datasets import data


# GLOBAL CONFIG

st.set_page_config(
    page_title="WHO TB Analytics Dashboard",
    layout="wide"
)

#side bar
st.sidebar.title("Navigation")
section = st.sidebar.radio(
    "Go to task:",
    (
        "Task 1 – Incidence & Mortality Trends",
        "Task 2 – Incidence Reduction Map",
        "Task 3 – Treatment Coverage Dashboard",
        "Task 4 – Incidence vs RR-TB Trends",
        "Task 5 – TB/HIV Co-infection Surveillance",
    )
)


# TASK 1 – Incidence & Mortality Trends

@st.cache_data
def load_task1_data():
    return pd.read_csv("data/visual1.csv")


def show_task1():
    df = load_task1_data()

    st.title("Task 1 – Global and Regional TB Incidence and Mortality")
    st.subheader("Visual 1: Incidence and mortality trends with global comparison (2017–2023)")

    st.write(
        "This view compares **TB incidence** and **mortality** per 100,000 population "
        "between the selected WHO region and the global average, including 95% confidence intervals."
    )

    
    controls_col, _ = st.columns([2, 3])

    with controls_col:
        region_options = sorted([r for r in df["region"].unique() if r != "Global"])
        default_region = "Africa" if "Africa" in region_options else region_options[0]

        region = st.selectbox(
            "Select WHO region:",
            options=region_options,
            index=region_options.index(default_region),
        )

        measure_options = sorted(df["measure"].unique())  
        selected_measures = st.multiselect(
            "Measures to display:",
            options=measure_options,
            default=measure_options,
        )

        show_ci = st.checkbox(
            "Show 95% confidence interval bands",
            value=True,
        )
    
  

    # Filter & Plot
    plot_df = df[
        ((df["region"] == region) | (df["region"] == "Global"))
        & (df["measure"].isin(selected_measures))
    ].copy()

    plot_df["series"] = plot_df["level"] + " " + plot_df["measure"]

    if plot_df.empty:
        st.warning("No data available for this combination of region and measures.")
        return

    base = alt.Chart(plot_df).encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y("rate:Q", title="Rate per 100,000 population"),
        color=alt.Color("series:N", title="Series"),
        tooltip=[
            "year:O",
            "region:N",
            "level:N",
            "measure:N",
            "rate:Q",
            "ci_low:Q",
            "ci_high:Q",
        ],
    )

    lines = base.mark_line(point=True)

    if show_ci:
        bands = alt.Chart(plot_df).mark_area(opacity=0.2).encode(
            x="year:O",
            y="ci_low:Q",
            y2="ci_high:Q",
            color=alt.Color("series:N", legend=None),
        )
        chart = bands + lines
    else:
        chart = lines

    chart = chart.properties(
        width=900,
        height=380,
        title=f"TB incidence and mortality: {region} vs Global",
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    with st.expander("Show data used in this plot"):
        st.dataframe(
            plot_df.sort_values(["measure", "level", "year"])[
                ["year", "region", "level", "measure", "rate", "ci_low", "ci_high"]
            ]
        )






# TASK 2 – Incidence Reduction Map

@st.cache_data
def load_task2_map_data():
    df_raw = pd.read_csv("data/visual2.csv")

    region_map = {
        "AFR": "Africa",
        "AMR": "Americas",
        "EMR": "Eastern Mediterranean",
        "EUR": "Europe",
        "SEAR": "South-East Asia",
        "WPR": "Western Pacific",
    }

    df = df_raw.copy()
    df["g_whoregion"] = df["g_whoregion"].astype(str).str.strip()
    df["region"] = df["g_whoregion"].map(region_map)
    df = df[~df["region"].isna()].copy()

    df_sub = df[df["year"].isin([2017, 2023])].copy()
    df_sub = df_sub[["country", "iso3", "region", "year", "e_inc_100k"]]

    wide = df_sub.pivot_table(
        index=["country", "iso3", "region"],
        columns="year",
        values="e_inc_100k",
    ).reset_index()

    wide = wide.rename(columns={2017: "inc_2017", 2023: "inc_2023"})
    wide = wide[wide["inc_2017"].notna() & wide["inc_2023"].notna()]
    wide = wide[wide["inc_2017"] > 0]

    wide["reduction_pct"] = (wide["inc_2017"] - wide["inc_2023"]) / wide["inc_2017"] * 100
    wide["reduction_pct_capped"] = wide["reduction_pct"].clip(lower=-50, upper=100)

    return wide


def show_task2():
    map_df = load_task2_map_data()

    st.title("Task 2 – Reduction in TB Incidence (2017–2023)")
    st.subheader("Visual 2: Global choropleth of incidence reduction")

    st.write(
        "This choropleth highlights the **percentage reduction in TB incidence** between 2017 and 2023. "
        "Darker colors indicate stronger reductions. Use the region filter to focus on specific WHO regions."
    )

    region_filter = st.selectbox(
        "Filter by WHO region:",
        options=["All regions"] + sorted(map_df["region"].unique().tolist()),
        index=0,
    )

    map_plot_df = (
        map_df.copy()
        if region_filter == "All regions"
        else map_df[map_df["region"] == region_filter].copy()
    )

    fig = px.choropleth(
        map_plot_df,
        locations="iso3",
        color="reduction_pct_capped",
        hover_name="country",
        hover_data={
            "region": True,
            "inc_2017": ":.1f",
            "inc_2023": ":.1f",
            "reduction_pct": ":.1f",
            "iso3": False,
        },
        color_continuous_scale="YlOrRd",
        range_color=(0, 100),
        labels={"reduction_pct_capped": "% reduction (2017–2023)"},
    )

    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=False),
        margin=dict(l=0, r=0, t=40, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Show underlying data"):
        st.dataframe(
            map_plot_df[
                ["country", "region", "inc_2017", "inc_2023", "reduction_pct"]
            ].sort_values("reduction_pct", ascending=False)
        )



# TASK 3 – Treatment Coverage Dashboard

@st.cache_data
def load_tb_cov_data():
    return pd.read_csv("data/visual3.csv")


def show_task3():
    tb_cov_df = load_tb_cov_data()

    # Robust column detection
    def find_col(target: str) -> str:
        target = target.upper()
        for c in tb_cov_df.columns:
            if c.upper() == target:
                return c
        raise KeyError(target)

    year_col = find_col("YEAR")
    country_col = find_col("COUNTRY")
    value_col = find_col("VALUE")
    value_lo_col = find_col("VALUE_LO")
    value_hi_col = find_col("VALUE_HI")

    for c in [year_col, value_col, value_lo_col, value_hi_col]:
        tb_cov_df[c] = pd.to_numeric(tb_cov_df[c], errors="coerce")

    tb_cov_df = tb_cov_df.dropna(subset=[value_col])

    st.title("Task 3 – TB Treatment Coverage Dashboard")
    st.markdown(
    "This dashboard examines **TB treatment coverage trends** across countries and highlights **top performers in each year**. \
    It also compares coverage patterns between **developed and developing regions** to reveal global disparities.")

    #3.1
    st.subheader("Visual 3.1: Country trends and yearly Top 5 coverage")
    
    colA, colB = st.columns([1, 1])

    # A
    with colA:
        st.markdown("##### Panel A: Coverage over time")

        all_countries = sorted(tb_cov_df[country_col].unique().tolist())
        selected_countries = st.multiselect(
            "Select up to 8 countries:",
            options=all_countries,
            default=["Algeria"],
            max_selections=8,
            key="countries_multi",
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
                    color=alt.Color(
                        f"{country_col}:N", scale=alt.Scale(scheme="category10")
                    ),
                    tooltip=[
                        alt.Tooltip(f"{country_col}:N", title="Country"),
                        alt.Tooltip(f"{year_col}:O", title="Year"),
                        alt.Tooltip(
                            f"{value_col}:Q", title="Coverage (%)", format=".1f"
                        ),
                    ],
                )
            )

            panelA_chart = (band_multi + line_multi).properties(
                width=420,
                height=260,
            )

            st.altair_chart(panelA_chart, use_container_width=False)
 
    # B
    with colB:
        st.markdown("##### Panel B: Top 5 in selected year")

        year_min = int(tb_cov_df[year_col].min())
        year_max = int(tb_cov_df[year_col].max())

        selected_year = st.slider(
            "Select year:",
            min_value=year_min,
            max_value=year_max,
            value=year_max,
            step=1,
            key="year_top5",
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
            .properties(width=420, height=260)
        )

        st.altair_chart(top5_chart, use_container_width=False)

    #3.2
    st.markdown("---")
    st.subheader("Visual 3.2: Compact coverage comparison by development status")

    developed_set = {
        "Australia",
        "Austria",
        "Belgium",
        "Canada",
        "Denmark",
        "Finland",
        "France",
        "Germany",
        "Iceland",
        "Ireland",
        "Israel",
        "Italy",
        "Japan",
        "Luxembourg",
        "Netherlands (Kingdom of the)",
        "New Zealand",
        "Norway",
        "Portugal",
        "Singapore",
        "Spain",
        "Sweden",
        "Switzerland",
        "United Kingdom of Great Britain and Northern Ireland",
        "United States of America",
        "Republic of Korea",
        "Cyprus",
        "Czechia",
        "Estonia",
        "Greece",
        "Hungary",
        "Latvia",
        "Lithuania",
        "Poland",
        "Slovakia",
        "Slovenia",
        "Malta",
    }

    tb_cov_df["DEV_STATUS"] = tb_cov_df[country_col].apply(
        lambda x: "Developed" if x in developed_set else "Developing"
    )

    mean_df = (
        tb_cov_df.groupby([country_col, "DEV_STATUS"], as_index=False)[value_col]
        .mean()
        .rename(columns={value_col: "MEAN_COV"})
    )
    tb_cov_df = tb_cov_df.merge(mean_df, on=[country_col, "DEV_STATUS"], how="left")

    devN = len(mean_df[mean_df["DEV_STATUS"] == "Developed"])
    worstDeveloping = (
        mean_df[mean_df["DEV_STATUS"] == "Developing"]
        .sort_values("MEAN_COV", ascending=True)
        .head(devN)[country_col]
        .tolist()
    )

    def compact(data, title):
        return (
            alt.Chart(data)
            .mark_rect()
            .encode(
                x=alt.X(f"{year_col}:O", title=""),
                y=alt.Y(
                    f"{country_col}:N",
                    axis=None,
                    sort=alt.SortField("MEAN_COV", order="descending"),
                ),
                color=alt.Color(
                    f"{value_col}:Q",
                    title="Coverage (%)",
                    scale=alt.Scale(domain=[0, 100], scheme="blues"),
                ),
                tooltip=[
                    alt.Tooltip(f"{country_col}:N", title="Country"),
                    alt.Tooltip(f"{year_col}:O", title="Year"),
                    alt.Tooltip(
                        f"{value_col}:Q", format=".1f", title="Coverage (%)"
                    ),
                ],
            )
            .properties(width=150, height=alt.Step(9), title=title)
        )

    heat_dev = compact(
        tb_cov_df[tb_cov_df["DEV_STATUS"] == "Developed"], "Developed countries"
    )

    heat_developing = compact(
        tb_cov_df[
            (tb_cov_df["DEV_STATUS"] == "Developing")
            & (tb_cov_df[country_col].isin(worstDeveloping))
        ],
        "Developing (lowest) countries",
    )

    center = st.columns([1, 3, 1])[1]
    with center:
        st.altair_chart(
            alt.hconcat(heat_dev, heat_developing).resolve_scale(color="shared"),
            use_container_width=False,
        )



# TASK 4 – Incidence vs RR-TB Trends

DATA_FILES_TASK4 = {
    "Global": {
        "incidence": "data/visual4/GTB_report_2025_incidence.csv",
        "rr": "data/visual4/GTB_report_2025_RR_prevalence.csv",
    },
    "WHO African Region": {
        "incidence": "data/visual4/African_region_report_2025_incidence.csv",
        "rr": "data/visual4/African_region_report_2025_RR_prevalence.csv",
    },
    "WHO/PAHO Region of the Americas": {
        "incidence": "data/visual4/Region_of_the_Americas_report_2025_incidence.csv",
        "rr": "data/visual4/Region_of_the_Americas_report_2025_RR_prevalence.csv",
    },
    "WHO Eastern Mediterranean Region": {
        "incidence": "data/visual4/Eastern_Mediterranean_region_report_2025_incidence.csv",
        "rr": "data/visual4/Eastern_Mediterranean_region_report_2025_RR_prevalence.csv",
    },
    "WHO European Region": {
        "incidence": "data/visual4/European_region_report_2025_incidence.csv",
        "rr": "data/visual4/European_region_report_2025_RR_prevalence.csv",
    },
    "WHO South-East Asia Region": {
        "incidence": "data/visual4/South_East_Asia_Region_report_2025_incidence.csv",
        "rr": "data/visual4/South_East_Asia_Region_report_2025_RR_prevalence.csv",
    },
    "WHO Western Pacific Region": {
        "incidence": "data/visual4/Western_Pacific_Region_report_2025_incidence.csv",
        "rr": "data/visual4/Western_Pacific_Region_report_2025_RR_prevalence.csv",
    },
}


@st.cache_data
def load_task4_data(region_key):
    files = DATA_FILES_TASK4.get(region_key)
    if not files:
        return pd.DataFrame()

    try:
        inc_df = pd.read_csv(files["incidence"])
        rr_df = pd.read_csv(files["rr"])

        if "Category" in inc_df.columns:
            inc_df = inc_df.rename(columns={"Category": "year"})

        inc_clean = inc_df.rename(
            columns={
                "Estimated TB incidence per 100 000 population": "tb_incidence",
                "Uncertainty interval (low)": "tb_incidence_low",
                "Uncertainty interval (high)": "tb_incidence_high",
            }
        )
        cols_to_keep = ["year", "tb_incidence", "tb_incidence_low", "tb_incidence_high"]
        inc_clean = inc_clean[[c for c in cols_to_keep if c in inc_clean.columns]]

        if "Category" in rr_df.columns:
            rr_df = rr_df.rename(columns={"Category": "year"})

        rr_clean = rr_df.rename(
            columns={
                "Previously treated pulmonary bacteriologically confirmed cases": "rr_prev_prevtx",
                "New pulmonary bacteriologically confirmed cases": "rr_prev_new",
            }
        )
        cols_to_keep_rr = ["year", "rr_prev_prevtx", "rr_prev_new"]
        rr_clean = rr_clean[[c for c in cols_to_keep_rr if c in rr_clean.columns]]

        if not inc_clean.empty and not rr_clean.empty:
            merged = pd.merge(inc_clean, rr_clean, on="year", how="inner")
            merged = merged[(merged["year"] >= 2017) & (merged["year"] <= 2023)]
            return merged
        else:
            return pd.DataFrame()

    except Exception:
        return pd.DataFrame()


def show_task4():
    st.title("Task 4 – TB Incidence and RR-TB Prevalence Trends")
    st.subheader("Visual 4: Incidence vs rifampicin-resistant TB (2017–2023)")

    st.write(
        "This visual compares **overall TB incidence** with **rifampicin-resistant (RR-TB) "
        "prevalence** among new and previously treated pulmonary cases within a selected WHO region."
    )

    region_options = list(DATA_FILES_TASK4.keys())
    selected_region = st.selectbox("Select WHO Region:", region_options)

    df = load_task4_data(selected_region)

    if df.empty:
        st.warning(f"Data not found for **{selected_region}**.")
        return

    COLOR_INCIDENCE = "#2ca02c"
    COLOR_CI = "#98df8a"
    COLOR_RR_PREV = "#ffbb78"
    COLOR_RR_NEW = "#ff7f0e"

    LABEL_INCIDENCE = "TB Incidence (per 100k)"
    LABEL_RR_PREV = "RR-TB: Previously treated cases (%)"
    LABEL_RR_NEW = "RR-TB: New cases (%)"

    base = alt.Chart(df).encode(x=alt.X("year:O", axis=alt.Axis(title="Year")))

    ci_band = base.mark_area(opacity=0.3, color=COLOR_CI).encode(
        y=alt.Y("tb_incidence_low:Q"),
        y2=alt.Y2("tb_incidence_high:Q"),
        tooltip=[
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("tb_incidence_low:Q", title="Incidence CI low"),
            alt.Tooltip("tb_incidence_high:Q", title="Incidence CI high"),
        ],
    )

    lines_base = (
        base.transform_fold(
            ["tb_incidence", "rr_prev_prevtx", "rr_prev_new"],
            as_=["Indicator_Code", "Value"],
        )
        .transform_calculate(
            Legend_Label="datum.Indicator_Code == 'tb_incidence' ? '"
            + LABEL_INCIDENCE
            + "' : datum.Indicator_Code == 'rr_prev_prevtx' ? '"
            + LABEL_RR_PREV
            + "' : '"
            + LABEL_RR_NEW
            + "'"
        )
    )

    lines = lines_base.mark_line(point=True, strokeWidth=3).encode(
        y=alt.Y("Value:Q", axis=alt.Axis(title="Indicator value")),
        color=alt.Color(
            "Legend_Label:N",
            scale=alt.Scale(
                domain=[LABEL_INCIDENCE, LABEL_RR_PREV, LABEL_RR_NEW],
                range=[COLOR_INCIDENCE, COLOR_RR_PREV, COLOR_RR_NEW],
            ),
            legend=alt.Legend(title="Indicator", orient="right"),
        ),
        tooltip=[
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("Legend_Label:N", title="Type"),
            alt.Tooltip("Value:Q", title="Value", format=".1f"),
        ],
    )

    chart = alt.layer(ci_band, lines).properties(
        title=f"{selected_region}: Incidence and RR-TB trends (2017–2023)", height=420
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    st.caption(
        "Note: Incidence is a rate per 100,000 population; RR-TB values are percentages of pulmonary bacteriologically confirmed TB cases."
    )

    with st.expander("View source data"):
        st.dataframe(df)



# TASK 5 – TB/HIV Co-infection

@st.cache_data
def load_task5_data():
    df = pd.read_csv("data/visual5.csv")
    df["iso_numeric"] = pd.to_numeric(df["iso_numeric"], errors="coerce")
    df["data_year"] = pd.to_numeric(df["data_year"], errors="coerce").astype("Int64")
    return df


def make_dashboard_task5(df_mode: pd.DataFrame, mode: str):
    world_map = alt.topo_feature(data.world_110m.url, "countries")

    region_select = alt.selection_point(fields=["g_whoregion"], name="RegionSel")

    map_chart = (
        alt.Chart(world_map)
        .mark_geoshape(stroke="white", strokeWidth=0.5)
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(
                df_mode,
                key="iso_numeric",
                fields=["country", "g_whoregion", "prev", "data_year", "source_type"],
            ),
        )
        .encode(
            color=alt.condition(
                alt.datum.prev != None,
                alt.Color(
                    "prev:Q",
                    title=f"HIV/TB prevalence (%) — {mode}",
                    scale=alt.Scale(scheme="oranges"),
                ),
                alt.value("lightgray"),
            ),
            opacity=alt.condition(region_select, alt.value(1.0), alt.value(0.4)),
            tooltip=[
                alt.Tooltip("country:N", title="Country"),
                alt.Tooltip("g_whoregion:N", title="WHO region"),
                alt.Tooltip("prev:Q", title="Prevalence (%)", format=".1f"),
                alt.Tooltip("source_type:N", title="Source"),
                alt.Tooltip("data_year:N", title="Data year"),
            ],
        )
        .properties(
            width=650,
            height=350,
            title=f"HIV/TB co-infection prevalence by country ({mode})",
        )
        .project("equalEarth")
        .add_params(region_select)
    )

    box_chart = (
        alt.Chart(df_mode)
        .mark_boxplot(outliers=True)
        .encode(
            x=alt.X("g_whoregion:N", title="WHO region"),
            y=alt.Y("prev:Q", title="HIV/TB prevalence (%)"),
            color=alt.condition(
                region_select,
                alt.Color("g_whoregion:N", title="WHO region"),
                alt.value("lightgray"),
            ),
        )
        .properties(
            width=650,
            height=280,
            title=f"HIV/TB prevalence by WHO region ({mode})",
        )
    )

    return (map_chart & box_chart).resolve_scale(color="independent")


def show_task5():
    hiv_long = load_task5_data()

    st.title("Task 5 – Global TB/HIV Co-infection Surveillance")
    st.subheader("Visual 5: Country-level map and regional distribution")

    st.markdown(
        "This dashboard visualizes **HIV/TB co-infection prevalence** using WHO "
        "non-routine surveillance data. Use the selector below to switch between "
        "**Combined**, **Survey**, and **Sentinel** estimates."
    )

    mode = st.radio(
        "Select data source for prevalence estimates:",
        options=["Combined", "Survey", "Sentinel"],
        index=0,
        horizontal=True,
    )

    df_mode = hiv_long[hiv_long["mode"] == mode].copy()
    chart = make_dashboard_task5(df_mode, mode)
    st.altair_chart(chart, use_container_width=True)

    with st.expander("Show data summary for current mode"):
        st.write(
            f"Number of countries with data ({mode}): "
            f"{df_mode['iso_numeric'].nunique()}"
        )
        st.dataframe(
            df_mode[
                ["country", "g_whoregion", "prev", "data_year", "source_type"]
            ].sort_values("g_whoregion")
        )


#render
if section.startswith("Task 1"):
    show_task1()
elif section.startswith("Task 2"):
    show_task2()
elif section.startswith("Task 3"):
    show_task3()
elif section.startswith("Task 4"):
    show_task4()
else:
    show_task5()
