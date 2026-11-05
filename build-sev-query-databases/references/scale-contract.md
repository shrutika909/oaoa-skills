# Production-scale replay contract

The replay must exercise investigation at realistic volume. Correctness on a
ten-row fixture does not demonstrate a production-like task.

## Default size profile

- Minimum `scenario.sqlite`: 500 MB (`500_000_000` bytes).
- Normal completed band: 500 MB through 3 GiB.
- Complete component maximum: 4 GiB.
- There is no fixed row-count target. Derive rows from approved source
  cardinality, row width, and the preserved investigation window.

The target is not a padding quota. Every row must come from an approved bounded
source or deterministic synthetic reconstruction whose population model is
grounded in approved source cardinalities and distributions. Never duplicate
rows, add random filler, or fabricate causal semantics to hit a byte count.

## Required scale schema

Every staged query source includes a private `volume` object:

```json
{
  "volume": {
    "profile": "production_scale",
    "scale_basis": "source_cardinality",
    "observed_source_rows": 18200000,
    "materialized_rows": 6400000,
    "observed_source_bytes": 2940000000,
    "estimated_materialized_bytes": 650000000,
    "sampling": {
      "strategy": "bounded_time_window",
      "fraction": 0.351648,
      "reason": "preserves complete baseline, incident, and recovery windows"
    },
    "preserved_distributions": [
      "event_time",
      "result",
      "caller_class",
      "latency_bucket"
    ]
  }
}
```

`scale_basis` is `source_cardinality` for approved transformed rows or
`approved_synthetic_population` for reconstruction. Synthetic reconstruction
records the source measurements used for population size, frequency, skew,
missingness, and temporal density. Unknown measurements block a claim of
production-scale fidelity.

## Evidence density

Bullseye evidence should be rare. Count both sources and rows privately. For a
large operational replay, start with these row-share bands and document any
departure:

| Role | Recommended row share |
|---|---:|
| Bullseye / causal | 0.1–2% |
| Supporting | 2–10% |
| Directional | 10–30% |
| Misleading / competing / negative | 58–87.9% |

Misleading evidence must remain plausible and falsifiable. Background rows may
be irrelevant to the incident while remaining faithful to the visible schema
and production distribution. Do not insert facts that contradict ground truth.

## Query behavior at scale

- enforce pagination and native row limits;
- preserve partitions or time-window pruning;
- support aggregation before detail inspection;
- preserve realistic duplicates, retries, missing values, and sparse columns;
- validate joins and group cardinalities over the full population;
- measure cold query latency without using a wall-clock grading threshold.

## Completion gate

The private manifest and scaffolding summary record database bytes, total rows,
source rows/bytes, per-resource rows/bytes, evidence-role row shares, sampling,
preserved distributions, and whether the 500 MB floor passed. Row count must be
explained by the original source population and row width.

An export below 500 MB is `blocked` unless the parent explicitly selects a
non-database architecture. Tiny fixtures must use `profile: contract_fixture`;
they prove portability and can never satisfy a real task's scale gate.
