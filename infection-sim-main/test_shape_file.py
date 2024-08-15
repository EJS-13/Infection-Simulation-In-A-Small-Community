import geopandas as gpd
import matplotlib.pyplot as plt

# # Load the shapefile into a GeoDataFrame
# shapefile_path = "files/shapefiles/Canmore_Land_Use_Districts.shp"
# gdf = gpd.read_file(shapefile_path)
#
# # Plot the shapefile
# gdf.plot()
#
# # Add title and show the plot
# plt.title("Shapefile Visualization")
# plt.show()


import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

# Load shapefile
shapefile_path = "files/shapefiles/Canmore_Land_Use_Districts.shp"
gdf = gpd.read_file(shapefile_path)

# Create a scatter plot for agent dots
agent_x = np.random.uniform(gdf.bounds.minx.min(), gdf.bounds.maxx.max(), 100)
agent_y = np.random.uniform(gdf.bounds.miny.min(), gdf.bounds.maxy.max(), 100)

# Plot the shapefile
ax = gdf.plot(figsize=(10, 10))
plt.scatter(agent_x, agent_y, color='red', label='Agents')  # Scatter plot for agent dots
plt.title("Shapefile Visualization with Agent Dots")
plt.legend()  # Show legend for agents
plt.show()



# import geopandas as gpd
#
# # Load the shapefile into a GeoDataFrame
# shapefile_path = "files/shapefiles/Canmore_Land_Use_Districts.shp"
# gdf = gpd.read_file(shapefile_path)
#
# # Print the first few rows of the GeoDataFrame to inspect the attribute table
# print("Attribute Table:")
# print(gdf.head())
#
# # Print the geometry column to inspect the geometries
# print("\nGeometry:")
# print(gdf.geometry)
#
# # Check the coordinate reference system (CRS) of the GeoDataFrame
# print("\nCoordinate Reference System:")
# print(gdf.crs)
#
# # Print the bounding box of the GeoDataFrame
# print("\nBounding Box:")
# print(gdf.total_bounds)
#
# # Plot the shapefile to visually inspect the geometries
# gdf.plot()