import numpy as np

from src.beamform import beamform_das, compute_tof, transmit_time_offset
from src.compound import compound_das
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
    assert error["lateral_mm"] <= 0.05
    assert error["axial_mm"] <= 0.02


def test_off_grid_position_is_parabolically_estimated():
    image, x, z = _off_grid_point_image()
    error = point_position_error(image, x, z, *TARGET)
    assert error["estimated_x_mm"] != x[np.argmin(abs(x - TARGET[0]))] * 1e3


def test_lateral_resolution_theory_band():
    image, x, z = _off_grid_point_image()
    measured = point_resolution(image, x, z, *TARGET)["lateral_fwhm_mm"]
    theory = 1.206 * (C / F0) * (30e-3 / (127 * PITCH)) * 1e3
    assert 0.75 * theory <= measured <= 1.25 * theory


def test_upsample_four_preserves_off_grid_position():
    rf = simulate_channels(TARGET[None, :], np.array([1.0]))
    x = np.arange(-4e-3, 4.0001e-3, 0.025e-3)
    z = np.arange(28e-3, 32.0001e-3, 0.025e-3)
    image = beamform_das(rf, C, FS, PITCH, x, z, interp="linear", apod="none", fnum=None, upsample=4)
    error = point_position_error(image, x, z, *TARGET)
    assert error["lateral_mm"] <= 0.05
    assert error["axial_mm"] <= 0.02


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
    for assumed_c, error in ((1500.0, low_error), (1580.0, high_error)):
        measured = error["estimated_z_mm"] - TARGET[1] * 1e3
        predicted = TARGET[1] * (assumed_c / C - 1.0) * 1e3
        assert abs(measured - predicted) <= 0.1 * abs(predicted)


def test_compute_tof_angle_fifteen_hand_value():
    angle, x, z, element = 15.0, 1e-3, 10e-3, -0.15e-3
    expected = ((x * np.sin(np.deg2rad(angle)) + z * np.cos(np.deg2rad(angle))
                 + np.sqrt((x - element) ** 2 + z ** 2)) / C
                + transmit_time_offset(angle, C))
    actual = compute_tof(np.array([[x]]), np.array([[z]]), np.array([element]), C, angle=angle)[0, 0, 0]
    assert actual == expected


def test_angle_zero_image_matches_previous_call():
    rf = simulate_channels(TARGET[None, :], np.array([1.0]))
    x = np.arange(-2e-3, 2.0001e-3, 0.05e-3)
    z = np.arange(28e-3, 32.0001e-3, 0.05e-3)
    old_call = beamform_das(rf, C, FS, PITCH, x, z, interp="linear", apod="none", fnum=None)
    angled_call = beamform_das(rf, C, FS, PITCH, x, z, interp="linear", apod="none", fnum=None, angle=0.0)
    assert np.allclose(old_call, angled_call)


def test_one_angle_compounding_matches_single_angle():
    rf = simulate_channels(TARGET[None, :], np.array([1.0]))
    x = np.arange(-2e-3, 2.0001e-3, 0.05e-3)
    z = np.arange(28e-3, 32.0001e-3, 0.05e-3)
    single = beamform_das(rf, C, FS, PITCH, x, z, interp="linear", apod="hann", fnum=None)
    compound = compound_das([rf], [0.0], C, FS, PITCH, x, z, interp="linear", apod="hann", fnum=None)
    assert np.allclose(single, compound)


def test_steered_and_compounded_off_grid_positions():
    angles = [-12.0, -6.0, 0.0, 6.0, 12.0]
    x = np.arange(-4e-3, 4.0001e-3, 0.025e-3)
    z = np.arange(28e-3, 32.0001e-3, 0.025e-3)
    rf_15 = simulate_channels(TARGET[None, :], np.array([1.0]), angle=15.0)
    steered = beamform_das(rf_15, C, FS, PITCH, x, z, interp="linear", apod="hann", fnum=None, angle=15.0)
    rfs = [simulate_channels(TARGET[None, :], np.array([1.0]), angle=angle) for angle in angles]
    compounded = compound_das(rfs, angles, C, FS, PITCH, x, z, interp="linear", apod="hann", fnum=None)
    for image in (steered, compounded):
        error = point_position_error(image, x, z, *TARGET)
        assert error["lateral_mm"] <= 0.05
        assert error["axial_mm"] <= 0.02


def test_simulated_angles_are_repeatable():
    from src.simulate import phantom_cyst
    points, amplitudes = phantom_cyst(seed=7, scatterers_per_resolution_cell=0.01)
    for angle in (-12.0, 0.0, 12.0):
        assert np.array_equal(simulate_channels(points, amplitudes, angle=angle),
                              simulate_channels(points, amplitudes, angle=angle))
