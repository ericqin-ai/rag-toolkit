import numpy as np


def positive_k(k: int) -> int:
    if not isinstance(k, int) or isinstance(k, bool) or k < 0:
        raise ValueError("top_k must be a nonnegative integer")
    return k


def vectors(values, dimension=None, count=None):
    arr = np.asarray(values, dtype=np.float32)
    if arr.ndim != 2 or arr.shape[1] == 0 or not np.isfinite(arr).all():
        raise ValueError("vectors must be a finite nonempty-dimensional matrix")
    if dimension is not None and arr.shape[1] != dimension:
        raise ValueError("vector dimension mismatch")
    if count is not None and len(arr) != count:
        raise ValueError("vector count mismatch")
    return arr
