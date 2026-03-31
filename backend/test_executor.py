
import sys
import os

# Ensure backend dir is in path
sys.path.append(os.getcwd())

from agents.executor_agent import ExecutorAgent

def log(msg):
    print(msg)
    with open("executor_test.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def test_executor():
    # clear log
    with open("executor_test.log", "w", encoding="utf-8") as f:
        f.write("Starting Executor Test...\n")

    log("Initializing ExecutorAgent...")
    try:
        agent = ExecutorAgent()
        
        if not agent.client:
            log("ERROR: Agent client is None. Env vars failed?")
        else:
            log("SUCCESS: Agent client initialized.")
            log(f"From: {agent.from_number}, To: {agent.to_number}")
            
        log("Sending Test Alert...")
        # Using dummy coordinates
        agent.send_alert({"lat": 28.7041, "lng": 77.1025}, "Test from Debug Script")
        log("Alert function called.")
    except Exception as e:
        log(f"EXCEPTION: {e}")

if __name__ == "__main__":
    test_executor()
