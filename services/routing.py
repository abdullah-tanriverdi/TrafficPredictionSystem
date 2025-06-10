import networkx as nx
from geopy.distance import geodesic
import math
import requests

#ağırlıklı graphda dijikstra algoritması ile iki düğüm arasında ki en kısa rotayı hesaplama işlemi
def calculate_route(G, start_node, end_node):
    try:
        path_nodes = nx.dijkstra_path(G, start_node, end_node, weight='weight')
    except nx.NetworkXNoPath:
        return None

    route_coords = []
    for i in range(len(path_nodes) - 1):
        edge_data = G.get_edge_data(path_nodes[i], path_nodes[i+1])
        if edge_data and 'points' in edge_data:
            route_coords.extend([(pt['lat'], pt['lng']) for pt in edge_data['points']])
        else:
            route_coords.append(path_nodes[i])
    route_coords.append(path_nodes[-1])
    return route_coords

def get_osrm_route(start, end, duration_factor=1.4): 
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true"
    }
    response = requests.get(url, params=params)
    if not response.ok:
        return None, None, None, None, None

    data = response.json()
    if not data.get("routes"):
        return None, None, None, None, None

    route_data = data["routes"][0]

    route_coords = [(lat, lon) for lon, lat in route_data["geometry"]["coordinates"]]
    total_distance_km = round(route_data["distance"] / 1000, 2)
    
    
    total_duration_min = round((route_data["duration"] * duration_factor) / 60, 1)
    
    average_speed = round(total_distance_km / (total_duration_min / 60), 1) if total_duration_min > 0 else 0

    directions = []
    for leg in route_data.get("legs", []):
        for step in leg.get("steps", []):
            name = step.get("name", "").strip()
            maneuver = step.get("maneuver", {})
            if not name:
                name = step.get("ref") or maneuver.get("type") or "Bilinmeyen yol"
            directions.append({
                "instruction": name,
                "distance": step.get("distance", 0),
                "duration": step.get("duration", 0),
                "maneuver": maneuver.get("type", ""),
                "location": maneuver.get("location", []),
                "text": name
            })

    return route_coords, directions, total_distance_km, total_duration_min, average_speed


def extract_street_names(osrm_directions):
    street_names = []
    seen = set()
    for step in osrm_directions:
        name = step.get("instruction") or step.get("text") or ""
        if name and name not in seen:
            street_names.append(name)
            seen.add(name)
    return street_names
