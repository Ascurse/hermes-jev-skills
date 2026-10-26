# Bind cached routing decisions to their request context

A cached JEV decision could be reused after Hermes changes provider, endpoint or
model within the same turn. Retain the original request whenever that context
changes, and record the compatibility basis without logging the endpoint. Count
an applied model change only when the outgoing model actually differs.
Invalidation lasts until the next turn, so A -> B -> A cannot revive a stale
decision or routing/effort notice. Normal repeated requests in an unchanged
context still reuse their decision.
The binding is claimed before classification. Concurrent callbacks keep their
original request while a same-context decision is pending, and context changes
invalidate the turn even during an RPC. Decision publication and the final
model/effort commit recheck the live turn object, binding and invalidation state.

| Version scope | Version | Evidence |
|---|---|---|
| Audited installed snapshot | 0.20.0 | Historical runtime/config/log inspection; no live upgrade |
| PR repository base | 0.24.0 | `7b56de6627557e8bebb22f1538d75b37555a5623` |
| Proposed package metadata | 0.24.1 | Paired library/manifest patch bump |

Evaluation comparison excludes synthetic, mixed and unclassified pairs. Measured
inputs require explicit provenance and execution evidence references; billed cost
requires a recognized billing source and receipt reference, and quality requires
structured human-review metadata. These are structurally validated caller
attestations; the tool does not independently authenticate execution or receipts.

Includes regression tests, an offline aggregate audit tool and the baseline,
architecture, evaluation, security and rollback package in `jev-baseline.md`.
Custom-provider routing remains blocked when identity cannot be established;
no live settings, inventory mappings or deployment changes are included.

Validation and known limitations: see `jev-validation.md`. This change does not
establish endpoint execution compatibility, quality improvements or savings.

Current local validation: **1,633 core tests and 71 dashboard tests passed**
(1,704 total) on Python 3.13.7/macOS, with global/system Git settings isolated
for the test process. Release scan (340 text files) and `git diff --check` passed.
Two independent security/regression reviewers rechecked the concurrency fix and
found no remaining actionable issue. The regression reviewer substituted the old
callback into the new race tests and reproduced eight failures; all 45 current
middleware tests pass. Earlier test totals are historical checkpoints.

CI remains unverified: GitHub's `test` and `Windows CLI fallback` runs on the
published head `9ee6de0` require maintainer approval (`action_required`). Local
checks do not certify the Linux/Windows or other-Python matrix. No merge or
deployment approval is implied.
