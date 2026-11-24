"""Conversation workflows. External actions are explicit and opt-in."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from threading import RLock
import re
import unicodedata

SERVICES = ("technical support", "billing", "general inquiries")
def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).lower().strip().split())

@dataclass
class Session:
    stage: str = "start"
    data: dict = field(default_factory=dict)

@dataclass(frozen=True)
class Reply:
    text: str
    done: bool = False
    transfer: str | None = None

class MemoryCalendar:
    """In-memory demo calendar; timestamps are in the configured local timezone."""
    def __init__(self):
        self.events = []
        self.lock = RLock()

    def free(self, start, minutes):
        end = start + timedelta(minutes=minutes)
        with self.lock:
            return (start.weekday() < 5 and start.time() >= time(9)
                    and end.date() == start.date() and end.time() <= time(17)
                    and all(end <= a or start >= b for a, b in self.events))

    def reserve(self, start, minutes):
        with self.lock:
            if not self.free(start, minutes):
                return False
            self.events.append((start, start + timedelta(minutes=minutes)))
            return True

    def next_slot(self, start, minutes):
        start = start.replace(second=0, microsecond=0)
        start += timedelta(minutes=(-start.minute) % 15)
        for i in range(14 * 96):
            candidate = start + timedelta(minutes=15*i)
            if self.free(candidate, minutes):
                return candidate
        return None

class Workflow:
    def __init__(self, kind, classifier=None, calendar=None, clock=None):
        if kind not in {"routing", "appointments", "outreach", "survey"}:
            raise ValueError("Unknown workflow")
        self.kind = kind
        self.classifier = classifier
        self.calendar = calendar or MemoryCalendar()
        self.clock = clock or datetime.now

    def start(self, session):
        session.stage = {"routing":"service", "appointments":"date", "outreach":"consent", "survey":"consent"}[self.kind]
        return Reply({
            "routing":"Hello. I am an automated assistant. Which department do you need: technical support, billing, or general inquiries?",
            "appointments":"Hello. I am an automated scheduling assistant. What appointment would you prefer? Please say or enter a date and time in YYYY-MM-DD HH:MM format.",
            "outreach":"Hello. I am an automated assistant with a fictional product demonstration. Would you like to hear about it?",
            "survey":"Hello. I am an automated assistant. May I ask a few optional questions about your recent support experience?",
        }[self.kind])

    def choice(self, text, options, aliases=None):
        t = normalize(text)
        if t in options:
            return t
        if aliases and t in aliases:
            return aliases[t]
        if self.classifier:
            value = self.classifier(t, options)
            if value in options:
                return value
        return None

    def answer(self, text):
        t = normalize(text)
        return {"yes":"yes", "no":"no", "sure":"yes", "okay":"yes", "yes please":"yes", "no thanks":"no"}.get(t)

    def step(self, session, text):
        if session.stage == "done":
            return Reply("This conversation has ended.", True)
        t = normalize(text)
        if t in {"stop", "opt out", "do not call", "unsubscribe"}:
            session.data["opt_out"] = True
            return self.finish(session, "Understood. This conversation is ending.")
        if not t:
            return Reply("Sorry, could you repeat that?")
        return getattr(self, "_" + self.kind)(session, text)

    @staticmethod
    def finish(session, text, transfer=None):
        session.stage = "done"
        return Reply(text, True, transfer)

    def _routing(self, s, text):
        if s.stage == "confirm" and self.answer(text) == "yes":
            return self.finish(s, "Thank you. I will transfer you now.", s.data["service"])
        if s.stage == "confirm" and self.answer(text) == "no":
            s.stage = "service"
            return Reply("Which department would you prefer?")
        service = self.choice(text, SERVICES, {"support":"technical support", "invoice":"billing", "information":"general inquiries"})
        if service:
            s.data["service"] = service
            s.stage = "confirm"
            return Reply(f"Would you like to be transferred to {service}?")
        if s.stage == "confirm":
            answer = self.answer(text)
            if answer == "yes":
                return self.finish(s, "Thank you. I will transfer you now.", s.data["service"])
            if answer == "no":
                s.stage = "service"
        return Reply("Which department do you need: technical support, billing, or general inquiries?")

    def _appointments(self, s, text):
        if s.stage == "confirm":
            answer = self.answer(text)
            if answer == "yes":
                slot = datetime.fromisoformat(s.data["slot"])
                if slot > self.clock() and self.calendar.reserve(slot, 30):
                    return self.finish(s, f"Your appointment is confirmed for {slot:%Y-%m-%d %H:%M}.")
                s.stage = "date"
                return Reply("That slot is no longer available. Please choose another date and time.")
            if answer == "no":
                s.stage = "date"
                return Reply("Please suggest another date and time.")
        try:
            date = datetime.strptime(text.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            return Reply("Please provide an explicit date and time in YYYY-MM-DD HH:MM format.")
        if date <= self.clock():
            return Reply("Please choose a future date and time.")
        slot = self.calendar.next_slot(date, 30)
        if slot is None:
            return Reply("No slot was found in the next two weeks. Please try another date.")
        s.data["slot"] = slot.isoformat()
        s.stage = "confirm"
        return Reply(f"The available appointment is {slot:%Y-%m-%d %H:%M}, for 30 minutes. Confirm?")

    def _outreach(self, s, text):
        answer = self.answer(text)
        if answer == "no":
            return self.finish(s, "Thank you for your time. Goodbye.")
        if s.stage == "consent" and answer == "yes":
            s.stage = "interest"
            return Reply("The fictional product is a free task-list demo. Would you like more information?")
        if s.stage == "interest" and answer == "yes":
            s.data["interested"] = True
            return self.finish(s, "Thank you. This is only a demonstration; no order has been placed.")
        return Reply("Please answer yes or no. You can say stop at any time.")

    def _survey(self, s, text):
        if s.stage == "consent":
            answer = self.answer(text)
            if answer == "no":
                return self.finish(s, "Thank you. Goodbye.")
            if answer == "yes":
                s.stage = "rating"
                return Reply("How would you rate your support experience from zero to five?")
            return Reply("Would you like to participate? Yes or no.")
        if s.stage == "rating":
            t = normalize(text)
            words = {"zero":0,"one":1,"two":2,"three":3,"four":4,"five":5}
            rating = int(t) if re.fullmatch(r"[0-5]", t) else words.get(t)
            if rating is None:
                return Reply("Please give a whole number from zero to five.")
            s.data["rating"] = rating
            s.stage = "resolved"
            return Reply("Was your issue resolved? Yes or no.")
        if s.stage == "resolved":
            answer = self.answer(text)
            if answer is None:
                return Reply("Was your issue resolved? Yes or no.")
            s.data["resolved"] = answer == "yes"
            s.stage = "feedback"
            return Reply("Any optional feedback? Say skip to omit it.")
        if s.stage == "feedback":
            # No free-text feedback is persisted in this demo.
            s.data["feedback_supplied"] = normalize(text) != "skip"
            return self.finish(s, "Thank you for your feedback. Goodbye.")
        return self.finish(s, "Thank you. Goodbye.")
