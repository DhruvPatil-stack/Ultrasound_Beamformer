# Theory

## Plane-wave time of flight

`t_tx(x,z,theta) = (x sin(theta) + z cos(theta)) / c`

`tau_i(x,z,theta) = t_tx(x,z,theta) + sqrt((x - x_i)^2 + z^2) / c + t_offset`

`t_tx`: transmit arrival time.

`x`: lateral image position.

`z`: image depth.

`theta`: steering angle.

`x_i`: lateral position of element `i`.

`c`: assumed sound speed.

`t_offset`: common positive offset used by simulation and beamforming.

## Coherent plane-wave compounding

`B_k(x,z) = DAS_k(x,z)`

`B_comp(x,z) = (1/K) sum(k=1..K) B_k(x,z)`

`I_comp(x,z) = |B_comp(x,z)|`

`B_k`: complex DAS image for steering angle `k`.

`B_comp`: equal-weight coherently compounded complex image.

`I_comp`: compounded envelope.

`K`: number of steering angles.

## Contrast-to-noise ratio

`CNR = |mu_in - mu_out| / sqrt(sigma_in^2 + sigma_out^2)`

`mu_in`: mean envelope in the cyst region.

`mu_out`: mean envelope in the outside ring.

`sigma_in`: envelope standard deviation in the cyst region.

`sigma_out`: envelope standard deviation in the outside ring.

## Contrast ratio

`CR (dB) = 20 log10(mu_out / mu_in)`

`CR`: contrast ratio in decibels.

`mu_out`: mean envelope in the outside ring.

`mu_in`: mean envelope in the cyst region.

## Rayleigh-envelope CNR ceiling (theory)

For a Rayleigh distributed envelope, the theoretical ratio of mean to standard
deviation is:

`mu_out / sigma_out = sqrt(pi / (4 - pi))`

This is a theoretical limit. It is not a measured CNR for the simulated cyst.

## Pulse repetition frequency and compounded frame rate (theory)

For maximum imaging depth `z_max`, the ideal pulse repetition frequency bound is:

`PRF_max = c / (2 z_max)`

For `K` transmissions per coherently compounded frame, the corresponding ideal
frame rate is:

`f_frame = PRF_max / K`

These equations omit scanner overhead. The numerical example in the README is
computed from the project sound speed, maximum image depth, and config G angle
count. It is a theoretical bound, not a measured acquisition rate.
