# Validation summary

Validation date: 2026-10-26.

Baseline validation command: `python -m pytest -q`.
Result: 14 passed, 0 failed, in 7.44 seconds.

The ablation table below reports the existing measurements from
[`ablation.csv`](ablation.csv), rounded for display. CR and CNR show means
and sample standard deviations across seeds 0 through 4.

| Config | FWHM mm | ISLR dB | PSL dB | Shallow clutter dB | CR dB | CNR |
|---|---:|---:|---:|---:|---:|---:|
| legacy | 0.3089 | -19.55 | -15.10 | -39.50 | 8.35 +/- 0.25 | 1.042 +/- 0.030 |
| A | 0.3089 | -19.23 | -14.73 | -39.41 | 8.44 +/- 0.27 | 1.051 +/- 0.032 |
| B | 0.3116 | -22.12 | -15.23 | -40.33 | 16.19 +/- 0.50 | 1.465 +/- 0.036 |
| C | 0.4918 | -26.95 | -30.99 | -35.79 | 18.65 +/- 0.24 | 1.534 +/- 0.017 |
| D | 0.9431 | -27.97 | -26.97 | -39.68 | 19.17 +/- 0.45 | 1.618 +/- 0.035 |
| E | 0.3064 | -23.25 | -14.79 | -40.81 | 19.03 +/- 0.80 | 1.541 +/- 0.042 |
| F | 0.4199 | -34.13 | -37.72 | -44.42 | 25.00 +/- 0.23 | 1.621 +/- 0.020 |
| G | 0.4066 | -35.89 | -38.87 | -50.43 | 28.33 +/- 0.23 | 1.648 +/- 0.020 |

Recorded full-demo runtime: 1331.3236 seconds, from
[`runtime.json`](runtime.json). The recorded run started on 2026-10-26.
The full demo was not rerun during this release cleanup; its measured
results are preserved.
