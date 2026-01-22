import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
import re

# ---------------- Utility ----------------

def sanitize_filename(name: str) -> str:
    """Hapus karakter ilegal untuk file name"""
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def pick_output_folder():
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Pilih folder output")
    if not folder:
        raise RuntimeError("Folder output tidak dipilih.")
    return Path(folder)


def pick_txt_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Pilih file waktu cut (.txt)",
        filetypes=[("Text files", "*.txt")]
    )
    if not file_path:
        raise RuntimeError("File TXT tidak dipilih.")
    return Path(file_path)


def pick_video_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Pilih file video offline",
        filetypes=[("Video files", "*.mp4 *.mkv *.mov *.avi *.webm")]
    )
    if not file_path:
        raise RuntimeError("File video tidak dipilih.")
    return Path(file_path)


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


# ---------------- Operations ----------------

def download_full_youtube(url: str, output_dir: Path):
    safe_title = sanitize_filename(get_youtube_title(url))
    output_template = output_dir / f"{safe_title}.mp4"

    cmd = [
        "yt-dlp",
        "-f", "bv+ba/b",
        "--merge-output-format", "mp4",
        url,
        "-o", str(output_template)
    ]

    subprocess.run(cmd, check=True)


def cut_youtube(url: str, txt_file: Path, output_dir: Path):
    cuts = parse_cuts(txt_file)
    title = get_youtube_title(url)
    safe_title = sanitize_filename(title)

    for idx, (start, end) in enumerate(cuts, start=1):
        section = f"*{start}-{end}"
        output_template = output_dir / f"{safe_title}_{idx}.mp4"

        cmd = [
            "yt-dlp",
            "--newline",
            "--progress",
            "--download-sections", section,
            "-f", "bv+ba/b",
            "--merge-output-format", "mp4",
            "--downloader", "ffmpeg",
            "--downloader-args", "ffmpeg:-c copy",
            url,
            "-o", str(output_template)
        ]
        subprocess.run(cmd, check=True)


def cut_offline_video(video_file: Path, txt_file: Path, output_dir: Path):
    cuts = parse_cuts(txt_file)
    base_name = sanitize_filename(video_file.stem)

    for idx, (start, end) in enumerate(cuts, start=1):
        output_file = output_dir / f"{base_name}_{idx}.mp4"

        cmd = [
            "ffmpeg",
            "-ss", start,
            "-to", end,
            "-i", str(video_file),
            "-c:v", "copy",
            "-c:a", "aac",
            str(output_file)
        ]
        subprocess.run(cmd, check=True)


# ---------------- GUI & Main ----------------

def choose_mode():
    root = tk.Tk()
    root.withdraw()
    mode = simpledialog.askstring(
        "Pilih Mode",
        "Masukkan nomor mode:\n"
        "1 - Download Full Video YouTube\n"
        "2 - Potong Video dari YouTube\n"
        "3 - Potong Video Offline"
    )
    if not mode or mode.strip() not in {"1", "2", "3"}:
        raise RuntimeError("Mode tidak valid.")
    return mode.strip()


def main():
    try:
        mode = choose_mode()
        output_dir = pick_output_folder()

        if mode == "1":
            url = simpledialog.askstring("YouTube URL", "Masukkan link YouTube:")
            if not url:
                raise RuntimeError("URL tidak diisi.")
            download_full_youtube(url, output_dir)
            messagebox.showinfo("Selesai", "Download full video selesai.")

        elif mode == "2":
            url = simpledialog.askstring("YouTube URL", "Masukkan link YouTube:")
            if not url:
                raise RuntimeError("URL tidak diisi.")
            txt_file = pick_txt_file()
            cut_youtube(url, txt_file, output_dir)
            messagebox.showinfo("Selesai", "Potong Video YouTube selesai.")

        elif mode == "3":
            video_file = pick_video_file()
            txt_file = pick_txt_file()
            cut_offline_video(video_file, txt_file, output_dir)
            messagebox.showinfo("Selesai", "Potong Video offline selesai.")

    except Exception as e:
        messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    main()
