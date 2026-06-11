# Daily Art Wallpaper

[![Build Status](https://github.com/lflowers01/PaintedDesktop/workflows/Build%20and%20Release/badge.svg)](https://github.com/lflowers01/PaintedDesktop/actions)
[![Latest Release](https://img.shields.io/github/v/release/lflowers01/PaintedDesktop?label=latest&sort=semver)](https://github.com/lflowers01/PaintedDesktop/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Automatically set your Windows desktop wallpaper to a different high-resolution oil painting landscape each day.

![Screenshot Placeholder](https://via.placeholder.com/800x600?text=Daily+Art+Wallpaper+Screenshot)

## Features

- **Automatic Daily Wallpaper Changes** — New oil painting landscape every day at a configurable time (default: 8:00 AM)
- **Resolution-Gated** — Only uses images equal to or larger than your monitor resolution
- **Curated Landscapes** — Strictly filters to oil painting landscapes, seascapes, and veduttas (architectural landscapes)
- **System Tray Controls** — Right-click menu for quick access to all functions
- **Current Wallpaper Info** — View the title, artist, year, and source of your current wallpaper with one click
- **Wallpaper History** — Browse past wallpapers with full metadata; click any to view details
- **Multiple Art Sources** — Pulls from Art Institute of Chicago (primary), Rijksmuseum (optional, requires free API key), and Wikimedia Commons (fallback)
- **Smart Caching** — Automatically caches images and cleans up old ones (keeps last 30)
- **No Overlays** — Clean images with no watermarks or text overlays
- **Customizable** — Adjust change time, resolution thresholds, and art style filters via settings window

## Installation

1. Download the latest installer from [Releases](https://github.com/lflowers01/PaintedDesktop/releases)
2. Run `DailyArtWallpaperSetup.exe`
3. Follow the installation wizard
4. *Optional*: Check "Launch at startup" during installation to run the app automatically when Windows starts

**No Python installation required** — the installer includes everything needed.

## Usage

Once installed, the app runs as a system tray icon (usually in the bottom-right corner of your taskbar).

### Tray Icon Menu

Right-click the tray icon to access:

- **What's on my desktop?** — Opens a popup showing the current wallpaper's title, artist, year, source institution, and a link to view it online
- **Change now** — Immediately fetches and sets a new painting (ignores the daily lock)
- **History** — Opens a window showing all previously set wallpapers (most recent first); double-click any entry for full details
- **Change time** — Opens the settings window to adjust when the daily swap occurs
- **Settings** — Open the full settings window to customize:
  - Change time (HH:MM format)
  - Minimum image resolution (auto-detected from your monitor)
  - Rijksmuseum API key (optional, improves variety)
  - Art style filters (landscape, seascape, vedutta)
  - Launch at startup toggle
- **Exit** — Close the application

## Getting a Rijksmuseum API Key (Optional)

The Rijksmuseum API provides access to even more high-resolution paintings. To enable it:

1. Visit [Rijksmuseum API](https://data.rijksmuseum.nl/user-generated-content/api/)
2. Sign up for a free account
3. Generate an API key
4. Copy the key and paste it into the Settings window under "Rijksmuseum API Key"

Without this key, the app will use the Art Institute of Chicago API (which has excellent coverage).

## Where Data Lives

All app data is stored in `%APPDATA%\DailyArtWallpaper\`:

- **`settings.json`** — Your preferences (change time, resolution, API keys, etc.)
- **`history.json`** — Metadata for all wallpapers that have been set (title, artist, year, source, date set)
- **`cache/`** — Local copies of the last 30 images (auto-managed; they're deleted as new ones are fetched)
- **`app.log`** — Application debug log (rotates when it reaches 1 MB)

## Building from Source

If you want to build the app yourself:

### Prerequisites

- Python 3.10 or later
- Windows (for wallpaper API support)
- Inno Setup (for building the installer, optional)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/lflowers01/PaintedDesktop.git
   cd PaintedDesktop
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r DailyArtWallpaper/requirements.txt
   ```

4. Run the app:
   ```bash
   python DailyArtWallpaper/main.py
   ```

### Building the Installer

1. Install PyInstaller and Inno Setup:
   ```bash
   pip install pyinstaller
   choco install innosetup  # or download from https://jrsoftware.org/isdl.php
   ```

2. Build the PyInstaller bundle:
   ```bash
   pyinstaller DailyArtWallpaper.spec
   ```

3. Build the installer:
   ```bash
   iscc installer/setup.iss
   ```

   The installer will be created at `dist/DailyArtWallpaperSetup.exe`.

## Architecture

```
DailyArtWallpaper/
├── main.py              # Entry point, tray icon, scheduler
├── wallpaper.py         # Windows wallpaper setter (ctypes)
├── fetcher.py           # API clients (ARTIC, Rijksmuseum, Wikimedia)
├── filter.py            # Painting genre/medium filtering
├── history.py           # history.json management
├── settings.py          # settings.json management + UI
├── info_popup.py        # Info & history popup windows
├── assets/
│   └── tray_icon.png    # 64×64 tray icon
└── requirements.txt
```

## Error Handling

- **Network unavailable**: If the network is down at change time, the app retries every 15 minutes.
- **No qualifying images**: After 10 fetch attempts across all sources, the app logs a failure and leaves the current wallpaper unchanged.
- **Image too small**: Images smaller than your monitor resolution are automatically skipped.

All errors are logged to `%APPDATA%\DailyArtWallpaper\app.log` with automatic rotation at 1 MB.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Troubleshooting

**The tray icon isn't showing:**
- Try restarting the application
- Ensure your system tray is visible on your taskbar
- Check that the app isn't already running in the background

**Wallpaper not changing:**
- Check `%APPDATA%\DailyArtWallpaper\app.log` for errors
- Verify your internet connection
- Try clicking "Change now" to force an immediate fetch
- Ensure your monitor resolution is being detected correctly (Settings window shows it)

**Settings aren't saving:**
- Ensure you have write permissions to `%APPDATA%\DailyArtWallpaper\`
- Check the app log for permission errors

## Contributing

Found a bug or have a feature request? Open an issue on [GitHub](https://github.com/lflowers01/PaintedDesktop/issues).

---

Enjoy your daily dose of art! 🎨

