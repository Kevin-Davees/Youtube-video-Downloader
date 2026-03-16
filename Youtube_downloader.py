import os
import sys
import shutil
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# ------------------------------------------------------------
#  Ensure yt-dlp is installed
#  FIX: Use subprocess instead of os.system; destroy temp root
# ------------------------------------------------------------
def setup():
    try:
        import yt_dlp
        return True
    except ImportError:
        temp_root = tk.Tk()
        temp_root.withdraw()
        answer = messagebox.askyesno(
            "yt-dlp missing",
            "yt-dlp is not installed. Install it now? (requires pip)",
            parent=temp_root
        )
        if answer:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "yt-dlp"],
                    check=True,
                    capture_output=True
                )
                import yt_dlp  # noqa: F401
                temp_root.destroy()
                return True
            except subprocess.CalledProcessError as e:
                messagebox.showerror(
                    "Error",
                    f"Installation failed:\n{e.stderr.decode()}\n\nPlease install manually: pip install yt-dlp",
                    parent=temp_root
                )
                temp_root.destroy()
                return False
        else:
            temp_root.destroy()
            return False


# ------------------------------------------------------------
#  FFmpeg availability check
#  FIX: Warn user upfront if FFmpeg is missing
# ------------------------------------------------------------
def check_ffmpeg():
    return shutil.which("ffmpeg") is not None


# ------------------------------------------------------------
#  Main application class
# ------------------------------------------------------------
class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("750x700")
        self.root.resizable(True, True)

        # FIX: Stop event for graceful thread shutdown
        self._stop_event = threading.Event()
        self.download_thread = None

        # Bright theme colors
        self.bg_color      = "#F0F0F0"
        self.fg_color      = "#000000"
        self.accent_color  = "#0078D7"
        self.secondary_bg  = "#FFFFFF"
        self.entry_bg      = "#FFFFFF"
        self.button_bg     = "#E1E1E1"

        self.root.configure(bg=self.bg_color)

        # Style configuration for ttk widgets
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', background=self.bg_color, foreground=self.fg_color,
                             fieldbackground=self.entry_bg)
        self.style.configure('TLabel',          background=self.bg_color, foreground=self.fg_color)
        self.style.configure('TFrame',          background=self.bg_color)
        self.style.configure('TLabelframe',     background=self.bg_color, foreground=self.fg_color)
        self.style.configure('TLabelframe.Label', background=self.bg_color, foreground=self.fg_color)
        self.style.configure('TButton',         background=self.button_bg, foreground=self.fg_color,
                             borderwidth=1, focusthickness=0)
        self.style.map('TButton',
                       background=[('active', self.accent_color), ('disabled', '#C0C0C0')],
                       foreground=[('active', 'white'),           ('disabled', '#888888')])
        self.style.configure('TEntry',          fieldbackground=self.entry_bg, foreground=self.fg_color)
        self.style.configure('TCombobox',       fieldbackground=self.entry_bg, foreground=self.fg_color)
        self.style.configure('Vertical.TScrollbar',   background=self.button_bg, troughcolor=self.bg_color)
        self.style.configure('Horizontal.TProgressbar', background=self.accent_color, troughcolor=self.secondary_bg)

        # Notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.single_tab   = ttk.Frame(self.notebook)
        self.multi_tab    = ttk.Frame(self.notebook)
        self.playlist_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.single_tab,   text="Single Video")
        self.notebook.add(self.multi_tab,    text="Multiple Videos")
        self.notebook.add(self.playlist_tab, text="Playlist")

        # Build each tab
        self.build_single_tab()
        self.build_multi_tab()
        self.build_playlist_tab()

        # Global progress bar and status (shared)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var,
                                            maximum=100, length=100, mode='determinate')
        self.progress_bar.pack(fill='x', padx=10, pady=(0, 5))

        self.status_label = ttk.Label(root, text="Ready", anchor='w')
        self.status_label.pack(fill='x', padx=10, pady=(0, 5))

        # Log area
        self.log_text = scrolledtext.ScrolledText(
            root, height=8, bg=self.secondary_bg,
            fg=self.fg_color, insertbackground=self.fg_color
        )
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Bind closing event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # FIX: Warn if FFmpeg is missing (needed for MP3 extraction and remuxing)
        if not check_ffmpeg():
            self.root.after(500, lambda: messagebox.showwarning(
                "FFmpeg not found",
                "FFmpeg was not found on your system.\n\n"
                "Audio extraction (MP3) and container remuxing (MP4/WebM) require FFmpeg.\n"
                "Download it from https://ffmpeg.org and add it to your system PATH."
            ))

    # --------------------------------------------------------
    #  Thread-safe UI helpers
    #  FIX: All UI updates scheduled on main thread via root.after
    # --------------------------------------------------------
    def log(self, message):
        """Thread-safe log — callable from any thread."""
        self.root.after(0, self._log_safe, message)

    def _log_safe(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def set_status(self, text):
        """Thread-safe status update."""
        self.root.after(0, self._set_status_safe, text)

    def _set_status_safe(self, text):
        self.status_label.config(text=text)

    def set_progress(self, percent):
        """Thread-safe progress bar update."""
        self.root.after(0, self.progress_var.set, percent)

    def reset_progress(self):
        self.root.after(0, self.progress_var.set, 0)

    # --------------------------------------------------------
    #  FIX: Button enable/disable helpers
    # --------------------------------------------------------
    def set_buttons_state(self, state):
        """Enable or disable all download buttons. state = 'normal' or 'disabled'."""
        for btn in (self._single_btn, self._multi_btn, self._playlist_btn):
            btn.config(state=state)

    def _download_started(self):
        self._stop_event.clear()
        self.root.after(0, self.set_buttons_state, 'disabled')

    def _download_finished(self):
        self.root.after(0, self.set_buttons_state, 'normal')

    # --------------------------------------------------------
    #  Helper: browse folder
    # --------------------------------------------------------
    def browse_folder(self, entry_widget):
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)

    # --------------------------------------------------------
    #  Single video tab
    # --------------------------------------------------------
    def build_single_tab(self):
        frame = self.single_tab
        row = 0

        # URL
        ttk.Label(frame, text="Video URL:").grid(row=row, column=0, sticky='w', padx=10, pady=(10, 5))
        self.single_url = ttk.Entry(frame, width=70)
        self.single_url.grid(row=row, column=1, columnspan=3, sticky='ew', padx=10, pady=(10, 5))
        row += 1

        # Folder selection
        ttk.Label(frame, text="Download folder:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.single_folder = ttk.Entry(frame, width=60)
        self.single_folder.grid(row=row, column=1, sticky='ew', padx=5, pady=5)
        self.single_folder.insert(0, os.path.join(os.path.expanduser("~"), "Downloads"))
        ttk.Button(frame, text="Browse",
                   command=lambda: self.browse_folder(self.single_folder)).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        # Quality options
        ttk.Label(frame, text="Quality:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.single_quality = ttk.Combobox(frame, values=[
            "Best video+audio (<=1080p)",
            "Audio only (MP3)",
            "Video only (best)",
            "Custom resolution"
        ], state="readonly", width=40)
        self.single_quality.grid(row=row, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        self.single_quality.current(0)
        row += 1

        # Custom resolution entry (hidden initially)
        # FIX: Store hint label in self so toggle can show/hide it
        self.single_custom_res_label = ttk.Label(frame, text="Max height:")
        self.single_custom_res_label.grid(row=row, column=0, sticky='w', padx=10, pady=(0, 5))
        self.single_custom_res_label.grid_remove()

        self.single_custom_res = ttk.Entry(frame, width=20)
        self.single_custom_res.grid(row=row, column=1, sticky='w', padx=5, pady=(0, 5))
        self.single_custom_res.grid_remove()

        self.single_custom_res_hint = ttk.Label(frame, text="e.g., 720, 480, 2160", foreground='gray')
        self.single_custom_res_hint.grid(row=row, column=2, sticky='w', padx=5, pady=(0, 5))
        self.single_custom_res_hint.grid_remove()
        row += 1

        # Output format (container)
        ttk.Label(frame, text="Output format:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.single_container = ttk.Combobox(frame, values=["Default", "MP4", "WebM"],
                                             state="readonly", width=20)
        self.single_container.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        self.single_container.current(0)
        row += 1

        self.single_quality.bind('<<ComboboxSelected>>', self.toggle_custom_res_single)

        # FIX: Store button reference for enable/disable
        self._single_btn = ttk.Button(frame, text="Download", command=self.start_single_download)
        self._single_btn.grid(row=row, column=1, pady=20)

        frame.columnconfigure(1, weight=1)

    def toggle_custom_res_single(self, event=None):
        if self.single_quality.get() == "Custom resolution":
            self.single_custom_res_label.grid()
            self.single_custom_res.grid()
            self.single_custom_res_hint.grid()
        else:
            self.single_custom_res_label.grid_remove()
            self.single_custom_res.grid_remove()
            self.single_custom_res_hint.grid_remove()

    # --------------------------------------------------------
    #  Multiple videos tab
    # --------------------------------------------------------
    def build_multi_tab(self):
        frame = self.multi_tab
        row = 0

        ttk.Label(frame, text="Enter URLs (one per line):").grid(
            row=row, column=0, sticky='w', padx=10, pady=(10, 0))
        row += 1
        self.multi_urls_text = tk.Text(frame, height=6, bg=self.entry_bg,
                                       fg=self.fg_color, insertbackground=self.fg_color)
        self.multi_urls_text.grid(row=row, column=0, columnspan=3, sticky='ew', padx=10, pady=5)
        row += 1

        ttk.Label(frame, text="Download folder:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.multi_folder = ttk.Entry(frame, width=60)
        self.multi_folder.grid(row=row, column=1, sticky='ew', padx=5, pady=5)
        self.multi_folder.insert(0, os.path.join(os.path.expanduser("~"), "Downloads"))
        ttk.Button(frame, text="Browse",
                   command=lambda: self.browse_folder(self.multi_folder)).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        ttk.Label(frame, text="Quality:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.multi_quality = ttk.Combobox(frame, values=[
            "Best video+audio (<=1080p)",
            "Audio only (MP3)",
            "Video only (best)",
            "Custom resolution"
        ], state="readonly", width=40)
        self.multi_quality.grid(row=row, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        self.multi_quality.current(0)
        row += 1

        # FIX: Store hint label in self
        self.multi_custom_res_label = ttk.Label(frame, text="Max height:")
        self.multi_custom_res_label.grid(row=row, column=0, sticky='w', padx=10, pady=(0, 5))
        self.multi_custom_res_label.grid_remove()

        self.multi_custom_res = ttk.Entry(frame, width=20)
        self.multi_custom_res.grid(row=row, column=1, sticky='w', padx=5, pady=(0, 5))
        self.multi_custom_res.grid_remove()

        self.multi_custom_res_hint = ttk.Label(frame, text="e.g., 720, 480, 2160", foreground='gray')
        self.multi_custom_res_hint.grid(row=row, column=2, sticky='w', padx=5, pady=(0, 5))
        self.multi_custom_res_hint.grid_remove()
        row += 1

        ttk.Label(frame, text="Output format:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.multi_container = ttk.Combobox(frame, values=["Default", "MP4", "WebM"],
                                            state="readonly", width=20)
        self.multi_container.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        self.multi_container.current(0)
        row += 1

        self.multi_quality.bind('<<ComboboxSelected>>', self.toggle_custom_res_multi)

        # FIX: Store button reference
        self._multi_btn = ttk.Button(frame, text="Download All", command=self.start_multi_download)
        self._multi_btn.grid(row=row, column=1, pady=20)

        frame.columnconfigure(1, weight=1)

    def toggle_custom_res_multi(self, event=None):
        if self.multi_quality.get() == "Custom resolution":
            self.multi_custom_res_label.grid()
            self.multi_custom_res.grid()
            self.multi_custom_res_hint.grid()
        else:
            self.multi_custom_res_label.grid_remove()
            self.multi_custom_res.grid_remove()
            self.multi_custom_res_hint.grid_remove()

    # --------------------------------------------------------
    #  Playlist tab
    # --------------------------------------------------------
    def build_playlist_tab(self):
        frame = self.playlist_tab
        row = 0

        ttk.Label(frame, text="Playlist URL:").grid(row=row, column=0, sticky='w', padx=10, pady=(10, 5))
        self.playlist_url = ttk.Entry(frame, width=70)
        self.playlist_url.grid(row=row, column=1, columnspan=3, sticky='ew', padx=10, pady=(10, 5))
        row += 1

        ttk.Label(frame, text="Range:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.playlist_range = ttk.Combobox(frame, values=[
            "Entire playlist",
            "First N videos",
            "Custom items"
        ], state="readonly", width=40)
        self.playlist_range.grid(row=row, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        self.playlist_range.current(0)
        row += 1

        self.playlist_n_label = ttk.Label(frame, text="Number of videos:")
        self.playlist_n_label.grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.playlist_n_label.grid_remove()
        self.playlist_n_entry = ttk.Entry(frame, width=20)
        self.playlist_n_entry.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        self.playlist_n_entry.grid_remove()
        row += 1

        self.playlist_custom_label = ttk.Label(frame, text="Items (e.g., 1-10, 3,5,8):")
        self.playlist_custom_label.grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.playlist_custom_label.grid_remove()
        self.playlist_custom_entry = ttk.Entry(frame, width=50)
        self.playlist_custom_entry.grid(row=row, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
        self.playlist_custom_entry.grid_remove()
        row += 1

        self.playlist_range.bind('<<ComboboxSelected>>', self.toggle_playlist_range)

        ttk.Label(frame, text="Download folder:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.playlist_folder = ttk.Entry(frame, width=60)
        self.playlist_folder.grid(row=row, column=1, sticky='ew', padx=5, pady=5)
        self.playlist_folder.insert(0, os.path.join(os.path.expanduser("~"), "Downloads"))
        ttk.Button(frame, text="Browse",
                   command=lambda: self.browse_folder(self.playlist_folder)).grid(row=row, column=2, padx=5, pady=5)
        row += 1

        ttk.Label(frame, text="Playlist subfolder (optional):").grid(
            row=row, column=0, sticky='w', padx=10, pady=5)
        self.playlist_subfolder = ttk.Entry(frame, width=60)
        self.playlist_subfolder.grid(row=row, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
        row += 1

        ttk.Label(frame, text="Quality:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.playlist_quality = ttk.Combobox(frame, values=[
            "Best video+audio (<=1080p)",
            "Audio only (MP3)",
            "Video only (best)",
            "Custom resolution"
        ], state="readonly", width=40)
        self.playlist_quality.grid(row=row, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        self.playlist_quality.current(0)
        row += 1

        # FIX: Store hint label in self
        self.playlist_custom_res_label = ttk.Label(frame, text="Max height:")
        self.playlist_custom_res_label.grid(row=row, column=0, sticky='w', padx=10, pady=(0, 5))
        self.playlist_custom_res_label.grid_remove()

        self.playlist_custom_res = ttk.Entry(frame, width=20)
        self.playlist_custom_res.grid(row=row, column=1, sticky='w', padx=5, pady=(0, 5))
        self.playlist_custom_res.grid_remove()

        self.playlist_custom_res_hint = ttk.Label(frame, text="e.g., 720, 480, 2160", foreground='gray')
        self.playlist_custom_res_hint.grid(row=row, column=2, sticky='w', padx=5, pady=(0, 5))
        self.playlist_custom_res_hint.grid_remove()
        row += 1

        ttk.Label(frame, text="Output format:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.playlist_container = ttk.Combobox(frame, values=["Default", "MP4", "WebM"],
                                               state="readonly", width=20)
        self.playlist_container.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        self.playlist_container.current(0)
        row += 1

        self.playlist_quality.bind('<<ComboboxSelected>>', self.toggle_custom_res_playlist)

        # FIX: Store button reference
        self._playlist_btn = ttk.Button(frame, text="Download Playlist", command=self.start_playlist_download)
        self._playlist_btn.grid(row=row, column=1, pady=20)

        frame.columnconfigure(1, weight=1)

    def toggle_playlist_range(self, event=None):
        self.playlist_n_label.grid_remove()
        self.playlist_n_entry.grid_remove()
        self.playlist_custom_label.grid_remove()
        self.playlist_custom_entry.grid_remove()

        selection = self.playlist_range.get()
        if selection == "First N videos":
            self.playlist_n_label.grid()
            self.playlist_n_entry.grid()
        elif selection == "Custom items":
            self.playlist_custom_label.grid()
            self.playlist_custom_entry.grid()

    def toggle_custom_res_playlist(self, event=None):
        if self.playlist_quality.get() == "Custom resolution":
            self.playlist_custom_res_label.grid()
            self.playlist_custom_res.grid()
            self.playlist_custom_res_hint.grid()
        else:
            self.playlist_custom_res_label.grid_remove()
            self.playlist_custom_res.grid_remove()
            self.playlist_custom_res_hint.grid_remove()

    # --------------------------------------------------------
    #  Helper: parse quality selection into yt-dlp format
    # --------------------------------------------------------
    def get_format_and_audio(self, quality_widget, custom_res_widget):
        text = quality_widget.get()
        if text == "Best video+audio (<=1080p)":
            return 'bestvideo[height<=1080]+bestaudio/best', False
        elif text == "Audio only (MP3)":
            return 'bestaudio/best', True
        elif text == "Video only (best)":
            return 'bestvideo/best', False
        elif text == "Custom resolution":
            res = custom_res_widget.get().strip()
            if res.isdigit():
                return f'bestvideo[height<={res}]+bestaudio/best', False
            else:
                messagebox.showerror("Error", "Invalid resolution. Falling back to 1080p.")
                return 'bestvideo[height<=1080]+bestaudio/best', False
        else:
            return 'bestvideo[height<=1080]+bestaudio/best', False

    def get_container_postprocessor(self, container_widget):
        """Return a postprocessor dict for remuxing, or None."""
        container = container_widget.get()
        if container == "MP4":
            # FIX: Corrected typo 'preferedformat' → 'preferredformat'
            return {'key': 'FFmpegVideoRemuxer', 'preferredformat': 'mp4'}
        elif container == "WebM":
            return {'key': 'FFmpegVideoRemuxer', 'preferredformat': 'webm'}
        else:
            return None

    # --------------------------------------------------------
    #  Download functions (run in threads)
    # --------------------------------------------------------
    def start_single_download(self):
        url = self.single_url.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        folder = self.single_folder.get().strip()
        if not folder:
            folder = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(folder, exist_ok=True)

        fmt, extract_audio = self.get_format_and_audio(self.single_quality, self.single_custom_res)
        container_pp = self.get_container_postprocessor(self.single_container)

        self._download_started()
        self.download_thread = threading.Thread(
            target=self.download_single,
            args=(url, folder, fmt, extract_audio, container_pp),
            daemon=True
        )
        self.download_thread.start()

    def download_single(self, url, folder, fmt, extract_audio, container_pp):
        import yt_dlp
        self.log(f"Starting download: {url}")
        self.set_status("Downloading...")
        self.reset_progress()

        ydl_opts = {
            'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
            'format': fmt,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self.progress_hook],
        }
        postprocessors = []
        if extract_audio:
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            })
        if container_pp and not extract_audio:
            postprocessors.append(container_pp)
        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.log(f"✅ Download complete: {url}")
            self.set_status("Download complete")
        except Exception as e:
            self.log(f"❌ Error: {e}")
            self.set_status("Error occurred")
        finally:
            self.reset_progress()
            self._download_finished()

    def start_multi_download(self):
        urls_text = self.multi_urls_text.get("1.0", tk.END).strip()
        if not urls_text:
            messagebox.showerror("Error", "Please enter at least one URL")
            return
        urls = [line.strip() for line in urls_text.splitlines() if line.strip()]
        folder = self.multi_folder.get().strip()
        if not folder:
            folder = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(folder, exist_ok=True)

        fmt, extract_audio = self.get_format_and_audio(self.multi_quality, self.multi_custom_res)
        container_pp = self.get_container_postprocessor(self.multi_container)

        self._download_started()
        self.download_thread = threading.Thread(
            target=self.download_multiple,
            args=(urls, folder, fmt, extract_audio, container_pp),
            daemon=True
        )
        self.download_thread.start()

    def download_multiple(self, urls, folder, fmt, extract_audio, container_pp):
        import yt_dlp
        total = len(urls)
        self.log(f"Starting download of {total} videos")
        self.set_status("Downloading...")
        self.reset_progress()

        ydl_opts = {
            'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
            'format': fmt,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self.progress_hook],
        }
        postprocessors = []
        if extract_audio:
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            })
        if container_pp and not extract_audio:
            postprocessors.append(container_pp)
        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors

        successful = 0
        failed = 0
        for i, url in enumerate(urls, 1):
            # FIX: Respect stop event — abort remaining downloads on close
            if self._stop_event.is_set():
                self.log("⚠️ Download cancelled by user.")
                break

            self.log(f"[{i}/{total}] Downloading: {url}")
            self.set_status(f"Downloading {i}/{total}...")

            # FIX: Show overall batch progress (not just per-file)
            overall_pct = ((i - 1) / total) * 100
            self.set_progress(overall_pct)

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                successful += 1
            except Exception as e:
                self.log(f"❌ Error on {url}: {e}")
                failed += 1
            time.sleep(1)

        self.log(f"✅ Summary: {successful} successful, {failed} failed")
        self.set_status("Batch download finished")
        self.reset_progress()
        self._download_finished()

    def start_playlist_download(self):
        url = self.playlist_url.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a playlist URL")
            return

        folder = self.playlist_folder.get().strip()
        if not folder:
            folder = os.path.join(os.path.expanduser("~"), "Downloads")
        subfolder = self.playlist_subfolder.get().strip()
        if subfolder:
            folder = os.path.join(folder, subfolder)
        os.makedirs(folder, exist_ok=True)

        range_choice = self.playlist_range.get()
        playlist_items = None
        if range_choice == "First N videos":
            n = self.playlist_n_entry.get().strip()
            if n.isdigit():
                playlist_items = f"1-{n}"
            else:
                messagebox.showerror("Error", "Invalid number")
                return
        elif range_choice == "Custom items":
            playlist_items = self.playlist_custom_entry.get().strip()
            if not playlist_items:
                messagebox.showerror("Error", "Please enter items")
                return

        fmt, extract_audio = self.get_format_and_audio(self.playlist_quality, self.playlist_custom_res)
        container_pp = self.get_container_postprocessor(self.playlist_container)

        self._download_started()
        self.download_thread = threading.Thread(
            target=self.download_playlist,
            args=(url, folder, fmt, extract_audio, container_pp, playlist_items),
            daemon=True
        )
        self.download_thread.start()

    def download_playlist(self, url, folder, fmt, extract_audio, container_pp, playlist_items):
        import yt_dlp
        self.log(f"Starting playlist download: {url}")
        self.set_status("Downloading playlist...")
        self.reset_progress()

        ydl_opts = {
            'outtmpl': os.path.join(folder, '%(playlist_index)s - %(title)s.%(ext)s'),
            'format': fmt,
            'quiet': True,
            'no_warnings': True,
            'yes_playlist': True,
            'progress_hooks': [self.progress_hook],
        }
        if playlist_items:
            ydl_opts['playlist_items'] = playlist_items

        postprocessors = []
        if extract_audio:
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            })
        if container_pp and not extract_audio:
            postprocessors.append(container_pp)
        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.log("✅ Playlist download complete")
            self.set_status("Playlist download finished")
        except Exception as e:
            self.log(f"❌ Error: {e}")
            self.set_status("Error occurred")
        finally:
            self.reset_progress()
            self._download_finished()

    # --------------------------------------------------------
    #  Progress hook (called from download thread)
    #  FIX: UI updates scheduled on main thread via root.after
    # --------------------------------------------------------
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total:
                downloaded = d.get('downloaded_bytes', 0)
                percent = downloaded / total * 100
                self.root.after(0, self.progress_var.set, percent)
            speed = d.get('_speed_str', 'N/A')
            eta   = d.get('_eta_str',   'N/A')
            self.root.after(0, self._set_status_safe, f"Downloading... {speed}  ETA: {eta}")
        elif d['status'] == 'finished':
            self.root.after(0, self._set_status_safe, "Processing...")

    # --------------------------------------------------------
    #  Close handler
    #  FIX: Signal stop event before closing to allow clean abort
    # --------------------------------------------------------
    def on_closing(self):
        if self.download_thread and self.download_thread.is_alive():
            if messagebox.askokcancel("Quit", "Download in progress. Really quit?"):
                self._stop_event.set()   # Signal worker thread to stop
                self.root.destroy()
        else:
            self.root.destroy()


# ------------------------------------------------------------
#  Main entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    if not setup():
        sys.exit(1)
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
