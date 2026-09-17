# Platform support

The core precompute package is pure Python and targets Python 3.10 through 3.13 on Linux, macOS and Windows. Research adapters may have narrower container/platform constraints, which must be frozen separately by exact image digest and platform identity before execution. Core tests require no network access and no third-party runtime dependency.
