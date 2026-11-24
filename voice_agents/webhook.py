"""Optional Flask/Twilio integration. Use one process for this prototype."""
import os
from threading import RLock
from time import monotonic
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, request, abort, Response
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import VoiceResponse, Gather
from .workflows import Workflow, Session
from .llm import classify

def create_app():
    token = os.environ["TWILIO_AUTH_TOKEN"]
    base = os.environ["PUBLIC_BASE_URL"].rstrip("/")
    if not base.startswith("https://"):
        raise ValueError("PUBLIC_BASE_URL must use HTTPS")
    kind = os.getenv("VOICE_WORKFLOW", "routing")
    calendar = None
    zone = ZoneInfo(os.getenv("CALENDAR_TIMEZONE", "UTC"))
    if kind == "appointments" and os.getenv("ENABLE_GOOGLE_CALENDAR") == "1":
        from .google_calendar import from_environment
        calendar = from_environment()
    workflow = Workflow(kind, classifier=classify if os.getenv("ENABLE_LLM") == "1" else None, calendar=calendar, clock=lambda: datetime.now(zone).replace(tzinfo=None))
    validator = RequestValidator(token)
    app = Flask(__name__)
    sessions = {}
    lock = RLock()
    routes = {"technical support":"TRANSFER_SUPPORT", "billing":"TRANSFER_BILLING", "general inquiries":"TRANSFER_GENERAL"}

    @app.before_request
    def verify():
        url = base + request.path
        if request.query_string:
            url += "?" + request.query_string.decode("ascii")
        if not validator.validate(url, request.form, request.headers.get("X-Twilio-Signature", "")):
            abort(403)

    def xml(reply):
        response = VoiceResponse()
        if reply.transfer:
            destination = os.getenv(routes[reply.transfer])
            if destination:
                response.say(reply.text)
                response.dial(destination, timeout=20, action="/transfer-result", method="POST")
            else:
                response.say("This is a demo. No transfer destination is configured.")
                response.hangup()
        elif reply.done:
            response.say(reply.text)
            response.hangup()
        else:
            gather = Gather(input="speech", action="/next", method="POST", language="en-US", speech_timeout="auto", timeout=6)
            gather.say(reply.text)
            response.append(gather)
            response.redirect("/next", method="POST")
        return Response(str(response), mimetype="application/xml")

    @app.post("/voice")
    def start():
        sid = request.form.get("CallSid")
        if not sid:
            abort(400)
        with lock:
            now = monotonic()
            for key in list(sessions):
                if now - sessions[key][1] > 1800:
                    del sessions[key]
            if len(sessions) >= 1000:
                abort(503)
            session = Session()
            sessions[sid] = (session, now)
            return xml(workflow.start(session))

    @app.post("/next")
    def advance():
        sid = request.form.get("CallSid")
        with lock:
            item = sessions.get(sid)
            if item is None or monotonic() - item[1] > 1800:
                sessions.pop(sid, None)
                from .workflows import Reply
                return xml(Reply("This session has expired. Goodbye.", True))
            session, _ = item
            try:
                reply = workflow.step(session, request.form.get("SpeechResult", ""))
            except Exception:
                from .workflows import Reply
                reply = Reply("The service is temporarily unavailable. Please try again later.", True)
            if reply.done:
                sessions.pop(sid, None)
            else:
                sessions[sid] = (session, monotonic())
            return xml(reply)

    @app.post("/transfer-result")
    def transfer_result():
        from .workflows import Reply
        status = request.form.get("DialCallStatus")
        return xml(Reply("The department is unavailable. Please try again later." if status != "completed" else "Thank you. Goodbye.", True))
    return app

if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
