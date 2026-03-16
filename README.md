# 🎬 YouTube Downloader

A lightweight, desktop GUI application for downloading YouTube videos, playlists, and audio — built with Python and powered by the [yt-dlp](https://github.com/yt-dlp/yt-dlp) library.

---

## ✨ Features


- **Single Video** — Download any YouTube video by URL
- **Multiple Videos** — Paste a list of URLs and batch-download them
- **Playlist** — Download an entire playlist, the first N videos, or a custom range
- **Quality Selection** — Best 1080p, audio-only MP3, video-only, or a custom resolution
- **Output Formats** — Default, MP4, or WebM container remuxing
- **Progress Bar** — Live download speed and ETA display
- **Safe Threading** — Downloads run in background threads; the UI stays responsive
- **Graceful Shutdown** — Confirms before cancelling an active download

---
![Download Demo](Assets/Download.gif)
---

![App Preview](Assets/3_in_1_image.png)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
---

## 📦 Dependencies

### Third-party (must be installed)

| Library | Purpose | Install |
|---|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Core download engine — fetches video/audio streams from YouTube and 1000+ other sites | `pip install yt-dlp` |
| [FFmpeg](https://ffmpeg.org/) | External binary for post-processing — merges video+audio streams, extracts MP3, remuxes containers | See [FFmpeg install guide](#3-install--update-ffmpeg) |

### Python Standard Library (built into Python — no install needed)

| Module | Purpose |
|---|---|
| `tkinter` + `ttk` | GUI framework — windows, tabs, buttons, dropdowns, progress bars |
| `tkinter.scrolledtext` | Scrollable log output area at the bottom of the window |
| `tkinter.filedialog` | Native OS folder-picker dialog (Browse button) |
| `tkinter.messagebox` | Native OS alert and confirmation dialogs |
| `threading` | Runs downloads in background threads so the UI never freezes |
| `os` | File path construction, folder creation (`os.makedirs`), home directory detection |
| `sys` | Access to the Python interpreter path (used for auto-installing yt-dlp via pip) |
| `shutil` | Detects whether FFmpeg is available on the system PATH (`shutil.which`) |
| `subprocess` | Runs pip install commands safely with error capture |
| `time` | Adds a short delay between batch downloads to reduce rate-limit risk |

> All standard library modules above are included with Python 3.8+ on all platforms. No additional installation is required for them.

### About yt-dlp

This project is built on top of **yt-dlp**, a feature-rich command-line audio/video downloader that is a community-maintained fork of the original `youtube-dl`. It supports:

- YouTube (videos, Shorts, playlists, channels, live streams)
- 1000+ other sites (Vimeo, Twitter/X, Instagram, SoundCloud, etc.)
- Format selection using powerful filter expressions (e.g., `bestvideo[height<=1080]+bestaudio`)
- Post-processing via FFmpeg (audio extraction, container remuxing, thumbnail embedding)
- Active development with frequent updates to bypass platform-side changes

> yt-dlp GitHub: https://github.com/yt-dlp/yt-dlp

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/youtube-downloader.git
cd youtube-downloader
```

### 2. Install Python dependencies

```bash
pip install yt-dlp
```

Or if you have a `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Install / Update FFmpeg

FFmpeg is required for **MP3 audio extraction** and **MP4 / WebM remuxing**. Without it, the app will still download videos in their default container.

#### Windows
```bash
# Using winget (Windows 10/11)
winget install --id Gyan.FFmpeg

# Or using Chocolatey
choco install ffmpeg
```

After installation, FFmpeg must be available in your system `PATH`. Verify with:
```bash
ffmpeg -version
```

#### macOS
```bash
brew install ffmpeg
```

#### Linux (Debian / Ubuntu)
```bash
sudo apt update && sudo apt install ffmpeg
```

#### Linux (Fedora / RHEL)
```bash
sudo dnf install ffmpeg
```

---

## 🔄 Updating Libraries

It is recommended to keep `yt-dlp` up to date, as YouTube frequently changes its internal APIs. An outdated `yt-dlp` is the most common cause of download failures.

### Update yt-dlp

```bash
# Via pip
pip install --upgrade yt-dlp

# Or using yt-dlp's built-in updater
yt-dlp -U
```

### Update FFmpeg

```bash
# Windows (winget)
winget upgrade Gyan.FFmpeg

# macOS
brew upgrade ffmpeg

# Linux
sudo apt upgrade ffmpeg
```

---

## ▶️ Running the App

```bash
python Youtube_downloader.py
```

On first run, if `yt-dlp` is not installed, the app will offer to install it automatically via pip.

---

## 🖥️ Usage

1. **Single Video tab** — Paste a YouTube URL, choose your quality and output format, then click **Download**.
2. **Multiple Videos tab** — Enter one URL per line, choose settings, then click **Download All**.
3. **Playlist tab** — Paste a playlist URL, optionally limit the range (first N, or custom indices), then click **Download Playlist**.

Downloaded files are saved to your `~/Downloads` folder by default. You can change this using the **Browse** button on any tab.

---

## ⚠️ Known Limitations & Errors

### 🔴 HTTP 429 — Too Many Requests (Rate Limiting)

When downloading **multiple videos or large playlists in quick succession**, YouTube may temporarily block your IP with an HTTP `429 Too Many Requests` error. This is a server-side rate limit and is not a bug in this application.

**You may see errors like:**
```
ERROR: [youtube] <video_id>: HTTP Error 429: Too Many Requests
❌ Error on https://...: HTTP Error 429
```

**How to handle it:**

| Action | How |
|---|---|
| Wait and retry | Pause for 5–15 minutes before trying again |
| Reduce batch size | Download fewer videos at once; avoid running multiple instances simultaneously |
| Use cookies | Export your YouTube cookies and pass them to yt-dlp to authenticate as a logged-in user, which raises rate limits |
| Use a VPN | Rotating your IP address can help bypass temporary blocks |

> **Note:** Downloading at very high frequency also risks temporary suspension of your YouTube account. Use this tool responsibly.

### Other Common Errors

| Error | Cause | Fix |
|---|---|---|
| `ffmpeg not found` | FFmpeg not installed or not in PATH | Install FFmpeg (see above) |
| `Requested format not available` | The selected quality is not available for that video | Try a different quality option |
| `Video unavailable` | Private, deleted, or geo-restricted video | Nothing can be done for private/deleted videos; try a VPN for geo-restrictions |
| `Sign in to confirm your age` | Age-restricted content | Export YouTube cookies and configure yt-dlp to use them |

---

## 📁 Project Structure

```
youtube-downloader/
├── yt_downloader_fixed.py   # Main application
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 📋 requirements.txt

Only third-party packages are listed here — standard library modules are built into Python and cannot be pip-installed.

```
# Third-party — install with: pip install -r requirements.txt
yt-dlp>=2024.1.1

# -------------------------------------------------------
# Standard library modules used (pre-installed with Python 3.8+)
# Listed here for documentation only — do NOT uncomment
# -------------------------------------------------------
# tkinter        (GUI framework)
# tkinter.ttk    (themed widgets)
# tkinter.scrolledtext
# tkinter.filedialog
# tkinter.messagebox
# threading      (background download threads)
# os             (path and folder operations)
# sys            (Python interpreter access)
# shutil         (FFmpeg PATH detection)
# subprocess     (pip install execution)
# time           (batch download delay)
```

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

> **Disclaimer:** This tool is intended for personal, non-commercial use only. Downloading copyrighted content may violate YouTube's Terms of Service and applicable laws. Always respect content creators' rights.
