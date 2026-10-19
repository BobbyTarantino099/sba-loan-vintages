"""
Splice re-recorded sentences into the voice take.

    python video/empalmar_voz.py      # then: python video/limpiar_voz.py

Reads video/voz.wav (the whole take) and the fragments listed in FRAGMENTOS, and writes
video/voz_empalmada.wav, which limpiar_voz.py cleans. Every recording is a source and is never
edited. With FRAGMENTOS empty (a clean take) it just copies the take, so the chain is always the
same commands.

When a sentence has to change after recording (in the first case, two of them overstated the
data), re-record only that sentence, with the same microphone, room and distance, and list it
here:

- cut into the take in the middle of a natural pause, so no word is touched;
- the fragment's gain is measured, not guessed: it is set to the loudness of the stretch it
  replaces (fragments recorded on another day came out 5-7 dB louder);
- each join is a 30 ms crossfade, short enough to be inaudible and long enough to avoid a click;
- if a fragment ends right on a consonant, give it a short fade-out (0.04 s worked).

Write down in this docstring which sentences were replaced and why: the take alone no longer
says what the video says.

Needs FFmpeg on PATH.
"""

from pathlib import Path
import re
import shutil
import subprocess

DIR = Path(__file__).resolve().parent
TOMA = DIR / "voz.wav"
DESTINO = DIR / "voz_empalmada.wav"

# (fragment, cut into the take at, back to the take at, fade-out at the fragment's end) in seconds.
# Example: (DIR / "voz_fragmento_s3.wav", 31.30, 42.00, 0.0),
FRAGMENTOS = []
FUNDIDO = 0.03      # s, crossfade at each join
# Take and fragments to one format before joining: a fragment recorded in stereo at 44.1 kHz
# would not crossfade with a mono 48 kHz take.
FORMATO = "aformat=channel_layouts=mono,aresample=48000"


def lufs(archivo: Path, desde: float | None = None, hasta: float | None = None) -> float:
    """Integrated loudness, in mono, of a file or a stretch of it."""
    rango = []
    if desde is not None:
        rango = ["-ss", f"{desde}", "-t", f"{hasta - desde}"]
    salida = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", *rango, "-i", str(archivo),
         "-af", "aformat=channel_layouts=mono,ebur128", "-f", "null", "-"],
        check=True, capture_output=True, text=True,
    ).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", salida)[-1])


def duracion(archivo: Path) -> float:
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(archivo)],
        check=True, capture_output=True, text=True,
    ).stdout)


def main() -> None:
    if not FRAGMENTOS:
        shutil.copyfile(TOMA, DESTINO)
        print(f"{TOMA.name} -> {DESTINO.name}: no fragments, take copied as is")
        return

    entradas = ["-i", str(TOMA)]
    partes, grafo, resumen = [], [], []
    desde = 0.0
    for k, (fragmento, entra, sale, fundido) in enumerate(FRAGMENTOS, start=1):
        assert entra >= desde, "fragments must be in order and must not overlap"
        entradas += ["-i", str(fragmento)]
        ganancia = lufs(TOMA, entra, sale) - lufs(fragmento)
        cola = ""
        if fundido:
            cola = f",afade=t=out:st={duracion(fragmento) - fundido:.3f}:d={fundido}"
        grafo.append(f"[0:a]{FORMATO},atrim={desde}:{entra},asetpts=PTS-STARTPTS[toma{k}]")
        grafo.append(f"[{k}:a]{FORMATO},volume={ganancia:.2f}dB{cola},asetpts=PTS-STARTPTS[frag{k}]")
        partes += [f"toma{k}", f"frag{k}"]
        resumen.append(f"{fragmento.name} {entra}-{sale} s ({ganancia:+.1f} dB)")
        desde = sale
    grafo.append(f"[0:a]{FORMATO},atrim=start={desde},asetpts=PTS-STARTPTS[resto]")
    partes.append("resto")

    # Chain the parts with crossfades: [a][b] -> x1, [x1][c] -> x2, ...
    actual = partes[0]
    for i, siguiente in enumerate(partes[1:], start=1):
        salida = "salida" if i == len(partes) - 1 else f"x{i}"
        grafo.append(f"[{actual}][{siguiente}]acrossfade=d={FUNDIDO}[{salida}]")
        actual = salida

    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *entradas,
         "-filter_complex", ";".join(grafo), "-map", "[salida]", str(DESTINO)],
        check=True,
    )
    print(f"{TOMA.name} -> {DESTINO.name}: " + " · ".join(resumen))


if __name__ == "__main__":
    main()
