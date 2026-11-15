import json
import tempfile
import unittest
from pathlib import Path

import miner


class MinerTest(unittest.TestCase):
    def test_forced_fold_and_applied_coercion_are_distinct(self):
        check = {"action": "fold", "fallback": True, "coerced": False, "error": "check is not legal facing a bet"}
        raise_to_bet = {"action": "bet", "fallback": False, "coerced": True, "error": "raise not legal; applied bet"}
        self.assertEqual(miner.execution_outcome(check), "forced_fold_fallback")
        self.assertEqual(miner.execution_outcome(raise_to_bet), "legal_executed_coercion")

    def test_regression_examples_deduplicate_category_tags(self):
        base = {
            "scope": "own",
            "match_id": "m_current",
            "hand_number": 16,
            "action_index": 4,
            "tool_args": {"action": "check"},
            "executed_action": "fold",
        }
        findings = [
            base | {"failure_category": "invalid_check", "failure_reason": "illegal check"},
            base | {"failure_category": "explicit_engine_error", "failure_reason": "engine error"},
        ]
        rows = miner.regression_examples(findings, {"own": {"target_actions": 368}}, {"m_current"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["numerator"], 1)
        self.assertEqual(rows[0]["denominator"], 368)
        self.assertEqual(rows[0]["failure_categories"], ["invalid_check", "explicit_engine_error"])
        self.assertTrue(rows[0]["is_current_entry"])

    def test_current_entry_uses_exact_published_metadata(self):
        old_root = miner.ROOT
        try:
            with tempfile.TemporaryDirectory() as temporary:
                miner.ROOT = Path(temporary)
                (miner.ROOT / "raw").mkdir()
                records = {}
                for match_id, deployment, checkpoint in (
                    ("m_old", "infer_old", "ckpt_old"),
                    ("m_current", "infer_current", "ckpt_current"),
                ):
                    match = {
                        "id": match_id,
                        "started_at": "2026-11-15T09:00:00Z" if match_id == "m_current" else "2026-11-15T08:00:00Z",
                        "finished_at": "2026-11-15T09:30:00Z" if match_id == "m_current" else "2026-11-15T08:30:00Z",
                        "seats": [{"seat": 0, "entry": {"id": miner.OUR_ORG, "org_id": miner.OUR_ORG, "submission_name": "current", "deployment_id": deployment, "model": "model", "deployment": {"version": 1, "checkpoint_id": checkpoint}}}],
                        "hands": [],
                    }
                    (miner.ROOT / "raw" / f"{match_id}.json").write_text(json.dumps(match))
                    records[match_id] = {"id": match_id, "result": "complete", "scopes": ["own"]}
                selected, identity = miner.current_entry_records(records)
                self.assertEqual(set(selected), {"m_current"})
                self.assertEqual(identity["deployment_id"], "infer_current")
                self.assertEqual(identity["selection"], "exact_published_entry_metadata")
        finally:
            miner.ROOT = old_root


if __name__ == "__main__":
    unittest.main()
