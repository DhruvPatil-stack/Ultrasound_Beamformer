"""Render README measurement and theory sections from recorded result files."""
import csv
import argparse
import json
import math
from pathlib import Path

from src.simulate import C
from run_demo import G_ANGLES, Z


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def _read_results():
    with (ROOT / "results/ablation.csv").open(newline="", encoding="utf-8") as handle:
        rows = {row["config"]: row for row in csv.DictReader(handle)}
    sound_speed = json.loads((ROOT / "results/sound_speed.json").read_text(encoding="utf-8"))
    runtime = json.loads((ROOT / "results/runtime.json").read_text(encoding="utf-8"))
    return rows, sound_speed, runtime


def _f(row, key):
    return float(row[key])


def _build_section(rows, sound_speed, runtime):
    lines = [
        "## Findings",
        "",
        "The table reports measured results from the seeded ablation. FWHM is",
        "measured at -6 dB. CR and CNR are means with sample standard deviations.",
        "The table values are rendered from `results/ablation.csv`.",
        "",
        "| Config | FWHM (mm, -6 dB) | ISLR (dB) | PSL (dB) | Shallow clutter (dB) | CR (dB, mean +/- std) | CNR (mean +/- std) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, row in rows.items():
        lines.append(
            f"| {name} | {_f(row, 'lateral_fwhm_mm'):.4f} | {_f(row, 'islr_db'):.2f} | "
            f"{_f(row, 'psl_db'):.2f} | {_f(row, 'shallow_clutter_db'):.2f} | "
            f"{_f(row, 'cr_mean_db'):.2f} +/- {_f(row, 'cr_std_db'):.2f} | "
            f"{_f(row, 'cnr_mean'):.3f} +/- {_f(row, 'cnr_std'):.3f} |"
        )

    a, b, c, e, f, g = (rows[k] for k in ("A", "B", "C", "E", "F", "G"))
    lines += [
        "",
        "Config A (nearest sampling) and config B (linear interpolation) have",
        f"similar measured lateral FWHM ({_f(a, 'lateral_fwhm_mm'):.4f} and {_f(b, 'lateral_fwhm_mm'):.4f} mm). "
        f"B raises CR by {_f(b, 'cr_mean_db') - _f(a, 'cr_mean_db'):.2f} dB and CNR by "
        f"{_f(b, 'cnr_mean') - _f(a, 'cnr_mean'):.3f} relative to A.",
        "",
        f"Config C adds Hann weighting to B: lateral FWHM widens by "
        f"{_f(c, 'lateral_fwhm_mm') - _f(b, 'lateral_fwhm_mm'):.4f} mm, while PSL "
        f"improves by {abs(_f(c, 'psl_db') - _f(b, 'psl_db')):.2f} dB.",
        "",
        "Config E adds fourfold upsampling to the linear, unweighted config B: "
        f"CR rises by {_f(e, 'cr_mean_db') - _f(b, 'cr_mean_db'):.2f} dB and CNR by "
        f"{_f(e, 'cnr_mean') - _f(b, 'cnr_mean'):.3f}; lateral FWHM changes by "
        f"{_f(e, 'lateral_fwhm_mm') - _f(b, 'lateral_fwhm_mm'):+.4f} mm.",
        "",
        "The legacy/A comparison is consistent with no clear image-quality gain "
        "from Hilbert-before-sum in this dataset. It does not isolate Hilbert "
        "placement from the other implementation differences.",
        "",
        "Relative to single-angle config C, five-angle config F changes measured "
        f"CR by {_f(f, 'cr_mean_db') - _f(c, 'cr_mean_db'):+.2f} dB, CNR by "
        f"{_f(f, 'cnr_mean') - _f(c, 'cnr_mean'):+.3f}, and shallow clutter by "
        f"{_f(f, 'shallow_clutter_db') - _f(c, 'shallow_clutter_db'):.2f} dB. "
        "Eleven-angle config G changes those metrics by "
        f"{_f(g, 'cr_mean_db') - _f(c, 'cr_mean_db'):+.2f} dB, "
        f"{_f(g, 'cnr_mean') - _f(c, 'cnr_mean'):+.3f}, and "
        f"{_f(g, 'shallow_clutter_db') - _f(c, 'shallow_clutter_db'):.2f} dB.",
        "",
        "## Sound-speed robustness",
        "",
        "The expected displacement is `dz = z (c_assumed / c_true - 1)`. "
        "Recorded values below are generated from `results/sound_speed.json`.",
        "",
        "| Assumed speed (m/s) | Predicted shift (mm) | Measured shift (mm) |",
        "|---:|---:|---:|",
    ]
    for speed, result in sound_speed.items():
        if speed == "1540":
            continue
        lines.append(f"| {speed} | {result['predicted_axial_shift_mm']:.4f} | {result['axial_shift_mm']:.4f} |")

    ideal_prf = C / (2 * float(max(Z)))
    rayleigh_cnr = math.sqrt(math.pi / (4 - math.pi))
    angle_limit = max(abs(float(angle)) for angle in G_ANGLES)
    lines += [
        "",
        "## Compounding",
        "",
        f"The implementation evaluates steering angles through +/-{angle_limit:g} degrees. "
        "The measured results show the contrast, CNR, and shallow-clutter changes "
        "above. The recorded full demo took "
        f"{float(runtime['elapsed_seconds']):.4f} seconds; its measurements are "
        "preserved in `results/`.",
        "",
        "## Limitations",
        "",
        "- Simulated static phantoms only; tissue motion is not modeled. Real-data validation is open work.",
        "- Coherent compounding requires multiple transmissions per image and reduces achievable frame rate.",
        "- Steering is limited to the implemented +/-" + f"{angle_limit:g} degrees.",
        "- Sound-speed error is tested only as a uniform mismatch.",
        "- Attenuation, element directivity, and depth-gain compensation are not modeled.",
        "",
        "## Theory (not measured results)",
        "",
        "For a Rayleigh envelope, the theoretical maximum `mu_out / sigma_out` is "
        f"`sqrt(pi / (4 - pi)) = {rayleigh_cnr:.3f}`. This theoretical limit is not "
        "the measured CNR of this phantom.",
        "",
        "For maximum depth `z_max`, the ideal pulse-repetition-frequency bound is "
        "`PRF_max = c / (2 z_max)`. The corresponding ideal compounded frame-rate "
        "bound is `f_frame = PRF_max / K`. Using the project sound speed, image "
        f"depth, and angle count gives `PRF_max = {ideal_prf / 1000:.1f} kHz`; "
        f"for `K = {len(G_ANGLES)}`, `f_frame = {ideal_prf / len(G_ANGLES) / 1000:.1f} kHz`. "
        "These theory bounds exclude system overhead and are not measured frame rates.",
        "",
        "## Recorded outputs",
        "",
        "See [the measured CSV](results/ablation.csv), [full metrics](results/metrics.json), "
        "[sound-speed results](results/sound_speed.json), and [runtime record](results/runtime.json).",
    ]
    return "\n".join(lines)


def main(check=False):
    rows, sound_speed, runtime = _read_results()
    readme = README.read_text(encoding="utf-8")
    intro = readme.split("## Findings", 1)[0]
    intro = intro.replace(
        "The demo creates the measured files in `results/` and the figures below. Its latest five-seed run took 1331.3236 seconds.",
        "The full demo creates the measured files in `results/` and the figures below. Its recorded runtime is listed in Findings.",
    )
    rendered = intro + _build_section(rows, sound_speed, runtime) + "\n"
    if check:
        if readme != rendered:
            raise SystemExit("README generated measurements differ from the recorded result files; run python -m tools.render_readme")
        print("README findings match the recorded CSV and JSON files.")
    else:
        README.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check generated README content without writing files.")
    main(check=parser.parse_args().check)
