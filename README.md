# 🚚 GPS Trajectory Simulator with Realistic Timing and Noise

This project simulates GPS route data using **real road network data** from OpenStreetMap (OSM).  
It incorporates **realistic timing** based on road types, traffic patterns, and junction delays.  
Additionally, it can generate **GPS noise** to simulate sensor inaccuracies and  
simulate **off-route anomalies** where vehicles deviate from the planned route and then return.

---

## 🧠 Features

- Realistic routing using OSM road network  
- Speed estimation based on road type and urban context  
- Time-of-day traffic modifiers (e.g., rush hour slowdowns)- Random delays at intersections (junctions)  
- Timestamp generation for each GPS point
- Off-route anomaly injection simulating route deviations and returns  
- Optional GPS noise injection to simulate real-world GPS drift  

---

## 📦 Requirements

Install Python dependencies with:

```bash
pip install osmnx networkx pandas numpy geopy
```

---

## 🚀 Usage

Generate Normal Route:

```bash
python generate_normalroute.py
```

Saves clean, timestamped GPS routes to dataset/normal_route/.

Generate Route with Anomalies

```bash
python generate_offroute.py
```
Saves GPS routes containing off-route deviations to dataset/off_route/.

---

## 📁 Project Structure

| File / Folder            | Description                                        |
|-------------------------|----------------------------------------------------|
| `generate_offroute.py`  | Script to generate GPS routes with off-route anomalies |
| `generate_normalroute.py` | Script to generate normal GPS routes                |
| `dataset/normal_route/` | Folder containing generated normal route CSV files  |
| `dataset/off_route/`    | Folder containing generated off-route anomaly CSV files |
| `images/`               | Folder to store generated map images                 |
| `utils/routing.py`      | Routing and GPS simulation utility functions         |
| `README.md`             | Project documentation                                |



---

## ⚙️ Configuration

The following aspects can be adjusted inside the script:

| Parameter                  | Description                                   | Example / Default                                                         |
| -------------------------- | --------------------------------------------- | ------------------------------------------------------------------------- |
| `SPEED_BY_HIGHWAY`         | Default speeds (km/h) per highway type        | motorway: 100, residential: 30                                            |
| `traffic_modifier(hour)`   | Traffic speed multiplier by time of day       | 0.7 during 7-9am and 5-7pm                                                |
| `is_junction(node)`        | Adds random wait time at intersections (secs) | Random between 3 and 10 seconds                                           |
| `add_gps_noise()`          | Adds positional noise (meters)                | Optional, 3-5 meters                                                      |
| `inject_off_route_anomaly` | Injects off-route segments in routes          | max\_anomalies=1, min\_length=5, max\_length=50, anomaly\_start\_prob=0.1 |

---

## 📍 Example Coordinates Used

```python
origin_coords = (40.3233635,28.0000311)         
destination_coords = (40.825069,29.9252826)
```

You can replace these with any coordinates globally.

---


## 🖼 Example Output

Normal Route:

<p align="center">
  <img src="route_map_normal_example.png" alt="Route Map Example" width="600"/>
</p>

Anomaly Route:

<p align="center">
  <img src="route_map_anomaly_example.png" alt="Route Map Example" width="600"/>
</p>

---

## 🕒 Performance Note

When simulating long routes or wide areas (e.g., across cities), you may see a warning like this:

```
UserWarning: This area is 16 times your configured Overpass max query area size...
```

This means OSMnx is automatically splitting the request into smaller sub-queries, which **can take several minutes** depending on internet speed and the Overpass server's load. Be patient — the result is cached locally for faster future runs.

To avoid pushing large temporary files, add the following to your `.gitignore`:

```
__pycache__/
.osmnx_cache/
```

---

## 🧪 Use Cases

- Simulating vehicle movement for testing GPS systems  
- Generating synthetic data for machine learning models  
- Route anomaly detection development  
- Academic research in transportation or logistics  

---

## 🤝 Contributing

Feel free to open issues or submit pull requests for improvements or new features.
