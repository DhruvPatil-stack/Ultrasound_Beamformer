"""B-mode display conversion."""
import numpy as np


def to_db(envelope, floor_db=-60.0):
    """Normalize an envelope and clip it to the requested display range."""
    peak = np.max(envelope)
    if peak <= 0:
        return np.full_like(envelope, floor_db, dtype=float)
    return np.clip(20.0 * np.log10(np.maximum(envelope / peak, np.finfo(float).tiny)), floor_db, 0.0)
