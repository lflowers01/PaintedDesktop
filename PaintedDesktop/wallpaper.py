"""Windows wallpaper setter using ctypes."""

import ctypes
import os
from pathlib import Path
from winreg import ConnectRegistry, OpenKey, SetValueEx, HKEY_CURRENT_USER, REG_SZ, REG_DWORD
import logging


logger = logging.getLogger(__name__)


def set_wallpaper(image_path: str) -> bool:
    """
    Set Windows desktop wallpaper.
    
    Args:
        image_path: Full path to image file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        image_path = os.path.abspath(image_path)

        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return False

        # Set wallpaper using ctypes
        user32 = ctypes.windll.user32
        result = user32.SystemParametersInfoW(20, 0, image_path, 3)

        if not result:
            logger.error(f"SystemParametersInfoW failed for {image_path}")
            return False

        # Set wallpaper style to Fill (10) and TileWallpaper to 0
        try:
            registry_path = r"Control Panel\Desktop"
            registry = ConnectRegistry(None, HKEY_CURRENT_USER)
            key = OpenKey(registry, registry_path, 0, 0x20000 | 2)  # Read and Write
            SetValueEx(key, "WallpaperStyle", 0, REG_SZ, "10")  # 10 = Fill
            SetValueEx(key, "TileWallpaper", 0, REG_SZ, "0")
            
            # Enable Windows to automatically pick an accent color from the background
            SetValueEx(key, "AutoColorization", 0, REG_DWORD, 1)
            key.Close()

            
        except Exception as e:
            logger.error(f"Failed to set wallpaper registry keys: {e}")
            # Continue even if registry fails

        logger.info(f"Wallpaper set successfully: {image_path}")
        return True

    except Exception as e:
        logger.error(f"Error setting wallpaper: {e}")
        return False


def get_monitor_resolution() -> tuple:
    """
    Get primary monitor resolution.
    
    Returns:
        Tuple of (width, height) in pixels
    """
    try:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
        height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
        return (width, height)
    except Exception as e:
        logger.warning(f"Failed to get monitor resolution: {e}")
        return (1920, 1080)  # Default fallback


def register_startup(app_path: str, enable: bool = True) -> bool:
    """
    Register or unregister app for Windows startup.
    
    Args:
        app_path: Full path to executable
        enable: True to register, False to unregister
        
    Returns:
        True if successful
    """
    try:
        registry_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        registry = ConnectRegistry(None, HKEY_CURRENT_USER)
        key = OpenKey(registry, registry_path, 0, 0x20000 | 2)  # Read and Write

        if enable:
            SetValueEx(key, "PaintedDesktop", 0, REG_SZ, app_path)
            logger.info("App registered for startup")
        else:
            try:
                from winreg import DeleteValue
                DeleteValue(key, "PaintedDesktop")
                logger.info("App unregistered from startup")
            except FileNotFoundError:
                pass

        key.Close()
        return True
    except Exception as e:
        logger.error(f"Error with startup registration: {e}")
        return False
