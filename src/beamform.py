"""Chunked analytic delay-and-sum beamformer."""
import numpy as np
from scipy.signal import hilbert, resample_poly


def compute_tof(x, z, elem_x, c):
    """Return 0-degree plane-wave transmit plus receive delays."""
    x = np.asarray(x)[..., None]
    z = np.asarray(z)[..., None]
    return (z + np.sqrt((x - np.asarray(elem_x)) ** 2 + z ** 2)) / c


def beamform_das(rf, c, fs, pitch, x_grid, z_grid, interp="linear", apod="hann",
                 fnum=1.5, upsample=1, row_chunk=16):
    """Beamform analytic RF; transmit time offset is zero, while real data can need one."""
    if interp not in {"nearest", "linear"} or apod not in {"none", "hann"}:
        raise ValueError("interp must be nearest/linear and apod must be none/hann")
    if fnum is not None and fnum <= 0:
        raise ValueError("fnum must be positive or None")
    analytic = hilbert(rf, axis=0)
    effective_fs = fs
    if upsample > 1:
        analytic = resample_poly(analytic, upsample, axis=0)
        effective_fs *= upsample
    n_samples, n_elements = analytic.shape
    elem_x = (np.arange(n_elements) - (n_elements - 1) / 2) * pitch
    output = np.zeros((len(z_grid), len(x_grid)), dtype=float)
    channels = np.arange(n_elements)[None, None, :]
    for start in range(0, len(z_grid), row_chunk):
        z = z_grid[start:start + row_chunk, None]
        x = x_grid[None, :]
        tof = compute_tof(x, z, elem_x, c)
        sample = tof * effective_fs
        lower = np.floor(sample).astype(int)
        valid = (lower >= 0) & (lower < n_samples)
        if interp == "nearest":
            index = np.rint(sample).astype(int)
            valid &= (index >= 0) & (index < n_samples)
            gathered = analytic[np.clip(index, 0, n_samples - 1), channels]
        else:
            upper = lower + 1
            valid &= (upper < n_samples)
            fraction = sample - lower
            low = analytic[np.clip(lower, 0, n_samples - 1), channels]
            high = analytic[np.clip(upper, 0, n_samples - 1), channels]
            gathered = low * (1.0 - fraction) + high * fraction
        if fnum is None:
            active = np.ones_like(valid)
            half_width = np.max(np.abs(x[..., None] - elem_x), axis=2, keepdims=True)
        else:
            half_width = z[..., None] / (2.0 * fnum)
            active = np.abs(x[..., None] - elem_x) <= half_width
        weights = active.astype(float)
        if apod == "hann":
            safe_width = np.maximum(half_width, np.finfo(float).eps)
            weights *= 0.5 * (1.0 + np.cos(np.pi * (x[..., None] - elem_x) / safe_width))
        weights *= valid
        denominator = weights.sum(axis=2)
        summed = (gathered * weights).sum(axis=2)
        output[start:start + len(z)] = np.abs(np.divide(summed, denominator, out=np.zeros_like(summed), where=denominator > 0))
    return output
