"""Measured image-quality metrics."""
import numpy as np


def _parabolic_coordinate(coord, values, index):
    if index == 0 or index == len(values) - 1:
        return float(coord[index])
    left, center, right = values[index - 1:index + 2]
    denominator = left - 2 * center + right
    offset = 0.5 * (left - right) / denominator if denominator != 0 else 0.0
    return float(coord[index] + offset * (coord[index + 1] - coord[index]))


def point_position_error(image, x_grid, z_grid, target_x, target_z, lateral_window=2e-3, axial_window=1e-3):
    x_mask = np.abs(x_grid - target_x) <= lateral_window
    z_mask = np.abs(z_grid - target_z) <= axial_window
    local = image[np.ix_(z_mask, x_mask)]
    local_peak = np.unravel_index(np.argmax(local), local.shape)
    peak = (np.flatnonzero(z_mask)[local_peak[0]], np.flatnonzero(x_mask)[local_peak[1]])
    estimated_x = _parabolic_coordinate(x_grid, image[peak[0]], peak[1])
    estimated_z = _parabolic_coordinate(z_grid, image[:, peak[1]], peak[0])
    return {"lateral_mm": float(abs(estimated_x - target_x) * 1e3), "axial_mm": float(abs(estimated_z - target_z) * 1e3), "estimated_x_mm": estimated_x * 1e3, "estimated_z_mm": estimated_z * 1e3}


def _crossing(coord, values, peak_index, side):
    threshold = values[peak_index] / 2.0
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


def _first_null(values, peak, direction):
    indices = range(peak - 1, 0, -1) if direction == "left" else range(peak + 1, len(values) - 1)
    for index in indices:
        if values[index] <= values[index - 1] and values[index] <= values[index + 1]:
            return index
    return 0 if direction == "left" else len(values) - 1


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
    inside = np.abs(x_grid - x_grid[xi]) <= 1.5 * width * 1e-3 if np.isfinite(width) else np.zeros_like(x_grid, bool)
    outside = ~inside
    islr = 10 * np.log10(np.sum(lateral[outside] ** 2) / np.sum(lateral[inside] ** 2)) if np.any(outside) else float("nan")
    left_null, right_null = _first_null(lateral, xi, "left"), _first_null(lateral, xi, "right")
    null_outside = np.ones_like(lateral, dtype=bool)
    null_outside[left_null:right_null + 1] = False
    psl = 20 * np.log10(np.max(lateral[null_outside]) / peak) if np.any(null_outside) and peak > 0 else float("nan")
    return {"lateral_fwhm_mm": width, "axial_fwhm_mm": fwhm(z_grid, axial), "islr_db": float(islr), "psl_db": float(psl), "first_nulls_mm": [float(x_grid[left_null] * 1e3), float(x_grid[right_null] * 1e3)]}


def cyst_metrics(image, x_grid, z_grid, radius=4e-3, center=(0.0, 30e-3)):
    x, z = np.meshgrid(x_grid, z_grid)
    distance = np.hypot(x - center[0], z - center[1])
    inside = image[distance <= 0.6 * radius]
    outside = image[(distance >= 1.4 * radius) & (distance <= 2.0 * radius)]
    mu_in, mu_out = np.mean(inside), np.mean(outside)
    cr = 20 * np.log10(mu_out / mu_in) if mu_in > 0 else float("inf")
    cnr = abs(mu_in - mu_out) / np.sqrt(np.var(inside) + np.var(outside))
    return {"cr_db": float(cr), "cnr": float(cnr)}


def shallow_clutter_db(image, x_grid, z_grid):
    """Measure the specified shallow off-axis patch relative to the image peak."""
    x, z = np.meshgrid(x_grid, z_grid)
    patch = image[(z >= 8e-3) & (z <= 14e-3) & (np.abs(x) >= 14e-3) & (np.abs(x) <= 19e-3)]
    peak = np.max(image)
    return float(20 * np.log10(np.mean(patch) / peak)) if len(patch) and peak > 0 else float("nan")
