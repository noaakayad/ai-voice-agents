"""Place ONE test call to a number you own or have permission to call."""
import argparse
import os

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute", action="store_true", help="Actually place the potentially billable test call")
    p.add_argument("--consent", action="store_true", help="Confirm permission from the recipient")
    args = p.parse_args()
    if not args.execute:
        print("Dry run: no call placed.")
        return
    if not args.consent:
        p.error("Recipient consent is required")
    from twilio.rest import Client
    base = os.environ["PUBLIC_BASE_URL"].rstrip("/")
    if not base.startswith("https://"):
        p.error("PUBLIC_BASE_URL must use HTTPS")
    client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
    client.calls.create(to=os.environ["DEMO_RECIPIENT"], from_=os.environ["TWILIO_FROM_NUMBER"], url=base+"/voice", method="POST")
    print("Test call requested.")

if __name__ == "__main__":
    main()
