import numpy as np

from src.beamform import beamform_das, compute_tof
from src.metrics import point_position_error, point_resolution
from src.simulate import C, F0, FS, PITCH, phantom_points, simulate_channels


def _centered_point_image():
    rf = simulate_channels(np.array([[0.0, 30e-3]]), np.array([1.0]))
    x = np.arange(-4e-3, 4.0001e-3, 0.025e-3)
    z = np.arange(28e-3, 32.0001e-3, 0.025e-3)
    return beamform_das(rf, C, FS, PITCH, x, z, interp="linear", apod="none", fnum=None), x, z


def test_compute_tof_hand_value():
    value = compute_tof(np.array([[0.0]]), np.array([[10e-3]]), np.array([0.0]), C)[0, 0, 0]
    assert value == 20e-3 / C


def test_center_point_position():
    image, x, z = _centered_point_image()
    error = point_position_error(image, x, z, 0.0, 30e-3)
    assert error["lateral_mm"] <= 0.2
    assert error["axial_mm"] <= 0.1


def test_center_point_symmetry():
    image, x, _ = _centered_point_image()
    assert abs(x[np.argmax(image[np.argmax(image.max(axis=1))])]) < 1e-12


def test_lateral_resolution_theory_band():
    image, x, z = _centered_point_image()
    measured = point_resolution(image, x, z, 0.0, 30e-3)["lateral_fwhm_mm"]
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
