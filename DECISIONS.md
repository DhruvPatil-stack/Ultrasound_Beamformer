# Release decisions and task list

## Release task list

- [x] Phase 0: Inspect the repository, run baseline checks, and verify identity and branch refs.
- [x] Phase 1: Remove private report details, repair cleanup and dependency files, add ignore rules and MIT license.
- [x] Phase 2: Add and run the isolated quick cyst demo; confirm release outputs remain unchanged.
- [x] Phase 3: Generate measured findings and theoretical limits from recorded result files.
- [x] Phase 4: Add automated checks, continuous integration, and public quick-start documentation.
- [x] Phase 5: Review, consolidate local history, and prepare exact push commands.

## Decisions

- Preserve recorded full-demo measurements. Do not rerun the full demo or change test tolerances.
- The quick demo measures cyst configurations C and G with seeds 0 and 1. It writes only to `results_quick/` and `figures_quick/`.
- The quick demo ran once on 2026-10-26. Its internal runtime was 223.58051340002567 seconds; the enclosing command measured 225.6104 seconds. Both are under five minutes. SHA-256 checks confirmed that `results/`, `figures/`, and `README.md` did not change.
- Render README measurement values from `results/ablation.csv`, `results/sound_speed.json`, and `results/runtime.json`. Label equations and derived bounds as theory.
- Keep `BLOCKED.md` local and uncommitted. It records a denied optional process-monitoring query and a documentation command that succeeded on one retry.
- Never store the full-demo or quick-demo output directories in Git. Keep the user’s existing `error.log` uncommitted.

## Current beamforming choices

- The simulator uses a Gaussian-modulated cosine pulse and deterministic seeded scatterers. Attenuation, element directivity, depth-gain compensation, and tissue motion are not modeled.
- DAS computes analytic channel data, applies nearest or linear delay interpolation, and supports optional Hann weighting, F-number aperture, and polyphase upsampling.
- Plane-wave steering uses a shared nonnegative transmit-time offset. Coherent compounding averages complex DAS images before envelope detection.
- `beamform_das` defaults to linear interpolation, Hann weighting, and no F-number aperture.
- Point position is estimated by a three-sample parabolic peak fit. Resolution uses -6 dB FWHM. Cyst results in the release files use seeds 0 through 4 and sample standard deviation.
- The steering implementation is evaluated through the range represented by config G. README theory calculations exclude scanner overhead and are not measured frame rates.

The eight commits after `5ae053f` were consolidated into one local release
commit. No push was performed. Publishing the rewritten branch requires the
force-with-lease command supplied in the handoff.
