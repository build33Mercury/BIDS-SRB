# Failure modes

The core package fails closed for unsafe paths, malformed manifests, empirical mutation attempts, missing files, hash mismatches and all calls to scientific `execute` while COMPUTE-GO is false. Unexpected exceptions return structured error records. Research adapters are intentionally unavailable in this public-candidate version.
