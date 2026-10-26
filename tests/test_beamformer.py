import numpy as np

from src.beamform import beamform_das, compute_tof
from src.metrics import point_position_error, point_resolution
from src.simulate import C, F0, FS, PITCH, phantom_points, simulate_channels


TARGET = np.array([0.037e-3, 30.013e-3])


def _off_grid_point_image():
    rf = simulate_channels(TARGET[None, :], np.array([1.0]))
    x = np.arange(-4e-3, 4.0001e-3, 0.025e-3)
    z = np.arange(28e-3, 32.0001e-3, 0.025e-3)
    return beamform_das(rf, C, FS, PITCH, x, z, interp="linear", apod="none", fnum=None), x, z


def test_compute_tof_hand_value():
    value = compute_tof(np.array([[0.0]]), np.array([[10e-3]]), np.array([0.0]), C)[0, 0, 0]
    assert value == 20e-3 / C


def test_off_grid_point_position():
    image, x, z = _off_grid_point_image()
    error = point_position_error(image, x, z, *TARGET)
    assert error["lateral_mm"] <= 0.2
    assert error["axial_mm"] <= 0.1


def test_off_grid_position_is_parabolically_estimated():
    image, x, z = _off_grid_point_image()
    error = point_position_error(image, x, z, *TARGET)
    assert error["estimated_x_mm"] != x[np.argmin(abs(x - TARGET[0]))] * 1e3


def test_lateral_resolution_theory_band():
    image, x, z = _off_grid_point_image()
    measured = point_resolution(image, x, z, *TARGET)["lateral_fwhm_mm"]
    theory = (C / F0) * (30e-3 / (127 * PITCH)) * 1e3
    assert 0.6 * theory <= measured <= 1.4 * theory


def test_outside_samples_are_zero_and_safe():
    rf = simulate_channels(np.array([[0.0, 10e-3]]), np.array([1.0]))
    image = beamform_das(rf, C, FS, PITCH, np.array([0.0]), np.array([80e-3]), fnum=None, apod="none")
    assert image[0, 0] == 0.0


def test_seeded_cyst_is_repeatable():
    from src.simulate import phantom_cyst
    first = phantom_cyst(seed=42)
    second = phantom_cyst(seed=42)
    assert np.array_equal(first[0], second[0])
    assert np.array_equal(first[1], second[1])


def test_fractional_path_shift_changes_channel_signal():
    base = simulate_channels(np.array([[0.0, 30e-3]]), np.array([1.0]))
    shifted_depth = 30e-3 + C / (8 * FS)
    shifted = simulate_channels(np.array([[0.0, shifted_depth]]), np.array([1.0]))
    assert np.max(np.abs(base[:, 64] - shifted[:, 64])) > 0.0


def test_sound_speed_error_shifts_the_axial_peak_in_expected_direction():
    rf = simulate_channels(TARGET[None, :], np.array([1.0]))
    x = np.arange(-2e-3, 2.0001e-3, 0.025e-3)
    z = np.arange(28e-3, 32.0001e-3, 0.025e-3)
    low = beamform_das(rf, 1500.0, FS, PITCH, x, z, interp="linear", apod="none", fnum=None)
    high = beamform_das(rf, 1580.0, FS, PITCH, x, z, interp="linear", apod="none", fnum=None)
    low_error = point_position_error(low, x, z, *TARGET)
    high_error = point_position_error(high, x, z, *TARGET)
    assert low_error["estimated_z_mm"] < TARGET[1] * 1e3 < high_error["estimated_z_mm"]
