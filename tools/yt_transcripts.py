#!/usr/bin/env python3
"""Descarca subtitrarile (auto sau manuale) ale videoclipurilor unui canal YouTube
si le salveaza ca text curat, cate un fisier .txt per video.

Uz personal (analiza, studiu). Ruleaza local, nu in medii cu YouTube blocat.

Cerinte:  pip install yt-dlp
Exemple:
  python tools/yt_transcripts.py https://www.youtube.com/@MonicaIon/videos --filtru spark
  python tools/yt_transcripts.py https://www.youtube.com/@MonicaIon/shorts --limita 20
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def lista_videouri(url, filtru, limita):
    cmd = ["yt-dlp", "--flat-playlist", "--print", "%(id)s\t%(title)s", url]
    if limita:
        cmd += ["--playlist-end", str(limita)]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    videouri = [linie.split("\t", 1) for linie in out.splitlines() if "\t" in linie]
    if filtru:
        videouri = [(i, t) for i, t in videouri if filtru.lower() in t.lower()]
    return videouri


def vtt_la_text(cale):
    linii, ultima = [], None
    for linie in cale.read_text(encoding="utf-8").splitlines():
        if not linie.strip() or "-->" in linie or linie.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        linie = re.sub(r"<[^>]+>", "", linie).strip()
        if linie and linie != ultima:  # subtitrarile auto repeta randurile
            linii.append(linie)
            ultima = linie
    return " ".join(linii)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("url", help="link canal/playlist, ex. https://www.youtube.com/@MonicaIon/videos")
    p.add_argument("--filtru", help="pastreaza doar titlurile care contin textul (ex. spark)")
    p.add_argument("--limita", type=int, help="cate videouri recente sa scaneze")
    p.add_argument("--limba", default="ro", help="cod limba subtitrare (implicit ro)")
    p.add_argument("--iesire", default="transcrieri", help="folder de iesire")
    a = p.parse_args()

    dest = Path(a.iesire)
    dest.mkdir(exist_ok=True)
    videouri = lista_videouri(a.url, a.filtru, a.limita)
    if not videouri:
        sys.exit("Niciun video gasit (verifica linkul sau filtrul).")

    for vid, titlu in videouri:
        print(f"-> {titlu}")
        subprocess.run(
            ["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs",
             "--sub-langs", a.limba, "--sub-format", "vtt",
             "-o", str(dest / f"{vid}.%(ext)s"), f"https://www.youtube.com/watch?v={vid}"],
            capture_output=True, text=True,
        )
        vtt = next(dest.glob(f"{vid}*.vtt"), None)
        if not vtt:
            print("   fara subtitrare disponibila")
            continue
        nume = re.sub(r"[^\w\- ]", "", titlu)[:80].strip() or vid
        (dest / f"{nume}.txt").write_text(
            f"{titlu}\nhttps://www.youtube.com/watch?v={vid}\n\n{vtt_la_text(vtt)}\n", encoding="utf-8")
        vtt.unlink()
    print(f"Gata. Fisierele sunt in {dest.resolve()}")


if __name__ == "__main__":
    main()
