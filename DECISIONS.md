# Decisions and task list

- [x] Phase 0: Read the original project and Git history.
- [x] Phase 1: Create the package layout and remove obsolete data and figures.
- [x] Phase 2: Add a deterministic local simulator.
- [x] Phase 3: Add chunked analytic DAS with interpolation, apodization, and F-number support.
- [x] Phase 4: Add B-mode conversion and measurement functions.
- [ ] Phase 5: Run and record tests.
- [ ] Phase 6: Run the demo and create measured results and figures.
- [ ] Phase 7: Write documentation from generated results.
- [ ] Phase 8: Commit and push.

## Technical choices

- The simulator uses a Gaussian-modulated cosine pulse. Its Gaussian width is derived from the requested 0.6 fractional bandwidth; attenuation and element directivity are not simulated.
- The cyst speckle count is estimated from 10 scatterers per wavelength-by-axial-resolution cell over a 20 mm by 20 mm cyst region. Scatterers are generated in chunks of 4096 to bound temporary arrays below 1 GB.
- The analytic RF signal has about 4 samples per cycle at 5.2 MHz (20.832 MHz / 5.2 MHz). Linear interpolation is therefore evaluated, not assumed superior.
- Test tolerances: point position limits are 0.2 mm lateral and 0.1 mm axial, as specified. Resolution is allowed +/-40% of lambda x F-number, as specified. The hand delay comparison uses exact binary-equivalent arithmetic from the same constants.
- No parameters are adjusted after observing a test result. Measured values are appended below after the test and demo runs.
- Point metrics use a local search window around each known simulated target. This prevents a stronger point elsewhere in the seven-point phantom from being incorrectly assigned to the target under test. Resolution is measured on a separate 0.025 mm lateral and axial local grid around the 30 mm point.

## Measured validation record

- [x] Phase 5: `pytest -q` reported 6 passed and 0 failed.
- [x] Phase 6: `run_demo.py` generated the ablation files and five figures.
- [x] Phase 7: Documentation uses values written by `results/ablation.csv`.
- The no-apodization, no-F-number configuration A measured a lateral FWHM of 0.145566789059316 mm at 30 mm. Lambda x F-number was 0.2331920048455482 mm, giving a measured ratio of 0.6242357629530667.
- Linear interpolation (B) was worse than nearest interpolation (A) for lateral FWHM in this simulator result, but it improved cyst CR and CNR. This is reported rather than hidden.
