import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog, filedialog, messagebox
import re


# ---------------- Utility ----------------

def sanitize_filename(name: str) -> str:
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
        filetypes=[("Video files", "*.mp4 *.mkv *.mov *.avi *.webm *.ts")]
    )

    if not file_path:
        raise RuntimeError("File video tidak dipilih.")

    return Path(file_path)


# ---------------- Time utilities ----------------

def time_to_seconds(t):
    h, m, s = map(int, t.split(":"))
    return h * 3600 + m * 60 + s


def get_video_duration(video_file: Path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_file)
        ],
        capture_output=True,
        text=True,
        check=True
    )

    return float(result.stdout.strip())


# ---------------- Parse TXT ----------------

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
                    f"Format salah di baris {i}. Gunakan format:\n00:00:00 - 00:00:00"
                )

            start, end = parts
            cuts.append((start, end))

    if not cuts:
        raise ValueError("File TXT kosong.")

    return cuts


# ---------------- YouTube ----------------

def get_youtube_title(url: str) -> str:
    result = subprocess.run(
        ["yt-dlp", "--get-title", url],
        capture_output=True,
        text=True,
        check=True
    )

    return result.stdout.strip()


def download_full_youtube(url: str, output_dir: Path):

    title = get_youtube_title(url)
    safe_title = sanitize_filename(title)

    output_template = output_dir / f"{safe_title}.mp4"

    cmd = [
        "yt-dlp",
        "--newline",
        "--progress",
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


# ---------------- Offline Cut ----------------

def cut_offline_video(video_file: Path, txt_file: Path, output_dir: Path):

    cuts = parse_cuts(txt_file)

    base_name = sanitize_filename(video_file.stem)

    duration = get_video_duration(video_file)

    for i, (start, end) in enumerate(cuts, start=1):

        start_sec = time_to_seconds(start)
        end_sec = time_to_seconds(end)

        if start_sec > duration or end_sec > duration:

            raise RuntimeError(
                f"Timestamp tidak ada dalam durasi video.\n\n"
                f"Durasi video: {duration/60:.2f} menit\n"
                f"Timestamp: {start} - {end}"
            )

        output_file = output_dir / f"{base_name}_{i}.mp4"

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


# ---------------- GUI ----------------

def choose_mode():

    root = tk.Tk()
    root.withdraw()

    mode = simpledialog.askstring(
        "Pilih Mode",
        "Masukkan nomor mode:\n\n"
        "1 - Download Full Video YouTube\n"
        "2 - Potong Video dari YouTube\n"
        "3 - Potong Video Offline"
    )

    if not mode or mode.strip() not in {"1", "2", "3"}:
        raise RuntimeError("Mode tidak valid.")

    return mode.strip()


# ---------------- Main ----------------

def main():

    try:

        mode = choose_mode()

        output_dir = pick_output_folder()

        if mode == "1":

            url = simpledialog.askstring(
                "YouTube URL",
                "Masukkan link YouTube:"
            )

            if not url:
                raise RuntimeError("URL tidak diisi.")

            download_full_youtube(url, output_dir)

            messagebox.showinfo(
                "Selesai",
                "Download full video selesai."
            )

        elif mode == "2":

            url = simpledialog.askstring(
                "YouTube URL",
                "Masukkan link YouTube:"
            )

            if not url:
                raise RuntimeError("URL tidak diisi.")

            txt_file = pick_txt_file()

            cut_youtube(url, txt_file, output_dir)

            messagebox.showinfo(
                "Selesai",
                "Potong Video YouTube selesai."
            )

        elif mode == "3":

            video_file = pick_video_file()

            txt_file = pick_txt_file()

            cut_offline_video(
                video_file,
                txt_file,
                output_dir
            )

            messagebox.showinfo(
                "Selesai",
                "Potong Video offline selesai."
            )

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )


if __name__ == "__main__":
    main()