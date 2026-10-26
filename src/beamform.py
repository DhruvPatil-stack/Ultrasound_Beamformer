"""Chunked analytic delay-and-sum beamformer."""
import numpy as np
from scipy.signal import hilbert, resample_poly


LATERAL_LIMIT = 20e-3


def transmit_time_offset(angle, c, lateral_limit=LATERAL_LIMIT):
    """Return the offset that makes the bounded plane-wave transmit time nonnegative."""
    return abs(np.sin(np.deg2rad(angle))) * lateral_limit / c


def compute_tof(x, z, elem_x, c, angle=0.0, time_offset=None):
    """Return plane-wave transmit plus receive delays."""
    x = np.asarray(x)[..., None]
    z = np.asarray(z)[..., None]
    if time_offset is None:
        time_offset = transmit_time_offset(angle, c)
    theta = np.deg2rad(angle)
    return (x * np.sin(theta) + z * np.cos(theta) + np.sqrt((x - np.asarray(elem_x)) ** 2 + z ** 2)) / c + time_offset


def beamform_das(rf, c, fs, pitch, x_grid, z_grid, interp="linear", apod="hann",
                 fnum=None, upsample=1, row_chunk=16, angle=0.0, return_complex=False):
    """Beamform analytic RF with the simulator's plane-wave time reference."""
    if interp not in {"nearest", "linear"} or apod not in {"none", "hann"}:
        raise ValueError("interp must be nearest/linear and apod must be none/hann")
    if fnum is not None and fnum <= 0:
        raise ValueError("fnum must be positive or None")
    analytic = hilbert(rf, axis=0)
    effective_fs = fs
    if upsample > 1:
        analytic = resample_poly(analytic, upsample, 1, axis=0)
        effective_fs *= upsample
    n_samples, n_elements = analytic.shape
    elem_x = (np.arange(n_elements) - (n_elements - 1) / 2) * pitch
    output = np.zeros((len(z_grid), len(x_grid)), dtype=complex)
    channels = np.arange(n_elements)[None, None, :]
    for start in range(0, len(z_grid), row_chunk):
        z = z_grid[start:start + row_chunk, None]
        x = x_grid[None, :]
        tof = compute_tof(x, z, elem_x, c, angle=angle)
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
        output[start:start + len(z)] = np.divide(summed, denominator, out=np.zeros_like(summed), where=denominator > 0)
    return output if return_complex else np.abs(output)
