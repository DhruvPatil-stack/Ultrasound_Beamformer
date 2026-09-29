import numpy as np
import matplotlib.pyplot as plt

# --- Load ---
envelope = np.load("envelope.npy")

# --- Normalize ---
envelope_norm = envelope / (envelope.max() + 1e-12)

# --- Log Compression ---
bmode = 20 * np.log10(envelope_norm)

# --- Dynamic Range Clip ---
bmode = np.clip(bmode, -60, 0)

# --- Plot ---
fig, ax = plt.subplots(figsize=(6, 8))
im = ax.imshow(
    bmode,
    cmap="gray",
    extent=[-20, 20, 50, 5],   # [x_min, x_max, z_max, z_min] in mm
    aspect="auto",
)
plt.colorbar(im, ax=ax, label="Amplitude (dB)")
ax.set_xlabel("Lateral Distance (mm)")
ax.set_ylabel("Axial Depth (mm)")
ax.set_title("Simulated B-Mode Ultrasound Image")
fig.tight_layout()
fig.savefig("b_mode_image.png", dpi=150)
print("Saved b_mode_image.png")
