import csv
import json
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import shape, Point
import requests
from collections import defaultdict

# # Step 0: Download the JSON data from the OpenPrescribing API
pcn_api_url = "https://openprescribing.net/api/1.0/org_location/?org_type=pcn"
pcn_map_response = requests.get(pcn_api_url)
pcn_map_response.raise_for_status()
pcn_map_filename = "pcn_map.geojson"
with open(pcn_map_filename, "w") as file:
    file.write(pcn_map_response.text)
print("Downloaded pcn_map.json")

# Step 1: Load JSON to create a mapping of storeId to its lat and long
store_locations = {}
with open("outputs/stores.json") as json_file:
    stores = json.load(json_file)
    for store in stores:
        storeId = store["storeId"]
        lat = store["lat"]
        long = store["long"]
        store_locations[storeId] = (lat, long)

# Load GeoJSON and prepare for processing
with open("pcn_map.geojson") as f:
    geojson = json.load(f)

gdf_shapes = gpd.GeoDataFrame.from_features(geojson["features"])

# Initialize a dictionary to hold red counts for each (shape_code, productId)
red_counts = defaultdict(lambda: defaultdict(int))


# Step 2 & 3: Aggregate Red counts per shape_code and productId
with open("outputs/stock_levels_all.csv", newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        storeId = int(row["storeId"])
        productId = row["productId"]
        if storeId in store_locations and row["stockLevel"] == "R":
            lat, long = store_locations[storeId]
            point = Point(long, lat)
            for idx, shape_row in gdf_shapes.iterrows():
                if point.within(shape_row.geometry):
                    shape_code = shape_row["code"]
                    red_counts[shape_code][productId] += 1
                    break

# Get unique productIds
productIds = set(pid for counts in red_counts.values() for pid in counts)


# Set coordinate system
gdf_shapes.crs = "EPSG:4326"
gdf_shapes = gdf_shapes.to_crs("EPSG:27700")

# Step 4: Generate and save a heatmap for each productId
for productId in productIds:
    # Create a column for red_counts specific to this productId
    gdf_shapes[f"red_counts_{productId}"] = gdf_shapes["code"].apply(
        lambda x: red_counts[x][productId]
    )

    # Plotting
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    gdf_shapes.plot(
        column=f"red_counts_{productId}",
        ax=ax,
        legend=True,
        cmap="OrRd",
        edgecolor="black",
    )
    plt.title(f"Out-of-stock levels by PCN for VMP {productId}")

    # Save to file
    plt.savefig(f"outputs/heatmap_{productId}.png")
    plt.close(fig)
