"""The plugin must not override a host's active handoff with a /new pause."""
import ast
from pathlib import Path
import unittest

class ContinuityRuleTests(unittest.TestCase):
    def test_scope_continuation_and_host_capability_are_explicit(self):
        path=Path(__file__).resolve().parents[1]/'hermes/plugin/hermes-handoff/__init__.py'
        tree=ast.parse(path.read_text())
        rule=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_RULE' for t in n.targets))
        self.assertLessEqual(len(rule),700)
        for text in ('not a pause','without asking for /new or repeated approvals','handoff adds no new authority','capsule-only host','stop controls','without verification'):
            self.assertIn(text,rule)
        self.assertNotIn('do not begin new work in that reply',rule)

if __name__=='__main__':unittest.main()
