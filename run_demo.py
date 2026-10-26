"""Run deterministic DAS ablation on local point and cyst phantoms."""
import argparse
import csv
import json
import time
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.beamform import beamform_das
from src.bmode import to_db
from src.compound import compound_das
from src.legacy_das import legacy_das
from src.metrics import cyst_metrics, point_position_error, point_resolution, shallow_clutter_db
from src.simulate import C, FS, PITCH, phantom_cyst, phantom_points, simulate_channels

X = np.arange(-20e-3, 20.0001e-3, 0.1e-3)
Z = np.arange(5e-3, 60.0001e-3, 0.05e-3)
CYST_X = np.arange(-15e-3, 15.0001e-3, 0.1e-3)
CYST_Z = np.arange(15e-3, 45.0001e-3, 0.05e-3)
F_ANGLES = [-12.0, -6.0, 0.0, 6.0, 12.0]
G_ANGLES = list(np.arange(-15.0, 15.1, 3.0))
CONFIGS = {
    "legacy": None,
    "A": {"interp": "nearest", "apod": "none", "fnum": None, "upsample": 1},
    "B": {"interp": "linear", "apod": "none", "fnum": None, "upsample": 1},
    "C": {"interp": "linear", "apod": "hann", "fnum": None, "upsample": 1},
    "D": {"interp": "linear", "apod": "hann", "fnum": 1.5, "upsample": 1},
    "E": {"interp": "linear", "apod": "none", "fnum": None, "upsample": 4},
    "F": {"interp": "linear", "apod": "hann", "fnum": None, "upsample": 1, "angles": F_ANGLES},
    "G": {"interp": "linear", "apod": "hann", "fnum": None, "upsample": 1, "angles": G_ANGLES},
}


def _beamform(rf_cache, config, x=X, z=Z):
    """Beamform a single acquisition or coherently compound cached angles."""
    if config is None:
        return legacy_das(rf_cache[0.0], C, FS, PITCH, x, z)
    options = {key: value for key, value in config.items() if key != "angles"}
    angles = config.get("angles")
    if angles is None:
        return beamform_das(rf_cache[0.0], C, FS, PITCH, x, z, **options)
    return compound_das([rf_cache[angle] for angle in angles], angles, C, FS, PITCH, x, z, **options)


def _plot_bmode(image, x, z, path, title):
    """Render a B-mode image on its physical axes."""
    fig, ax = plt.subplots(figsize=(6, 7))
    shown = ax.imshow(to_db(image), cmap="gray", extent=[x[0] * 1e3, x[-1] * 1e3, z[-1] * 1e3, z[0] * 1e3], aspect="auto", vmin=-60, vmax=0)
    ax.set(xlabel="Lateral position (mm)", ylabel="Depth (mm)", title=title)
    ax.set_xlim(-15, 15); ax.set_ylim(45, 15)
    fig.colorbar(shown, ax=ax, label="Amplitude (dB)")
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def _write_readme_table(rows):
    """Replace the generated ablation table without changing surrounding prose."""
    table = ["| Config | FWHM (mm, -6 dB) | ISLR (dB) | PSL (dB) | Shallow clutter (dB) | CR (dB, mean +/- std) | CNR (mean +/- std) |", "|---|---:|---:|---:|---:|---:|---:|"]
    table += [f"| {r['config']} | {r['lateral_fwhm_mm']:.4f} | {r['islr_db']:.2f} | {r['psl_db']:.2f} | {r['shallow_clutter_db']:.2f} | {r['cr_mean_db']:.2f} +/- {r['cr_std_db']:.2f} | {r['cnr_mean']:.3f} +/- {r['cnr_std']:.3f} |" for r in rows]
    readme = Path("README.md"); text = readme.read_text(encoding="utf-8")
    before, _, after = text.partition("<!-- RESULTS:START -->"); _, _, after = after.partition("<!-- RESULTS:END -->")
    readme.write_text(before + "<!-- RESULTS:START -->\n" + "\n".join(table) + "\n<!-- RESULTS:END -->" + after, encoding="utf-8")


def _rf_cache(locations, amplitudes, angles):
    """Simulate each requested angle once for this phantom realization."""
    return {angle: simulate_channels(locations, amplitudes, angle=angle) for angle in sorted(set(angles))}


def _run_quick():
    """Measure cyst contrast for C and G without modifying release results."""
    started = datetime.now().astimezone().isoformat()
    timer = time.perf_counter()
    results_dir = Path("results_quick")
    figures_dir = Path("figures_quick")
    results_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)
    seeds = (0, 1)
    names = ("C", "G")
    values = {name: [] for name in names}
    for seed in seeds:
        locations, amplitudes = phantom_cyst(seed=seed)
        rf_cache = _rf_cache(locations, amplitudes, [0.0, *G_ANGLES])
        for name in names:
            image = _beamform(rf_cache, CONFIGS[name], CYST_X, CYST_Z)
            values[name].append({"seed": seed, **cyst_metrics(image, CYST_X, CYST_Z)})
            if seed == seeds[0]:
                _plot_bmode(image, CYST_X, CYST_Z,
                            figures_dir / f"cyst_{name}.png",
                            f"Quick cyst phantom: config {name}, seed {seed}")
    rows = []
    for name in names:
        cr = np.array([value["cr_db"] for value in values[name]])
        cnr = np.array([value["cnr"] for value in values[name]])
        rows.append({"config": name, "cr_mean_db": float(cr.mean()),
                     "cr_std_db": float(cr.std(ddof=1)),
                     "cnr_mean": float(cnr.mean()), "cnr_std": float(cnr.std(ddof=1))})
    with (results_dir / "ablation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    measured = {"mode": "quick", "seeds": list(seeds),
                "summary": rows, "per_seed": values}
    (results_dir / "metrics.json").write_text(
        json.dumps(measured, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    elapsed = time.perf_counter() - timer
    (results_dir / "runtime.json").write_text(
        json.dumps({"started": started, "elapsed_seconds": elapsed}, indent=2) + "\n",
        encoding="utf-8")


def main(quick=False):
    if quick:
        return _run_quick()
    started = datetime.now().astimezone().isoformat(); timer = time.perf_counter()
    Path("results").mkdir(exist_ok=True); Path("figures").mkdir(exist_ok=True)
    point_locations, point_amplitudes = phantom_points(); all_angles = [0.0, *F_ANGLES, *G_ANGLES]
    point_rf = _rf_cache(point_locations, point_amplitudes, all_angles)
    fig, ax = plt.subplots(figsize=(7, 6))
    shown = ax.imshow(point_rf[0.0], extent=[0, point_rf[0.0].shape[1] - 1, point_rf[0.0].shape[0] / FS * 1e6, 0], aspect="auto", cmap="seismic")
    ax.set(xlabel="Element index", ylabel="Time (microseconds)", title="Point phantom channel data")
    fig.colorbar(shown, ax=ax, label="Amplitude"); fig.tight_layout(); fig.savefig("figures/channel_data.png", dpi=150); plt.close(fig)
    point_images = {name: _beamform(point_rf, config) for name, config in CONFIGS.items()}
    target_x, target_z = point_locations[2]
    x_fine = np.arange(target_x - 2e-3, target_x + 2.0001e-3, 0.025e-3); z_fine = np.arange(target_z - 2e-3, target_z + 2.0001e-3, 0.025e-3)
    fine_point_images = {name: _beamform(point_rf, config, x_fine, z_fine) for name, config in CONFIGS.items()}
    rows, measured = [], {}; cyst_values = {name: [] for name in CONFIGS}; cyst_images = {}
    for seed in range(5):
        locations, amplitudes = phantom_cyst(seed=seed); cyst_rf = _rf_cache(locations, amplitudes, all_angles)
        for name, config in CONFIGS.items():
            image = _beamform(cyst_rf, config, CYST_X, CYST_Z); cyst_values[name].append(cyst_metrics(image, CYST_X, CYST_Z))
            if seed == 0: cyst_images[name] = image
    for name in CONFIGS:
        resolution = point_resolution(fine_point_images[name], x_fine, z_fine, target_x, target_z)
        errors = [point_position_error(point_images[name], X, Z, px, pz) for px, pz in point_locations]
        cr = np.array([value["cr_db"] for value in cyst_values[name]]); cnr = np.array([value["cnr"] for value in cyst_values[name]])
        row = {"config": name, **resolution, "shallow_clutter_db": shallow_clutter_db(point_images[name], X, Z), "cr_mean_db": float(cr.mean()), "cr_std_db": float(cr.std(ddof=1)), "cnr_mean": float(cnr.mean()), "cnr_std": float(cnr.std(ddof=1))}
        rows.append(row); measured[name] = {**row, "point_errors_mm": errors}
    with open("results/ablation.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    Path("results/metrics.json").write_text(json.dumps(measured, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    _plot_bmode(point_images["C"], X, Z, "figures/points_bmode.png", "Point phantom: config C")
    _plot_bmode(cyst_images["C"], CYST_X, CYST_Z, "figures/cyst_bmode.png", "Cyst phantom: config C")
    fig, axes = plt.subplots(1, len(CONFIGS), figsize=(24, 5), sharey=True)
    for ax, name in zip(axes, CONFIGS):
        ax.imshow(to_db(point_images[name]), cmap="gray", extent=[X[0] * 1e3, X[-1] * 1e3, Z[-1] * 1e3, Z[0] * 1e3], aspect="auto", vmin=-60, vmax=0); ax.set(title=name, xlabel="Lateral (mm)")
    axes[0].set_ylabel("Depth (mm)"); fig.tight_layout(); fig.savefig("figures/ablation_panel.png", dpi=150); plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for ax, name in zip(axes, ("C", "F", "G")):
        ax.imshow(to_db(cyst_images[name]), cmap="gray", extent=[CYST_X[0] * 1e3, CYST_X[-1] * 1e3, CYST_Z[-1] * 1e3, CYST_Z[0] * 1e3], aspect="auto", vmin=-60, vmax=0); ax.set(title=name, xlabel="Lateral (mm)")
    axes[0].set_ylabel("Depth (mm)"); fig.tight_layout(); fig.savefig("figures/compounding_panel.png", dpi=150); plt.close(fig)
    zi = np.argmin(abs(Z - 30e-3)); fig, ax = plt.subplots(figsize=(7, 4))
    for name in ("C", "G"):
        profile = point_images[name][zi] / point_images[name][zi].max(); ax.plot(X * 1e3, 20 * np.log10(np.maximum(profile, 1e-12)), label=name)
    ax.set(xlabel="Lateral position (mm)", ylabel="Relative amplitude (dB)", ylim=(-60, 2), title="Lateral profile at 30 mm"); ax.legend(); fig.tight_layout(); fig.savefig("figures/compounding_profile.png", dpi=150); plt.close(fig)
    speed = {}
    for assumed_c in (1500.0, 1540.0, 1580.0):
        image = beamform_das(point_rf[0.0], assumed_c, FS, PITCH, x_fine, z_fine, interp="linear", apod="none", fnum=None)
        error = point_position_error(image, x_fine, z_fine, target_x, target_z); resolution = point_resolution(image, x_fine, z_fine, target_x, target_z)
        speed[str(int(assumed_c))] = {"predicted_axial_shift_mm": target_z * (assumed_c / C - 1.0) * 1e3, "axial_shift_mm": error["estimated_z_mm"] - target_z * 1e3, "lateral_fwhm_mm": resolution["lateral_fwhm_mm"]}
    Path("results/sound_speed.json").write_text(json.dumps(speed, indent=2) + "\n", encoding="utf-8")
    elapsed = time.perf_counter() - timer; Path("results/runtime.json").write_text(json.dumps({"started": started, "elapsed_seconds": elapsed}, indent=2) + "\n", encoding="utf-8")
    _write_readme_table(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true",
                        help="Run only cyst configs C and G for seeds 0 and 1; write to *_quick folders.")
    args = parser.parse_args()
    main(quick=args.quick)
