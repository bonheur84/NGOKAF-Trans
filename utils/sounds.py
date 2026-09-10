"""Sound effects module — soft musical tones, no OS beeps.

Generates pleasant WAV sounds programmatically using sine waves and
plays them via QSoundEffect (non-blocking, no external files needed).
"""
from __future__ import annotations

import io
import logging
import math
import struct
import wave
from functools import lru_cache
from pathlib import Path
from tempfile import gettempdir

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

logger = logging.getLogger(__name__)

# ─── WAV generation helpers ───────────────────────────────────────────────────

SAMPLE_RATE = 44100


def _sine_wave(
    frequency: float,
    duration: float,
    volume: float = 0.45,
    attack: float = 0.01,
    release: float = 0.12,
) -> bytes:
    """Return raw 16-bit PCM bytes for a sine wave with soft envelope."""
    n_samples = int(SAMPLE_RATE * duration)
    attack_s = int(SAMPLE_RATE * attack)
    release_s = int(SAMPLE_RATE * release)
    out = []
    for i in range(n_samples):
        if i < attack_s:
            env = i / attack_s
        elif i > n_samples - release_s:
            env = (n_samples - i) / release_s
        else:
            env = 1.0
        sample = math.sin(2 * math.pi * frequency * i / SAMPLE_RATE)
        val = int(sample * env * volume * 32767)
        out.append(struct.pack("<h", max(-32768, min(32767, val))))
    return b"".join(out)


def _chord(
    freqs: list[float],
    duration: float,
    volume: float = 0.35,
    attack: float = 0.015,
    release: float = 0.18,
) -> bytes:
    """Mix multiple sine waves together (chord)."""
    per_vol = volume / len(freqs)
    n_samples = int(SAMPLE_RATE * duration)
    attack_s = int(SAMPLE_RATE * attack)
    release_s = int(SAMPLE_RATE * release)
    out = []
    for i in range(n_samples):
        if i < attack_s:
            env = i / attack_s
        elif i > n_samples - release_s:
            env = (n_samples - i) / release_s
        else:
            env = 1.0
        mix = sum(math.sin(2 * math.pi * f * i / SAMPLE_RATE) for f in freqs)
        val = int(mix * env * per_vol * 32767)
        out.append(struct.pack("<h", max(-32768, min(32767, val))))
    return b"".join(out)


def _build_wav(pcm_data: bytes) -> bytes:
    """Wrap raw PCM bytes in a valid WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def _sequence(*segments: bytes) -> bytes:
    """Concatenate PCM segments (before WAV wrapping)."""
    return b"".join(segments)


# ─── Sound definitions ────────────────────────────────────────────────────────

def _make_success() -> bytes:
    """Upward two-note ding — C5 -> E5 (success / sale confirmed)."""
    note1 = _sine_wave(523.25, 0.12, volume=0.40, attack=0.01, release=0.06)
    gap   = _sine_wave(0, 0.04, volume=0)
    note2 = _sine_wave(659.25, 0.22, volume=0.42, attack=0.01, release=0.15)
    return _sequence(note1, gap, note2)


def _make_error() -> bytes:
    """Two descending notes — soft alert, not harsh."""
    note1 = _sine_wave(440.0, 0.12, volume=0.38, attack=0.01, release=0.06)
    gap   = _sine_wave(0, 0.03, volume=0)
    note2 = _sine_wave(349.23, 0.22, volume=0.38, attack=0.01, release=0.15)
    return _sequence(note1, gap, note2)


def _make_warning() -> bytes:
    """Single mid-tone pulse — gentle caution."""
    return _sine_wave(523.25, 0.18, volume=0.36, attack=0.01, release=0.12)


def _make_notification() -> bytes:
    """Bright three-note ascending arpeggio — C5 E5 G5 (notification bell)."""
    n1 = _sine_wave(523.25, 0.10, volume=0.38, attack=0.005, release=0.05)
    g1 = _sine_wave(0, 0.03, volume=0)
    n2 = _sine_wave(659.25, 0.10, volume=0.40, attack=0.005, release=0.05)
    g2 = _sine_wave(0, 0.03, volume=0)
    n3 = _sine_wave(783.99, 0.25, volume=0.42, attack=0.005, release=0.18)
    return _sequence(n1, g1, n2, g2, n3)


def _make_click() -> bytes:
    """Ultra-short soft click for navigation buttons."""
    return _sine_wave(880.0, 0.055, volume=0.28, attack=0.003, release=0.04)


def _make_print() -> bytes:
    """Warm chord rise — signals printing / ticket generated."""
    n1 = _chord([523.25, 659.25], 0.14, volume=0.36, attack=0.01, release=0.08)
    g  = _sine_wave(0, 0.04, volume=0)
    n2 = _chord([523.25, 659.25, 783.99], 0.28, volume=0.38, attack=0.01, release=0.20)
    return _sequence(n1, g, n2)


def _make_bus_full() -> bytes:
    """Urgent triple descending pulse — bus fully booked alert.

    Three quick descending tones (A4 → F4 → D4) followed by a low
    resonant chord to signal that no more seats are available.
    Very distinct from print (ascending) and error (only 2 notes).
    """
    # Three quick descending pulses
    hit1 = _sine_wave(440.00, 0.10, volume=0.50, attack=0.005, release=0.06)
    gap1 = _sine_wave(0, 0.04, volume=0)
    hit2 = _sine_wave(349.23, 0.10, volume=0.50, attack=0.005, release=0.06)
    gap2 = _sine_wave(0, 0.04, volume=0)
    hit3 = _sine_wave(293.66, 0.10, volume=0.50, attack=0.005, release=0.06)
    gap3 = _sine_wave(0, 0.06, volume=0)
    # Low resonant chord (D3 + A3) — heavy, final
    chord = _chord([146.83, 220.00], 0.45, volume=0.52, attack=0.01, release=0.30)
    return _sequence(hit1, gap1, hit2, gap2, hit3, gap3, chord)


# ─── Cache & playback ─────────────────────────────────────────────────────────

_SOUND_DIR = Path(gettempdir()) / "ngokaf_sounds"
_SOUND_DIR.mkdir(exist_ok=True)

_GENERATORS = {
    "success":      _make_success,
    "error":        _make_error,
    "warning":      _make_warning,
    "notification": _make_notification,
    "click":        _make_click,
    "print":        _make_print,
    "bus_full":     _make_bus_full,
}

_players: dict[str, QSoundEffect] = {}


@lru_cache(maxsize=None)
def _wav_path(name: str) -> str:
    """Generate WAV file on first call, cache path for subsequent calls."""
    gen = _GENERATORS.get(name)
    if gen is None:
        return ""
    wav_bytes = _build_wav(gen())
    path = _SOUND_DIR / f"{name}.wav"
    path.write_bytes(wav_bytes)
    return str(path)


def _get_player(name: str) -> QSoundEffect | None:
    """Return (or create) a QSoundEffect player for the given sound name."""
    if name in _players:
        return _players[name]
    path = _wav_path(name)
    if not path:
        return None
    player = QSoundEffect()
    player.setSource(QUrl.fromLocalFile(path))
    player.setVolume(0.85)
    _players[name] = player
    return player


def play(name: str) -> None:
    """Play a sound by name. Non-blocking. Silent on any error."""
    try:
        player = _get_player(name)
        if player:
            player.play()
    except Exception as exc:
        logger.debug("Sound play error (%s): %s", name, exc)


# ─── Convenience wrappers ─────────────────────────────────────────────────────

def play_success()      -> None: play("success")
def play_error()        -> None: play("error")
def play_warning()      -> None: play("warning")
def play_notification() -> None: play("notification")
def play_click()        -> None: play("click")
def play_print()        -> None: play("print")
def play_bus_full()     -> None: play("bus_full")
