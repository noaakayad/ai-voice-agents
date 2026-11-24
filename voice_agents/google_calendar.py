"""Optional Google Calendar adapter for a dedicated test calendar."""
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo
from .workflows import MemoryCalendar


class GoogleCalendar(MemoryCalendar):
    def __init__(self, service, calendar_id, zone="UTC"):
        super().__init__()
        self.service = service
        self.calendar_id = calendar_id
        self.zone = ZoneInfo(zone)

    def timestamp(self, value):
        return value.replace(tzinfo=self.zone).astimezone(timezone.utc).isoformat()

    def free(self, start, minutes):
        if not super().free(start, minutes):
            return False
        end = start + timedelta(minutes=minutes)
        result = self.service.freebusy().query(body={
            "timeMin": self.timestamp(start), "timeMax": self.timestamp(end),
            "items": [{"id": self.calendar_id}],
        }).execute()["calendars"][self.calendar_id]
        if result.get("errors"):
            raise RuntimeError("Calendar availability could not be verified")
        return not result["busy"]

    def reserve(self, start, minutes):
        with self.lock:
            if not self.free(start, minutes):
                return False
            end = start + timedelta(minutes=minutes)
            self.service.events().insert(calendarId=self.calendar_id, body={
                "summary": "Voice agent demo appointment",
                "start": {"dateTime": self.timestamp(start)},
                "end": {"dateTime": self.timestamp(end)},
            }).execute()
            self.events.append((start, end))
            return True


def from_environment():
    import os
    import google.auth
    from googleapiclient.discovery import build
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/calendar"])
    service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
    return GoogleCalendar(service, os.environ["GOOGLE_CALENDAR_ID"], os.getenv("CALENDAR_TIMEZONE", "UTC"))
