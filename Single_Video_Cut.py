import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

# ===== KONFIGURASI WAKTU POTONG =====
START_TIME = "00:00:00"
END_TIME = "00:26:00"
# ==================================


def pick_video_file():
    root = tk.Tk()
    root.withdraw()  # sembunyikan window kosong

    file_path = filedialog.askopenfilename(
        title="Pilih file video",
        filetypes=[
            ("Video files", "*.mp4 *.mkv *.mov *.avi *.webm"),
            ("All files", "*.*")
        ]
    )

    if not file_path:
        raise RuntimeError("Tidak ada file yang dipilih.")

    return Path(file_path)


def get_next_output_name(input_file: Path):
    base = input_file.stem
    ext = input_file.suffix
    folder = input_file.parent

    counter = 1
    while True:
        output = folder / f"{base}_{counter}{ext}"
        if not output.exists():
            return output
        counter += 1


def cut_video(input_file: Path, output_file: Path):
    cmd = [
        "ffmpeg",
        "-ss", START_TIME,
        "-to", END_TIME,
        "-i", str(input_file),
        "-c", "copy",
        str(output_file)
    ]

    subprocess.run(cmd, check=True)


def main():
    try:
        input_video = pick_video_file()
        output_video = get_next_output_name(input_video)

        cut_video(input_video, output_video)

        messagebox.showinfo(
            "Selesai",
            f"Video berhasil dipotong:\n{output_video.name}"
        )

    except Exception as e:
        messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    main()
