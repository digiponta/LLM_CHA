import unittest
from adaptive_retention_eval_v023351 import Event
from important_competition_v0340 import traces,run
from auto_pin_protection_v0330 import evaluate

class ImportantCompetitionTests(unittest.TestCase):
    def test_five_scenarios(self):
        self.assertEqual(len(traces()),5)
    def test_sixty_rows(self):
        self.assertEqual(len(run()["rows"]),60)
    def test_all_capacities(self):
        self.assertTrue(all(row["capacity_compliant"] for row in run()["rows"]))
    def test_all_auto_pin_budgets(self):
        self.assertTrue(all(row.get("budget_compliant",True) for row in run()["rows"]))
    def test_same_query_denominator(self):
        for name in traces():
            records=[r for r in run()["rows"] if r["scenario"]==name]
            self.assertEqual(len({r["important_queries"] for r in records}),1)
    def test_explicit_preserved(self):
        records=[r for r in run()["rows"] if r["scenario"]=="explicit_protection"
                 and r["policy"]=="protected_auto_pin_v033"]
        self.assertTrue(all("指定" in r["explicit_pins"] for r in records))
    def test_reallocation_threshold_sensitive(self):
        events=[Event("observe","旧A",True),Event("observe","旧B",True)]
        events += [Event("observe",f"一時{i}") for i in range(10)]
        events += [Event("observe","新A",True)]
        early=evaluate(events,4,min_age_for_reallocation=4)
        late=evaluate(events,4,min_age_for_reallocation=100)
        self.assertGreater(early["auto_demotions"],late["auto_demotions"])
    def test_capacity_two_explicit_priority(self):
        events=[Event("observe","指定",True),Event("observe","一時",True)]
        events += [Event("observe",f"別{i}",True) for i in range(8)]
        result=evaluate(events,2,explicit_topics=("指定",))
        self.assertIn("指定",result["final_topics"])
    def test_deterministic(self):
        self.assertEqual(run(),run())
    def test_query_not_inserted(self):
        r=evaluate([Event("query","存在しない",True)],4)
        self.assertNotIn("存在しない",r["final_topics"])

if __name__=="__main__":
    unittest.main()
