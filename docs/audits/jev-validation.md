# Validation and independent review

## Current final verification

The worktree started clean on `codex/jev-routing-isolation` at `9ee6de0`, matching
the published PR head. Existing audit, telemetry, provenance checks and prior
fixes were preserved. This continuation adds a verified concurrency fix and its
regressions; it does not install the branch or modify production configuration.

### Three review findings

1. **Version scopes verified:** installed plugin manifest still reads 0.20.0;
   repository base `7b56de6` reads 0.24.0; branch library and plugin manifest both
   read 0.24.1. The audit describes the historical installed snapshot, and the
   proposed patch targets the newer repository base. Only non-secret version
   metadata was read; live routing settings, credentials and messages were not.
2. **Model and reasoning-effort isolation:** sequential A -> B -> A stays
   invalidated until new turn state. Independent regression review additionally
   reproduced a concurrent publication defect in `9ee6de0`: initial callbacks
   could classify different contexts and commit stale model/effort changes.
   The first context is now claimed before RPC, simultaneous followers keep their
   original request, and publication plus final mutation revalidate live turn
   object identity, binding and invalidation state under the lock. No global lock
   is held during classifier RPC. First-request telemetry is assigned at admission,
   so delayed and rejected callbacks retain the correct request denominator.
3. **Evaluation separation:** synthetic, unclassified and mixed pairs remain
   excluded from measured deltas. Execution evidence, recognized billing source
   and receipt references, and structured human review remain required. These are
   structurally validated caller attestations, not independently authenticated
   executions, billing or human identities. No new measurement claims are made.

### Executed checks

Python 3.13.7 on macOS arm64, with `GIT_CONFIG_GLOBAL=/dev/null` and
`GIT_CONFIG_NOSYSTEM=1` scoped to the test subprocesses:

| Check | Actual result |
|---|---|
| `python3 -m unittest discover -s tests` | 1,633 passed, 34.337 seconds, exit 0 |
| `python3 -m unittest discover -s router-dashboard/tests` | 71 passed, 2.155 seconds, exit 0 |
| Total discovered tests | 1,704 passed |
| `python3 scripts/check_release.py` | Passed, 340 text files; 56 existing binaries unscanned |
| `git diff --check` | Passed |

The core/dashboard suites emit ResourceWarnings for existing socket, file and
database fixtures (28 and 12 warnings respectively). Expected negative-path test
tracebacks also appear; neither suite reports a failed test. No tests were
silently skipped to obtain these results. This is local evidence, not the
repository's complete multi-OS/multi-Python CI matrix.

### Independent review and safeguards

Two independent read-only reviewers examined the complete scoped diff and the
additional fix. The security reviewer ran 45 middleware plus 11 evaluation-tool
tests successfully. The regression reviewer ran all 45 middleware tests with zero
failures, errors or skips and substituted the previous callback in memory: the
new concurrency tests produced eight expected failures, demonstrating that they
catch the old routing and effort leaks. Both reviewers rechecked the fix and
reported no remaining actionable issue.

New tests exercise actual configured effort on Chat Completions and Responses,
all four binding components (provider, endpoint, host model and outgoing model),
pending first decisions, changes during `effort.pick`, turn replacement including
reused IDs, and no duplicate simultaneous classifier calls. Existing pin,
shadow, explicit-effort, disabled-reasoning, malformed-config, router-exception
and custom-provider safeguards pass in the full suite.

The complete base-to-worktree diff is restricted to the middleware, tests, audit
and offline evaluation tools/docs, changelog and paired release metadata. No
runtime configuration, production routing pool, dependency, deployment workflow
or unrelated workspace change is included. Release/sensitive-pattern checks find
no credential material; the credential-style URL in a regression is a deliberate
`private-sentinel` fixture. No changed binary requires new visual inspection.

### CI, publication gate and remaining limitations

GitHub's `test` and `Windows CLI fallback` runs for published head `9ee6de0` are
both `action_required`, not passing test results:

- [Core CI approval required](https://github.com/kerpopule/hermes-jev-skills/actions/runs/39312596832)
- [Windows CLI approval required](https://github.com/kerpopule/hermes-jev-skills/actions/runs/39312596723)

The authenticated account has no write/admin permission on the upstream repository
and cannot provide that maintainer approval. Because the requested publication
gate requires all required checks to pass, this continuation is committed locally
and its push/PR update is held while those CI runs require approval. The published
PR remains at `9ee6de0`; this report and the updated PR-description artifact are
prepared locally. Any later push requires CI validation of its exact new head
before merge readiness is asserted. Local passing checks do not satisfy that
cross-platform gate. No merge, deployment or Hermes restart was performed.

The reproduced concurrency defect is resolved for guarded model/effort commits.
Remaining architectural boundaries are unchanged: named custom identity is not
provided reliably by the host; aliases remain operator assertions; credential or
inventory drift at an unchanged endpoint cannot be certified; later middleware
or gateways can rewrite requests; measurement provenance is caller-attested.
Custom-provider enablement, end-to-end execution compatibility, measured savings
and comparative quality remain unverified. PR #51 is not yet merge-ready.

## Earlier PR #51 focused follow-up

The review was limited to the three requested concerns. Before implementation,
new regressions reproduced A -> B -> A cache revival (including stale notices)
and synthetic records entering measured deltas. Those regressions now pass.

- Version evidence is explicit in the audit and PR description: installed audit
  snapshot 0.20.0, original source revision `45ed9d4`, rebased repository base
  `7b56de6` at 0.24.0, proposed package 0.24.1. No new runtime inspection, installer
  or restart was performed in this follow-up.
- A context mismatch invalidates routing for the remaining turn. Regression
  sequences cover A -> B -> A -> B for provider, endpoint, host model and outgoing
  request model, active/shadow behavior, no extra classifier calls, no request
  mutation, no stale notices/effort, independent sessions and next-turn reset.
- Comparator tests cover synthetic and mixed provenance, missing/invalid
  execution attestations, cost-source whitelist and evidence references, typed
  human-review metadata, valid schema/delta calculations and synthetic pollution
  exclusion. These are synthetic unit fixtures, not model measurements.
- Targeted suites: **40 middleware tests and 11 offline audit/evaluation tests
  passed**. Full suite: **1,628 tests passed**, exit 0, 34.097 seconds, with
  `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1` in the test process.
- Both independent read-only reviewers found no actionable issue in the focused
  changes. They inspected code/tests/docs; the implementation agent ran the tests.
- Release scan passed for 340 text files; changed Python AST syntax checks and
  `git diff --check` passed. Existing upstream binaries remain unscanned and
  unchanged by this follow-up.

The 1,340, 1,621 and 1,628 results are historical checkpoints, not the current
test count. Measurement evidence is structurally checked caller
attestation; authenticity must be audited separately. No live compatibility,
quality or savings claim is added, and no merge or deployment is authorized.

## Earlier implementation checks

- After rebasing onto refreshed upstream 0.24.0: **1,621 tests passed**, exit 0,
  34.043 seconds with the same isolated Git environment. The branch release
  metadata is 0.24.1; the installed runtime remains 0.20.0. Rebase conflicts were
  limited to changelog/version metadata; newer provider-neutral manifest text,
  pin normalization and effort behavior were preserved.
- Final upstream-based release scan passed for **340 text files**. It lists
  existing upstream binary evidence as unscanned; this patch changes no binaries.
  Final `git diff --check` passed. Both independent reviewers rechecked the
  rebased diff and validation artifact and found no new actionable issue.
- Full suite: **1,340 tests passed**, Python 3.13, exit 0, 30.434 seconds.
  Run with `GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1` in the test process.
  This was the earlier v0.20-based patch check and affects only subprocess
  environment, not user Git configuration.
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
initial 0.20.1 metadata. Added the required matching changelog section; isolated
run passed all 1,340 tests. Neither failure was skipped.

## Standards review

Independent read-only reviewer checked documented contribution/privacy standards
and code-smell heuristics. Initial findings: missing release metadata; unchecked
event-kind data in aggregate report; missing validation artifact. Added paired
0.20.1 version metadata and changelog, a closed event-kind vocabulary plus a
synthetic private-sentinel regression, context-managed file handles and this
artifact. After upstream reconciliation release metadata advanced to 0.24.1.
Reviewer rechecked code changes and reported no remaining actionable
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
