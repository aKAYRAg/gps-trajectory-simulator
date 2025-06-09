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
    return base_kmh / 3.6

def is_junction(G, node):
    return len(list(G.successors(node))) > 2

def haversine_distance(p1, p2):
    return geodesic(p1, p2).meters

def add_edge_travel_time(G, is_urban=True, ref_hour=8):
    for u, v, k, data in G.edges(keys=True, data=True):
        highway = data.get("highway", "primary")
        if isinstance(highway, list):
            highway = highway[0]

        speed = estimate_speed(highway, is_urban)
        speed *= traffic_modifier(ref_hour)
        length = data.get("length", 1)

        data["travel_time"] = length / speed

def generate_gps_route_with_nodes(origin_coords, destination_coords, start_time=None):
    BUFFER = 0.2
    north = max(origin_coords[0], destination_coords[0]) + BUFFER
    south = min(origin_coords[0], destination_coords[0]) - BUFFER
    east = max(origin_coords[1], destination_coords[1]) + BUFFER
    west = min(origin_coords[1], destination_coords[1]) - BUFFER

    bbox = (west, south, east, north)
    G = ox.graph_from_bbox(bbox, network_type="drive", simplify=True)
    add_edge_travel_time(G, is_urban=True)

    orig_node = ox.nearest_nodes(G, origin_coords[1], origin_coords[0])
    dest_node = ox.nearest_nodes(G, destination_coords[1], destination_coords[0])
    route = nx.shortest_path(G, orig_node, dest_node, weight="travel_time")
    nodes = ox.graph_to_gdfs(G, edges=False).loc[route]

    return G, route, nodes

def simulate_gps_from_nodes(G, route, start_time=None, anomaly_flags=None):
    current_time = start_time or datetime(2025, 6, 1, 8, 0, 0)
    gps_data = []

    for i in range(len(route) - 1):
        n1 = G.nodes[route[i]]
        n2 = G.nodes[route[i + 1]]

        coord1 = (n1['y'], n1['x'])
        coord2 = (n2['y'], n2['x'])
        segment_dist = haversine_distance(coord1, coord2)

        edge_data = G.get_edge_data(route[i], route[i + 1]) or G.get_edge_data(route[i + 1], route[i])
        if edge_data is None:
            print(f"[WARNING] Edge not found between {route[i]} and {route[i+1]}. Skipping segment.")
            continue

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
            "longitude": coord2[1],
            "anomaly_flag": anomaly_flags[i+1] if anomaly_flags is not None else "normal"
        })

    return pd.DataFrame(gps_data)

def inject_off_route_anomaly(G, route, deviation_distance=None, max_trials=10,
                                         anomaly_start_prob=1.0, min_length=3, max_length=6, max_anomalies=2):
    if deviation_distance is None:
        deviation_distance = max(0.004, max_length * 0.0015)

    new_route = []
    anomaly_flags = []
    anomalies_injected = 0
    i = 0
    route_len = len(route)

    while i < route_len - 1:
        new_route.append(route[i])
        anomaly_flags.append("normal")

        if anomalies_injected < max_anomalies and 2 <= i <= route_len - 6:
            if random.random() < anomaly_start_prob:
                anomaly_length = random.randint(min_length, max_length)
                neighbors = list(G.neighbors(route[i]))
                random.shuffle(neighbors)
                injected_this_round = False

                for neighbor in neighbors:
                    if neighbor not in route:
                        try:
                            raw_x = G.nodes[neighbor]['x']
                            raw_y = G.nodes[neighbor]['y']
                            x, y = float(raw_x), float(raw_y)

                            x_offset = random.uniform(-deviation_distance, deviation_distance)
                            y_offset = random.uniform(-deviation_distance, deviation_distance)

                            try:
                                far_node = ox.distance.nearest_nodes(G, x + x_offset, y + y_offset)
                            except Exception as e:
                                print(f"[WARNING] Could not find nearest node for offset: {e}")
                                continue

                            full_path = nx.shortest_path(G, neighbor, far_node, weight="length")
                            if len(full_path) < anomaly_length:
                                continue

                            path_length_m = get_path_length(G, full_path)
                            if path_length_m < anomaly_length * 30:
                                continue

                            start_idx = random.randint(0, len(full_path) - anomaly_length)
                            off_route_segment = full_path[start_idx : start_idx + anomaly_length]

                            if any(n in route for n in off_route_segment):
                                continue

                            remaining_route = route[i+1:]
                            nearest_node_on_route = None
                            shortest_dist = float('inf')

                            for rnode in remaining_route:
                                try:
                                    length = nx.shortest_path_length(G, off_route_segment[-1], rnode, weight='length')
                                    if length < shortest_dist:
                                        shortest_dist = length
                                        nearest_node_on_route = rnode
                                except:
                                    continue

                            if nearest_node_on_route is None:
                                continue

                            try:
                                connection_path = nx.shortest_path(G, route[i], off_route_segment[0], weight="length")
                            except Exception as e:
                                print(f"[WARNING] Connection path not found: {e}")
                                continue

                            try:
                                return_path = nx.shortest_path(G, off_route_segment[-1], nearest_node_on_route, weight='length')
                            except Exception as e:
                                print(f"[EXCEPTION] Return path error: {e}")
                                continue

                            # Connection path label
                            for idx, node in enumerate(connection_path[1:]):
                                if idx == 0:
                                    new_route.append(node)
                                    anomaly_flags.append("off_route_start")
                                else:
                                    new_route.append(node)
                                    anomaly_flags.append("off_route_continue")

                            # Off-route segment 
                            for node in off_route_segment:
                                new_route.append(node)
                                anomaly_flags.append("off_route_continue")

                            # Return path 
                            for node in return_path[1:]:
                                new_route.append(node)
                                anomaly_flags.append("off_route_return")

                            anomalies_injected += 1
                            injected_this_round = True
                            break
                        except Exception as e:
                            print(f"[EXCEPTION] During anomaly: {e}")
                            continue

                if injected_this_round:
                    i += 1
                    continue

        i += 1

    for j in range(i, route_len):
        new_route.append(route[j])
        anomaly_flags.append("normal")

    return new_route, anomaly_flags


def get_path_length(G, path):
    total_length = 0
    for u, v in zip(path[:-1], path[1:]):
        edge_data = G.get_edge_data(u, v) or G.get_edge_data(v, u)
        if edge_data:
            if isinstance(edge_data, dict):
                edge_info = list(edge_data.values())[0]
                total_length += edge_info.get("length", 0)
    return total_length
