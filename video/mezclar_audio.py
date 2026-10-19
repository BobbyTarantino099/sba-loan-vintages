"""
Mix the cleaned voice with a music bed for the whole video.

    python video/mezclar_audio.py               # uses MUSICA below
    python video/mezclar_audio.py musica_2.mp3  # try another track

Reads video/composicion/voz_limpia.wav (limpiar_voz.py) and a track in video/, and writes
video/composicion/mezcla.wav, which is what the composition plays. Run it once the cut is final.
The length is read from the composition itself (the root's data-duration in index.html), so the
mix and the video cannot drift apart.

The music is NOT in the repository: its licence allows using it inside a video, not
redistributing the file on its own. Write down where it comes from in video/README.md, with the
track's page link (the first case lost it by downloading without an account).

How the bed is set, measured rather than guessed:

1. The music is cut to the video's length and brought to -28 LUFS over that stretch, 9 dB under
   the voice (-19 LUFS). That is what is heard in the pauses and under the closing card. Tracks
   arrive mastered at -10 to -12 LUFS, so this is a big cut.
2. The voice ducks it: a sidechain compressor keyed on the voice lowers the music while the voice
   speaks and lets it come back in the pauses.
3. A short fade-in, and a fade-out that ends exactly with the video, so the track does not stop
   mid-phrase.
4. A limiter at -1 dBFS on the sum. The mono voice at -19 LUFS becomes -16 LUFS once it plays on
   both channels, the usual stereo target for web video.

Needs FFmpeg on PATH.
"""

from pathlib import Path
import re
import subprocess
import sys

DIR = Path(__file__).resolve().parent
VOZ = DIR / "composicion" / "voz_limpia.wav"
INDICE = DIR / "composicion" / "index.html"
DESTINO = DIR / "composicion" / "mezcla.wav"

MUSICA = "musica_2.mp3"   # the chosen track; its source and licence go in video/README.md

BASE_LUFS = -28.0     # music level when the voice is silent
FUNDIDO_ENTRADA = 0.8
FUNDIDO_SALIDA = 3.5  # ends exactly at the video's end

# Ducking: how hard and how fast the voice pushes the music down.
DUCKING = "threshold=0.02:ratio=4:attack=25:release=500:knee=4"


def duracion_video() -> float:
    """The root composition's length, read from index.html."""
    raiz = re.search(r'id="root"[^>]*?data-duration="([\d.]+)"', INDICE.read_text(encoding="utf-8"), re.S)
    assert raiz, "index.html: the root div needs a data-duration"
    return float(raiz.group(1))


def lufs(archivo: Path, hasta: float | None = None) -> float:
    rango = ["-t", f"{hasta}"] if hasta else []
    salida = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", *rango, "-i", str(archivo),
         "-af", "ebur128", "-f", "null", "-"],
        check=True, capture_output=True, text=True,
    ).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", salida)[-1])


def mezclar(musica: Path, destino: Path, duracion: float) -> float:
    ganancia = BASE_LUFS - lufs(musica, duracion)
    grafo = ";".join([
        f"[1:a]atrim=0:{duracion},asetpts=PTS-STARTPTS,aresample=48000,"
        f"aformat=channel_layouts=stereo,volume={ganancia:.2f}dB,"
        f"afade=t=in:st=0:d={FUNDIDO_ENTRADA},"
        f"afade=t=out:st={duracion - FUNDIDO_SALIDA}:d={FUNDIDO_SALIDA}[musica]",
        # The voice is mono: copy it to both channels at full level (plain up-mixing lowers each
        # channel 3 dB), and pad it with silence to the video's length, because the sidechain
        # compressor stops when its key stops and would take the closing card's music with it.
        f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_dur={duracion},asplit=2[clave][voz]",
        f"[musica][clave]sidechaincompress={DUCKING}[cama]",
        "[voz][cama]amix=inputs=2:normalize=0:duration=longest,"
        f"atrim=0:{duracion},alimiter=limit=0.891:level=disabled[salida]",
    ])
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-i", str(VOZ), "-i", str(musica),
         "-filter_complex", grafo, "-map", "[salida]", str(destino)],
        check=True,
    )
    return ganancia


def main() -> None:
    musica = DIR / (sys.argv[1] if len(sys.argv) > 1 else MUSICA)
    destino = Path(sys.argv[2]) if len(sys.argv) > 2 else DESTINO
    duracion = duracion_video()
    ganancia = mezclar(musica, destino, duracion)
    print(f"{VOZ.name} + {musica.name} ({ganancia:+.1f} dB), {duracion} s -> {destino}")


if __name__ == "__main__":
    main()
