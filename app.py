import streamlit as st
import altair as alt
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.title('Mapping Education and Safety: Analyzing Chicago Public Schools and Police Beats')
st.text("by Dianne Park (yewonp3)")

st.subheader("Introduction")
st.write("""Understanding how education and safety intersect in urban environments is crucial for addressing the challenges that communities face. In this project, we analyze Chicago Public Schools (CPS) and police beat boundaries to provide insights into the distribution of educational institutions and public safety zones across Chicago. This analysis is especially useful for policymakers, educators, and families who wish to understand the geographical relationships between schools and safety infrastructure.
        Using data from publicly available datasets, including CPS School Locations and Chicago Police Beat Boundaries, we provide interactive visualizations to help users explore the spatial distribution of schools, identify areas with high school densities, and visualize police beat boundaries across the city.
        This tool is designed to be intuitive and informative for anyone—whether you are a community member seeking insights, a student studying data visualization, or an official looking to make data-driven decisions.""")

def load_data():
    df_policebeats = pd.read_csv("PoliceBeatDec2012.csv")
    df_school = pd.read_csv("CPS_School_Locations_SY1415.csv")
    
    gdf_police = gpd.GeoDataFrame(
        df_policebeats, geometry=gpd.GeoSeries.from_wkt(df_policebeats["the_geom"])
    ).set_crs(epsg=4326)
    
    gdf_school = gpd.GeoDataFrame(
        df_school, geometry=gpd.GeoSeries.from_wkt(df_school["the_geom"])
    ).set_crs(epsg=4326)
    
    return gdf_police, gdf_school

gdf_police, gdf_school = load_data()

st.subheader("Understanding the Datasets")
st.markdown("""
            1. Chicago Public Schools Dataset: This dataset includes detailed information about school locations, names, and types (e.g., charter, magnet, or neighborhood schools). Understanding where schools are concentrated can reveal educational opportunities and gaps in specific neighborhoods.
            2. Police Beats Dataset: Police beats are administrative boundaries used for organizing law enforcement operations. Each beat covers a specific region of Chicago, helping allocate police resources effectively.        
            """)
st.markdown("""
            Education and safety are interdependent pillars of community well-being. Schools rely on safe environments for children to learn and thrive, while police beats provide insights into how safety resources are allocated geographically. By visualizing these datasets together:
            - Policymakers can identify neighborhoods that may need additional resources.
            - Families can explore where schools are located relative to safety zones.
            - Researchers and students can analyze how infrastructure impacts communities.
            """)

# SCHOOL LOCATION DATASET VIZ
# sidebar - filtering school types
school_types = gdf_school["SCH_TYPE"].unique()
selected_types = st.sidebar.multiselect( "Select School Types to Display:", options=school_types, default=list(school_types))

# filter data based on selected school types
filtered_schools = gdf_school[gdf_school["SCH_TYPE"].isin(selected_types)].copy()

# school density by longitude and latitude bins
filtered_schools = filtered_schools.copy()
filtered_schools["Longitude"] = filtered_schools.geometry.x
filtered_schools["Latitude"] = filtered_schools.geometry.y
filtered_schools = filtered_schools.drop(columns=["geometry"], errors='ignore')


#heatmap
st.subheader("School Density Heatmap Analysis")
heatmap = (
    alt.Chart(filtered_schools)
    .mark_rect()
    .encode(
        alt.X("Longitude:Q", bin=alt.Bin(maxbins=30), title="Longitude"),
        alt.Y("Latitude:Q", bin=alt.Bin(maxbins=30), title="Latitude"),
        alt.Color("count()", scale=alt.Scale(scheme="viridis"), title="School Count"),
        tooltip=["count()"]
    )
    .properties(width=700, height=500)
)
st.altair_chart(heatmap, use_container_width=True)
st.write("The School Density Heatmap visually represents the distribution of Chicago Public Schools by dividing the city into geographic grid cells based on longitude and latitude. Each cell is colored using a gradient from light yellow to dark blue, where darker shades indicate higher concentrations of schools. This allows users to quickly identify areas with dense clusters of schools and regions with fewer educational facilities. By highlighting these patterns, the heatmap reveals potential disparities in school access, helping urban planners, policymakers, and families understand where additional resources or infrastructure may be needed.")

# POLICE BEATS BOUNDARY DATASET VIZ
st.subheader("Police Beat Sizes Bar Chart Analysis")

def load_police_data():
    df_policebeats = pd.read_csv("PoliceBeatDec2012.csv")
    
    gdf_police = gpd.GeoDataFrame(
        df_policebeats, geometry=gpd.GeoSeries.from_wkt(df_policebeats["the_geom"])
    ).set_crs(epsg=4326)

    gdf_police["Area (sq km)"] = gdf_police.geometry.to_crs(epsg=3857).area / 1e6
    gdf_police_clean = gdf_police.drop(columns=["geometry"]).copy()
    
    return gdf_police, gdf_police_clean

gdf_police, gdf_police_clean = load_police_data()

# Remove invalid geometries
valid_police = gdf_police[~gdf_police.geometry.is_empty & gdf_police.geometry.notnull()]
valid_schools = gdf_school[~gdf_school.geometry.is_empty & gdf_school.geometry.notnull()]

area_chart = (alt.Chart(gdf_police_clean)
    .mark_bar()
    .encode(
        x=alt.X("BEAT:N", title="Police Beat", sort="-y"),
        y=alt.Y("Area (sq km):Q", title="Area (sq km)"),
        tooltip=["BEAT:N", "Area (sq km):Q"]
    )
    .properties(width=700, height=500, title="Police Beats by Area (sq km)")
)
st.altair_chart(area_chart, use_container_width=True)
st.write("The Police Beat Sizes Bar Chart Analysis visually compares the spatial coverage of each police beat in Chicago, measured in square kilometers. Each bar represents a single police beat, with its length corresponding to the area size. The chart is sorted in descending order, making it easy to identify the largest and smallest beats at a glance. By highlighting differences in beat sizes, this visualization helps uncover potential disparities in resource allocation or geographical coverage, as larger beats may require more policing resources to manage effectively. Tooltips provide additional details, such as the beat ID and exact area size, allowing users to explore specific beats interactively.")


# interactive basemap plot
st.subheader("Chicago Schools and Police Beats Explorer")
layer_selection = st.sidebar.selectbox("Select Map Layer to Display:", ["School Locations", "Police Beats", "Both"])

def plot_map(layer_selection):

    m = folium.Map(location=[41.8781, -87.6298], zoom_start=11)
    
    if layer_selection in ["School Locations", "Both"]:
        for _, row in valid_schools.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=5,
                color='blue',
                fill=True,
                fill_opacity=0.7,
                popup=f"School: {row.get('SCHOOL_NM', 'Unknown')}"
            ).add_to(m)

    if layer_selection in ["Police Beats", "Both"]:
        folium.GeoJson(
            valid_police,
            style_function=lambda x: {'color': 'red', 'weight': 0.5, 'fillOpacity': 0.1},
            tooltip=folium.GeoJsonTooltip(fields=["BEAT"], aliases=["Police Beat:"])
        ).add_to(m)
        
    return m

map_result = plot_map(layer_selection)
st_folium(map_result, width=700, height=500)
st.write("The Chicago Schools and Police Beats Explorer allows users to explore the spatial relationships between Chicago Public Schools and police beat boundaries. School locations are represented as blue circles, with tooltips providing details such as the school name and type, while police beats are displayed as red boundary lines that outline the areas covered by law enforcement. Users can toggle between viewing schools, police beats, or both layers using the sidebar, providing flexibility to focus on specific data. This map helps visualize how schools are distributed across the city relative to safety zones, enabling users to identify clusters of schools within certain police beats or areas where educational and safety resources may be sparse.")

st.subheader("Citation for Datasets")
police_link = "https://data.cityofchicago.org/Public-Safety/Boundaries-Police-Beats-current-/aerh-rz74"
school_link = "https://data.cityofchicago.org/Education/Chicago-Public-Schools-School-Locations-SY1415/3fhj-xtn5"
st.write("Police Beats Boundary Dataset: [PoliceBeatDec2012.csv](%s)" % police_link)
st.write("School Location Dataset: [CPS_School_Locations_SY1415.csv](%s)" % school_link)
