from geopy.distance import geodesic

start = (40.991295, 29.024563)
end = (41.025636, 29.096305)

distance_m = geodesic(start, end).meters
print(f"Mesafe: {distance_m:.2f} metre")