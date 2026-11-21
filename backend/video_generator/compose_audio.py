"""
Generates soft ambient background music and mixes it with the voiceovers for exactly 90.0 seconds.
"""

import math
import subprocess
from pathlib import Path
import imageio_ffmpeg
import numpy as np
from scipy.io import wavfile

AUDIO_DIR = Path(__file__).resolve().parent / "audio_assets"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SAMPLE_RATE = 44100
TOTAL_DURATION = 90.0  # seconds


def generate_soft_ambient_music(output_wav_path: Path):
    """Generates a warm, calm medical documentary piano/pad ambient background track."""
    total_samples = int(SAMPLE_RATE * TOTAL_DURATION)
    t = np.linspace(0, TOTAL_DURATION, total_samples, endpoint=False)
    audio = np.zeros(total_samples, dtype=np.float32)

    # Note frequencies in Hz
    NOTE_FREQ = {
        "C3": 130.81, "E3": 164.81, "F3": 174.61, "G3": 196.00, "A3": 220.00, "B3": 246.94,
        "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88,
        "C5": 523.25, "D5": 587.33, "E5": 659.25, "G5": 783.99
    }

    # Chords (warm medical progression: Cmaj9 -> Fmaj7 -> Am7 -> Gsus4)
    CHORDS = [
        ["C3", "G3", "C4", "E4", "B4", "D5"],      # Cmaj9
        ["F3", "C4", "F4", "A4", "C5", "E5"],      # Fmaj7
        ["A3", "E4", "A4", "C5", "E5", "G5"],      # Am7
        ["G3", "D4", "G4", "B4", "D5", "A4"],      # Gadd9
    ]

    chord_duration = 4.0  # seconds per chord
    loop_duration = len(CHORDS) * chord_duration  # 16s

    num_loops = int(math.ceil(TOTAL_DURATION / loop_duration))

    for loop in range(num_loops):
        for c_idx, chord in enumerate(CHORDS):
            start_time = loop * loop_duration + c_idx * chord_duration
            if start_time >= TOTAL_DURATION:
                break

            start_sample = int(start_time * SAMPLE_RATE)
            chord_len = min(int(chord_duration * 1.5 * SAMPLE_RATE), total_samples - start_sample)
            if chord_len <= 0:
                continue

            t_chord = np.linspace(0, chord_len / SAMPLE_RATE, chord_len, endpoint=False)
            # Soft exponential decay with warm sustain
            envelope = np.exp(-t_chord * 0.45) * (1.0 - np.exp(-t_chord * 15.0))

            chord_wave = np.zeros(chord_len, dtype=np.float32)
            for note in chord:
                freq = NOTE_FREQ.get(note, 440.0)
                # Fundamental + soft second & third harmonics
                w = (
                    0.60 * np.sin(2 * np.pi * freq * t_chord) +
                    0.25 * np.sin(2 * np.pi * (freq * 2) * t_chord + 0.3) +
                    0.10 * np.sin(2 * np.pi * (freq * 3) * t_chord + 0.6)
                )
                chord_wave += w

            chord_wave = chord_wave * envelope * 0.08
            audio[start_sample:start_sample + chord_len] += chord_wave

    # Soft master limiter & normalize to -18dB
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = (audio / max_val) * 0.22

    # Smooth fade out at the very end (87-90s)
    fade_start = int(87.0 * SAMPLE_RATE)
    fade_len = total_samples - fade_start
    if fade_len > 0:
        fade_curve = np.linspace(1.0, 0.0, fade_len)
        audio[fade_start:] *= fade_curve

    # Stereo expansion
    stereo = np.column_stack((audio * 0.95, audio * 1.05))
    int16_audio = (stereo * 32767).astype(np.int16)

    wavfile.write(str(output_wav_path), SAMPLE_RATE, int16_audio)
    print(f"✓ Soft ambient music written to {output_wav_path}")


def mix_master_audio(output_mp3: Path):
    """Mixes voiceover segments with calibrated start delays and background music."""
    bg_wav = AUDIO_DIR / "bg_music.wav"
    generate_soft_ambient_music(bg_wav)

    # Voiceovers and exact start delays in ms
    # Timeline:
    # Scene 1: 0 - 10s (VO starts at 0.4s)
    # Scene 2: 10 - 25s (VO starts at 10.4s)
    # Scene 3: 25 - 45s (VO starts at 25.4s)
    # Scene 4: 45 - 60s (intro at 45.3s, hi at 49.0s, switch at 54.5s, or at 56.5s)
    # Scene 5: 60 - 75s (VO starts at 60.4s)
    # Scene 6: 75 - 85s (VO starts at 75.3s)
    # Scene 7: 85 - 90s (VO starts at 85.1s)
    VO_SCHEDULE = [
        ("scene1_en.mp3", 400),
        ("scene2_en.mp3", 10400),
        ("scene3_en.mp3", 25400),
        ("scene4_intro.mp3", 45300),
        ("scene4_hi.mp3", 49200),
        ("scene4_switch.mp3", 54200),
        ("scene4_or.mp3", 56200),
        ("scene5_en.mp3", 60400),
        ("scene6_en.mp3", 75300),
        ("scene7_en.mp3", 85100),
    ]

    inputs = ["-i", str(bg_wav)]
    for fname, _ in VO_SCHEDULE:
        inputs.extend(["-i", str(AUDIO_DIR / fname)])

    # Construct filter_complex
    # input 0 is bg music
    filter_parts = []
    # Set bg music volume to 0.45 (-7dB)
    filter_parts.append("[0:a]volume=0.45[bg];")

    delayed_tags = []
    for idx, (fname, delay_ms) in enumerate(VO_SCHEDULE):
        in_idx = idx + 1
        tag = f"vo{idx}"
        filter_parts.append(f"[{in_idx}:a]adelay={delay_ms}|{delay_ms},volume=1.25[{tag}];")
        delayed_tags.append(f"[{tag}]")

    all_vos = "".join(delayed_tags)
    filter_parts.append(f"{all_vos}amix=inputs={len(VO_SCHEDULE)}:normalize=0[vo_mix];")
    filter_parts.append("[bg][vo_mix]amix=inputs=2:duration=first:dropout_transition=2[outa]")

    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", "".join(filter_parts),
        "-map", "[outa]",
        "-t", "90.0",
        "-b:a", "192k",
        str(output_mp3)
    ]

    print("Mixing master audio track with FFmpeg...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print("FFmpeg error:", res.stderr)
        raise RuntimeError("Audio mixing failed")

    print(f"✓ Mastered 90-second soundtrack generated at {output_mp3}")


if __name__ == "__main__":
    mix_master_audio(AUDIO_DIR / "master_soundtrack_90s.mp3")

