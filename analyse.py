import pandas as pd

from upsetplot import plot
from matplotlib import pyplot as plt
import yaml
import geopandas

with open("config.yaml", "r") as file:
    vmps = yaml.safe_load(file)["vmps"]

names_to_codes = {}
codes_to_names = {}
for vmp in vmps:
    names_to_codes[vmp["name"]] = vmp["snomed_code"]
    codes_to_names[vmp["snomed_code"]] = vmp["name"]


# Load the datasets
stores = pd.read_json("outputs/stores.json")
gdf = geopandas.GeoDataFrame(
    stores, geometry=geopandas.points_from_xy(stores.long, stores.lat), crs="EPSG:4326"
)
df = pd.read_csv("outputs/stock_levels_all.csv", dtype={"productId": str})

df["has_stock"] = df["stockLevel"].isin(["G", "A"])
df["product_name"] = df.productId.apply(lambda x: codes_to_names[x])

def investigate():
    utrogestan = df[df.productId == names_to_codes["Utrogestan 100mg"]]
    lisdex = df[(df.productId == names_to_codes["Lisedexamfetamine 20mg caps"]) | (df.productId == names_to_codes["Lisedexamfetamine 30mg caps"])]
    # * Which are the stores that do NOT have utrogestan and DO have lisdex?
    
    no_utrogestan_stores = utrogestan[utrogestan.has_stock == False].storeId
    lisdex_stores = lisdex[lisdex.has_stock == True].storeId
    asd = df.loc[list(set(no_utrogestan_stores).intersection(set(lisdex_stores)))]
    gdf[gdf.storeId.isin((asd.storeId.value_counts() > 1).index)]
    breakpoint()
    # plotting shows nothing interesting by location.
    
    s = 4
    # *  Which are the stores that DO have utrogestan and NONE of the others?
    # * There are about 50 which have BOTH lisdex but nothing else - who are they?
    
def time_dimension():
    df = pd.read_csv('outputs/timeseries.csv', parse_dates=['datetime'])
    df["product_name"] = df.productId.apply(lambda x: codes_to_names.get(str(x), "?"))

    df['availability'] = df['A'] + df['G']

    df.set_index('datetime', inplace=True)

    grouped = df.groupby('product_name').resample('D')['availability'].sum().reset_index()
    pivot_df = grouped.pivot(index='datetime', columns='product_name', values='availability')
    pivot_df.plot(kind='line', figsize=(10, 6))

    plt.title('Availability Over Time by product')
    plt.ylabel('Availability (%)')
    plt.xlabel('Date')

    plt.legend(title='product')
    plt.show()





def upsert_plot(with_stock=True):
    """Upsert plot to visualise co-occurence of products.

    The theory is that one of these might be useful as a denominator
    """

    # Initialize a DataFrame to capture whether each VMP is in stock in each store
    store_vmp_matrix = pd.DataFrame()

    # For each VMP, determine if it is in stock in each store and add this information to the matrix
    for vmp in vmps:
        df_vmp = df[df["productId"] == vmp["snomed_code"]]
        df_vmp = df_vmp[["storeId", "has_stock"]].drop_duplicates().set_index("storeId")
        if with_stock:
            store_vmp_matrix[vmp["name"]] = df_vmp["has_stock"]
        else:
            store_vmp_matrix[vmp["name"]] = ~df_vmp["has_stock"]

    if with_stock:
        # Fill NaN values with False, indicating no stock for stores not listed with a particular VMP
        store_vmp_matrix = store_vmp_matrix.fillna(False)
    else:
        store_vmp_matrix = store_vmp_matrix.fillna(True)
    
    # Generate a binary key for each row to summarize its VMP stock status
    store_vmp_matrix["combination_key"] = store_vmp_matrix.apply(
        lambda row: "".join(row.astype(int).astype(str)), axis=1
    )

    # Count the occurrences of each combination
    combination_counts = store_vmp_matrix["combination_key"].value_counts()

    # Define  VMP names in the same order as in combination keys
    vmp_categories = [vmp["name"] for vmp in vmps]

    # Convert the binary string index to a list of tuples representing the presence/absence of each VMP
    def binary_str_to_presence_tuple(binary_str):
        return tuple(bool(int(bit)) for bit in binary_str)

    # Create a new DataFrame to hold the expanded binary string information
    expanded_data = []

    for binary_str, count in combination_counts.items():
        presence_tuple = binary_str_to_presence_tuple(binary_str)
        expanded_data.append((*presence_tuple, count))

    # Create a DataFrame from the expanded data. This is human-readable
    df_expanded = pd.DataFrame(expanded_data, columns=[*vmp_categories, "count"])

    # Now, create the MultiIndex from the columns representing VMPs
    multi_index = pd.MultiIndex.from_frame(df_expanded[vmp_categories])

    # Create a new Series with this MultiIndex and the counts as values
    upset_data = pd.Series(df_expanded["count"].values, index=multi_index)
 
    # Plot using UpSet
    upset = plot(upset_data)
    if with_stock:
        plt.title("Overlap of Stores with Stock of Different VMPs")
    else:
        plt.title("Overlap of Stores without Stock of Different VMPs")
    plt.show()




#do_plot(with_stock=False)
#investigate()
time_dimension()