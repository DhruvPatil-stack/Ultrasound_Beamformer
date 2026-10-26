# Ultrasound DAS Beamformer

This project is a delay-and-sum beamformer validated on deterministic simulated data.
It is a student project. It is not a medical device.

The local simulator produces point targets and a speckle phantom with an anechoic cyst.
The beamformer forms an analytic channel signal before it sums delayed channels.
Parameters are similar to published plane-wave research settings. No PICMUS data is used.

## Run

```text
python -m pip install -r requirements.txt
pytest -q
python run_demo.py
```

The demo creates `results/ablation.csv`, `results/metrics.json`, and the figures below.

![Point-phantom channel data](figures/channel_data.png)

![Point phantom B-mode image](figures/points_bmode.png)

![Cyst phantom B-mode image](figures/cyst_bmode.png)

![Ablation comparison](figures/ablation_panel.png)

## Results

The table is written by `run_demo.py` from `results/ablation.csv`. FWHM is measured at -6 dB, or half of the envelope peak.

<!-- RESULTS:START -->
| Config | FWHM (mm, -6 dB) | ISLR (dB) | PSL (dB) | CR (dB, mean +/- std) | CNR (mean +/- std) |
|---|---:|---:|---:|---:|---:|
| legacy | 0.3089 | -19.55 | -15.10 | 8.34 +/- 0.25 | 1.041 +/- 0.030 |
| A | 0.3089 | -19.23 | -14.73 | 8.44 +/- 0.27 | 1.051 +/- 0.032 |
| B | 0.3116 | -22.12 | -15.23 | 16.19 +/- 0.50 | 1.465 +/- 0.036 |
| C | 0.4918 | -26.95 | -30.99 | 18.65 +/- 0.24 | 1.534 +/- 0.017 |
| D | 0.9431 | -27.97 | -26.97 | 19.17 +/- 0.45 | 1.618 +/- 0.035 |
<!-- RESULTS:END -->

See [the measured CSV](results/ablation.csv) and [the full metrics](results/metrics.json).

Config A has the best measured lateral resolution. Config D has the best measured cyst contrast and CNR. The config D profile has a wider main lobe with visible wings.

## Sound-speed robustness

Physics predicts that a lower assumed sound speed places the target shallow, while a higher assumed sound speed places it deep. For assumed speeds of 1500, 1540, and 1580 m/s, the measured axial shifts were -0.7530, 0.0007, and 0.7750 mm; lateral FWHM values were 1.6468, 0.3116, and 1.5657 mm, respectively. See [the measured result](results/sound_speed.json).

## Limitations

- Simulated data only.
- One plane wave at normal incidence.
- A single plane wave limits contrast. Multi-angle compounding is the standard fix.
- No attenuation.
- No element directivity.
- No speed-of-sound error.
- No depth gain compensation.
- No transmit time offset.
- Not tested on real data.
