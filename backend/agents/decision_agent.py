import time

class DecisionAgent:
    def decide(self, signal: dict, safety_state: dict, mode: str = "fixed"):
        """
        Decides the action based on mode and signal.
        Focuses only on Fixed Path (stoppage-check and deviation-emergency).
        """
        status = signal.get("status")
        
        if status == "DEVIATION":
            return "EMERGENCY_DEVIATION"
        
        if status == "STOPPAGE":
            return self._handle_safety_check(safety_state)
        
        return "NORMAL"

    def _handle_safety_check(self, safety_state: dict):
        """Helper to manage the 60s WhatsApp safety check window"""
        if safety_state.get("replied_safe"):
            return "NORMAL"
            
        if safety_state.get("active"):
            elapsed = time.time() - safety_state.get("start_time", 0)
            if elapsed > 60:
                return "EMERGENCY_TIMEOUT"
            return "WAIT_FOR_REPLY"
        else:
            return "SEND_SAFETY_NOTICE"
