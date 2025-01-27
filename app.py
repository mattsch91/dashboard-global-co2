import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from vega_datasets import data
import pycountry

# Load the data
dat = pd.read_csv("https://nyc3.digitaloceanspaces.com/owid-public/data/co2/owid-co2-data.csv")

legend = pd.read_csv("https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-codebook.csv")
feature_descriptions = dict(zip(legend["column"], legend["description"]))
                 
st.set_page_config(layout="wide")

# =======================================
# Define Sidebar filters
# =======================================

# define quantitative features
feature_options = [col for col in dat.columns if dat[col].dtype in [np.float64, np.int64] and col != "year"]

st.sidebar.header("Define features and parameters")
# function to display description over hover
def format_feature_with_description(feature):
    desc = feature_descriptions.get(feature, "No description available")
    return f"{feature} - {desc}"
# Feature selection
selected_feature = st.sidebar.selectbox(
    "Select Quantitative Feature:",
    options=feature_options,
    index=feature_options.index("co2_per_capita") if "co2_per_capita" in feature_options else 0,
    format_func = lambda x: format_feature_with_description(x)
)
# Year selection
selected_year = st.sidebar.slider(
    "Select Year:",
    min_value=int(dat["year"].min()),
    max_value=int(dat["year"].max()),
    value=2022,
)
# Country selection
selected_countries = st.sidebar.multiselect(
    "Select Countries for Line Chart:",
    options=dat["country"].unique(),
    default=["China", "United Kingdom", "Germany", "Japan", "United States"]
)
# Slider for year range
year_range = st.sidebar.slider(
    "Select Year Range:",
    min_value=int(dat["year"].min()),
    max_value=int(dat["year"].max()),
    value=(1945, 2023)
)
# Feature selection for scatter plot X-axis
selected_feature_scatter_x = st.sidebar.selectbox(
    "Select Feature for Scatter Plot (X-axis):",
    options=feature_options,
    index=feature_options.index("energy_per_gdp") if "energy_per_gdp" in feature_options else 0,
    format_func = lambda x: format_feature_with_description(x)
)
# Feature selection size
selected_feature_scatter_size = st.sidebar.selectbox(
    "Select Feature for Scatter Plot (point size):",
    options=feature_options,
    index=feature_options.index("population") if "population" in feature_options else 0,
    format_func = lambda x: format_feature_with_description(x)
)
scatter_type = st.sidebar.selectbox(
    "Choose Axis Scale for Scatter Plot:",
    options = ["linear", "log"], index = 0)

# ========================================
# Filter data
# ========================================
dat_map = dat[dat["year"] == selected_year].copy()
# Helper function to get ISO code
def get_iso_code(country_name):
    try:
        return int(pycountry.countries.lookup(country_name).numeric)
    except LookupError:
        return None

dat_map["country_id"] = dat_map['iso_code'].apply(get_iso_code)
dat_line = dat[(dat["country"].isin(selected_countries)) & (dat["year"].between(year_range[0], year_range[1]))]
dat_scatter = dat[dat["year"] == selected_year].copy()
dat_scatter = dat_scatter[dat_scatter["country"] != "World"]

# ========================================
# Plot data
# ========================================

# ========================================
# Map Chart
# ========================================
# Sample countries data (GeoJSON format)
countries = alt.topo_feature(data.world_110m.url, 'countries')

map_chart = alt.Chart(countries).mark_geoshape().encode(
    color=alt.Color(selected_feature, title=selected_feature.replace('_', ' ').title(), type = 'quantitative'),
    tooltip=['country:N', alt.Tooltip(selected_feature, type = 'quantitative')]
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(dat_map, 'country_id', [selected_feature, 'country'])
).project(
    type='equirectangular'
).interactive()

st.subheader(f"World {selected_feature.replace('_', ' ').title()} in {selected_year} by Country")
st.altair_chart(map_chart, use_container_width=True)

# ========================================
# Line Chart
# ========================================
c1 = alt.Chart(dat_line).mark_line().encode(
    x="year",
    y=alt.Y(selected_feature, title=selected_feature.replace('_', ' ').title()),
    color="country",
    tooltip=["country", selected_feature, "year"]
).interactive()

# ========================================
# Scatter Plot
# ========================================
c2 = alt.Chart(dat_scatter).mark_circle().encode(
    x=alt.X(selected_feature_scatter_x, 
            scale = alt.Scale(type = scatter_type),
            title=selected_feature_scatter_x.replace('_', ' ').title()),
    y=alt.Y(selected_feature, 
            scale = alt.Scale(type = scatter_type),            
            title=selected_feature.replace('_', ' ').title()),
    size = selected_feature_scatter_size,
    tooltip = ["country", selected_feature_scatter_x, selected_feature, selected_feature_scatter_size]
).interactive()

# Create two columns for the side-by-side plots
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"{selected_feature.replace('_', ' ').title()} Over Time")
    st.altair_chart(c1, use_container_width=True)
    
with col2:
    st.subheader(f"{selected_feature.replace('_', ' ').title()} vs. {selected_feature_scatter_x.replace('_', ' ').title()} in {selected_year}")
    st.altair_chart(c2, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Created with [Streamlit](https://streamlit.io).")
st.markdown("""The [data](https://github.com/owid/co2-data) underlying this dashboard was obtained from 
            [Our World in Data](https://ourworldindata.org/co2-and-greenhouse-gas-emissions). """)     
