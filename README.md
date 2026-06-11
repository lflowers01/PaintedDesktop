# PaintedDesktop

[![Build Status](https://github.com/lflowers01/PaintedDesktop/workflows/Build%20and%20Release/badge.svg)](https://github.com/lflowers01/PaintedDesktop/actions)
[![Latest Release](https://img.shields.io/github/v/release/lflowers01/PaintedDesktop?label=latest&sort=semver)](https://github.com/lflowers01/PaintedDesktop/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Automatically set your Windows desktop wallpaper to a different high-resolution oil painting landscape every day.

![Screenshot Placeholder](/screenshot.png)

## Features

- **Daily wallpaper rotation** — a new oil painting landscape every day at a time you choose
- **Resolution gated** — only fetches images at or above your monitor's native resolution
- **Oil painting landscapes only** — strictly filtered to landscapes, seascapes, and veduttas in oil
- **No accounts or API keys** — pulls from Rijksmuseum and Art Institute of Chicago for free
- **System tray controls** — everything accessible from a right-click menu, no persistent window
- **What's on my desktop?** — one click to see the painting title, artist, year, and source
- **Wallpaper history** — browse every painting that's been set, with full metadata
- **Clean wallpapers** — no overlaid text, watermarks, or UI chrome on the image itself
- **Smart caching** — keeps the last 30 images locally, cleans up older ones automatically

## Installation

1. Download the latest `PaintedDesktopSetup.exe` from [Releases](https://github.com/lflowers01/PaintedDesktop/releases)
2. Run the installer and follow the wizard
3. PaintedDesktop will start automatically and sit in your system tray

No Python installation required — everything is bundled.

## Usage

PaintedDesktop runs as a system tray icon in the bottom-right corner of your taskbar. Right-click it to access all controls:

- **What's on my desktop?** — shows the current painting's title, artist, year, source institution, and a link to view it on the museum's website
- **Change now** — immediately fetches and sets a new painting, bypassing the daily lock
- **History** — opens a window listing every wallpaper that's been set, most recent first; double-click any entry for full details
- **Settings** — opens the settings window
- **Exit** — closes the app

## Settings

| Setting | Default | Description |
|---|---|---|
| Change time | 08:00 | Time of day the wallpaper rotates |
| Min resolution | auto-detected | Minimum image size; defaults to your monitor resolution |
| Art styles | Landscape, Seascape | Which genres to include |
| Launch at startup | On | Whether to start with Windows |

## Art Sources

PaintedDesktop pulls from two free museum APIs with no accounts or keys needed:

- **Rijksmuseum** (primary) — 700,000+ works, heavy in Dutch Golden Age oil painting landscapes. Very high resolution scans.
- **Art Institute of Chicago** (fallback) — excellent general collection with strong landscape coverage and flexible resolution requests via IIIF.

## Where Data Lives

All app data is stored in `%APPDATA%\PaintedDesktop\`:

| File/Folder | Contents |
|---|---|
| `settings.json` | Your preferences |
| `history.json` | Metadata for every wallpaper that's been set |
| `cache/` | Local copies of the last 30 images |
| `app.log` | Debug log, rotates at 1 MB |

To open this folder: press `Win + R`, type `%APPDATA%\PaintedDesktop`, hit Enter.

## Building from Source

### Prerequisites

- Python 3.10+
- Windows (wallpaper API is Windows-only)
- Inno Setup (only needed to build the installer)

### Run from source

```bash
git clone https://github.com/lflowers01/PaintedDesktop.git
cd PaintedDesktop
python -m venv venv
venv\Scripts\activate
pip install -r PaintedDesktop/requirements.txt
python PaintedDesktop/main.py
```

### Build the installer

```bash
pip install pyinstaller
pyinstaller PaintedDesktop.spec
iscc installer/setup.iss
```

The installer will be at `installer/dist/PaintedDesktopSetup.exe`.

## Troubleshooting

**Tray icon not showing** — check that the app isn't already running in the background. Look in Task Manager for `PaintedDesktop.exe`.

**Wallpaper not changing** — check `%APPDATA%\PaintedDesktop\app.log` for errors. Try "Change now" from the tray menu to force an immediate fetch.

**Wrong resolution** — open Settings and confirm the width and height match your monitor.

## License

MIT — see [LICENSE](LICENSE).

## Contributing

Open an issue or PR on [GitHub](https://github.com/lflowers01/PaintedDesktop/issues).