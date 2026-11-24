import unittest
from unittest.mock import Mock
from datetime import datetime
from voice_agents.google_calendar import GoogleCalendar

class CalendarAdapterTests(unittest.TestCase):
    def test_busy_slot_not_inserted(self):
        service = Mock()
        service.freebusy().query().execute.return_value = {"calendars":{"demo":{"busy":[{}]}}}
        calendar = GoogleCalendar(service, "demo")
        self.assertFalse(calendar.reserve(datetime(2030,1,2,10),30))
        service.events.assert_not_called()

    def test_free_slot_inserted(self):
        service = Mock()
        service.freebusy().query().execute.return_value = {"calendars":{"demo":{"busy":[]}}}
        calendar = GoogleCalendar(service, "demo")
        self.assertTrue(calendar.reserve(datetime(2030,1,2,10),30))
        service.events().insert.assert_called_once()
