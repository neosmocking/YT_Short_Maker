import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
import re


def ask_youtube_url():
    root = tk.Tk()
    root.withdraw()
    url = simpledialog.askstring("YouTube URL", "Masukkan link YouTube:")
    if not url:
        raise RuntimeError("URL YouTube tidak diisi.")
    return url.strip()


def pick_txt_file():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Pilih file waktu cut (.txt)",
        filetypes=[("Text files", "*.txt")]
    )
    if not path:
        raise RuntimeError("File TXT tidak dipilih.")
    return Path(path)


def pick_output_folder():
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Pilih folder output")
    if not folder:
        raise RuntimeError("Folder output tidak dipilih.")
    return Path(folder)


def parse_cuts(txt_file: Path):
    cuts = []
    with txt_file.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            if "-" not in line:
                raise ValueError(f"Format salah di baris {i}")
            start, end = map(str.strip, line.split("-", 1))
            cuts.append((start, end))
    if not cuts:
        raise ValueError("File TXT kosong.")
    return cuts


def get_youtube_title(url: str) -> str:
    result = subprocess.run(
        ["yt-dlp", "--get-title", url],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def download_sections(url: str, title: str, cuts, output_dir: Path):
    safe_title = sanitize_filename(title)

    for idx, (start, end) in enumerate(cuts, start=1):
        section = f"*{start}-{end}"
        output_template = output_dir / f"{safe_title}_{idx}.%(ext)s"

        cmd = [
            "yt-dlp",
            "--newline",
            "--progress",
            "--download-sections", section,
            "-f", "bv+ba/b",
            "--downloader", "ffmpeg",
            "--downloader-args", "ffmpeg:-c copy",
            url,
            "-o", str(output_template)
        ]
  
        subprocess.run(cmd, check=True)


def main():
    try:
        url = ask_youtube_url()
        txt = pick_txt_file()
        output_dir = pick_output_folder()

        cuts = parse_cuts(txt)
        title = get_youtube_title(url)

        download_sections(url, title, cuts, output_dir)

        messagebox.showinfo(
            "Selesai",
            f"{len(cuts)} video berhasil disimpan di:\n{output_dir}"
        )

    except Exception as e:
        messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    main()
