from utils.routing import generate_gps_route_with_nodes, inject_off_route_anomaly, simulate_gps_from_nodes
from datetime import datetime
import os

if __name__ == "__main__":
    origin_coords = (40.731573, 31.563471)
    destination_coords = (39.967761, 32.630573)
    start_time = datetime(2025, 6, 1, 8, 0, 0)

    G, route = generate_gps_route_with_nodes(origin_coords, destination_coords)

    # Off-route anomaly parameters
    anomaly_start_prob = 0.1
    min_length = 5
    max_length = 50
    max_anomalies = 3

    new_route, anomaly_flags = inject_off_route_anomaly(
        G, route,
        anomaly_start_prob=anomaly_start_prob,
        min_length=min_length,
        max_length=max_length,
        max_anomalies=max_anomalies
    )

    df = simulate_gps_from_nodes(G, new_route, start_time, anomaly_flags)

    os.makedirs("dataset/off_route", exist_ok=True)
    index = len(os.listdir("dataset/off_route")) + 1
    filename = f"dataset/off_route/route_{index:03}.csv"
    df.to_csv(filename, index=False)

    print(f"Off-route anomaly route created and saved: {filename}")
