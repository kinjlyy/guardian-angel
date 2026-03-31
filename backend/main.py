from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

# Import agents and services
from agents.route_guardian import RouteGuardianAgent
from agents.decision_agent import DecisionAgent
from agents.executor_agent import ExecutorAgent
from services.path_store import PathStore
from services.history_store import HistoryStore

app = FastAPI()

# Enable CORS for Streamlit UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents and stores
route_guardian = RouteGuardianAgent()
decision_agent = DecisionAgent()
executor_agent = ExecutorAgent()
path_store = PathStore()
history_store = HistoryStore()

# Safety state for stoppage handling
safety_state = {
    "active": False,
    "start_time": None,
    "replied_safe": False
}

print("=" * 60)
print("🛡 Guardian Angel Backend Initialized")
print("=" * 60)

# Request models
class PathRequest(BaseModel):
    route: list  # [[lng, lat], [lng, lat], ...]
    eta_seconds: int

class LocationUpdate(BaseModel):
    lat: float
    lng: float
    mode: str = "fixed"

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "Guardian Angel Backend Running"}

@app.post("/set-path")
async def set_path(req: PathRequest):
    """
    Save the selected route and reset safety state
    """
    print(f"\n[SET-PATH] Received route with {len(req.route)} points, ETA: {req.eta_seconds}s")
    
    # Save to path store
    path_store.save(req.route, req.eta_seconds)
    
    # Set route in guardian agent
    route_guardian.set_path(req.route)
    
    # Reset safety state
    safety_state["active"] = False
    safety_state["start_time"] = None
    safety_state["replied_safe"] = False
    
    print("[SET-PATH] Route saved and guardian configured")
    return {"status": "ok", "message": "Route saved successfully"}

@app.post("/move")
async def move(loc: LocationUpdate):
    """
    Process location update from user
    """
    print(f"\n[MOVE] Location: ({loc.lat:.6f}, {loc.lng:.6f})")
    
    # Log location to history
    history_store.log_location(loc.lat, loc.lng, loc.mode)
    
    # Observe location with RouteGuardian
    signal = route_guardian.observe({"lat": loc.lat, "lng": loc.lng}, mode=loc.mode)
    print(f"[ROUTE GUARDIAN] Status: {signal['status']}, Distance: {signal.get('distance_m', 'N/A')}m")
    
    # Get decision from DecisionAgent
    decision = decision_agent.decide(signal, safety_state, mode=loc.mode)
    print(f"[DECISION AGENT] Decision: {decision}")
    
    dist_val = signal.get("distance_m")
    
    # Execute actions based on decision
    if decision == "EMERGENCY_DEVIATION":
        print("[EXECUTOR] 🚨 EMERGENCY DEVIATION - Sending alerts!")
        executor_agent.send_alert(
            location={"lat": loc.lat, "lng": loc.lng},
            reason="Significant path deviation detected"
        )
        return {
            "decision": "EMERGENCY_DEVIATION",
            "status": signal["status"],
            "distance_m": dist_val
        }
    
    elif decision == "SEND_SAFETY_NOTICE":
        print("[EXECUTOR] ⚠️ STOPPAGE - Sending WhatsApp safety check")
        executor_agent.send_safety_message()
        
        # Activate safety check window
        safety_state["active"] = True
        safety_state["start_time"] = time.time()
        safety_state["replied_safe"] = False
        
        return {
            "decision": "SEND_SAFETY_NOTICE",
            "status": signal["status"],
            "distance_m": dist_val,
            "message": "Safety check sent via WhatsApp"
        }
    
    elif decision == "WAIT_FOR_REPLY":
        elapsed = time.time() - safety_state.get("start_time", 0)
        print(f"[EXECUTOR] ⏳ Waiting for safety reply... ({elapsed:.1f}s / 60s)")
        
        return {
            "decision": "WAIT_FOR_REPLY",
            "status": signal["status"],
            "distance_m": dist_val,
            "elapsed_seconds": round(elapsed, 1)
        }
    
    elif decision == "EMERGENCY_TIMEOUT":
        print("[EXECUTOR] 🚨 EMERGENCY TIMEOUT - No response to safety check!")
        executor_agent.send_alert(
            location={"lat": loc.lat, "lng": loc.lng},
            reason="User stopped and did not respond to safety check"
        )
        
        # Reset safety state after emergency
        safety_state["active"] = False
        safety_state["replied_safe"] = False
        
        return {
            "decision": "EMERGENCY_TIMEOUT",
            "status": signal["status"],
            "distance_m": dist_val,
            "message": "Emergency alert sent - no response to safety check"
        }
    
    else:  # NORMAL
        # IMPORTANT: Reset safety state once moving normally to handle next stoppage
        if safety_state["active"]:
            print("[EXECUTOR] ✅ Movement resumed. Resetting safety check state.")
            safety_state["active"] = False
            safety_state["replied_safe"] = False
            
        return {
            "decision": "NORMAL",
            "status": signal["status"],
            "distance_m": dist_val
        }

@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    """
    Handle incoming WhatsApp messages (Twilio webhook)
    """
    form_data = await request.form()
    body = form_data.get("Body", "").strip().upper()
    from_number = form_data.get("From", "")
    
    print(f"\n[WHATSAPP WEBHOOK] From: {from_number}, Message: {body}")
    
    # Check if user replied "YES" to safety check
    if "YES" in body and safety_state.get("active"):
        print("[WHATSAPP] ✅ User confirmed safety!")
        safety_state["replied_safe"] = True
        safety_state["active"] = False
        
        return {"status": "ok", "message": "Safety confirmed"}
    
    print("[WHATSAPP] Message received but not a safety confirmation")
    return {"status": "ok", "message": "Message received"}

@app.get("/status")
async def get_status():
    """
    Get current system status (for debugging)
    """
    return {
        "route_set": route_guardian.route is not None,
        "route_points": len(route_guardian.route) if route_guardian.route else 0,
        "safety_state": safety_state,
        "history_count": history_store.get_count()
    }

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Guardian Angel Backend on http://127.0.0.1:8000")
    print("📍 Endpoints:")
    print("   - POST /set-path")
    print("   - POST /move")
    print("   - POST /whatsapp-webhook")
    print("   - GET /status")
    print("   - GET /")
    uvicorn.run(app, host="127.0.0.1", port=8000)