import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}


def pick_video_file():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Pilih file video",
        filetypes=[("Video files", "*.mp4 *.mkv *.mov *.avi *.webm")]
    )

    if not file_path:
        raise RuntimeError("Video tidak dipilih.")

    return Path(file_path)


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


def parse_cuts(txt_file: Path):
    cuts = []

    with txt_file.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            if "-" not in line:
                raise ValueError(f"Format salah di baris {line_number}: {line}")

            start, end = map(str.strip, line.split("-", 1))
            cuts.append((start, end))

    if not cuts:
        raise ValueError("File TXT tidak berisi waktu cut.")

    return cuts


def cut_video(input_video: Path, cuts):
    base = input_video.stem
    ext = input_video.suffix
    folder = input_video.parent

    for idx, (start, end) in enumerate(cuts, start=1):
        output = folder / f"{base}_{idx}{ext}"

        cmd = [
            "ffmpeg",
            "-ss", start,
            "-to", end,
            "-i", str(input_video),
            "-c", "copy",
            str(output)
        ]

        subprocess.run(cmd, check=True)


def main():
    try:
        video = pick_video_file()
        txt = pick_txt_file()

        cuts = parse_cuts(txt)
        cut_video(video, cuts)

        messagebox.showinfo(
            "Selesai",
            f"Berhasil membuat {len(cuts)} potongan video."
        )

    except Exception as e:
        messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    main()
