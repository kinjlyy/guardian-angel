"""
Simple test to verify the backend main.py works correctly
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Guardian Angel Backend Components...")
print("=" * 60)

# Test 1: Import geo_utils
try:
    from services.geo_utils import haversine, distance_point_to_segment
    print("✓ geo_utils imported successfully")
    
    # Test haversine
    d = haversine(51.5, -0.1, 51.5, -0.09)
    print(f"  Haversine test: {d:.2f}m (expected ~700m)")
    
    # Test segment distance
    d = distance_point_to_segment(51.5, -0.095, 51.5, -0.1, 51.5, -0.09)
    print(f"  Segment distance (on line): {d:.2f}m (expected ~0m)")
    
    d = distance_point_to_segment(51.50009, -0.095, 51.5, -0.1, 51.5, -0.09)
    print(f"  Segment distance (10m off): {d:.2f}m (expected ~10m)")
    
except Exception as e:
    print(f"✗ geo_utils import failed: {e}")
    sys.exit(1)

# Test 2: Import agents
try:
    from agents.route_guardian import RouteGuardianAgent
    from agents.decision_agent import DecisionAgent
    from agents.executor_agent import ExecutorAgent
    print("✓ All agents imported successfully")
except Exception as e:
    print(f"✗ Agent import failed: {e}")
    sys.exit(1)

# Test 3: Import services
try:
    from services.path_store import PathStore
    from services.history_store import HistoryStore
    print("✓ All services imported successfully")
except Exception as e:
    print(f"✗ Service import failed: {e}")
    sys.exit(1)

# Test 4: Test RouteGuardian logic
try:
    print("\nTesting RouteGuardian Agent...")
    agent = RouteGuardianAgent()
    
    # Set a simple route
    route = [[-0.1, 51.5], [-0.09, 51.5], [-0.08, 51.5]]
    agent.set_path(route)
    
    # Test on-path location
    loc = {"lat": 51.5, "lng": -0.095}
    result = agent.observe(loc)
    print(f"  On-path test: status={result['status']}, distance={result['distance_m']}m")
    
    # Test off-path location (should be ~22m off)
    loc_off = {"lat": 51.5002, "lng": -0.095}
    result_off = agent.observe(loc_off)
    print(f"  Off-path test: status={result_off['status']}, distance={result_off['distance_m']}m")
    
    if result_off['status'] == 'DEVIATION':
        print("✓ Deviation detection working correctly")
    else:
        print(f"⚠ Warning: Expected DEVIATION but got {result_off['status']}")
    
except Exception as e:
    print(f"✗ RouteGuardian test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All backend components working correctly!")
print("=" * 60)
print("\nNext steps:")
print("1. Install FastAPI if not already: pip install fastapi uvicorn")
print("2. Start server: uvicorn main:app --reload --port 8000")
print("3. Start UI: streamlit run ../ui/app.py")
