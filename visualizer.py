import pandas as pd
import glob
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import base64
from io import BytesIO

file_location = "gps/*.txt"

files = glob.glob(file_location) # Combine all files
data_list = []

for file in files:
    df = pd.read_csv(
        file,
        header=None,
        names=["type", "line", "long", "lat", "ignore1", "ignore2", "tak", "ignore3", "ignore4", "destination"],
    )
    data_list.append(df)

data = pd.concat(data_list)

data['type'] = data['type'].astype(int)
data['long'] = data['long'] / 1e6  # Convert to decimal degrees
data['lat'] = data['lat'] / 1e6

data = data.dropna(subset=['long', 'lat']) # Drop rows with invalid coordinates

vehicle_types = {1: "Trolleybus", 2: "Bus", 3: "Tram", 7: "Nightbus"} # Vehicle types

# Create heatmaps for each vehicle type
for v_type, v_name in vehicle_types.items():
    # Filter data for the current vehicle type
    v_data = data[data['type'] == v_type]
    
    # Skip if no data for the vehicle type
    if v_data.empty:
        print(f"No data found for {v_name}. Skipping...")
        continue

    # Create the heatmap
    print(f"Creating heatmap for {v_name}...")
    map_center = [v_data['lat'].mean(), v_data['long'].mean()]
    heatmap_map = folium.Map(location=map_center, zoom_start=12)
    
    # Don't change these values.
    HeatMap(
        data=v_data[['lat', 'long']].values,
        radius=10,
        blur=15,
        min_opacity=1,
        max_zoom=15,
        gradient={0.2: 'blue', 0.4: 'green', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'},  # Gradient colors
    ).add_to(heatmap_map)
    
    # Generate destination graph
    dest_counts = v_data['destination'].value_counts()
    plt.figure(figsize=(6, 4))
    dest_counts.plot(kind='bar', color='red')
    plt.title(f"Destinations for {v_name}")
    plt.xlabel("Destination")
    plt.ylabel("Count")
    plt.tight_layout()
    
    # Save graph to a base64-encoded image
    img = BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    encoded_img = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()

    # Add the image to the map
    html = f'<img src="data:image/png;base64,{encoded_img}" style="width:400px;height:300px;">'
    popup = folium.Popup(html, max_width=500)
    folium.Marker(location=map_center, popup=popup).add_to(heatmap_map)
    
    # Save the heatmap
    heatmap_map.save(f"{v_name}_heatmap.html")
    print(f"{v_name} heatmap saved as {v_name}_heatmap.html.")
