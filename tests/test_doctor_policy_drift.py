"""Doctor names the policies whose tuned_on version the provider's model does not match.

Every live decision on such a policy is replaced by its on_drift action, silently: Zen's free
`jev-1.13-free` against policies tuned on jev-1.14.0 is the case this was written for.
"""
from __future__ import annotations

import unittest

from jevkit import cli, policy


class PolicyDriftWarnings(unittest.TestCase):
    def test_an_older_provider_model_names_every_drifted_policy(self):
        warnings = cli._policy_drift_warnings("jev-1.13-free")
        self.assertEqual(len(warnings), 1)
        self.assertIn("jev-1.13-free", warnings[0])
        for name in ("lane", "loop-step", "retry"):
            self.assertIn(name, warnings[0])

    def test_the_tuned_version_gives_no_warning(self):
        tuned = {policy.load(name).get("tuned_on") for name in policy.shipped_names()}
        self.assertEqual(len(tuned), 1)
        self.assertEqual(cli._policy_drift_warnings(tuned.pop()), [])

    def test_an_unversioned_model_is_not_evidence_of_drift(self):
        self.assertEqual(cli._policy_drift_warnings("jev-latest"), [])
        self.assertEqual(cli._policy_drift_warnings(None), [])


if __name__ == "__main__":
    unittest.main()
