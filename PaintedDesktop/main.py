"""PaintedDesktop: a tray app that sets a new oil-painting wallpaper every day."""

import ctypes
import itertools
import logging
import os
import random
import sys
import threading
from datetime import datetime, time, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import pystray
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from fetcher import ARTICFetcher, RijksmuseumFetcher, WikimediaFetcher
from history import HistoryManager
from settings import APP_VERSION, SettingsManager
from ui import UI, HistoryWindow, InfoWindow, SettingsWindow
from wallpaper import enable_dpi_awareness, get_monitor_resolution, register_startup, set_wallpaper

SOURCES = (ARTICFetcher, RijksmuseumFetcher, WikimediaFetcher)  # priority order
ATTEMPTS_PER_SOURCE = 6
MAX_RETRY_DELAY = timedelta(minutes=15)
CACHE_SIZE = 30
ASSETS = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "assets"

logger = logging.getLogger("PaintedDesktop")


def get_app_data_dir() -> str:
    appdata = os.environ.get("APPDATA")
    return os.path.join(appdata, "PaintedDesktop") if appdata else os.path.expanduser("~/.painteddesktop")


def setup_logging(data_dir: str):
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.INFO)  # DEBUG from urllib3/PIL filled the log in days
    handler = RotatingFileHandler(Path(data_dir) / "app.log", maxBytes=1024 * 1024,
                                  backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    root.addHandler(handler)
    if sys.stderr:  # None in the windowed exe
        root.addHandler(logging.StreamHandler())
    sys.excepthook = lambda *exc: logger.critical("Unhandled exception", exc_info=exc)
    threading.excepthook = lambda args: logger.critical(
        f"Unhandled exception in {args.thread.name}",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


def last_scheduled_time(now: datetime, change_time: time) -> datetime:
    """The most recent daily change moment at or before now."""
    today = datetime.combine(now.date(), change_time)
    return today if now >= today else today - timedelta(days=1)


def is_change_due(last_set: Optional[datetime], now: datetime, change_time: time) -> bool:
    """True if no wallpaper has been set since the most recent scheduled change time.
    This also catches up after the PC was off or asleep at the change time."""
    return last_set is None or last_set < last_scheduled_time(now, change_time)


def retry_delay(failures: int) -> timedelta:
    """1, 2, 4, 8 then 15 minutes. Quick at first because boot-time failures are usually
    the network not being up yet."""
    return min(timedelta(minutes=2 ** max(failures - 1, 0)), MAX_RETRY_DELAY)


_instance_mutex = None


def already_running() -> bool:
    global _instance_mutex
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _instance_mutex = kernel32.CreateMutexW(None, False, "Local\\PaintedDesktop.SingleInstance")
    return ctypes.get_last_error() == 183  # ERROR_ALREADY_EXISTS


class PaintedDesktop:
    def __init__(self):
        self.app_data_dir = get_app_data_dir()
        setup_logging(self.app_data_dir)
        logger.info(f"PaintedDesktop {APP_VERSION} starting")
        self.settings = SettingsManager(self.app_data_dir)
        self.history = HistoryManager(self.app_data_dir)
        self.cache_dir = Path(self.app_data_dir) / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.change_lock = threading.Lock()
        self.wake = threading.Event()  # set to re-check the schedule now (or to exit)
        self.running = True
        self.tray_icon = None
        self.ui = None

    # Wallpaper

    def screen_size(self):
        return self.settings.get_min_resolution() or get_monitor_resolution()

    def _find_and_set(self) -> Optional[dict]:
        screen, mode = self.screen_size(), self.settings.get_display_mode()
        styles = self.settings.get_art_styles()
        random.shuffle(styles)
        used = self.history.get_used_ids()
        logger.info(f"Looking for a painting: {screen[0]}x{screen[1]} {mode}, styles {styles}")

        for source in SOURCES:
            fetcher = source(screen, mode)
            fresh = (p for style in styles for p in fetcher.candidates(style) if p["id"] not in used)
            for painting in itertools.islice(fresh, ATTEMPTS_PER_SOURCE):
                path = fetcher.fetch_image(painting, self.cache_dir)
                if path and set_wallpaper(path, mode):
                    self.history.add_entry(
                        title=painting["title"], artist=painting["artist"], year=painting["year"],
                        source_institution=painting["institution"], source_url=painting["source_url"],
                        image_url=painting.get("image_url", ""), painting_id=painting["id"],
                        image_path=path)
                    self._cleanup_cache(keep=path)
                    logger.info(f"Wallpaper set from {fetcher.NAME}: {painting['title']}")
                    return painting
            logger.warning(f"No usable painting from {fetcher.NAME}")
        return None

    def change_wallpaper(self, manual: bool = False) -> bool:
        if not self.change_lock.acquire(blocking=False):
            if manual:
                self.notify("Already looking for a new painting…")
            return False
        try:
            painting = self._find_and_set()
        except Exception:
            logger.exception("Error fetching/setting wallpaper")
            painting = None
        finally:
            self.change_lock.release()

        self.update_tooltip()
        if painting and manual:
            self.notify(f"{painting['title']}\n{painting['artist']}", "New wallpaper")
        elif not painting:
            logger.warning("Could not find a suitable painting; will retry")
            if manual:
                self.notify("Couldn't fetch a new painting right now. Check your internet "
                            "connection; PaintedDesktop will keep trying.")
        return bool(painting)

    def _cleanup_cache(self, keep: str):
        """Keep the newest CACHE_SIZE images; never delete the current wallpaper."""
        try:
            for tmp in self.cache_dir.glob("*.tmp"):
                tmp.unlink(missing_ok=True)
            files = sorted(self.cache_dir.glob("*.jpg"), key=lambda f: f.stat().st_mtime, reverse=True)
            for old in files[CACHE_SIZE:]:
                if os.path.abspath(old) != os.path.abspath(keep):
                    old.unlink(missing_ok=True)
        except OSError as e:
            logger.warning(f"Error cleaning cache: {e}")

    # Scheduler

    def run_scheduler(self):
        failures = 0
        retry_at = datetime.min
        while self.running:
            now = datetime.now()
            if now >= retry_at and is_change_due(self.history.last_set_time(), now,
                                                 self.settings.get_change_time()):
                if self.change_wallpaper():
                    failures, retry_at = 0, datetime.min
                else:
                    failures += 1
                    retry_at = now + retry_delay(failures)
                    logger.info(f"Next attempt at {retry_at:%H:%M}")
            # Event.wait uses a monotonic clock, so this also re-checks soon after sleep/resume.
            self.wake.wait(30)
            self.wake.clear()

    # Tray

    def notify(self, message: str, title: str = "PaintedDesktop"):
        try:
            if self.tray_icon:
                self.tray_icon.notify(message, title)
        except Exception as e:
            logger.debug(f"Notification failed: {e}")

    def update_tooltip(self):
        entry = self.history.get_last_entry()
        text = f"PaintedDesktop\n{entry['title']}" if entry else "PaintedDesktop"
        if self.tray_icon:
            self.tray_icon.title = text[:120]  # Windows caps tooltips at 128 characters

    def show_current_info(self, icon=None, item=None):
        entry = self.history.get_last_entry()
        if entry:
            self.ui.show("info", lambda root: InfoWindow(root, entry))
        else:
            self.notify("No painting yet. One is on its way.")

    def show_history(self, icon=None, item=None):
        history = list(self.history.get_history())
        self.ui.show("history", lambda root: HistoryWindow(root, history))

    def show_settings(self, icon=None, item=None):
        self.ui.show("settings", lambda root: SettingsWindow(
            root, self.settings, get_monitor_resolution(), self.app_data_dir, self.on_settings_saved))

    def on_settings_saved(self):
        self.apply_startup_setting()
        self.wake.set()  # a new change time may already be due

    def change_wallpaper_now(self, icon=None, item=None):
        logger.info("Manual wallpaper change requested")
        threading.Thread(target=self.change_wallpaper, kwargs={"manual": True},
                         name="manual-change", daemon=True).start()

    def apply_startup_setting(self):
        if getattr(sys, "frozen", False):  # only the installed exe registers itself
            register_startup(sys.executable, bool(self.settings.get("launch_at_startup", True)))

    def exit_app(self, icon=None, item=None):
        logger.info("Exiting")
        self.running = False
        self.wake.set()
        if self.ui:
            self.ui.quit()
        if self.tray_icon:
            self.tray_icon.stop()

    def run(self):
        self.apply_startup_setting()
        self.ui = UI(str(ASSETS / "tray_icon.png"))
        icon_path = ASSETS / "tray_icon.png"
        image = Image.open(icon_path) if icon_path.exists() else Image.new("RGBA", (64, 64), (70, 130, 180, 255))
        self.tray_icon = pystray.Icon("PaintedDesktop", image, "PaintedDesktop", pystray.Menu(
            pystray.MenuItem("What's on my desktop?", self.show_current_info, default=True),
            pystray.MenuItem("Change now", self.change_wallpaper_now),
            pystray.MenuItem("History", self.show_history),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings", self.show_settings),
            pystray.MenuItem("Exit", self.exit_app),
        ))
        self.update_tooltip()
        threading.Thread(target=self.run_scheduler, name="scheduler", daemon=True).start()
        self.tray_icon.run()  # blocks until exit_app


def main():
    enable_dpi_awareness()
    if already_running():
        import tkinter
        import tkinter.messagebox
        root = tkinter.Tk()
        root.withdraw()
        tkinter.messagebox.showinfo(
            "PaintedDesktop", "PaintedDesktop is already running. Look for its icon in the "
                              "system tray (you may need to click the ^ arrow).", parent=root)
        return
    PaintedDesktop().run()
    logging.shutdown()
    # Tearing down a Tk interpreter that lives on another thread can hang or crash the
    # process at interpreter exit; everything is saved by now, so leave immediately.
    os._exit(0)


if __name__ == "__main__":
    main()
