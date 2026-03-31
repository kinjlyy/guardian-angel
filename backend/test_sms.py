
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv

# Force load .env from the parent directory
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

def log(msg):
    print(msg)
    with open("sms_run.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def test_sms():
    # clear log
    with open("sms_run.log", "w", encoding="utf-8") as f:
        f.write("Starting test...\n")

    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_num = os.getenv("TWILIO_FROM")
    to_num = os.getenv("EMERGENCY_TO")

    log(f"SID found: {'Yes' if sid else 'No'}")
    log(f"Token found: {'Yes' if token else 'No'}")
    log(f"From: {from_num}")
    log(f"To: {to_num}")

    if not sid or not token:
        log("Error: Missing credentials")
        return

    try:
        client = Client(sid, token)
        log("Attempting to send test message...")
        message = client.messages.create(
            body="Test message from Guardian Angel Debugger",
            from_=from_num,
            to=to_num
        )
        log(f"Message sent! SID: {message.sid}")
    except TwilioRestException as e:
        log(f"Twilio Error: {e}")
    except Exception as e:
        log(f"General Error: {e}")

if __name__ == "__main__":
    test_sms()
