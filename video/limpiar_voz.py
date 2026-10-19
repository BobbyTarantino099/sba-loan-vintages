"""
Clean the voice recording for the video.

    python video/empalmar_voz.py
    python video/limpiar_voz.py

Reads video/voz_empalmada.wav (empalmar_voz.py builds it from the take, which is a source and
never edited) and writes video/composicion/voz_limpia.wav, which mezclar_audio.py mixes. Needs
FFmpeg on PATH. The filter chain, in order:

1. Down-mix to mono, INSIDE the chain: the voice is a single source. With `-ac 1` the down-mix
   happens after the filters, the loudness is measured on stereo (+3 dB) and the gain comes out
   3 dB short.
2. High-pass at 80 Hz: removes rumble and hum below the voice.
3. FFT denoise (20 dB) with the noise floor at -70 dB. The floor has to sit BELOW the real noise
   of the room. Measure it in a pause before trusting this value: in the first case's room the
   noise was -63 dB RMS, and with the floor at -60 dB the filter barely acted. That was caught by
   measuring the pauses before and after, not by ear.
4. A soft noise gate (ratio 4, not a hard cut) to lower what is left in the pauses.
5. Loudness to -19 LUFS, the usual target for MONO speech (-16 is the stereo one), in two passes:
   measure the cleaned voice, then apply exactly the gain that is missing, with a limiter at
   -1.5 dBFS for the loudest syllables. `loudnorm` was tried first and dropped: it switches mode
   on its own when the peaks do not fit, and landed anywhere between -18.8 and -22 LUFS.

Chosen by ear in the first case out of three samples: none, this one, and a stronger
non-local-means filter (`anlmdn`), which also cut the end of the audio in FFmpeg 9.0. This one
lowered the pauses from 32 to ~41 dB below the voice without touching the pronunciation. Only
the noise floor should need changing, and only if the recording room changes.
"""

from pathlib import Path
import re
import subprocess

DIR = Path(__file__).resolve().parent
ORIGEN = DIR / "voz_empalmada.wav"
DESTINO = DIR / "composicion" / "voz_limpia.wav"

LIMPIEZA = ",".join([
    "aformat=channel_layouts=mono",
    "highpass=f=80",
    "afftdn=nr=20:nf=-70",
    "agate=threshold=0.003:ratio=4:attack=5:release=150",
])

OBJETIVO_LUFS = -19.0
TECHO_DB = -1.5


def medir() -> float:
    """First pass: integrated loudness (LUFS) of the cleaned voice."""
    salida = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(ORIGEN),
         "-af", f"{LIMPIEZA},ebur128", "-f", "null", "-"],
        check=True, capture_output=True, text=True,
    ).stderr
    # The summary at the end carries the last "I:" line.
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", salida)[-1])


def main() -> None:
    ganancia = OBJETIVO_LUFS - medir()
    techo = 10 ** (TECHO_DB / 20)
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(ORIGEN),
         "-af", f"{LIMPIEZA},volume={ganancia:.2f}dB,alimiter=limit={techo:.4f}:level=disabled",
         "-ar", "48000", str(DESTINO)],
        check=True,
    )
    print(f"{ORIGEN.name} -> {DESTINO.relative_to(DIR)}  (gain {ganancia:+.1f} dB)")


if __name__ == "__main__":
    main()
