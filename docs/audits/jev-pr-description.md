# Bind cached routing decisions to their request context

A cached JEV decision could be reused after Hermes changes provider, endpoint or
model within the same turn. Retain the original request whenever that context
changes, and record the compatibility basis without logging the endpoint. Count
an applied model change only when the outgoing model actually differs.

Includes regression tests, an offline aggregate audit tool and the baseline,
architecture, evaluation, security and rollback package in `jev-baseline.md`.
Custom-provider routing remains blocked when identity cannot be established;
no live settings, inventory mappings or deployment changes are included.

Validation and known limitations: see `jev-validation.md`. This change does not
establish endpoint execution compatibility, quality improvements or savings.
