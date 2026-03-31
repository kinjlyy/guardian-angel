
import sys
import os
sys.path.append(os.getcwd())

from services.geo_utils import distance_point_to_segment
from agents.route_guardian import RouteGuardianAgent

def test():
    print("--- Testing Math ---")
    # 1. Point on the line (London approx)
    d = distance_point_to_segment(51.5, -0.095, 51.5, -0.1, 51.5, -0.09)
    print(f"Test 1 (On Line): {d:.2f}m (Expected ~0)")

    # 2. Point 10 meters north of line
    d = distance_point_to_segment(51.50009, -0.095, 51.5, -0.1, 51.5, -0.09)
    print(f"Test 2 (10m North): {d:.2f}m (Expected ~10)")
    
    print("\n--- Testing Agent ---")
    agent = RouteGuardianAgent()
    # Route: A -> B -> C
    # A(51.5, -0.1), B(51.5, -0.09), C(51.5, -0.08)
    route = [[-0.1, 51.5], [-0.09, 51.5], [-0.08, 51.5]] # [lng, lat]
    agent.set_path(route)
    
    # Test point between A and B
    loc = {"lat": 51.5, "lng": -0.095}
    res = agent.observe(loc)
    print(f"Agent Observation (On Path): {res['status']} d={res['distance_m']}m")
    
    # Test point slightly off
    loc_off = {"lat": 51.5002, "lng": -0.095} # ~22m north
    res_off = agent.observe(loc_off)
    print(f"Agent Observation (Off Path): {res_off['status']} d={res_off['distance_m']}m")
    
if __name__ == "__main__":
    test()
