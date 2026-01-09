# Wallpaper Downloader for ASUS ZenBook Duo

Python script for downloading, processing, and applying wallpapers to dual-screen ASUS ZenBook Duo laptops (UX481, UX482, UX581, UX582). Automatically splits images for the upper and lower screens.

## Features

- **Dual-screen support**: Automatically crops and applies wallpapers to both screens
- **Multiple sources**: Downloads from Pexels API or Reddit
- **Smart cropping**: Intelligently scales and crops images to fit both screen dimensions
- **Configurable**: Customize themes, dimensions, and download sources via JSON config

## Setup

1. **Download WallpaperChanger.exe**
   - Download the executable from [WallpaperChanger](https://github.com/philhansen/WallpaperChanger/releases)
   - Place `WallpaperChanger.exe` in the `wallpaper_downloader` directory

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure settings**
   - Edit `config.json` to set your Pexels API key (optional), theme, and screen dimensions
   - Adjust `upper_width`, `upper_height`, `lower_width`, `lower_height` for your specific model
   - Set `offset_px` to match the gap between your screens

## Usage

```bash
python download_wallpaper.py
```

The script will:
1. Download a wallpaper from Pexels or Reddit based on your theme
2. Process and crop it for both screens
3. Apply the wallpapers using WallpaperChanger.exe

## Configuration

Edit `config.json` to customize:

- `source_mode`: "pexels" or "reddit"
- `pexels_api_key`: Your Pexels API key (optional, falls back to Reddit if not set)
- `theme`: Search theme for wallpapers
- `upper_width/upper_height`: Upper screen dimensions
- `lower_width/lower_height`: Lower screen dimensions
- `offset_px`: Pixel offset between screens
- `test_mode`: Set to `true` to use a local test image

## Requirements

- Windows 7+ (for WallpaperChanger.exe)
- Python 3.x
- Pillow (PIL)
- requests library

