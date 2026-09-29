import numpy as np
import h5py
from scipy.signal import hilbert

# --- Load data ---
with h5py.File("sample_rf_data.hdf5", "r") as f:
    rf_data = f["rf_data"][:]
    c       = float(f["c"][()])
    fs      = float(f["fs"][()])
    pitch   = float(f["pitch"][()])

n_samples, n_elements = rf_data.shape

# --- Geometry ---
# Element positions centered at 0 along x-axis
elem_x = (np.arange(n_elements) - (n_elements - 1) / 2) * pitch  # (128,)

# Image grid
x_vec = np.linspace(-20e-3, 20e-3, 100)   # lateral,  (100,)
z_vec = np.linspace(5e-3,  50e-3, 200)    # axial,    (200,)

# --- Vectorized Time-of-Flight ---
# Shapes expanded for broadcasting: (200, 100, 1) vs (1, 1, 128)
z   = z_vec[:, None, None]          # (200, 1,   1)
x   = x_vec[None, :, None]          # (1,   100, 1)
xi  = elem_x[None, None, :]         # (1,   1,   128)

# Plane-wave transmit: t = (z + sqrt((x - xi)^2 + z^2)) / c
tof = (z + np.sqrt((x - xi) ** 2 + z ** 2)) / c   # (200, 100, 128)

# --- Delay and Sum ---
idx = np.round(tof * fs).astype(int)               # sample indices

# Mask out-of-bounds indices
valid = (idx >= 0) & (idx < n_samples)
idx   = np.where(valid, idx, 0)

# Gather amplitudes: rf_data[idx, channel_axis]
# channel index broadcast: (1, 1, 128)
ch_idx = np.arange(n_elements)[None, None, :]      # (1, 1, 128)

amplitudes = rf_data[idx, ch_idx]                  # (200, 100, 128)
amplitudes = np.where(valid, amplitudes, 0.0)

beamformed = amplitudes.sum(axis=2)                # (200, 100)

# --- Envelope Detection ---
# Apply Hilbert along depth axis (axis=0 → rows = depth samples)
envelope = np.abs(hilbert(beamformed, axis=0))     # (200, 100)

# --- Save ---
np.save("envelope.npy", envelope)

print(f"Envelope matrix shape : {envelope.shape}")
print("Saved to envelope.npy")
