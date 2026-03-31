import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def distance_point_to_segment(lat_p, lng_p, lat_a, lng_a, lat_b, lng_b):
    """
    Calculates the minimum distance (in meters) from point P to the segment AB.
    Uses a locally flat earth approximation which is accurate enough for
    city-scale distances (errors < 0.1% for < 100km).
    """
    R = 6371000  # meters
    
    # Convert lat/lng to radians
    lat_p_rad = math.radians(lat_p)
    lat_a_rad = math.radians(lat_a)
    lat_b_rad = math.radians(lat_b)
    
    # Cosine of average latitude for longitude scaling
    cos_lat = math.cos((lat_a_rad + lat_b_rad + lat_p_rad) / 3.0)
    
    # Project to locally flat cartesian coordinates (x=lng, y=lat)
    # Scale x by cos(lat) to make units comparable (meters-ish space, but we'll scale back at the end)
    # Actually simpler: Convert relative diffs to meters immediately
    
    x_p = (lng_p - lng_a) * cos_lat * R * (math.pi / 180)
    y_p = (lat_p - lat_a) * R * (math.pi / 180)
    
    x_b = (lng_b - lng_a) * cos_lat * R * (math.pi / 180)
    y_b = (lat_b - lat_a) * R * (math.pi / 180)
    
    # Vector AB: (x_b, y_b)
    # Vector AP: (x_p, y_p)
    
    # Dot product of AP and AB
    dot = x_p * x_b + y_p * y_b
    # Squared length of AB
    len_sq = x_b * x_b + y_b * y_b
    
    # Normalized projection parameter t
    # P_proj = A + t * (B - A)
    if len_sq == 0:
        param = -1
    else:
        param = dot / len_sq
        
    if param < 0:
        # P is closest to A
        dx = x_p
        dy = y_p
    elif param > 1:
        # P is closest to B
        dx = x_p - x_b
        dy = y_p - y_b
    else:
        # P is closest to projection on segment
        dx = x_p - param * x_b
        dy = y_p - param * y_b
        
    return math.sqrt(dx * dx + dy * dy)
