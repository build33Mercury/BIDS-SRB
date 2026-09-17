class BidsSrbError(Exception):
    pass

class ManifestError(BidsSrbError):
    pass

class UnsafePathError(BidsSrbError):
    pass

class ComputeLockedError(BidsSrbError):
    pass
