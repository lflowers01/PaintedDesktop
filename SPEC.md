# Daily Art Wallpaper — Build Spec

## Overview

A Windows background service that automatically sets the desktop wallpaper to a different high-resolution oil painting landscape each day. The user can look up the painting's metadata on demand, but the wallpaper image itself is clean — no overlaid text, no watermarks.

---

## Functional Requirements

### Core Behavior

- On startup and once per day (at a configurable time, default: midnight local time), fetch a new painting and set it as the Windows desktop wallpaper.
- If the day has already been served (i.e., the app runs but a wallpaper was already set today), do nothing — do not re-fetch or change the wallpaper until the next day's trigger fires.
- The wallpaper image must be **equal to or larger than the user's primary monitor resolution**. If the fetched image is smaller, skip it and fetch another.
- The wallpaper display mode should be set to **Fill** (so it scales correctly without black bars and without distorting aspect ratio).

### Art Source

- Pull paintings from the **Wikimedia Commons / Rijksmuseum API / Art Institute of Chicago API** (free, high-res, no auth required for basic use). Preferred priority order:
  1. **Art Institute of Chicago (ARTIC) API** — large images, good metadata, no key required
  2. **Rijksmuseum API** — requires a free API key, very high resolution
  3. **Wikimedia Commons** — fallback
- Filter strictly to:
  - Medium: **oil on canvas** or **oil on panel** (or equivalent oil painting media)
  - Subject/genre: **landscape**, **seascape**, or **veduta** (townscape/architectural landscape)
  - Exclude: portraits, still life, abstract, religious scenes (unless incidentally set in a landscape)

### Metadata Storage

- For every wallpaper that gets set, save a local record containing:
  - Painting title
  - Artist name
  - Year / date (if available)
  - Source institution
  - Source URL / image URL
  - Date it was set as wallpaper
- Store this in a simple **JSON file** (`history.json`) in the app's data directory.
- Paintings should not repeat until the history is exhausted (track used IDs).

### User-Facing Info Access

- Provide a **system tray icon** with a right-click context menu containing:
  - **"What's on my desktop?"** — opens a small popup window showing: title, artist, year, institution, and a clickable link to the source page
  - **"Change now"** — immediately fetches and sets a new painting (ignores the daily lock)
  - **"History"** — opens a small UI window listing past wallpapers (date, title, artist) with each entry clickable to show full metadata; most recent first
  - **"Change time"** — inline submenu or simple time-picker popup to set the daily swap time (e.g. 8:00 AM); saves immediately to `settings.json`
  - **"Settings"** — opens a settings window (see below)
  - **"Exit"** — closes the app

### Settings Window

Configurable options:

| Setting | Default | Description |
|---|---|---|
| Change time | `08:00` | Time of day (local) to swap wallpaper; configurable via tray right-click menu directly (no need to open full settings window) |
| Min resolution | auto-detect | Minimum image width × height; defaults to primary monitor resolution |
| API key (Rijksmuseum) | empty | Optional; enables Rijksmuseum source |
| Art style filter | landscape | Dropdown or checkboxes for landscape / seascape / veduta |
| Launch at startup | true | Whether to register with Windows startup |

Settings persist in a `settings.json` file in the app data directory.

---

## Technical Requirements

### Language & Stack

- **Python 3.10+** preferred (easy Windows wallpaper API access via `ctypes`, good HTTP libraries)
- Alternatively, **C# / .NET 6+** is acceptable if Python is not preferred — both are fine
- If Python:
  - `requests` or `httpx` for API calls
  - `ctypes` for setting wallpaper via `SystemParametersInfo`
  - `Pillow` for image resolution validation
  - `pystray` + `PIL` for system tray icon
  - `tkinter` or `customtkinter` for settings/info windows
  - `schedule` or `APScheduler` for daily trigger
  - Package as a standalone `.exe` using **PyInstaller**

### Windows Integration

- Set wallpaper using `SystemParametersInfo(SPI_SETDESKWALLPAPER, ...)` via `ctypes.windll.user32`
- Set wallpaper style to **Fill (10)** by writing to the registry:
  - `HKCU\Control Panel\Desktop` → `WallpaperStyle = 10`, `TileWallpaper = 0`
- Register for startup via registry key `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

### Image Handling

- Download image to a local cache folder (`%APPDATA%\DailyArtWallpaper\cache\`)
- Validate resolution using Pillow before setting — must be `>=` primary monitor dimensions
- Keep only the last 30 images in cache; delete older ones
- Filename format: `YYYY-MM-DD_<painting_id>.<ext>`

### Error Handling

- If no qualifying image is found after 10 fetch attempts (wrong size, wrong genre, API error), log the failure and leave the current wallpaper unchanged
- Log errors to `app.log` in the app data directory (rotating log, max 1 MB)
- If the network is unavailable at change time, retry every 15 minutes until successful

---

## File Structure

```
DailyArtWallpaper/
├── main.py                  # Entry point, tray icon, scheduler
├── wallpaper.py             # Windows wallpaper setter
├── fetcher.py               # API clients (ARTIC, Rijksmuseum, Wikimedia)
├── filter.py                # Genre/medium filtering logic
├── history.py               # history.json read/write
├── settings.py              # settings.json read/write + settings window
├── info_popup.py            # "What's on my desktop?" window
├── assets/
│   └── tray_icon.png        # 64×64 tray icon
├── data/                    # Created at runtime in %APPDATA%
│   ├── history.json
│   ├── settings.json
│   ├── app.log
│   └── cache/
└── requirements.txt
```

---

## API Details

### Art Institute of Chicago (primary)

- Base URL: `https://api.artic.edu/api/v1/artworks/search`
- No API key needed
- Filter query: `medium_display:oil` + `subject_titles:landscape` (or `seascape`)
- Image URL pattern: `https://www.artic.edu/iiif/2/{image_id}/full/full/0/default.jpg`
  - The IIIF endpoint supports requesting a specific pixel size — use `{width},` in the size parameter to request at least monitor width
- Check `image_id` field is not null before using

### Rijksmuseum (secondary, requires free API key)

- Base URL: `https://www.rijksmuseum.nl/api/en/collection`
- Params: `key=<apikey>`, `type=painting`, `material=oil+paint`, `f.type.en.norm=landscape`
- Image URL from `webImage.url` field
- Check `webImage.width` and `webImage.height` for resolution

### Fallback behavior

- If both primary sources fail or return no valid results after retries, skip the day and log the failure. Do not crash.

---

## Out of Scope

- No GUI beyond the tray icon + popup windows described above
- No multi-monitor support (use primary monitor only)
- No social sharing, no cloud sync
- No macOS or Linux support

---

## Deliverables

1. Fully working Python source code matching the file structure above
2. `requirements.txt`
3. PyInstaller `.spec` file to produce the distributable build
4. A **lightweight installer** built with **Inno Setup** (preferred) or NSIS — single `.exe` that installs the app, sets up the startup registry entry, and places a Start Menu shortcut. Should be under ~15 MB ideally.
5. A **GitHub Actions workflow** (`.github/workflows/release.yml`) that:
   - Triggers on a new version tag (e.g. `v1.0.0`)
   - Builds the PyInstaller bundle on a Windows runner
   - Compiles the Inno Setup installer
   - Publishes a GitHub Release with the installer `.exe` attached as a release asset automatically
6. A polished `README.md` (see below)

---

## GitHub Repository

This project will be public on GitHub and linked from the developer's personal portfolio site, so it should be well-presented.

### README.md Requirements

The README should include:

- **Project name + one-line description** at the top
- **Screenshot or demo GIF** placeholder (note where to drop in a screenshot)
- **Features list** — brief, scannable bullets covering: daily wallpaper swap, resolution gating, oil painting landscapes only, system tray controls, metadata popup, history view
- **Installation** — just "download the latest installer from Releases and run it"; no Python needed for end users
- **Usage** — how to use the tray icon; mention right-click for all controls
- **Getting a Rijksmuseum API key** — short paragraph, link to `https://data.rijksmuseum.nl/user-generated-content/api/`; note it's optional but improves variety
- **Where data lives** — `%APPDATA%\DailyArtWallpaper\` with a brief breakdown of what's in there
- **Building from source** — steps for developers who want to clone and run from Python directly
- **License** — MIT
- Badges at top: build status (GitHub Actions), latest release version, license

### Additional Repository Structure

```
.github/
└── workflows/
    └── release.yml       # Build + publish installer on version tag
installer/
└── setup.iss             # Inno Setup script
```

---

## Notes for the Builder

- The ARTIC IIIF endpoint is the most reliable free source for large images. Prioritize it.
- When checking painting genre, match against `subject_titles`, `category_titles`, and `classification_titles` — landscape paintings are sometimes filed under "landscapes" in one field and not another.
- The tray icon UX is the entire user interface. Keep it snappy — info popup should appear in under 200ms from click.
- The wallpaper cache should be self-cleaning; don't accumulate GBs of images silently.
- If the user's monitor resolution cannot be detected, default to a minimum of 1920×1080.

---

## A Note on This Spec

This document is a starting point, not a rigid contract. If the builder identifies a better approach to any part of this — a more reliable API source, a cleaner architecture, a better packaging strategy, improved error handling patterns, or anything else — they should feel free to deviate from or expand on what's written here. The goal is a polished, reliable, well-presented piece of software. Use good judgment.