import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from vega_datasets import data
import pycountry

# Load the data
dat = pd.read_csv("https://nyc3.digitaloceanspaces.com/owid-public/data/co2/owid-co2-data.csv")


# =======================================
# Define Sidebar filters
# =======================================

# ========================================
# Line Chart
# ========================================
st.sidebar.header("Line Chart")
# Country selection
selected_countries = st.sidebar.multiselect(
    "Select Countries:",
    options=dat["country"].unique(),
    default=["Germany", "France", "Italy", "United Kingdom", "United States"]
)
# Feature selection
feature_options_line = [col for col in dat.columns if dat[col].dtype in [np.float64, np.int64]]
selected_feature_line = st.sidebar.selectbox(
    "Select Feature for Line Chart:",
    options=feature_options_line,
    index=feature_options_line.index("co2_per_capita") if "co2_per_capita" in feature_options_line else 0
)
# Slider for year range
year_range = st.sidebar.slider(
    "Select Year Range for Line Chart:",
    min_value=int(dat["year"].min()),
    max_value=int(dat["year"].max()),
    value=(2000, 2022)
)

# ========================================
# Map Chart
# ========================================
st.sidebar.header("Map Chart")
# Year selection
selected_year = st.sidebar.slider(
    "Select Year:",
    min_value=int(dat["year"].min()),
    max_value=int(dat["year"].max()),
    value=2022,
)
# Feature selection
feature_options_map = [col for col in dat.columns if dat[col].dtype in [np.float64, np.int64]]
selected_feature_map = st.sidebar.selectbox(
    "Select Feature for Map Chart:",
    options=feature_options_map,
    index=feature_options_map.index("co2_per_capita") if "co2_per_capita" in feature_options_map else 0
)

# ========================================
# Filter data
# ========================================
dat_filtered = dat[(dat["country"].isin(selected_countries)) & (dat["year"].between(year_range[0], year_range[1]))]
dat_year = dat[dat["year"] == selected_year].copy()

# Helper function to get ISO code
def get_iso_code(country_name):
    try:
        return int(pycountry.countries.lookup(country_name).numeric)
    except LookupError:
        return None

dat_year["country_id"] = dat_year['iso_code'].apply(get_iso_code)

# ========================================
# Plot data
# ========================================

# Line Chart
st.subheader(f"{selected_feature_line.replace('_', ' ').title()} Over Time")
c1 = alt.Chart(dat_filtered).mark_line().encode(
    x="year",
    y=alt.Y(selected_feature_line, title=selected_feature_line.replace('_', ' ').title()),
    color="country",
    tooltip=[selected_feature_line, "year"]
).interactive().properties(
    width=600, height=400
)
st.altair_chart(c1, use_container_width=True)

# Map Chart
st.subheader(f"World {selected_feature_map.replace('_', ' ').title()} in {selected_year} by Country")

# Sample countries data (GeoJSON format)
countries = alt.topo_feature(data.world_110m.url, 'countries')

map_chart = alt.Chart(countries).mark_geoshape().encode(
    color=alt.Color(selected_feature_map, title=selected_feature_map.replace('_', ' ').title(), type = 'quantitative'),
    tooltip=['country:N', alt.Tooltip(selected_feature_map, type = 'quantitative')]
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dat_year, 'country_id', [selected_feature_map, 'country'])
).properties(
    width=1000,
    height=500#,
    #title=f"World CO2 per Capita by Country in {selected_year}"
).project(
    type='equirectangular'
).interactive()

st.altair_chart(map_chart, use_container_width=True)



# Footer
st.markdown("---")
st.markdown(
    "Created with [Streamlit](https://streamlit.io)."
)
