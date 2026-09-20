"""Procedurally synthesized retro sound effects (no external audio files needed)."""

import numpy as np
import pygame

SAMPLE_RATE = 44100


def _to_sound(samples):
    stereo = np.column_stack([samples, samples]).astype(np.int16)
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


def make_blip(freq_start, freq_end, duration, volume=0.5):
    """A short square-wave sweep, like the classic laser 'pew'."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = np.linspace(freq_start, freq_end, len(t))
    phase = np.cumsum(2 * np.pi * freq / SAMPLE_RATE)
    wave = np.sign(np.sin(phase))
    envelope = np.linspace(1.0, 0.0, len(t))
    return _to_sound(wave * envelope * volume * 32767)


def make_explosion(duration, volume=0.6, decay=5.0, thump_freq=90, thump_amount=0.5,
                    crackle=0.0, crack_freq=(900, 150), crack_duration=0.05, noise_cutoff=None):
    """Decaying noise layered with a low-frequency thump and an initial crack transient.

    noise_cutoff, if set, low-passes the noise bed (like make_rumble) so it reads
    as a deep boom instead of a bright hiss.
    """
    n = int(SAMPLE_RATE * duration)
    t_env = np.linspace(0, 1, n, endpoint=False)
    t = np.linspace(0, duration, n, endpoint=False)
    envelope = np.exp(-decay * t_env)

    noise = np.random.uniform(-1, 1, n)
    if noise_cutoff:
        window = max(1, int(SAMPLE_RATE / noise_cutoff))
        kernel = np.ones(window) / window
        noise = np.convolve(noise, kernel, mode="same")
        noise = noise / (np.max(np.abs(noise)) + 1e-9)
    thump = np.sin(2 * np.pi * thump_freq * t) * np.exp(-decay * 1.6 * t_env)
    signal = noise * envelope * (1 - thump_amount) + thump * thump_amount

    if crackle > 0:
        crackle_mask = (np.random.random(n) < 0.08).astype(float)
        signal += np.random.uniform(-1, 1, n) * crackle_mask * crackle * envelope

    if crack_duration > 0:
        crack_n = int(SAMPLE_RATE * crack_duration)
        crack_freqs = np.linspace(crack_freq[0], crack_freq[1], crack_n)
        crack_phase = np.cumsum(2 * np.pi * crack_freqs / SAMPLE_RATE)
        crack_wave = np.sign(np.sin(crack_phase)) * np.linspace(1.0, 0.0, crack_n)
        signal[:crack_n] += crack_wave * 0.6

    signal = signal / (np.max(np.abs(signal)) + 1e-9)
    return _to_sound(signal * volume * 32767)


def make_rumble(duration, volume=0.25, cutoff_freq=90):
    """Low-pass filtered noise loop, for the ship's thruster."""
    n = int(SAMPLE_RATE * duration)
    noise = np.random.uniform(-1, 1, n)
    window = max(1, int(SAMPLE_RATE / cutoff_freq))
    kernel = np.ones(window) / window
    filtered = np.convolve(noise, kernel, mode="same")
    return _to_sound(filtered * volume * 32767)


def make_siren(duration, freq_low, freq_high, mod_rate, volume=0.3):
    """A warbling tone loop, for the flying saucer's hum."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = freq_low + (freq_high - freq_low) * (0.5 + 0.5 * np.sin(2 * np.pi * mod_rate * t))
    phase = np.cumsum(2 * np.pi * freq / SAMPLE_RATE)
    wave = np.sign(np.sin(phase))
    return _to_sound(wave * volume * 32767)


class Sounds:
    def __init__(self):
        self.shoot = make_blip(950, 500, 0.09, volume=0.35)
        self.ufo_shoot = make_blip(500, 200, 0.12, volume=0.35)
        self.asteroid_explosion = make_explosion(
            0.35, volume=0.55, decay=6.0, thump_freq=160, thump_amount=0.3,
            crackle=0.5, crack_freq=(1200, 300), crack_duration=0.04,
        )
        self.ship_explosion = make_explosion(
            1.3, volume=0.85, decay=1.5, thump_freq=38, thump_amount=0.8,
            crackle=0.15, crack_freq=(500, 80), crack_duration=0.08, noise_cutoff=250,
        )
        self.thrust = make_rumble(1.0, volume=0.18)
        self.ufo_hum = make_siren(1.5, 250, 450, mod_rate=2.5, volume=0.22)
