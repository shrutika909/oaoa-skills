# Synthetic reconstruction contract

## Release rule

Deterministic pseudonymization is permitted only inside the private authoring
boundary. It is not an export control. An exportable task must be regenerated
from a fictional specification that contains no production rows,
queries, names, paths, URLs, identifiers, distributions, or implementation
details.

## Boundary

1. Source adapters inspect authorized Scuba, Daiquery, Hive, Presto, and LogView material
   inside Meta.
2. The author records only abstract semantics: schemas, relationships,
   constraints, temporal shapes, failure sequences, and required edge cases.
3. `scripts/synthetic_reconstruct.py` consumes only that specification.
4. The generated staging data passes three independent release gates.

The reconstruction process never sends raw extracts to an LLM. An LLM may
help author fictional names or scenarios only after the specification has
passed confidentiality review.

## Common intermediate representation

The specification declares fictional datasets with:

- source type and operation
- one opaque source-lineage identity per distinct production resource
- fictional resource and query identifiers
- fictional columns and native types
- deterministic field generators
- row counts and time bounds
- primary, unique, and foreign-key constraints
- temporal ordering and required edge cases
- technical invariants to validate
- a SHA-256 binding to the exact input specification

Supported generator kinds are `sequence_id`, `timestamp_series`, `enum_cycle`,
`integer_series`, `float_series`, `constant`, `template`, and `foreign_key`.
Foreign keys reference a named pool created by `sequence_id`; they never hash or
reuse a production identifier.

Synthetic reconstruction preserves resource boundaries. It does not flatten
different source datasets or tool families into one generic table. Each source
lineage receives a different fictional resource name and tool-specific storage
object.

## Over-normalization gate

Normalization may replace identities and shift absolute time. It must not erase
dataset boundaries, tool-native schemas and types, joins, ordering, relative
timing, scope distinctions, cardinality, error semantics, contradictions,
negative evidence, or decoy falsifiers. Each staged source declares an
executable invariant, and each distinct source lineage remains a distinct
fictional resource. A technically tidy replay that makes the investigation
shallower fails this gate.

## Adapter responsibilities

| Adapter | Abstract privately | Reconstruct fictionally |
|---|---|---|
| Scuba | aggregation, filters, windows, sampling behavior | events, dimensions, counters, timestamps |
| Hive | partitions, joins, pruning and SQL behavior | databases, tables, paths, partitions and rows |
| Daiquery | bounded lookup, filtering, ordering, and response shape | datasets, fields, identifiers, and records |
| Presto | joins, grouping, aggregation, and plan-relevant shape | catalogs, schemas, tables, query text, and records |
| LogView | event order, exception chains, retries and correlations | services, traces, endpoints, messages and stacks |

## Release gates

### Identity safety

No real person, account, service, host, database, table, URL, MID, trace,
request, task, diff, SEV, or other production identifier is present.

### Confidentiality safety

No proprietary architecture, business rule, source query, internal path,
production distribution, dashboard, stack frame, or implementation detail is
present. Unknown fields fail closed.

### Technical fidelity

The generated task preserves only the approved general challenge: joins,
constraints, ordering, aggregation behavior, error chains, edge cases, and
query semantics. Each invariant has an executable validation result.

All three gates must pass. “No PII detected” alone
does not make an artifact exportable.
