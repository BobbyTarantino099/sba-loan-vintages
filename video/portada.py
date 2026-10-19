"""
Extract the video's poster frame: the still the case page shows until the reader presses play.

    python video/portada.py

Reads the newest render in video/composicion/renders/ (not versioned) and writes
video/portada.jpg, which IS versioned: the site copies it with scripts/cases/sync_figures.py,
and without the render it could not be made again.

Pick a frame that invites pressing play and does not repeat a figure of the case. In the first
case it was the end of scene 1, the hook fully settled. Check it is not mid-animation: a counter
halfway up puts a wrong number on the page.

Needs FFmpeg on PATH.
"""

from pathlib import Path
import subprocess

DIR = Path(__file__).resolve().parent
RENDERS = DIR / "composicion" / "renders"
DESTINO = DIR / "portada.jpg"

SEGUNDO = 17.6    # s on the root timeline. Set it to a settled frame of the hook.
ANCHO = 1280     # the page column is ~56rem; 1280 covers it at 1.5x


def main() -> None:
    renders = sorted(RENDERS.glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    assert renders, f"no render in {RENDERS}: run `npm run render` first"
    render = renders[-1]
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{SEGUNDO}",
         "-i", str(render), "-frames:v", "1", "-vf", f"scale={ANCHO}:-2", "-q:v", "3",
         str(DESTINO)],
        check=True,
    )
    print(f"{render.name} @ {SEGUNDO} s -> {DESTINO.name} ({DESTINO.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
