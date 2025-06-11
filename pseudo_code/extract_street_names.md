```pseudo
FUNCTION extract_street_names (osrm_directions) RETURNS list of unique street names

INITALIZE empty list street_names
INITALIZE empty set seen_names

FOR each step in osrm_directions DO
    GET instruction or text field as name
    IF name is not empty AND not in seen_names THEN
        APPEND name to street_names
        ADD name to seen_names

RETURN street_names