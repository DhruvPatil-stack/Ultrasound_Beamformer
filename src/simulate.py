"""Deterministic plane-wave RF channel simulator."""
import numpy as np

C = 1540.0
FS = 20.832e6
PITCH = 0.3e-3
F0 = 5.2e6
FRACTIONAL_BANDWIDTH = 0.6


def element_positions(n_elements=128, pitch=PITCH):
    return (np.arange(n_elements) - (n_elements - 1) / 2.0) * pitch


def _pulse(fs, f0, fractional_bandwidth):
    sigma = np.sqrt(2.0 * np.log(2.0)) / (np.pi * fractional_bandwidth * f0)
    time = np.arange(-3 * sigma, 3 * sigma + 1 / fs, 1 / fs)
    return time, np.exp(-(time ** 2) / (2 * sigma ** 2)) * np.cos(2 * np.pi * f0 * time)


def simulate_channels(scatterers, amplitudes, c=C, fs=FS, pitch=PITCH,
                      n_elements=128, f0=F0, fractional_bandwidth=FRACTIONAL_BANDWIDTH,
                      max_depth=65e-3, chunk_size=4096):
    """Simulate 0-degree plane-wave channels with a transmit time offset of zero."""
    scatterers = np.asarray(scatterers, dtype=float)
    amplitudes = np.asarray(amplitudes, dtype=float)
    if scatterers.ndim != 2 or scatterers.shape[1] != 2 or len(scatterers) != len(amplitudes):
        raise ValueError("scatterers must have shape (N, 2) with one amplitude per point")
    pulse_t, _ = _pulse(fs, f0, fractional_bandwidth)
    sigma = np.max(np.abs(pulse_t)) / 3.0
    support = int(np.ceil(3 * sigma * fs)) + 1
    n_samples = int(np.ceil(2 * max_depth / c * fs)) + 2 * support + 2
    rf = np.zeros((n_samples, n_elements), dtype=np.float64)
    elem_x = element_positions(n_elements, pitch)
    offsets = np.arange(-support, support + 1)
    for first in range(0, len(scatterers), chunk_size):
        points = scatterers[first:first + chunk_size]
        amp = amplitudes[first:first + chunk_size]
        distance = np.sqrt((points[:, None, 0] - elem_x[None, :]) ** 2 + points[:, None, 1] ** 2)
        tau = (points[:, None, 1] + distance) / c
        centers = np.floor(tau * fs).astype(int)
        samples = centers[:, :, None] + offsets[None, None, :]
        valid = (samples >= 0) & (samples < n_samples)
        channels = np.broadcast_to(np.arange(n_elements)[None, :, None], samples.shape)
        relative_time = samples / fs - tau[:, :, None]
        pulse = np.exp(-(relative_time ** 2) / (2 * sigma ** 2)) * np.cos(2 * np.pi * f0 * relative_time)
        values = amp[:, None, None] * pulse
        flat = channels[valid] * n_samples + samples[valid]
        rf += np.bincount(flat, weights=values[valid], minlength=n_samples * n_elements).reshape(n_elements, n_samples).T
    return rf


def phantom_points():
    """Return seven unit-amplitude point targets in metres."""
    points = [(0.037e-3, z * 1e-3 + 0.013e-3) for z in (10, 20, 30, 40, 50)]
    points += [(-5.963e-3, 30.013e-3), (6.037e-3, 30.013e-3)]
    return np.asarray(points), np.ones(7)


def phantom_cyst(seed=42, scatterers_per_resolution_cell=10):
    """Return a seeded speckle phantom with a 4 mm anechoic cyst."""
    rng = np.random.default_rng(seed)
    wavelength = C / F0
    axial_resolution = C / (F0 * FRACTIONAL_BANDWIDTH)
    area = (30e-3) * (30e-3)
    count = int(np.ceil(scatterers_per_resolution_cell * area / (wavelength * axial_resolution)))
    candidates = np.column_stack((rng.uniform(-15e-3, 15e-3, count * 2), rng.uniform(15e-3, 45e-3, count * 2)))
    radius = np.hypot(candidates[:, 0], candidates[:, 1] - 30e-3)
    points = candidates[radius > 4e-3][:count]
    amplitudes = rng.standard_normal(len(points))
    return points, amplitudes
