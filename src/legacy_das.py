"""Unchanged baseline DAS algorithm retained for ablation."""
import numpy as np
from scipy.signal import hilbert


def legacy_das(rf_data, c, fs, pitch, x_grid, z_grid):
    """Baseline: nearest sample, no apodization, Hilbert after summation."""
    n_samples, n_elements = rf_data.shape
    elem_x = (np.arange(n_elements) - (n_elements - 1) / 2) * pitch
    z = z_grid[:, None, None]
    x = x_grid[None, :, None]
    xi = elem_x[None, None, :]
    tof = (z + np.sqrt((x - xi) ** 2 + z ** 2)) / c
    idx = np.round(tof * fs).astype(int)
    valid = (idx >= 0) & (idx < n_samples)
    idx = np.where(valid, idx, 0)
    channels = np.arange(n_elements)[None, None, :]
    amplitudes = np.where(valid, rf_data[idx, channels], 0.0)
    return np.abs(hilbert(amplitudes.sum(axis=2), axis=0))
