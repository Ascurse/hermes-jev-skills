"""Offline reports must distinguish request reuse and missing execution evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


def load(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditTools(unittest.TestCase):
    def test_untrusted_event_kind_is_not_published(self):
        result = load("audit_routing")._summarize([
            json.dumps({"kind": "private-sentinel"}), json.dumps({"kind": {"bad": "shape"}})])
        self.assertEqual(result["events"], {"unknown": 2})
        self.assertNotIn("private-sentinel", json.dumps(result))

    def test_followups_do_not_inflate_turn_denominator(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text("\n".join(json.dumps(r) for r in [
                {"kind": "route_effective", "first_request": True, "applied": True},
                {"kind": "route_effective", "first_request": False, "applied": True},
                {"kind": "route_effective", "first_request": True, "applied": False},
            ]) + "\nnot-json\n")
            result = load("audit_routing").summarize(path)
        self.assertEqual(result["request_application_rate"], 2 / 3)
        self.assertEqual(result["first_request_application_rate"], 1 / 2)
        self.assertEqual(result["malformed"], 1)

    def test_unverified_execution_cannot_produce_measured_difference(self):
        rows = [{"case_id": "a", "run_id": "1", "arm": arm,
                 "actual_cost_usd": 0.1, "latency_ms": 20} for arm in ("baseline", "routed")]
        result = load("compare_routing_eval").compare(rows)
        self.assertEqual(result["execution_verified_pairs"], 0)
        self.assertEqual(result["routed_minus_baseline"], {})

    def test_paired_measurements_and_duplicate_rejection(self):
        module = load("compare_routing_eval")
        rows = [{"case_id": "a", "run_id": "1", "arm": arm,
                 "execution_verified": True, "cost_source": "synthetic-fixture",
                 "actual_cost_usd": cost} for arm, cost in (("baseline", 0.2), ("routed", 0.1))]
        self.assertAlmostEqual(module.compare(rows)["routed_minus_baseline"]["actual_cost_usd"]["mean"], -0.1)
        with self.assertRaises(ValueError):
            module.compare(rows + rows)

    def test_replay_never_buys_missing_answers(self):
        module = load("replay_routing_eval")
        with self.assertRaises(ValueError):
            module.replay([{"case_id": "missing"}], {}, [])
        result = module.replay([{
            "case_id": "pinned", "category": "coding", "prompt": "Implement median",
            "current": "unknown:user-choice", "provider": "unknown", "pinned": True,
            "answers": {}}], {}, [])
        self.assertFalse(result[0]["routed"])
        self.assertEqual(result[0]["model"], "unknown:user-choice")
