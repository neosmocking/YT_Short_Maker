import subprocess
from pathlib import Path
import re
import yt_dlp
import os

# ---------------- CONFIG ----------------

BASE_DIR = Path(__file__).parent
CLIP_DIR = BASE_DIR / "Clip"
COOKIES_PATH = BASE_DIR / "Cookies" / "cookies.txt"

CLIP_DIR.mkdir(exist_ok=True, parents=True)

# ---------------- Utility ----------------

def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def time_to_seconds(t):
    h, m, s = map(int, t.split(":"))
    return h * 3600 + m * 60 + s


# ---------------- TXT Parser ----------------

def parse_cuts(txt_file: Path):
    cuts = []
    dash_pattern = re.compile(r"\s*[-–—]\s*")

    with txt_file.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):

            line = line.strip()
            if not line:
                continue

            parts = dash_pattern.split(line)

            if len(parts) != 2:
                raise ValueError(
                    f"Format salah di baris {i}. Gunakan:\n00:00:00 - 00:00:00"
                )

            cuts.append((parts[0], parts[1]))

    return cuts


# ---------------- YouTube ----------------

def get_video_info(url):
    opts = {
        "quiet": True,
        "cookies": str(COOKIES_PATH) if COOKIES_PATH.exists() else None
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def choose_resolution(info):

    formats = info["formats"]

    resolutions = sorted({
        f["height"] for f in formats if f.get("height")
    })

    print("\nResolusi tersedia:")
    for r in resolutions:
        print(f"{r}p")

    choice = input("\nPilih resolusi (contoh 720): ")

    return choice


def download_youtube(url):

    info = get_video_info(url)
    title = sanitize_filename(info["title"])

    resolution = choose_resolution(info)

    output_path = CLIP_DIR / f"{title}.mp4"

    ydl_opts = {
        "format": f"bestvideo[height<={resolution}]+bestaudio/best",
        "outtmpl": str(output_path),
        "merge_output_format": "mp4",
        "noplaylist": True,
    }

    if COOKIES_PATH.exists():
        ydl_opts["cookies"] = str(COOKIES_PATH)
        print("✔ Menggunakan cookies")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print("\nDownloading...")
        ydl.download([url])

    return output_path


# ---------------- FFmpeg Cut ----------------

def cut_video(video_file: Path, txt_file: Path):

    cuts = parse_cuts(txt_file)
    base_name = sanitize_filename(video_file.stem)

    for i, (start, end) in enumerate(cuts, start=1):

        output_file = CLIP_DIR / f"{base_name}_{i}.mp4"

        cmd = [
            "ffmpeg",
            "-ss", start,
            "-to", end,
            "-i", str(video_file),
            "-c:v", "copy",
            "-c:a", "aac",
            str(output_file)
        ]

        print(f"\n✂ Cutting {start} → {end}")
        subprocess.run(cmd, check=True)

    print("\n✔ Semua clip selesai!")


# ---------------- Main ----------------

def main():

    print("""
Pilih Mode:
1 - Download Full YouTube
2 - Download + Cut YouTube
3 - Cut Video Offline
""")

    mode = input("Masukkan pilihan: ").strip()

    if mode == "1":

        url = input("Masukkan URL YouTube: ")
        download_youtube(url)

    elif mode == "2":

        url = input("Masukkan URL YouTube: ")
        txt_path = input("Masukkan path file TXT: ")

        video = download_youtube(url)
        cut_video(video, Path(txt_path))

    elif mode == "3":

        video_path = input("Masukkan path video: ")
        txt_path = input("Masukkan path file TXT: ")

        cut_video(Path(video_path), Path(txt_path))

    else:
        print("Mode tidak valid")


if __name__ == "__main__":
    main()