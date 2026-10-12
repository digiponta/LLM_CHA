import unittest
from types import SimpleNamespace
from retention_shadow_v0360 import RetentionShadow
from multi_topic_context_v0233821 import MultiTopicContext
from conversation_topic_adapter_v0233822 import ConversationTopicAdapter

class ShadowTests(unittest.TestCase):
    def test_disabled_routes_do_not_update(self):
        a=RetentionShadow()
        a.observe_route(SimpleNamespace(action="COMMAND",topic="宇宙"))
        self.assertEqual(a.stats()["observed_events"],0)
    def test_no_topic_not_recorded(self):
        a=RetentionShadow()
        a.observe_route(SimpleNamespace(action="READY",topic=None))
        self.assertEqual(a.stats()["observed_events"],0)
    def test_ready_observation(self):
        a=RetentionShadow()
        a.observe_route(SimpleNamespace(action="READY",topic="宇宙"))
        self.assertEqual(a.stats()["observed_events"],1)
    def test_reset(self):
        a=RetentionShadow()
        a.observe_route(SimpleNamespace(action="READY",topic="宇宙"))
        a.reset()
        self.assertEqual(a.stats()["observed_events"],0)
    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            RetentionShadow(17)
    def test_shadow_does_not_change_live_context(self):
        context=MultiTopicContext()
        adapter=ConversationTopicAdapter(context)
        route=adapter.process_user_turn("宇宙とは")
        before=context.snapshot()
        shadow=RetentionShadow()
        shadow.observe_route(route)
        self.assertEqual(context.snapshot(),before)
    def test_over_capacity_does_not_change_real_topics(self):
        context=MultiTopicContext(max_topics=8,ttl_turns=100)
        adapter=ConversationTopicAdapter(context)
        shadow=RetentionShadow(capacity=2)
        for topic in ("宇宙","数学","GPU"):
            route=adapter.process_user_turn(topic+"とは")
            shadow.observe_route(route)
        self.assertEqual(len(context.topics),3)
        self.assertEqual(len(shadow.stats()["retention"]["final_topics"]),2)
    def test_route_action_stays_ready(self):
        adapter=ConversationTopicAdapter()
        route=adapter.process_user_turn("GPUとは")
        RetentionShadow().observe_route(route)
        self.assertEqual(route.action,"READY")

if __name__=="__main__":
    unittest.main()
