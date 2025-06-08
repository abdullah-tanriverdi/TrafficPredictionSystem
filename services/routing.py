import networkx as nx
from geopy.distance import geodesic
import math
import requests

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

def get_turn_by_turn(route_coords):
    turn_by_turn = []
    for i in range(1, len(route_coords)-1):
        prev = route_coords[i-1]
        curr = route_coords[i]
        nxt = route_coords[i+1]

        v1 = (curr[0]-prev[0], curr[1]-prev[1])
        v2 = (nxt[0]-curr[0], nxt[1]-curr[1])

        angle = math.degrees(
            math.atan2(v2[1], v2[0]) - math.atan2(v1[1], v1[0])
        )
        if angle < -180:
            angle += 360
        elif angle > 180:
            angle -= 360

        if angle > 30:
            turn = "Sağa Dönüş"
        elif angle < -30:
            turn = "Sola Dönüş"
        else:
            turn = "Düz İlerle"

        dist_m = geodesic(prev, curr).meters
        turn_by_turn.append({
            'instruction': turn,
            'distance': round(dist_m, 1),
            'location': curr
        })
    return turn_by_turn

def get_osrm_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true"  
    }
    response = requests.get(url, params=params)
    if response.ok:
        data = response.json()
        if data.get("routes"):
            route = data["routes"][0]["geometry"]["coordinates"]
            steps = data["routes"][0]["legs"][0]["steps"]  
            route_coords = [(lat, lon) for lon, lat in route]

           
            directions = []
            for step in steps:
                maneuver = step.get("maneuver", {})
                instruction = step.get("maneuver", {}).get("instruction", "")
                if not instruction:
                    instruction = step.get("name", "")
                distance = step.get("distance", 0)
                directions.append({
                    "instruction": step.get("name", ""),
                    "distance": round(distance, 1),
                    "maneuver": maneuver.get("type", ""),
                    "text": step.get("maneuver", {}).get("instruction", "")
                })
            return route_coords, directions
    return None, None
