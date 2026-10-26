"""Coherent plane-wave compounding."""
import numpy as np

from src.beamform import beamform_das


def compound_das(rf_list, angles, c, fs, pitch, x_grid, z_grid, **kwargs):
    """Sum equal-weight complex angle images before taking the envelope."""
    if len(rf_list) != len(angles) or not rf_list:
        raise ValueError("rf_list and angles must have the same nonzero length")
    complex_images = [beamform_das(rf, c, fs, pitch, x_grid, z_grid,
                                   angle=angle, return_complex=True, **kwargs)
                      for rf, angle in zip(rf_list, angles)]
    return np.abs(np.sum(complex_images, axis=0) / len(complex_images))
