"""Windows desktop integration: wallpaper, screen size and launch-at-startup."""

import ctypes
import logging
import os
from winreg import HKEY_CURRENT_USER, KEY_READ, KEY_WRITE, REG_DWORD, REG_SZ, DeleteValue, OpenKey, SetValueEx

logger = logging.getLogger(__name__)

SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE_SENDCHANGE = 3
WALLPAPER_STYLES = {"fill": "10", "fit": "6"}
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def enable_dpi_awareness():
    """Report real pixels instead of DPI-scaled ones (a 2560x1600 screen at 150% otherwise
    reads as 1707x1067) and render Tk windows crisply. Must run before any window is created."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # system DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception as e:
            logger.debug(f"Could not enable DPI awareness: {e}")


def set_wallpaper(image_path: str, mode: str = "fill") -> bool:
    """Set the desktop wallpaper. mode is "fill" (crop to cover) or "fit" (whole image, black bars)."""
    try:
        image_path = os.path.abspath(image_path)
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return False

        # Windows reads the style when the wallpaper is applied, so write it first.
        try:
            with OpenKey(HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, KEY_READ | KEY_WRITE) as key:
                SetValueEx(key, "WallpaperStyle", 0, REG_SZ, WALLPAPER_STYLES.get(mode, "10"))
                SetValueEx(key, "TileWallpaper", 0, REG_SZ, "0")
                SetValueEx(key, "JPEGImportQuality", 0, REG_DWORD, 100)  # no lossy re-encode
                SetValueEx(key, "AutoColorization", 0, REG_DWORD, 1)  # accent colour follows the painting
            if mode == "fit":
                with OpenKey(HKEY_CURRENT_USER, r"Control Panel\Colors", 0, KEY_READ | KEY_WRITE) as key:
                    SetValueEx(key, "Background", 0, REG_SZ, "0 0 0")
                # The registry value only applies at next sign-in; this applies it now.
                ctypes.windll.user32.SetSysColors(1, (ctypes.c_int * 1)(1), (ctypes.c_ulong * 1)(0))
        except OSError as e:
            logger.warning(f"Failed to set wallpaper style: {e}")

        if not ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, image_path, SPIF_UPDATEINIFILE_SENDCHANGE):
            logger.error(f"SystemParametersInfoW failed for {image_path}")
            return False

        logger.info(f"Wallpaper set: {image_path}")
        return True
    except Exception as e:
        logger.error(f"Error setting wallpaper: {e}")
        return False


def set_lock_screen(image_path: str) -> bool:
    """Set the lock screen image via WinRT (per-user, no admin needed)."""
    try:
        import asyncio
        from winrt.windows.storage import StorageFile
        from winrt.windows.system.userprofile import LockScreen

        async def apply():
            file = await StorageFile.get_file_from_path_async(os.path.abspath(image_path))
            await LockScreen.set_image_file_async(file)

        asyncio.run(apply())
        logger.info(f"Lock screen set: {image_path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to set lock screen: {e}")
        return False


def get_monitor_resolution() -> tuple:
    """Primary monitor resolution in physical pixels."""
    try:
        user32 = ctypes.windll.user32
        size = (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
        if size[0] > 0 and size[1] > 0:
            return size
    except Exception as e:
        logger.warning(f"Failed to get monitor resolution: {e}")
    return (1920, 1080)


def register_startup(app_path: str, enable: bool = True) -> bool:
    """Add or remove the HKCU Run entry that launches the app at sign-in."""
    try:
        with OpenKey(HKEY_CURRENT_USER, RUN_KEY, 0, KEY_READ | KEY_WRITE) as key:
            if enable:
                SetValueEx(key, "PaintedDesktop", 0, REG_SZ, f'"{app_path}"')
            else:
                try:
                    DeleteValue(key, "PaintedDesktop")
                except FileNotFoundError:
                    pass
        return True
    except OSError as e:
        logger.error(f"Error with startup registration: {e}")
        return False
