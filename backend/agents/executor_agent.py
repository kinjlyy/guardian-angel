import os
from twilio.rest import Client
from dotenv import load_dotenv
import time

# Handle .env loading from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../backend/agents
parent_dir = os.path.dirname(os.path.dirname(current_dir)) # .../guardian-angel (Wait, backend/agents -> backend -> guardian-angel is 2 hops up? No, 3 hops?)
# backend/agents is 2 levels deep from backend.
# Let's just use the known structure.

# .../guardian-angel/backend/agents
# dirname -> .../guardian-angel/backend
# dirname -> .../guardian-angel
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '.env')

if not os.path.exists(env_path):
    print(f"[DEBUG] .env not found at {env_path}, trying specific path...")
    env_path = r"c:\Users\kinjal\guardian-angel\.env"

print(f"[DEBUG] Loading .env from: {env_path}")
load_dotenv(env_path)

class ExecutorAgent:
    def __init__(self):
        self.sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM")
        self.whatsapp_from = os.getenv("WHATSAPP_FROM") or self.from_number
        self.to_number = os.getenv("EMERGENCY_TO")
        
        # Cooldown management
        self.last_alert_time = 0
        self.ALERT_COOLDOWN_SEC = 300 # 5 minutes

        if self.sid and self.token:
            self.client = Client(self.sid, self.token)
            print(f"[DEBUG] Twilio Client Initialized.")
            print(f"        SMS From: {self.from_number}")
            print(f"        WhatsApp From: {self.whatsapp_from}")
            print(f"        Guardian To: {self.to_number}")
        else:
            self.client = None
            print("[ERROR] Twilio Credentials MISSING in ExecutorAgent!")

    def send_alert(self, location: dict, reason: str):
        now = time.time()
        if now - self.last_alert_time < self.ALERT_COOLDOWN_SEC:
            print(f"[EXECUTOR] Alert suppressed (cooldown active). Reason: {reason}")
            return
        self.last_alert_time = now
        
        message = (
            f"Guardian Angel Alert: {reason}\n"
            f"Loc: {location['lat']}, {location['lng']}\n"
            f"Link: http://maps.google.com/?q={location['lat']},{location['lng']}"
        )

        print("[ALERT PREVIEW]", message)

        if not self.client:
            print("[ERROR] No Twilio Client available to send SMS.")
            return

        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )
            print(f"[TWILIO SUCCESS] Alert SMS Sent! SID: {msg.sid}")
        except Exception as e:
            print(f"[TWILIO ERROR] Failed to send Alert SMS: {e}")

        # Trigger Voice Call
        self.make_call(reason)

    def make_call(self, reason: str):
        if not self.client:
            return

        # TwiML to speak the message
        twiml_content = (
            f"<Response>"
            f"<Say>Guardian Angel Alert. The user has stopped for too long or deviated. Reason: {reason}. Please check your SMS for location.</Say>"
            f"</Response>"
        )

        try:
            call = self.client.calls.create(
                twiml=twiml_content,
                to=self.to_number,
                from_=self.from_number
            )
            print(f"[TWILIO SUCCESS] Alert Call Initiated! SID: {call.sid}")
        except Exception as e:
            print(f"[TWILIO ERROR] Failed to make Alert Call: {e}")

    def send_safety_message(self):
        """
        Asks the user if they are okay via WhatsApp.
        """
        victim_phone = os.getenv("VICTIM_PHONE")
        if not victim_phone:
            print("[ERROR] No VICTIM_PHONE configured.")
            return

        msg_body = "Am I safe? Reply YES if you are safe. If you don't reply, your guardian will be alerted in 60s."
        print(f"[SAFETY CHECK] Sending WhatsApp to {victim_phone} from {self.whatsapp_from}: {msg_body}")
        
        if self.client:
            try:
                # Use WHATSAPP_FROM specifically
                message = self.client.messages.create(
                    body=msg_body,
                    from_=f"whatsapp:{self.whatsapp_from}",
                    to=f"whatsapp:{victim_phone}"
                )
                print(f"[TWILIO SUCCESS] Safety WhatsApp Sent! SID: {message.sid}")
            except Exception as e:
                print(f"[TWILIO ERROR] Safety WhatsApp Failed. Full Error: {str(e)}")
