import requests
import networkx as nx
from geopy.distance import geodesic
from config import HERE_API_KEY


# koordinatlar arasında here apiden trafik verisi çekme işlemi
def fetch_traffic_data(lat_min, lat_max, lon_min, lon_max):

    bbox = f"{lon_min},{lat_min},{lon_max},{lat_max}" #bbox formatına alma

    traffic_url = "https://data.traffic.hereapi.com/v7/flow"
    params = {
        "in": f"bbox:{bbox}",
        "locationReferencing": "shape",
        "apiKey": HERE_API_KEY
    }
    response = requests.get(traffic_url, params=params)
    if response.ok:
        return response.json().get("results", [])
    else:
        return None


# trafik verilerini alarak ağırlıklı multidigraph oluşturma işlemi
def build_weighted_graph(traffic_results, lat_min, lat_max, lon_min, lon_max):

    G = nx.DiGraph()
    for segment in traffic_results:
        current_flow = segment.get("currentFlow", {})
        jam_factor = current_flow.get("jamFactor", 1.0) # tıkanıklık katsayısı
        location = segment.get("location", {})
        shape = location.get("shape", {})
        links = shape.get("links", [])

        for link in links:
            points = link.get("points", [])
            if len(points) < 2:
                continue
            filtered_points = [pt for pt in points if lat_min <= pt['lat'] <= lat_max and lon_min <= pt['lng'] <= lon_max]
            if len(filtered_points) < 2:
                continue

            #iki nokta arasında mesafeyi ve ağırlığı hesaplama
            for i in range(len(filtered_points) - 1):
                start = (filtered_points[i]['lat'], filtered_points[i]['lng'])
                end = (filtered_points[i+1]['lat'], filtered_points[i+1]['lng'])
                length_m = geodesic(start, end).meters
                weight = length_m * jam_factor
                G.add_edge(start, end, weight=weight, points=[filtered_points[i], filtered_points[i+1]])
    return G

# noktaya en yakın node bulma işlemi 
def find_nearest_node(G, point, max_distance=500):
    nearest = None
    min_dist = float('inf')
    for node in G.nodes:
        dist = geodesic(node, point).meters
        if dist < min_dist and dist <= max_distance:
            min_dist = dist
            nearest = node
    return nearest