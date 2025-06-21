import pandas as pd
import random
from datetime import datetime
import os
from geopy.distance import geodesic
from utils.routing import generate_gps_route_with_nodes, simulate_gps_from_nodes, inject_off_route_anomaly


df_cities = pd.read_csv("turkey_cities.csv")

def get_valid_city_pair(min_distance_km=100):
    for _ in range(100):  
        sample = df_cities.sample(2).reset_index(drop=True)
        origin_coords = (sample.loc[0, "latitude"], sample.loc[0, "longitude"])
        destination_coords = (sample.loc[1, "latitude"], sample.loc[1, "longitude"])
        distance = geodesic(origin_coords, destination_coords).km
        if distance >= min_distance_km:
            return sample.loc[0, "city"], origin_coords, sample.loc[1, "city"], destination_coords
    return None  
#route counter
N = 20  

os.makedirs("dataset/normal_route", exist_ok=True)
os.makedirs("dataset/off_route", exist_ok=True)

for i in range(N):
    result = get_valid_city_pair(min_distance_km=100)
    if not result:
        print(f"[{i+1}] city pair nor found ")
        continue

    origin_name, origin_coords, dest_name, destination_coords = result
    print(f"[{i+1}] {origin_name} ➜ {dest_name}")

    try:
        
        G, route = generate_gps_route_with_nodes(origin_coords, destination_coords)
        start_time = datetime(2025, 6, 1, 8, 0, 0)

        
        df_normal = simulate_gps_from_nodes(G, route, start_time)
        filename_normal = f"dataset/normal_route/route_{i+1:03}.csv"
        df_normal.to_csv(filename_normal, index=False)

        
        new_route, anomaly_flags = inject_off_route_anomaly(
            G, route,
            anomaly_start_prob=0.1,
            min_length=5,
            max_length=50,
            max_anomalies=2
        )
        df_off = simulate_gps_from_nodes(G, new_route, start_time, anomaly_flags)
        filename_off = f"dataset/off_route/route_{i+1:03}.csv"
        df_off.to_csv(filename_off, index=False)

        print(f"✓ {filename_normal} ve {filename_off} created and saved")

    except Exception as e:
        print(f"[{i+1}]  Error: {e}")
