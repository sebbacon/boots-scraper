import pandas as pd
import matplotlib.pyplot as plt
import yaml

product_data = {}
with open("config.yaml", "r") as file:
    data = yaml.safe_load(file)["vmps"]
    for d in data:
        product_data[d["snomed_code"]] = d["name"]


# Reading the CSV data
df = pd.read_csv("outputs/stock_levels_all.csv")


# Calculating the percentage of each stockLevel within each productId
percentages = (
    df.groupby("productId")["stockLevel"]
    .value_counts(normalize=True)
    .unstack(fill_value=0)
    * 100
)
# Mapping stockLevel to colors for the plot
color_map = {
    "G": "green",
    "A": [1, 0.75, 0],
    "R": "red",
}  # RGB for amber normalized to [0, 1]


# Iterating through each productId to generate a horizontal bar chart
for product_id, row in percentages.iterrows():
    plt.figure(figsize=(10, 1))  # Fixed width bar, height is arbitrary

    # Extracting the values and colors in the order G, A, R
    values = [row.get(level, 0) for level in ["G", "A", "R"]]
    colors = [color_map[level] for level in ["G", "A", "R"]]

    # Plotting the stacked bar chart
    plt.barh(
        str(product_id),
        values,
        color=colors,
        edgecolor="black",
        left=[0, sum(values[:1]), sum(values[:2])],
    )
    plt.xlim(0, 100)  # Ensure the bar extends from 0% to 100%
    plt.xticks([])  # Remove x-ticks as we will write values in text
    plt.yticks([])  # Remove y-ticks as there's only one bar per plot
    plt.tight_layout()

    # Filename incorporating the productId
    filename = f"outputs/product_{product_id}_stock_levels.png"
    plt.savefig(filename)
    plt.close()  # Close the figure to avoid displaying it inline


index_md = []

for product_id, row in percentages.iterrows():
    filename = f"outputs/product_{product_id}_stock_levels.png"
    name = product_data.get(str(product_id), product_id)
    green_percentage = int(row.get("G", 0))
    index_md.append(f"*{name}: {green_percentage}% green*")
    index_md.append(f"![bar chart](./{filename})")
    heatmap_path = f"./heatmap_{product_id}.png"
    index_md.append(f"([<img src='{heatmap_path}' width='200'>]({heatmap_path}))")

with open("outputs/index.md", "w") as f:
    f.write("\n".join(index_md))
