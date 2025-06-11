```pseudo
FUNCTION find_nearest_node(G, target_point, max_distance=500 meters) RETURNS nearest_node OR None
    SET min_distance = infinity
    SET nearest_node = None

    FOR each node in G.nodes DO
        CALCULATE distance = geodesic(node, target_point) in meters
        IF distance < min_distance AND distance <= max_distance THEN
            SET min_distance = distance
            SET nearest_node = node

    RETURN nearest_node
