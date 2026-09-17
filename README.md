# BIDS-SRB

BIDS-SRB is the **BIDS Semantic Robustness Benchmark**, research software for prospectively testing metadata-driven neuroimaging workflow semantics.

## Status

This public candidate is **PRE-OUTCOME and COMPUTE-LOCKED**.

The project currently has **19/25 precompute gates closed**. Scientific execution is not authorized. Baseline/sham scientific outcomes remain 0, metadata-fault outcomes remain 0, and the frozen global denominator remains N=9.

The `bids-srb execute` command therefore fails closed by design.

BIDS-SRB is not an official BIDS validator or certification program, not an OpenNeuro service, not a NiPreps or PennLINC product, and not a Springer Nature product.

## Scope

BIDS-SRB is not presented as the first metadata audit, the first BIDS metadata tool, or the first use of metamorphic testing. Its research scope is the narrower conjunction of prospectively frozen controlled metadata transformations, layered validator/interpreter/workflow/derivative response contracts, protected-payload checks, exact-version consequence observation, prespecified repair inverses, and preservation of null, adverse, and silent outcomes.

The software does not support prevalence, defect-rate, comparative-software-reliability, or tool-ranking claims.

## Public-candidate capabilities

The package provides deterministic, offline-capable commands for manifest validation, read-only dataset inspection, execution planning, synthetic fixture generation, static verification, canonicalization, comparison, synthetic repair testing, diagnostic reporting, and static replay.

```text
bids-srb version
bids-srb schema
bids-srb validate-manifest MANIFEST.json
bids-srb inspect-dataset DATASET
bids-srb plan MANIFEST.json
bids-srb generate SYNTHETIC_CASE.json --output-dir OUT
bids-srb verify MANIFEST.json --root DATASET
bids-srb execute MANIFEST.json
bids-srb canonicalize INPUT.json --output OUTPUT.json
bids-srb compare A.json B.json
bids-srb repair RECIPE.json --root SYNTHETIC_DIR
bids-srb report RECORD.json --output REPORT.json
bids-srb replay RECIPE.json --output-dir OUT
```

`execute` intentionally returns a fail-closed response in version 0.1.0.dev1.

## Canonicalization

Gate 15 closed on canonicalizer v5.2. The strict provenance profile retains scientifically relevant stochastic values. A construction-equivalence profile may normalize only narrowly justified operational noise in historical synthetic construction evidence. Future scientific runs must explicitly freeze/equal random seeds; construction-only normalization cannot be used as evidence of scientific repeatability.

## Safety boundaries

* Empirical datasets are read only by inspection/verification functions.
* Synthetic mutation and repair require `fixture_class: synthetic`.
* Relative paths are checked against traversal and absolute-path escapes.
* The core package does not require network access.
* Scientific execution remains locked.
* No external human independence is claimed.

## Development

Run:

```text
python -m unittest discover -s tests -v
```

See `docs/GATE20_MATURITY.md`, `docs/CLAIM_CEILING.md`, and `protocol/PRECOMPUTE_AUTHORITY.json`.
