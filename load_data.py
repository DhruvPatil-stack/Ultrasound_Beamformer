import os
import numpy as np
import h5py
import matplotlib.pyplot as plt

HDF5_FILE = "sample_rf_data.hdf5"

if not os.path.exists(HDF5_FILE):
    print("sample_rf_data.hdf5 not found — generating synthetic PICMUS-style dataset...")

    rng = np.random.default_rng(seed=42)
    rf = rng.standard_normal((3328, 128)).astype(np.float32) * 0.05

    # Inject a strong echo (simulated heart-valve reflection) around row 1500
    spike_rows = np.arange(1495, 1506)
    rf[spike_rows, :] += 5.0 * np.sin(
        2 * np.pi * np.linspace(0, 1, len(spike_rows))[:, None]
        * np.ones((1, 128))
    )

    with h5py.File(HDF5_FILE, "w") as f:
        f.create_dataset("rf_data", data=rf)
        f.create_dataset("c",     data=np.float64(1540.0))
        f.create_dataset("fs",    data=np.float64(20.832e6))
        f.create_dataset("pitch", data=np.float64(0.0003))

    print(f"Saved {HDF5_FILE}")

# --- Extraction ---
with h5py.File(HDF5_FILE, "r") as f:
    rf_data = f["rf_data"][:]
    c       = float(f["c"][()])
    fs      = float(f["fs"][()])
    pitch   = float(f["pitch"][()])

print(f"\nrf_data shape : {rf_data.shape}")
print(f"c (m/s)       : {c}")
print(f"fs (Hz)       : {fs:.6e}")
print(f"pitch (m)     : {pitch}")

# --- Plot channel 64 ---
channel = rf_data[:, 64]
time_us = np.arange(len(channel)) / fs * 1e6  # convert to microseconds

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(time_us, channel, linewidth=0.8, color="steelblue")
ax.set_xlabel("Time (µs)")
ax.set_ylabel("Amplitude")
ax.set_title("Raw RF Signal — Channel 64 (center transducer)")
ax.axvline(x=1500 / fs * 1e6, color="red", linestyle="--",
           linewidth=1.0, label="Echo @ row 1500")
ax.legend()
fig.tight_layout()
fig.savefig("channel_64_plot.png", dpi=150)
print("\nPlot saved to channel_64_plot.png")
