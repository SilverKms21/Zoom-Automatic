**English** | [Português (Brasil)](README.pt-BR.md)

# Zoom Automatic

A Linux desktop utility with a macOS-inspired dark interface that automates dynamic camera cuts (*punch-in* and *smooth zoom*) based on speech pauses and keeps the speaker centered using facial detection.

Designed to speed up talking-head video pre-editing, **Zoom Automatic** processes raw footage, preserves the original audio track without re-encoding, and exports an edit-ready `.mp4` compatible with any non-linear video editor (including sandboxed Flatpak and AppImage builds).

---

## Features

* **Automatic Speech Pause Detection:** Analyzes the audio stream via FFmpeg (`silencedetect`) to place zoom transitions at natural pauses between sentences.
* **Face Lock (Auto-Framing):** Detects the primary face in frame with OpenCV (`Haar Cascade`) and adjusts the crop anchor point to keep the speaker centered.
* **Fast 30-Second Preview Tab:** Builds a lightweight in-memory proxy cache of the first 30 seconds for smooth playback, interactive timeline scrubbing, cut-to-cut navigation, and an optional crop-frame guide overlay.
* **Two Movement Styles:**
  * **Punch (`punch`):** Instant jump cut between wide (`1.0x`) and zoomed framing.
  * **Smooth (`smooth`):** Progressive zoom-in and zoom-out using an *ease-in-out* curve.
* **Flexible Export:** Choose between rendering the **full video** or just the **30-second preview clip** in H.264 (`libx264`, `yuv420p`, CRF 18) with direct audio stream copy (`-c:a copy`).

---

## Dependencies

### 1. Standalone Linux Executable (`Zoom-Automatic`)
The compiled binary bundles Python, Tkinter, and OpenCV. Only **FFmpeg** is required on the host system:

* **Ubuntu / Debian / Linux Mint:**
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ```
* **Fedora:**
  ```bash
  sudo dnf install -y ffmpeg
  ```
* **Arch Linux:**
  ```bash
  sudo pacman -S ffmpeg
  ```

### 2. Running or Building from Source
In addition to **FFmpeg**, running from source requires Python virtual environment and Tkinter packages:

* **System packages (Ubuntu / Debian / Mint):**
  ```bash
  sudo apt update && sudo apt install -y ffmpeg python3 python3-venv python3-tk
  ```
* **Python dependencies (`requirements.txt`):**
  * `opencv-python-headless` — frame processing, cropping, and facial detection without GUI toolkit conflicts.
  * `pyinstaller` *(optional)* — required only when packaging into a standalone binary.

---

## Quick Start (Linux Executable)

1. Download **`Zoom-Automatic`** from the **[Releases](../../releases)** page.
2. Grant execution permissions:
   ```bash
   chmod +x Zoom-Automatic
   ```
3. Launch via double-click or terminal:
   ```bash
   ./Zoom-Automatic
   ```
4. Select your **Original Video** and **Save Location**, adjust zoom settings, inspect the cuts in the **Preview** tab, and click **Export Full Video**.

---

## Running from Source

1. Clone the repository and enter the project directory:
   ```bash
   git clone [https://github.com/oudim/zoom-automatic.git](https://github.com/oudim/zoom-automatic.git)
   cd zoom-automatic
   ```

2. Create an isolated virtual environment (`.venv`) and install dependencies:
   ```bash
   python3 -m venv .venv
   .venv/bin/python -m ensurepip --upgrade
   .venv/bin/python -m pip install --upgrade pip
   .venv/bin/python -m pip install -r requirements.txt
   ```

3. Start the application:
   ```bash
   PYTHONNOUSERSITE=1 .venv/bin/python main.py
   ```

---

## Building the Standalone Executable

With `.venv` active, install PyInstaller and bundle all modules into a single Linux binary:

```bash
PYTHONNOUSERSITE=1 .venv/bin/python -m pip install pyinstaller

PYTHONNOUSERSITE=1 .venv/bin/pyinstaller \
  --onefile \
  --noconsole \
  --paths . \
  --name "Zoom-Automatic" \
  --collect-data cv2 \
  main.py
```

The compiled executable will be placed in `dist/Zoom-Automatic`.

---

## Project Structure

```text
zoom-automatic/
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── .gitignore               # Git ignore rules
├── LICENSE                  # MIT License
├── core/
│   ├── analyzer.py          # Metadata extraction, FFmpeg silence detection & face anchor
│   ├── zoom_engine.py       # Keyframe generation, easing interpolation & crop geometry
│   ├── preview_engine.py    # 30s RAM proxy cache & crop guide renderer
│   └── renderer.py          # Full/partial H.264 rendering & audio muxing
└── ui/
    ├── theme.py             # macOS Dark palette & custom canvas widgets
    ├── editor_tab.py        # Source/output file selectors, zoom settings & export worker
    ├── preview_tab.py       # Real-time preview player, timeline & cut navigation
    └── app_window.py        # Main window & segmented tab bar
```

---

## License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
