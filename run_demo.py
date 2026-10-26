"""Run deterministic DAS ablation on local point and cyst phantoms."""
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.beamform import beamform_das
from src.bmode import to_db
from src.legacy_das import legacy_das
from src.metrics import cyst_metrics, point_position_error, point_resolution
from src.simulate import C, FS, PITCH, phantom_cyst, phantom_points, simulate_channels

X = np.arange(-20e-3, 20.0001e-3, 0.1e-3)
Z = np.arange(5e-3, 60.0001e-3, 0.05e-3)
CONFIGS = {
    "legacy": None,
    "A": {"interp": "nearest", "apod": "none", "fnum": None, "upsample": 1},
    "B": {"interp": "linear", "apod": "none", "fnum": None, "upsample": 1},
    "C": {"interp": "linear", "apod": "hann", "fnum": None, "upsample": 1},
    "D": {"interp": "linear", "apod": "hann", "fnum": 1.5, "upsample": 1},
}


def _beamform(rf, config, x=X, z=Z):
    return legacy_das(rf, C, FS, PITCH, x, z) if config is None else beamform_das(rf, C, FS, PITCH, x, z, **config)


def _plot_bmode(image, path, title):
    fig, ax = plt.subplots(figsize=(6, 7))
    shown = ax.imshow(to_db(image), cmap="gray", extent=[X[0] * 1e3, X[-1] * 1e3, Z[-1] * 1e3, Z[0] * 1e3], aspect="auto", vmin=-60, vmax=0)
    ax.set(xlabel="Lateral position (mm)", ylabel="Depth (mm)", title=title)
    ax.set_xlim(-15, 15); ax.set_ylim(45, 15)
    fig.colorbar(shown, ax=ax, label="Amplitude (dB)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _write_readme_table(rows):
    table = ["| Config | FWHM (mm, -6 dB) | ISLR (dB) | PSL (dB) | CR (dB, mean +/- std) | CNR (mean +/- std) |", "|---|---:|---:|---:|---:|---:|"]
    table += [f"| {r['config']} | {r['lateral_fwhm_mm']:.4f} | {r['islr_db']:.2f} | {r['psl_db']:.2f} | {r['cr_mean_db']:.2f} +/- {r['cr_std_db']:.2f} | {r['cnr_mean']:.3f} +/- {r['cnr_std']:.3f} |" for r in rows]
    readme = Path("README.md")
    text = readme.read_text(encoding="utf-8")
    before, _, after = text.partition("<!-- RESULTS:START -->")
    _, _, after = after.partition("<!-- RESULTS:END -->")
    readme.write_text(before + "<!-- RESULTS:START -->\n" + "\n".join(table) + "\n<!-- RESULTS:END -->" + after, encoding="utf-8")


def main():
    Path("results").mkdir(exist_ok=True)
    Path("figures").mkdir(exist_ok=True)
    point_locations, point_amplitudes = phantom_points()
    point_rf = simulate_channels(point_locations, point_amplitudes)
    fig, ax = plt.subplots(figsize=(7, 6))
    shown = ax.imshow(point_rf, extent=[0, point_rf.shape[1] - 1, point_rf.shape[0] / FS * 1e6, 0], aspect="auto", cmap="seismic")
    ax.set(xlabel="Element index", ylabel="Time (microseconds)", title="Point phantom channel data")
    fig.colorbar(shown, ax=ax, label="Amplitude")
    fig.tight_layout(); fig.savefig("figures/channel_data.png", dpi=150); plt.close(fig)
    point_images = {name: _beamform(point_rf, config) for name, config in CONFIGS.items()}
    target_x, target_z = point_locations[2]
    x_fine = np.arange(target_x - 2e-3, target_x + 2.0001e-3, 0.025e-3)
    z_fine = np.arange(target_z - 2e-3, target_z + 2.0001e-3, 0.025e-3)
    fine_point_images = {name: _beamform(point_rf, config, x_fine, z_fine) for name, config in CONFIGS.items()}
    rows, measured = [], {}
    cyst_values = {name: [] for name in CONFIGS}
    cyst_images = {}
    for seed in range(5):
        cyst_locations, cyst_amplitudes = phantom_cyst(seed=seed)
        cyst_rf = simulate_channels(cyst_locations, cyst_amplitudes)
        for name, config in CONFIGS.items():
            image = _beamform(cyst_rf, config)
            cyst_values[name].append(cyst_metrics(image, X, Z))
            if seed == 0:
                cyst_images[name] = image
    for name in CONFIGS:
        resolution = point_resolution(fine_point_images[name], x_fine, z_fine, target_x, target_z)
        errors = [point_position_error(point_images[name], X, Z, px, pz) for px, pz in point_locations]
        cr = np.array([value["cr_db"] for value in cyst_values[name]])
        cnr = np.array([value["cnr"] for value in cyst_values[name]])
        row = {"config": name, **resolution, "cr_mean_db": float(cr.mean()), "cr_std_db": float(cr.std(ddof=1)), "cnr_mean": float(cnr.mean()), "cnr_std": float(cnr.std(ddof=1))}
        rows.append(row)
        measured[name] = {**row, "point_errors_mm": errors}
    with open("results/ablation.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    Path("results/metrics.json").write_text(json.dumps(measured, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    _plot_bmode(point_images["D"], "figures/points_bmode.png", "Point phantom: config D")
    _plot_bmode(cyst_images["D"], "figures/cyst_bmode.png", "Cyst phantom: config D")
    fig, axes = plt.subplots(1, 5, figsize=(16, 5), sharey=True)
    for ax, name in zip(axes, CONFIGS):
        ax.imshow(to_db(point_images[name]), cmap="gray", extent=[X[0] * 1e3, X[-1] * 1e3, Z[-1] * 1e3, Z[0] * 1e3], aspect="auto", vmin=-60, vmax=0)
        ax.set(title=name, xlabel="Lateral (mm)")
    axes[0].set_ylabel("Depth (mm)")
    fig.tight_layout(); fig.savefig("figures/ablation_panel.png", dpi=150); plt.close(fig)
    zi = np.argmin(abs(Z - target_z))
    fig, ax = plt.subplots(figsize=(7, 4))
    for name in ("legacy", "D"):
        profile = point_images[name][zi] / point_images[name][zi].max()
        ax.plot(X * 1e3, 20 * np.log10(np.maximum(profile, 1e-12)), label=name)
    ax.set(xlabel="Lateral position (mm)", ylabel="Relative amplitude (dB)", ylim=(-60, 2), title="Lateral profile at target depth")
    ax.legend(); fig.tight_layout(); fig.savefig("figures/lateral_profile.png", dpi=150); plt.close(fig)
    speed = {}
    for assumed_c in (1500.0, 1540.0, 1580.0):
        image = beamform_das(point_rf, assumed_c, FS, PITCH, x_fine, z_fine, interp="linear", apod="none", fnum=None)
        error = point_position_error(image, x_fine, z_fine, target_x, target_z)
        resolution = point_resolution(image, x_fine, z_fine, target_x, target_z)
        speed[str(int(assumed_c))] = {"axial_shift_mm": error["estimated_z_mm"] - target_z * 1e3, "lateral_fwhm_mm": resolution["lateral_fwhm_mm"]}
    Path("results/sound_speed.json").write_text(json.dumps(speed, indent=2) + "\n", encoding="utf-8")
    _write_readme_table(rows)


if __name__ == "__main__":
    main()
