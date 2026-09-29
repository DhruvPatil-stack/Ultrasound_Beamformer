Ultrasound Delay-and-Sum (DAS) Beamforming Engine
A lightweight, fully vectorized Python pipeline that reconstructs a standard 2D B-Mode clinical ultrasound image from raw synthetic radiofrequency (RF) channel data.
I built this rapid proof-of-concept to demonstrate hands-on application of acoustic physics, RF channel processing, and beamforming algorithms using standard Python biosignal workflows.

Pipeline Architecture
Data Ingestion: Extracts raw voltage matrices, sampling frequencies, and transducer element pitch from an HDF5 dataset.

Vectorized Time-of-Flight: Calculates geometric transmit/receive delays across a 100x200 spatial grid for a 128-element linear array, utilizing NumPy broadcasting to bypass standard nested loops for rapid execution.

Delay-and-Sum (DAS): Converts time delays to matrix indices, aligns the staggered channel data, and sums across the 128-element axis to force constructive interference at the focal coordinates.

Envelope Detection: Applies a Hilbert transform to extract the low-frequency acoustic intensity envelope from the high-frequency RF carrier wave.

Log Compression: Compresses the massive acoustic dynamic range into decibels (dB), clipped between -60 and 0 dB, to render the final grayscale B-Mode image.

Visual Outputs
Raw RF Signal (Center Transducer)

Reconstructed B-Mode Image

Tech Stack
NumPy: Matrix manipulation, broadcasting, and time-delay calculations.

SciPy: DSP applications (Hilbert transform).

h5py: Ingestion of standard medical imaging datasets.

Matplotlib: Clinical image rendering and dynamic range mapping.
