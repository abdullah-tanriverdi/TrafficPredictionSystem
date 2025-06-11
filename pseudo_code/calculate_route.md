FUNCTION calculate_route(G, start_node, end_node) RETURNS route_coords OR None

    TRY
        path_nodes = Dijkstra shortest path in G from start_node to end_node using edge weights
    CATCH no path exception
        RETURN None

    INITIALIZE empty route_coords list

    FOR i in range from 0 to length(path_nodes) - 2 DO
        GET edge_data between path_nodes[i] and path_nodes[i+1]
        IF edge_data contains 'points' attribute THEN
            EXTEND route_coords by all points (lat, lon) in edge_data['points']
        ELSE
            APPEND path_nodes[i] coordinate

    APPEND last node coordinate path_nodes[-1]

    RETURN route_coords
