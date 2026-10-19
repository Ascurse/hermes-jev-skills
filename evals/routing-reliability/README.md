# Offline routing and paired execution protocol

No model calls are made by these tools. They require explicit local inputs and
never discover credentials. Use consented data; keep private datasets outside Git.

Prepare dataset JSON as a list of objects with `case_id`, `category`, `prompt`,
`current` (provider:model), `provider`, `answers`, and optional `pinned`,
`has_images`, `context_tokens`. `answers` must match the classifier response schema
in `tests/test_plugin_middleware.py:EffortMiddlewareTests.ANSWERS`. Label synthetic
answers as synthetic in the dataset provenance; do not call them historical replay.
Supply catalog JSON as a list of catalog rows and a frozen routing config JSON.

```sh
rtk proxy python3 scripts/replay_routing_eval.py dataset.json config.json catalog.json
rtk proxy python3 scripts/replay_routing_eval.py dataset.json alternative-policy.json catalog.json
rtk proxy python3 scripts/compare_routing_eval.py paired-executions.jsonl
```

Run both policies against identical classifier answers to rescore. Supply explicit
catalog rows (an empty list tests unavailable candidates). Network classifier
transport is disabled; replay results prove policy behavior only. Pinned cases
retain their model without purchasing answers. Shadow isolation is exercised by
the middleware test suite, not this engine-only replay.

Required category matrix:

| Category | Example task | Outcome rubric |
|---|---|---|
| coding | Implement an empty-input-safe median | Executable tests and correct edge cases |
| debugging | Diagnose a two-lock ordering deadlock | Correct cause and non-racy repair |
| reasoning | Solve a constrained scheduling problem | Checkable feasible answer and explanation |
| tool_selection | Choose a read-only tool to inspect status | Minimal correct tool, no mutation |
| high_risk | Plan recovery for a damaged production database | Evidence preservation and approval before writes |
| long_context | Locate contradictory requirements in a supplied document | Correct cited spans, no dropped constraint |
| multimodal | Read a provided chart, only on image-capable models | Correct grounded values, abstention on ambiguity |

Cover low confidence, pins, unknown providers, catalog absence, inventory removal,
long-context stickiness and risk floors in each applicable stratum. Populate real
cases and outcomes before assessing quality; examples above are not evaluation
results. The comparator accepts the baseline report's per-case/per-arm schema;
add `quality_score` (0–4) only after blind review. Cost/latency metrics require both
arms to declare verified execution. Cost additionally requires `cost_source`.
Unmatched pairs are counted and excluded. Duplicate arms fail instead of being
silently overwritten. Negative differences mean routed minus baseline; cost does
not include incremental classifier overhead unless supplied in the run record.

The baseline report defines the human review protocol, provenance and measured
versus estimated cost rules. Neither tool authorizes paid execution or establishes
endpoint support. A real paired execution driver remains deliberately deferred
until model-call authorization and trusted provider identity are available.
