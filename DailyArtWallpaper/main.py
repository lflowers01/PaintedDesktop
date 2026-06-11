"""Main entry point for Daily Art Wallpaper app."""

import sys
import os
import logging
import threading
import time
from pathlib import Path
from datetime import datetime, time as dt_time
from PIL import Image
import pystray
import schedule

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from settings import SettingsManager, SettingsWindow
from history import HistoryManager
from wallpaper import set_wallpaper, get_monitor_resolution, register_startup
from fetcher import ARTICFetcher, RijksmuseumFetcher
from filter import PaintingFilter
from info_popup import InfoPopup, HistoryWindow


# Setup logging
def setup_logging(data_dir: str):
    """Setup rotating file logger."""
    log_dir = Path(data_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # File handler (rotating)
    from logging.handlers import RotatingFileHandler
    fh = RotatingFileHandler(
        log_file,
        maxBytes=1024*1024,  # 1 MB
        backupCount=5
    )
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger


# Get app data directory
def get_app_data_dir() -> str:
    """Get app data directory (Windows APPDATA)."""
    if sys.platform == 'win32':
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            return os.path.join(appdata, 'DailyArtWallpaper')
    return os.path.expanduser('~/.dailyartwallpaper')


class DailyArtWallpaper:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        self.app_data_dir = get_app_data_dir()
        self.logger = setup_logging(self.app_data_dir)
        self.logger.info("Daily Art Wallpaper starting...")
        
        self.settings_manager = SettingsManager(self.app_data_dir)
        self.history_manager = HistoryManager(self.app_data_dir)
        
        self.cache_dir = Path(self.app_data_dir) / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.tray_icon = None
        self.scheduler_thread = None
        self.running = True
        self.last_wallpaper_date = None
        
        # Setup monitor resolution
        self.min_resolution = self.settings_manager.get_min_resolution()
        if self.min_resolution[0] == 0:
            self.min_resolution = get_monitor_resolution()
            self.settings_manager.set_min_resolution(*self.min_resolution)
    
    def create_tray_icon(self):
        """Create system tray icon."""
        try:
            # Create a simple icon image
            icon_image = Image.new('RGB', (64, 64), color='blue')
            
            menu = pystray.Menu(
                pystray.MenuItem("What's on my desktop?", self.show_current_info),
                pystray.MenuItem("Change now", self.change_wallpaper_now),
                pystray.MenuItem("History", self.show_history),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Change time", self.show_change_time_menu),
                pystray.MenuItem("Settings", self.show_settings),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self.exit_app),
            )
            
            self.tray_icon = pystray.Icon(
                "DailyArtWallpaper",
                icon_image,
                "Daily Art Wallpaper",
                menu
            )
            
            self.logger.info("Tray icon created")
        except Exception as e:
            self.logger.error(f"Error creating tray icon: {e}")
    
    def show_change_time_menu(self, icon, item):
        """Show submenu for changing time."""
        times = []
        for hour in range(24):
            for minute in [0, 30]:
                time_str = f"{hour:02d}:{minute:02d}"
                times.append(
                    pystray.MenuItem(
                        time_str,
                        lambda h=hour, m=minute: self.set_change_time(h, m)
                    )
                )
        
        # For now, just open a simple time picker
        self.show_settings(icon, item)
    
    def set_change_time(self, hour: int, minute: int):
        """Set the daily change time."""
        self.settings_manager.set_change_time(hour, minute)
        self.logger.info(f"Change time set to {hour:02d}:{minute:02d}")
        # Reschedule the job
        self.schedule_daily_wallpaper()
    
    def show_current_info(self, icon=None, item=None):
        """Show current wallpaper info popup."""
        last_entry = self.history_manager.get_last_entry()
        if last_entry:
            popup = InfoPopup(last_entry)
            popup.show_threaded()
        else:
            self.logger.info("No wallpaper set yet")
    
    def show_history(self, icon=None, item=None):
        """Show history window."""
        history = self.history_manager.get_history()
        if history:
            window = HistoryWindow(history)
            window.show_threaded()
        else:
            self.logger.info("No history yet")
    
    def show_settings(self, icon=None, item=None):
        """Show settings window."""
        settings_window = SettingsWindow(self.settings_manager, self.on_settings_close)
        settings_window.show_threaded()
    
    def on_settings_close(self):
        """Called when settings window closes."""
        self.schedule_daily_wallpaper()
    
    def change_wallpaper_now(self, icon=None, item=None):
        """Immediately fetch and set new wallpaper."""
        self.logger.info("Manual wallpaper change requested")
        self._fetch_and_set_wallpaper()
    
    def _get_painting_metadata(self, painting: dict, source: str) -> dict:
        """Extract metadata from painting dict."""
        if source == 'artic':
            return {
                'title': painting.get('title', 'Unknown'),
                'artist': painting.get('artist_display', 'Unknown'),
                'year': painting.get('date_display', ''),
                'painting_id': painting.get('id', ''),
                'source_url': f"https://www.artic.edu/artworks/{painting.get('id', '')}",
            }
        elif source == 'rijksmuseum':
            return {
                'title': painting.get('title', 'Unknown'),
                'artist': painting.get('principalMaker', 'Unknown'),
                'year': painting.get('dating', {}).get('presentationDate', ''),
                'painting_id': painting.get('objectNumber', painting.get('id', '')),
                'source_url': painting.get('links', {}).get('self', ''),
            }
        return {}
    
    def _fetch_and_set_wallpaper(self) -> bool:
        """Fetch a new painting and set it as wallpaper."""
        try:
            # Check if we already set a wallpaper today
            today = datetime.now().strftime('%Y-%m-%d')
            last_date = self.settings_manager.get('last_wallpaper_date')
            if last_date == today:
                self.logger.info("Wallpaper already set today, skipping")
                return False
            
            min_res = self.settings_manager.get_min_resolution()
            art_styles = self.settings_manager.get('art_styles', ['landscape', 'seascape'])
            painting_filter = PaintingFilter(art_styles)
            
            used_ids = self.history_manager.get_used_ids()
            
            # Try ARTIC first
            artic_fetcher = ARTICFetcher()
            max_attempts = 10
            attempts = 0
            
            while attempts < max_attempts:
                for style in art_styles:
                    paintings = artic_fetcher.search(style, limit=50)
                    for painting in paintings:
                        painting_id = painting.get('id')
                        if painting_id in used_ids:
                            continue
                        
                        if not painting_filter.passes_filter(painting):
                            continue
                        
                        # Try to fetch image
                        image_path = artic_fetcher.fetch_image(painting, min_res, self.cache_dir)
                        if image_path:
                            # Set wallpaper
                            if set_wallpaper(image_path):
                                # Save to history
                                metadata = self._get_painting_metadata(painting, 'artic')
                                image_url = artic_fetcher.get_image_url(painting.get('image_id'))
                                
                                self.history_manager.add_entry(
                                    title=metadata['title'],
                                    artist=metadata['artist'],
                                    year=metadata['year'],
                                    source_institution="Art Institute of Chicago",
                                    source_url=metadata['source_url'],
                                    image_url=image_url,
                                    painting_id=metadata['painting_id'],
                                    image_path=image_path
                                )
                                
                                # Update settings
                                self.settings_manager.set('last_wallpaper_date', today)
                                self.settings_manager.set('last_wallpaper_id', painting_id)
                                
                                # Cleanup old cache
                                self._cleanup_cache()
                                
                                self.logger.info(f"Wallpaper set: {metadata['title']}")
                                return True
                
                attempts += 1
            
            # Try Rijksmuseum if enabled
            api_key = self.settings_manager.get('rijksmuseum_api_key')
            if api_key:
                rij_fetcher = RijksmuseumFetcher(api_key)
                for style in art_styles:
                    paintings = rij_fetcher.search(style, limit=50)
                    for painting in paintings:
                        painting_id = painting.get('objectNumber')
                        if painting_id in used_ids:
                            continue
                        
                        image_path = rij_fetcher.fetch_image(painting, min_res, self.cache_dir)
                        if image_path:
                            if set_wallpaper(image_path):
                                metadata = self._get_painting_metadata(painting, 'rijksmuseum')
                                self.history_manager.add_entry(
                                    title=metadata['title'],
                                    artist=metadata['artist'],
                                    year=metadata['year'],
                                    source_institution="Rijksmuseum",
                                    source_url=metadata['source_url'],
                                    image_url=image_path,
                                    painting_id=metadata['painting_id'],
                                    image_path=image_path
                                )
                                
                                self.settings_manager.set('last_wallpaper_date', today)
                                self.settings_manager.set('last_wallpaper_id', painting_id)
                                self._cleanup_cache()
                                
                                self.logger.info(f"Wallpaper set from Rijksmuseum: {metadata['title']}")
                                return True
            
            self.logger.warning("Could not find suitable painting after max attempts")
            return False
            
        except Exception as e:
            self.logger.error(f"Error fetching/setting wallpaper: {e}")
            return False
    
    def _cleanup_cache(self):
        """Keep only last 30 images in cache."""
        try:
            files = sorted(self.cache_dir.glob("*.jpg"), key=lambda x: x.stat().st_mtime)
            if len(files) > 30:
                for f in files[:-30]:
                    f.unlink()
                    self.logger.debug(f"Deleted cache file: {f}")
        except Exception as e:
            self.logger.warning(f"Error cleaning cache: {e}")
    
    def schedule_daily_wallpaper(self):
        """Schedule daily wallpaper fetch."""
        schedule.clear()
        
        change_time = self.settings_manager.get_change_time()
        time_str = f"{change_time.hour:02d}:{change_time.minute:02d}"
        
        schedule.every().day.at(time_str).do(self._fetch_and_set_wallpaper)
        self.logger.info(f"Scheduled daily wallpaper fetch at {time_str}")
    
    def run_scheduler(self):
        """Run the scheduler in a background thread."""
        self.schedule_daily_wallpaper()
        
        # Also try to fetch on startup
        self._fetch_and_set_wallpaper()
        
        while self.running:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    
    def exit_app(self, icon=None, item=None):
        """Exit the application."""
        self.logger.info("Exiting...")
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
        sys.exit(0)
    
    def run(self):
        """Run the application."""
        try:
            # Create tray icon
            self.create_tray_icon()
            
            # Start scheduler thread
            self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            # Run tray icon (blocking)
            self.tray_icon.run()
        except Exception as e:
            self.logger.error(f"Error running app: {e}")
            sys.exit(1)


def main():
    """Entry point."""
    app = DailyArtWallpaper()
    app.run()


if __name__ == '__main__':
    main()
