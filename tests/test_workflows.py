import unittest
from datetime import datetime
from voice_agents.workflows import Workflow, Session, MemoryCalendar

class WorkflowTests(unittest.TestCase):
    def setup_workflow(self, kind, **kwargs):
        workflow, session = Workflow(kind, **kwargs), Session()
        workflow.start(session)
        return workflow, session

    def test_routing_requires_confirmation(self):
        w,s = self.setup_workflow("routing")
        self.assertIsNone(w.step(s,"billing").transfer)
        self.assertEqual(w.step(s,"yes").transfer,"billing")

    def test_routing_change(self):
        w,s = self.setup_workflow("routing")
        w.step(s,"billing")
        w.step(s,"technical support")
        self.assertEqual(w.step(s,"yes").transfer,"technical support")

    def test_isolated_sessions(self):
        w,s = self.setup_workflow("routing")
        other = Session(); w.start(other)
        w.step(s,"billing")
        self.assertIsNone(w.step(other,"yes").transfer)

    def test_classifier_allowlist(self):
        w,s = self.setup_workflow("routing", classifier=lambda t,o: "unconfigured")
        self.assertIsNone(w.step(s,"random").transfer)
        self.assertEqual(s.stage,"service")

    def test_booking_only_after_confirmation(self):
        cal = MemoryCalendar()
        w,s = self.setup_workflow("appointments", calendar=cal, clock=lambda:datetime(2030,1,1,8))
        w.step(s,"2030-01-02 10:00")
        self.assertEqual(cal.events,[])
        self.assertTrue(w.step(s,"yes").done)
        self.assertEqual(len(cal.events),1)
        self.assertFalse(cal.reserve(datetime(2030,1,2,10,15),30))

    def test_calendar_closing_time(self):
        cal=MemoryCalendar()
        self.assertFalse(cal.free(datetime(2030,1,2,16,45),30))

    def test_booking_conflict_after_offer(self):
        cal=MemoryCalendar()
        w,s=self.setup_workflow("appointments", calendar=cal, clock=lambda:datetime(2030,1,1,8))
        w.step(s,"2030-01-02 10:00")
        cal.reserve(datetime(2030,1,2,10),30)
        self.assertFalse(w.step(s,"yes").done)

    def test_outreach_refusal(self):
        w,s=self.setup_workflow("outreach")
        self.assertTrue(w.step(s,"no").done)
        self.assertNotIn("interested",s.data)

    def test_opt_out(self):
        w,s=self.setup_workflow("outreach")
        self.assertTrue(w.step(s,"stop").done)
        self.assertTrue(s.data["opt_out"])

    def test_survey(self):
        w,s=self.setup_workflow("survey")
        w.step(s,"yes");w.step(s,"7")
        self.assertEqual(s.stage,"rating")
        w.step(s,"four");w.step(s,"yes")
        self.assertTrue(w.step(s,"skip").done)
        self.assertEqual(s.data["rating"],4)
        self.assertFalse(s.data["feedback_supplied"])

if __name__ == "__main__":
    unittest.main()
