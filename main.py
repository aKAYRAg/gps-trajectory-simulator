import osmnx as ox
import networkx as nx
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from datetime import datetime, timedelta
import random

SPEED_BY_HIGHWAY = {
    "motorway": 100,
    "trunk": 85,
    "primary": 70,
    "secondary": 55,
    "tertiary": 45,
    "residential": 30,
    "service": 20
}

def traffic_modifier(hour):
    if 7 <= hour <= 9 or 17 <= hour <= 19:
        return 0.7
    elif 0 <= hour <= 6:
        return 1.2
    else:
        return 1.0

def estimate_speed(highway, is_urban):
    base_kmh = SPEED_BY_HIGHWAY.get(highway, 50)
    if is_urban:
        base_kmh *= 0.8
    return base_kmh / 3.6  # m/s

def is_junction(G, node):
    return len(list(G.successors(node))) > 2

def haversine_distance(p1, p2):
    return geodesic(p1, p2).meters

def generate_gps_route(origin_coords, destination_coords, start_time=None):

    BUFFER = 0.5  # 11 km

    north = max(origin_coords[0], destination_coords[0]) + BUFFER
    south = min(origin_coords[0], destination_coords[0]) - BUFFER
    east = max(origin_coords[1], destination_coords[1]) + BUFFER
    west = min(origin_coords[1], destination_coords[1]) - BUFFER

    bbox = (west, south, east, north)
    G = ox.graph_from_bbox(bbox, network_type="drive")


    orig_node = ox.nearest_nodes(G, origin_coords[1], origin_coords[0])
    dest_node = ox.nearest_nodes(G, destination_coords[1], destination_coords[0])

    route = nx.shortest_path(G, orig_node, dest_node, weight="length")
    nodes = ox.graph_to_gdfs(G, edges=False).loc[route]

    gps_data = []
    current_time = start_time or datetime(2025, 6, 1, 8, 0, 0)

    for i in range(len(nodes) - 1):
        n1 = nodes.iloc[i]
        n2 = nodes.iloc[i + 1]

        coord1 = (n1.y, n1.x)
        coord2 = (n2.y, n2.x)
        segment_dist = haversine_distance(coord1, coord2)

        edge_data = G.get_edge_data(route[i], route[i + 1])

        edge_attrs = min(edge_data.values(), key=lambda d: d.get("length", float('inf')))
        highway = edge_attrs.get("highway", "primary")
        if isinstance(highway, list):
            highway = highway[0]


        is_urban = highway in ["residential", "service"]

        base_speed = estimate_speed(highway, is_urban)
        traffic_factor = traffic_modifier(current_time.hour)
        actual_speed = base_speed * traffic_factor

        duration = segment_dist / actual_speed

        if is_junction(G, route[i]):
            duration += random.uniform(3, 10)

        current_time += timedelta(seconds=duration)
        gps_data.append({
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "latitude": coord2[0],
            "longitude": coord2[1]
        })

    df = pd.DataFrame(gps_data)
    return df

def add_gps_noise(df, noise_radius=10):
    noisy_df = df.copy()
    for i in range(len(df)):
        angle = random.uniform(0, 2 * np.pi)
        offset = random.uniform(0, noise_radius)
        meters_per_deg_lat = 111111
        meters_per_deg_lon = 111111 * np.cos(np.radians(df.iloc[i].latitude))
        delta_lat = (offset / meters_per_deg_lat) * np.cos(angle)
        delta_lon = (offset / meters_per_deg_lon) * np.sin(angle)
        noisy_df.at[i, 'latitude'] += delta_lat
        noisy_df.at[i, 'longitude'] += delta_lon
    return noisy_df

if __name__ == "__main__":
    origin_coords = (40.3233635,28.0000311)      
    destination_coords = (40.825069,29.9252826) 

    df_ref = generate_gps_route(origin_coords, destination_coords)
    df_ref.to_csv("reference_route.csv", index=False)

    df_noisy = add_gps_noise(df_ref)
    df_noisy.to_csv("noisy_route.csv", index=False)

    print(" files created: reference_route.csv and noisy_route.csv")
