"""
Join the voice when it was recorded in parts, one per scene.

    python video/unir_partes.py       # then: empalmar_voz.py, limpiar_voz.py

Optional: only when the voice was recorded in parts. Reads the recordings listed in PARTES and
writes video/voz.wav, the single take the rest of the chain expects. The recordings are sources and are never edited. Recording one part per scene
made the pauses and the pronunciation easier, and a mistake costs one part instead of the take.

What joining them takes, measured rather than guessed:

1. **Same loudness.** In the second case the parts came out between -21.6 and -17.0 LUFS:
   joined as they were, the level would jump at every scene change. Each one is brought to the median of the parts before
   joining; limpiar_voz.py then sets the level of the whole.
2. **Same edges.** Each part is trimmed to LEAD seconds before the first word, so every scene
   starts the same way however long the recorder ran before speaking.
3. **No click at the end.** Parts tend to stop while the last word is still decaying (the
   recorder stopped a moment early). Transcribe each part on its own to check the last word is
   complete; if it is, a short fade-out is enough.
4. **The same pause between scenes**, PAUSA seconds of silence, and a second at both ends of the
   take, which is what the first case's single take had.

Needs FFmpeg on PATH, and numpy to find where the voice starts.
"""

from pathlib import Path
import re
import statistics
import subprocess
import wave

import numpy as np

DIR = Path(__file__).resolve().parent
# One recording per scene, in order. Name them so they sort: "Part 1.wav", "Part 2.wav", ...
PARTES = sorted(DIR.glob("Part *.wav"))
DESTINO = DIR / "voz.wav"

LEAD = 0.10      # s kept before the first word of each part
FUNDIDO = 0.04   # s fade-out at the end of each part
PAUSA = 0.80     # s of silence between parts
BORDE = 1.0      # s of silence at both ends of the take
UMBRAL_DB = 18   # the voice starts this far above the part's own noise floor


def lufs(archivo: Path) -> float:
    salida = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(archivo),
         "-af", "aformat=channel_layouts=mono,ebur128", "-f", "null", "-"],
        check=True, capture_output=True, text=True,
    ).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", salida)[-1])


def inicio_voz(archivo: Path) -> float:
    """First 20 ms frame more than UMBRAL_DB above the part's noise floor."""
    with wave.open(str(archivo)) as w:
        sr, canales = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, canales)[:, 0]
    x = x.astype(float) / 32768
    paso = int(sr * 0.02)
    m = len(x) // paso
    rms = 20 * np.log10(np.sqrt((x[: m * paso].reshape(m, paso) ** 2).mean(1)) + 1e-9)
    piso = np.percentile(rms, 5)
    return float(np.argmax(rms > piso + UMBRAL_DB) * 0.02)


def duracion(archivo: Path) -> float:
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(archivo)],
        check=True, capture_output=True, text=True,
    ).stdout)


def main() -> None:
    niveles = [lufs(p) for p in PARTES]
    objetivo = statistics.median(niveles)

    entradas, grafo, etiquetas, resumen = [], [], [], []
    for k, (parte, nivel) in enumerate(zip(PARTES, niveles)):
        desde = max(0.0, inicio_voz(parte) - LEAD)
        largo = duracion(parte) - desde
        entradas += ["-i", str(parte)]
        silencio = BORDE if k == 0 else 0.0
        cola = BORDE if k == len(PARTES) - 1 else PAUSA
        grafo.append(
            f"[{k}:a]aformat=channel_layouts=mono,aresample=48000,"
            f"atrim=start={desde:.3f},asetpts=PTS-STARTPTS,"
            f"volume={objetivo - nivel:.2f}dB,"
            f"afade=t=out:st={largo - FUNDIDO:.3f}:d={FUNDIDO},"
            f"adelay={int(silencio * 1000)},apad=pad_dur={cola}[p{k}]"
        )
        etiquetas.append(f"[p{k}]")
        resumen.append(f"{parte.name} ({objetivo - nivel:+.1f} dB, from {desde:.2f} s)")
    grafo.append("".join(etiquetas) + f"concat=n={len(PARTES)}:v=0:a=1[salida]")

    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *entradas,
         "-filter_complex", ";".join(grafo), "-map", "[salida]", str(DESTINO)],
        check=True,
    )
    print(f"-> {DESTINO.name} ({duracion(DESTINO):.2f} s, parts at {objetivo:.1f} LUFS)")
    for linea in resumen:
        print("  " + linea)


if __name__ == "__main__":
    main()
