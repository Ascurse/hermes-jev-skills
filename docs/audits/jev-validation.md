# Validation and independent review

## Final checks

- Full suite: **1,340 tests passed**, Python 3.13, exit 0, 30.434 seconds.
  Run with `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1` in the test process.
  This affects only subprocess environment, not user Git configuration.
- Requested suites tested separately before final additions: middleware 31 passed,
  jevkit 213 passed, route health 44 passed. Final full run includes these and five
  offline audit/evaluation tests.
- Release check: passed for 208 text files at the preceding scan; final scan
  repeated after this document was added. Existing dashboard PNG is excluded by
  the scanner; it was unchanged and no image-security claim is made.
- `git diff --check`: passed at the preceding scan, repeated before delivery.
- Existing suite emits ResourceWarnings for sockets/files/databases and expected
  negative-path test tracebacks. Final test status is successful; warnings are
  not claimed fixed.

Commands (from repository):

```sh
GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 rtk proxy python3 -m unittest discover -s tests
rtk proxy python3 scripts/check_release.py
rtk git diff --check
```

## Failures investigated

The initial ordinary-environment run failed one unrelated lane fixture:
`test_scope_sensitive_paths_and_check_tails` expected two out-of-scope files but
found one. A targeted rerun reproduces the failure with ordinary Git settings;
all 28 lane tests pass when global/system Git config are disabled. The fixture
creates `.env.local`; global ignore behavior affects its file enumeration.
The exact ignore rule was not changed. This is an environment-dependent test
limitation, not a claim that ordinary-environment full tests pass.

A subsequent isolated full run caught missing versioned release notes for the
new 0.20.1 metadata. Added the required matching changelog section; final isolated
run passed all 1,340 tests. Neither failure was skipped.

## Standards review

Independent read-only reviewer checked documented contribution/privacy standards
and code-smell heuristics. Initial findings: missing release metadata; unchecked
event-kind data in aggregate report; missing validation artifact. Added paired
0.20.1 version metadata and changelog, a closed event-kind vocabulary plus a
synthetic private-sentinel regression, context-managed file handles and this
artifact. Reviewer rechecked code changes and reported no remaining actionable
standards or code-smell findings; tests were run by the implementation agent.

## Spec and security review

Separate independent read-only reviewer checked the user specification and narrow
patch. Initial findings: runnable evaluation framework missing; validation evidence
pending; universal endpoint compatibility acceptance remains unproved. Added offline
replay/rescoring, paired comparison, regression tests and category protocol. Reviewer
closed the framework finding and reported no new must-fix issue. Validation is
recorded above. The architectural blocker remains: preserving legacy operator
aliases is not proof of endpoint support. No review certifies live provider routing.

## Boundaries

No paid APIs, live model integration tests, production configuration changes,
gateway restart, installation, merge or deployment. Router and middleware tests
use mocks/fixtures. The suite includes local integration fixtures; they are not
evidence of actual upstream execution. Provider inventory changes and cross-provider
entitlements cannot be certified without a host identity contract. Concurrent
first callbacks and credential changes at the same endpoint remain residual risks.

Full provider-aware remediation is blocked. The narrow hardening patch is prepared
for review; custom routing enablement and any rollout require further evidence.
