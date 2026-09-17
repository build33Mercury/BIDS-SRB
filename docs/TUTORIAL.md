# Precompute tutorial

1. Validate the bundled synthetic manifest:
   `bids-srb validate-manifest fixtures/synthetic/example_case.json --json`
2. Produce a deterministic plan:
   `bids-srb plan fixtures/synthetic/example_case.json --json`
3. Reconstruct the synthetic fixture:
   `bids-srb generate fixtures/synthetic/example_case.json --output-dir demo --json`
4. Confirm that scientific execution is locked:
   `bids-srb execute fixtures/synthetic/example_case.json --json`
   This command must return a nonzero status and a `ComputeLockedError` record.

The tutorial intentionally stops before any admitted research workflow execution.
