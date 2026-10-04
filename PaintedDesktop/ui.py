"""Tkinter windows. All of them run on one dedicated thread with a single hidden root:
Tk isn't thread-safe, and the old one-Tk()-per-window-per-thread approach froze and crashed."""

import logging
import os
import queue
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import ttk

from PIL import Image, ImageTk

from settings import APP_VERSION, STYLES

logger = logging.getLogger(__name__)

TITLE_FONT = ("Segoe UI Semibold", 14)
MUTED = "#6b6b6b"


def _friendly_date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%B %d, %Y at %I:%M %p").replace(" 0", " ")
    except (TypeError, ValueError):
        return "unknown"


def _present(win: tk.Toplevel):
    """Center the window and bring it in front of other apps (tray apps open behind otherwise)."""
    win.update_idletasks()
    x = (win.winfo_screenwidth() - win.winfo_reqwidth()) // 2
    y = (win.winfo_screenheight() - win.winfo_reqheight()) // 3
    win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
    win.deiconify()
    win.lift()
    win.attributes("-topmost", True)
    win.after(300, lambda: win.attributes("-topmost", False))
    win.focus_force()


class UI:
    """Owns the Tk root on its own thread. Other threads hand work over with call()/show()."""

    def __init__(self, icon_path=None):
        self._queue = queue.Queue()
        self._windows = {}
        self._icon_path = icon_path
        threading.Thread(target=self._run, name="ui", daemon=True).start()

    def _run(self):
        self.root = tk.Tk()
        self.root.withdraw()
        if self._icon_path and os.path.exists(self._icon_path):
            self._icon = tk.PhotoImage(file=self._icon_path)
            self.root.iconphoto(True, self._icon)  # default icon for every window
        self._poll()
        self.root.mainloop()

    def _poll(self):
        while True:
            try:
                fn = self._queue.get_nowait()
            except queue.Empty:
                break
            try:
                fn()
            except Exception:
                logger.exception("UI error")
        self.root.after(100, self._poll)

    def call(self, fn):
        self._queue.put(fn)

    def show(self, key: str, factory):
        """Open the window built by factory(root), or raise it if it's already open."""
        def open_window():
            win = self._windows.get(key)
            if win is not None and win.winfo_exists():
                _present(win)
            else:
                self._windows[key] = factory(self.root)
        self.call(open_window)

    def quit(self):
        self.call(lambda: self.root.quit())


class InfoWindow(tk.Toplevel):
    """Details of one painting, with a preview."""

    def __init__(self, root, entry: dict):
        super().__init__(root)
        self.withdraw()
        self.title("What's on my desktop?")
        self.resizable(False, False)
        scale = self.winfo_fpixels("1i") / 96
        width = int(520 * scale)

        frame = ttk.Frame(self, padding=int(16 * scale))
        frame.pack(fill="both", expand=True)

        path = entry.get("image_path")
        has_image = bool(path) and os.path.exists(path)
        if has_image:
            try:
                img = Image.open(path)
                img.thumbnail((width, int(width * 0.75)))
                self._photo = ImageTk.PhotoImage(img)  # keep a reference or Tk shows a blank
                ttk.Label(frame, image=self._photo).pack(pady=(0, 12))
            except Exception as e:
                logger.debug(f"No preview for {path}: {e}")

        ttk.Label(frame, text=entry.get("title") or "Untitled", font=TITLE_FONT,
                  wraplength=width, justify="left").pack(anchor="w")
        details = [entry.get("artist"), entry.get("year"), entry.get("source_institution")]
        ttk.Label(frame, text="\n".join(d for d in details if d), wraplength=width,
                  justify="left").pack(anchor="w", pady=(4, 0))
        ttk.Label(frame, text=f"Set {_friendly_date(entry.get('date_set'))}",
                  foreground=MUTED).pack(anchor="w", pady=(8, 0))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(16, 0))
        url = entry.get("source_url")
        if url:
            ttk.Button(buttons, text="More about this painting",
                       command=lambda: webbrowser.open(url)).pack(side="left")
        if has_image:
            ttk.Button(buttons, text="Open image",
                       command=lambda: os.startfile(path)).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Close", command=self.destroy).pack(side="right")
        self.bind("<Escape>", lambda e: self.destroy())
        _present(self)


class HistoryWindow(tk.Toplevel):
    def __init__(self, root, history: list):
        super().__init__(root)
        self.withdraw()
        self.title("Wallpaper History")
        scale = self.winfo_fpixels("1i") / 96
        self.geometry(f"{int(760 * scale)}x{int(480 * scale)}")
        self.minsize(int(480 * scale), int(260 * scale))

        frame = ttk.Frame(self, padding=int(12 * scale))
        frame.pack(fill="both", expand=True)
        count = len(history)
        summary = (f"{count} painting{'s' if count != 1 else ''} so far. Double-click one for details."
                   if count else "No wallpapers yet. Use “Change now” from the tray menu.")
        ttk.Label(frame, text=summary, foreground=MUTED).pack(anchor="w", pady=(0, 8))

        ttk.Style(self).configure("History.Treeview", rowheight=int(24 * scale))
        table = ttk.Frame(frame)
        table.pack(fill="both", expand=True)
        columns = {"date": ("Date", 100), "title": ("Title", 280), "artist": ("Artist", 200),
                   "source": ("Source", 140)}
        tree = ttk.Treeview(table, columns=list(columns), show="headings", style="History.Treeview")
        for key, (label, w) in columns.items():
            tree.heading(key, text=label, anchor="w")
            tree.column(key, width=int(w * scale), anchor="w", stretch=key == "title")
        scrollbar = ttk.Scrollbar(table, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i, entry in enumerate(history):
            tree.insert("", "end", iid=str(i), values=(
                (entry.get("date_set") or "")[:10], entry.get("title") or "Untitled",
                (entry.get("artist") or "").split(" (")[0], entry.get("source_institution") or ""))

        def open_selected(_event=None):
            for iid in tree.selection():
                InfoWindow(root, history[int(iid)])

        tree.bind("<Double-1>", open_selected)
        tree.bind("<Return>", open_selected)

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Details", command=open_selected).pack(side="left")
        ttk.Button(buttons, text="Close", command=self.destroy).pack(side="right")
        self.bind("<Escape>", lambda e: self.destroy())
        _present(self)


class SettingsWindow(tk.Toplevel):
    def __init__(self, root, settings, screen, data_dir: str, on_save=None):
        super().__init__(root)
        self.withdraw()
        self.title("PaintedDesktop Settings")
        self.resizable(False, False)
        self.settings = settings
        self.on_save = on_save
        scale = self.winfo_fpixels("1i") / 96
        pad = int(16 * scale)

        frame = ttk.Frame(self, padding=pad)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        row = 0

        def section(text):
            nonlocal row
            ttk.Label(frame, text=text, font=("Segoe UI Semibold", 10)).grid(
                row=row, column=0, sticky="nw", pady=(0, 14), padx=(0, pad))

        # Daily change time
        section("New painting daily at")
        change = settings.get_change_time()
        self.hour = tk.StringVar(value=f"{change.hour:02d}")
        self.minute = tk.StringVar(value=f"{change.minute:02d}")
        time_row = ttk.Frame(frame)
        time_row.grid(row=row, column=1, sticky="w", pady=(0, 14))
        ttk.Spinbox(time_row, from_=0, to=23, width=3, format="%02.0f", wrap=True,
                    textvariable=self.hour).pack(side="left")
        ttk.Label(time_row, text=" : ").pack(side="left")
        ttk.Spinbox(time_row, from_=0, to=59, width=3, format="%02.0f", wrap=True,
                    textvariable=self.minute).pack(side="left")
        ttk.Label(time_row, text="  (24-hour)", foreground=MUTED).pack(side="left")
        row += 1

        # Painting types
        section("Paintings")
        styles_box = ttk.Frame(frame)
        styles_box.grid(row=row, column=1, sticky="w", pady=(0, 14))
        current = set(settings.get_art_styles())
        self.styles = {key: tk.BooleanVar(value=key in current) for key in STYLES}
        for key, label in STYLES.items():
            ttk.Checkbutton(styles_box, text=label, variable=self.styles[key]).pack(anchor="w")
        row += 1

        # Display mode
        section("Display")
        mode_box = ttk.Frame(frame)
        mode_box.grid(row=row, column=1, sticky="w", pady=(0, 14))
        self.mode = tk.StringVar(value=settings.get_display_mode())
        ttk.Radiobutton(mode_box, text="Fit: show the whole painting (black bars)",
                        value="fit", variable=self.mode).pack(anchor="w")
        ttk.Radiobutton(mode_box, text="Fill: cover the screen (edges cropped)",
                        value="fill", variable=self.mode).pack(anchor="w")
        row += 1

        # Minimum image size
        section("Image size")
        size_box = ttk.Frame(frame)
        size_box.grid(row=row, column=1, sticky="w", pady=(0, 14))
        custom = settings.get_min_resolution()
        self.auto_size = tk.BooleanVar(value=custom is None)
        ttk.Checkbutton(size_box, text=f"Match my screen ({screen[0]} × {screen[1]})",
                        variable=self.auto_size, command=self._toggle_size).pack(anchor="w")
        custom_row = ttk.Frame(size_box)
        custom_row.pack(anchor="w", pady=(4, 0))
        self.width = tk.StringVar(value=str((custom or screen)[0]))
        self.height = tk.StringVar(value=str((custom or screen)[1]))
        ttk.Label(custom_row, text="At least").pack(side="left")
        self.size_inputs = [
            ttk.Spinbox(custom_row, from_=640, to=15360, increment=10, width=6, textvariable=self.width),
            ttk.Spinbox(custom_row, from_=480, to=8640, increment=10, width=6, textvariable=self.height),
        ]
        self.size_inputs[0].pack(side="left", padx=(6, 0))
        ttk.Label(custom_row, text="×").pack(side="left", padx=4)
        self.size_inputs[1].pack(side="left")
        ttk.Label(custom_row, text="px").pack(side="left", padx=(4, 0))
        self._toggle_size()
        row += 1

        # Startup
        section("Startup")
        self.startup = tk.BooleanVar(value=bool(settings.get("launch_at_startup", True)))
        ttk.Checkbutton(frame, text="Launch PaintedDesktop when I sign in to Windows",
                        variable=self.startup).grid(row=row, column=1, sticky="w", pady=(0, 14))
        row += 1

        # Lock screen
        section("Lock screen")
        self.lock_screen = tk.BooleanVar(value=bool(settings.get("set_lock_screen", True)))
        ttk.Checkbutton(frame, text="Use the painting as my lock screen too",
                        variable=self.lock_screen).grid(row=row, column=1, sticky="w", pady=(0, 14))
        row += 1

        self.error = ttk.Label(frame, text="", foreground="#c42b1c")
        self.error.grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1

        buttons = ttk.Frame(frame)
        buttons.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(buttons, text=f"PaintedDesktop {APP_VERSION}", foreground=MUTED).pack(side="left")
        ttk.Button(buttons, text="Open data folder",
                   command=lambda: os.startfile(data_dir)).pack(side="left", padx=(12, 0))
        ttk.Button(buttons, text="Save", command=self._save).pack(side="right")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right", padx=(0, 8))
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._save())
        _present(self)

    def _toggle_size(self):
        state = "disabled" if self.auto_size.get() else "normal"
        for widget in self.size_inputs:
            widget.configure(state=state)

    def _save(self):
        try:
            hour, minute = int(self.hour.get()), int(self.minute.get())
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError
        except ValueError:
            return self.error.configure(text="Enter a time between 00:00 and 23:59.")
        styles = [key for key, var in self.styles.items() if var.get()]
        if not styles:
            return self.error.configure(text="Pick at least one kind of painting.")
        size = None
        if not self.auto_size.get():
            try:
                size = (int(self.width.get()), int(self.height.get()))
                if min(size) <= 0:
                    raise ValueError
            except ValueError:
                return self.error.configure(text="Enter a valid width and height in pixels.")

        self.settings.set_change_time(hour, minute)
        self.settings.set("art_styles", styles)
        self.settings.set("display_mode", self.mode.get())
        self.settings.set_min_resolution(*(size or (None, None)))
        self.settings.set("launch_at_startup", self.startup.get())
        self.settings.set("set_lock_screen", self.lock_screen.get())
        self.destroy()
        if self.on_save:
            self.on_save()
