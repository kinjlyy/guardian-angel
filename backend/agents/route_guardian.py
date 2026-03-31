from services.geo_utils import distance_point_to_segment

class RouteGuardianAgent:
    def __init__(self):
        self.route = None
        self.threshold_meters = 15  # allowed deviation (TIGHTENED)
        
        # Stoppage Detection
        self.last_location = None
        self.last_move_time = None
        self.STOPPAGE_THRESHOLD_SEC = 40
        self.STOPPAGE_DISTANCE_M = 5
        
        print("RouteGuardianAgent initialized with Segment Distance Logic")

    def set_path(self, route):
        """
        route = [[lng, lat], [lng, lat], ...]
        """
        self.route = route
        self.last_location = None
        self.last_move_time = None

    def _distance_to_route(self, lat, lng):
        """
        Find minimum distance from point to any route segment
        """
        min_dist = float("inf")
        if not self.route or len(self.route) < 2:
             return float("inf")

        for i in range(len(self.route) - 1):
            p1 = self.route[i]
            p2 = self.route[i+1]
            # route points are [lng, lat]
            d = distance_point_to_segment(lat, lng, p1[1], p1[0], p2[1], p2[0])
            min_dist = min(min_dist, d)
            
        return min_dist

    def _is_odd_place(self, lat, lng):
        """
        Heuristic check: Is this place unusual for the user?
        Checks distance to the nearest historical point in the database.
        """
        from services.history_store import HistoryStore
        from services.geo_utils import haversine
        
        store = HistoryStore()
        history = store.get_all_history()
        
        if len(history) < 5:
            return False # Not enough data to determine 'oddness'
            
        min_dist_to_familiar = min([haversine(lat, lng, h[0], h[1]) for h in history])
        
        # If more than 300m from any familiar spot, mark as 'odd'
        if min_dist_to_familiar > 300:
            print(f"[DEBUG] Odd Place Detected! Min dist to familiar: {min_dist_to_familiar:.1f}m")
            return True
        return False

    def observe(self, location: dict, mode: str = "fixed"):
        """
        Observes location and returns a signal based on current mode.
        Priority: DEVIATION > STOPPAGE > ON_PATH
        """
        lat, lng = location["lat"], location["lng"]
        import time
        from services.geo_utils import haversine
        current_time = time.time()
        
        status = "ON_PATH"
        distance = 0
        stoppage_signal = False

        # 1. Calculate Path Distance (Fixed Path)
        if self.route:
            distance = self._distance_to_route(lat, lng)

        # 2. Track Movement / Stoppage logic
        if self.last_location:
            moved_dist = haversine(self.last_location["lat"], self.last_location["lng"], lat, lng)
            if moved_dist > self.STOPPAGE_DISTANCE_M:
                self.last_location = location
                self.last_move_time = current_time
            else:
                # Stationary
                if (current_time - self.last_move_time) > self.STOPPAGE_THRESHOLD_SEC:
                    stoppage_signal = True
        else:
            self.last_location = location
            self.last_move_time = current_time

        # 3. Decision Logic (PRIORITY: Deviation > Stoppage)
        if not self.route:
            status = "UNKNOWN"
        elif distance > self.threshold_meters:
            status = "DEVIATION"
        elif stoppage_signal:
            status = "STOPPAGE"
        else:
            status = "ON_PATH"

        return {
            "mode": mode,
            "status": status,
            "distance_m": round(distance, 2),
            "location": location,
            "stoppage_detected": stoppage_signal
        }
