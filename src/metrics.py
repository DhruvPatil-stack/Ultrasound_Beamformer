"""Measured image-quality metrics."""
import numpy as np


def point_position_error(image, x_grid, z_grid, target_x, target_z, lateral_window=2e-3, axial_window=1e-3):
    x_mask = np.abs(x_grid - target_x) <= lateral_window
    z_mask = np.abs(z_grid - target_z) <= axial_window
    local = image[np.ix_(z_mask, x_mask)]
    local_peak = np.unravel_index(np.argmax(local), local.shape)
    peak = (np.flatnonzero(z_mask)[local_peak[0]], np.flatnonzero(x_mask)[local_peak[1]])
    lateral = abs(x_grid[peak[1]] - target_x) * 1e3
    axial = abs(z_grid[peak[0]] - target_z) * 1e3
    return {"lateral_mm": float(lateral), "axial_mm": float(axial)}


def _crossing(coord, values, peak_index, side):
    threshold = values[peak_index] / np.sqrt(2.0)
    indices = range(peak_index, 0, -1) if side == "left" else range(peak_index, len(values) - 1)
    for i in indices:
        j = i - 1 if side == "left" else i + 1
        if (values[i] - threshold) * (values[j] - threshold) <= 0:
            fraction = (threshold - values[i]) / (values[j] - values[i])
            return coord[i] + fraction * (coord[j] - coord[i])
    return np.nan


def fwhm(coord, values):
    peak = int(np.argmax(values))
    left, right = _crossing(coord, values, peak, "left"), _crossing(coord, values, peak, "right")
    return float((right - left) * 1e3) if np.isfinite(left + right) else float("nan")


def point_resolution(image, x_grid, z_grid, target_x, target_z):
    x_mask = np.abs(x_grid - target_x) <= 2e-3
    z_mask = np.abs(z_grid - target_z) <= 1e-3
    local = image[np.ix_(z_mask, x_mask)]
    local_peak = np.unravel_index(np.argmax(local), local.shape)
    zi, xi = np.flatnonzero(z_mask)[local_peak[0]], np.flatnonzero(x_mask)[local_peak[1]]
    lateral = image[zi]
    axial = image[:, xi]
    width = fwhm(x_grid, lateral)
    peak = lateral[xi]
    mask = np.abs(x_grid - x_grid[xi]) > 1.5 * width * 1e-3 if np.isfinite(width) else np.zeros_like(x_grid, bool)
    psl = 20 * np.log10(np.max(lateral[mask]) / peak) if np.any(mask) and peak > 0 else float("nan")
    return {"lateral_fwhm_mm": width, "axial_fwhm_mm": fwhm(z_grid, axial), "psl_db": float(psl)}


def cyst_metrics(image, x_grid, z_grid, radius=4e-3, center=(0.0, 30e-3)):
    x, z = np.meshgrid(x_grid, z_grid)
    distance = np.hypot(x - center[0], z - center[1])
    inside = image[distance <= 0.6 * radius]
    outside = image[(distance >= 1.4 * radius) & (distance <= 2.0 * radius)]
    mu_in, mu_out = np.mean(inside), np.mean(outside)
    cr = 20 * np.log10(mu_out / mu_in) if mu_in > 0 else float("inf")
    cnr = abs(mu_in - mu_out) / np.sqrt(np.var(inside) + np.var(outside))
    return {"cr_db": float(cr), "cnr": float(cnr)}
