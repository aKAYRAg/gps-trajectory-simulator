from utils.routing import generate_gps_route_with_nodes, simulate_gps_from_nodes
from datetime import datetime
import os

if __name__ == "__main__":
    origin_coords = (40.3233635, 28.0000311)
    destination_coords = (40.825069, 29.9252826)
    start_time = datetime(2025, 6, 1, 8, 0, 0)

    G, route, nodes = generate_gps_route_with_nodes(origin_coords, destination_coords)
    df = simulate_gps_from_nodes(G, route, start_time)

    os.makedirs("dataset/normal_route", exist_ok=True)
    index = len(os.listdir("dataset/normal_route")) + 1
    filename = f"dataset/normal_route/route_{index:03}.csv"
    df.to_csv(filename, index=False)

    print(f"Normal rota dosyası oluşturuldu: {filename}")
