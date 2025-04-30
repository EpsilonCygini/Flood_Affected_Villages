import pandas as pd
import folium
import geopandas as gpd
from folium.plugins import HeatMap

# Load GeoJSON (district boundaries)
districts = gpd.read_file("Balrampur_V.geojson")

# Load Excel files
flood_10_15 = pd.read_excel("LIST OF (10-15 TIMES) FLOOD AFFETED SETTLEMENT VILLAGE 2009-2024.xlsx")
flood_3 = pd.read_excel("LIST OF 3 TIMES FLOOD AFFECTED SETTLEMENT DURING 2020-2024.xlsx")

# Standardize column names
flood_10_15.columns = flood_10_15.columns.str.strip().str.upper()
flood_3.columns = flood_3.columns.str.strip().str.upper()

# Convert DMS to decimal degrees
def dms_to_decimal(coord):
    import re
    match = re.match(r"(\d+)°\s*(\d+)'[\s]*(\d+(?:\.\d+)?)", str(coord).replace("’", "'").replace("″", '"').replace("′", "'"))
    if not match:
        return None
    d, m, s = map(float, match.groups())
    return d + m / 60 + s / 3600

def extract_lat_lon(df):
    df = df.dropna(subset=["LATITUDE", "LONGITUDE"]).copy()
    df["LAT_DEC"] = df["LATITUDE"].apply(lambda x: dms_to_decimal(x))
    df["LON_DEC"] = df["LONGITUDE"].apply(lambda x: dms_to_decimal(x))
    return df.dropna(subset=["LAT_DEC", "LON_DEC"])

flood_10_15 = extract_lat_lon(flood_10_15)
flood_3 = extract_lat_lon(flood_3)

# Create map
m = folium.Map(
    location=[26.8, 80.9],
    zoom_start=7,
    tiles=None
)

# Add Esri World Imagery (satellite view like Google Earth)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr='Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community',
    name='Esri Satellite',
    overlay=False,
    control=True
).add_to(m)


# Add district boundaries
folium.GeoJson(
    districts,
    name="villname",
    style_function=lambda feature: {
        "fillColor": "transparent",
        "color": "white",       # Boundary color changed to white
        "weight": 1.5,
        "fillOpacity": 0.1,
    },
    tooltip=folium.GeoJsonTooltip(fields=["villname"], aliases=["District:"])
).add_to(m)

# Add heatmap layers
heat_10_15 = [[row["LAT_DEC"], row["LON_DEC"]] for _, row in flood_10_15.iterrows()]
HeatMap(
    heat_10_15,
    name="Flooded 10-15 Times",
    radius=18,
    blur=15,
    max_zoom=13,
    gradient={0.2: 'orange', 0.4: 'red', 0.8: 'darkred'}
).add_to(m)
for _, row in flood_10_15.iterrows():
    folium.CircleMarker(
        location=[row["LAT_DEC"], row["LON_DEC"]],
        radius=4,
        color='darkred',
        fill=True,
        fill_color='darkred',
        fill_opacity=0.8,
        popup=f'{row.get("DISTRICT", "Unknown District")}, {row.get("SETTLEMENT/VILLAGE", "Village")}'
    ).add_to(m)

heat_3 = [[row["LAT_DEC"], row["LON_DEC"]] for _, row in flood_3.iterrows()]
HeatMap(
    heat_3,
    name="Flooded 3 Times",
    radius=18,
    blur=15,
    max_zoom=13,
    gradient={0.2: 'lightblue', 0.4: 'blue', 0.8: 'darkblue'}
).add_to(m)
for _, row in flood_3.iterrows():
    folium.CircleMarker(
        location=[row["LAT_DEC"], row["LON_DEC"]],
        radius=4,
        color='darkblue',
        fill=True,
        fill_color='darkblue',
        fill_opacity=0.8,
        popup=f'{row.get("DISTRICT", "Unknown District")}, {row.get("SETTLEMENT / VILLAGE", "Village")}'
    ).add_to(m)

# Add layer toggle
folium.LayerControl().add_to(m)

# Save output
m.save("flood_heatmap_with_districts.html")
