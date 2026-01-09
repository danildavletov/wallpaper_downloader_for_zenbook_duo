#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script for downloading wallpapers from the internet, cropping them for two screens, and applying them.
"""

import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple, Optional

import requests
from PIL import Image


def load_config(config_path: str = "config.json") -> dict:
    """Loads configuration from a JSON file."""
    script_dir = Path(__file__).parent
    config_file = script_dir / config_path
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return config


def download_wallpaper_from_pexels(api_key: str, theme: str, min_width: int, min_height: int, orientation: str = "landscape") -> Optional[bytes]:
    """
    Downloads wallpapers via Pexels API by the specified theme.
    
    Args:
        api_key: Pexels API key
        theme: Wallpaper theme for search
        min_width: Minimum image width
        min_height: Minimum image height
        orientation: Image orientation (landscape, portrait, square)
    
    Returns:
        Image bytes or None in case of error
    """
    if not api_key:
        print("Pexels API key not specified, skipping Pexels...")
        return None
    
    # Search for images via Pexels API
    search_url = "https://api.pexels.com/v1/search"
    headers = {
        "Authorization": api_key
    }
    params = {
        "query": theme,
        "per_page": 20,
        "orientation": orientation,
        "size": "large",
        "page": random.randint(1, 10)  # Случайная страница для большего разнообразия
    }
    
    try:
        print(f"Searching for wallpapers by theme: {theme}...")
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        photos = data.get("photos", [])
        
        if not photos:
            print("No images found for the specified theme")
            return None
        
        # Collect all images of suitable size
        suitable_photos = []
        for photo in photos:
            width = photo.get("width", 0)
            height = photo.get("height", 0)
            
            if width >= min_width and height >= min_height:
                image_url = photo.get("src", {}).get("original", "")
                if image_url:
                    suitable_photos.append((image_url, width, height))
        
        if not suitable_photos:
            print(f"No images found with minimum resolution {min_width}x{min_height}")
            return None
        
        # Randomly select one image from suitable ones
        selected_url, selected_width, selected_height = random.choice(suitable_photos)
        print(f"Downloading randomly selected image: {selected_width}x{selected_height}...")
        img_response = requests.get(selected_url, timeout=30)
        img_response.raise_for_status()
        
        return img_response.content
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading wallpapers from Pexels: {e}")
        return None


def download_wallpaper_from_reddit(theme: str, min_width: int, min_height: int) -> Optional[bytes]:
    """
    Downloads a random wallpaper from popular Reddit wallpaper subreddits.
    
    Args:
        theme: Wallpaper theme (not used, kept for compatibility)
        min_width: Minimum image width
        min_height: Minimum image height
    
    Returns:
        Image bytes or None in case of error
    """
    # Popular wallpaper subreddits
    subreddits = ["wallpaper", "wallpapers", "MinimalWallpaper", "EarthPorn", "SpacePorn", 
                  "CityPorn", "SkyPorn", "WaterPorn", "AbandonedPorn"]
    
    headers = {
        "User-Agent": "WallpaperDownloader/1.0 (by /u/wallpaperbot)"
    }
    
    # Try subreddits in random order
    random.shuffle(subreddits)
    
    for subreddit in subreddits:
        try:
            print(f"Downloading from Reddit r/{subreddit}...")
            
            # Get top posts from the past month
            url = f"https://www.reddit.com/r/{subreddit}/top.json"
            params = {"limit": 100, "t": "month"}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            posts = response.json().get("data", {}).get("children", [])
            if not posts:
                continue
            
            # Collect all image URLs
            image_urls = []
            for post in posts:
                post_data = post.get("data", {})
                url_overridden = post_data.get("url_overridden_by_dest", "")
                
                # Check if it's a direct image link
                if url_overridden and any(ext in url_overridden.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    image_urls.append(url_overridden)
                # Or try to get from preview
                elif post_data.get("preview"):
                    images = post_data.get("preview", {}).get("images", [])
                    if images:
                        img_url = images[0].get("source", {}).get("url", "").replace("&amp;", "&")
                        if img_url:
                            image_urls.append(img_url)
            
            if not image_urls:
                continue
            
            # Randomly select and download an image
            random.shuffle(image_urls)
            for image_url in image_urls[:20]:  # Try up to 20 images
                try:
                    print(f"Downloading: {image_url[:60]}...")
                    img_response = requests.get(image_url, headers=headers, timeout=30)
                    img_response.raise_for_status()
                    
                    # Check image dimensions
                    from io import BytesIO
                    img = Image.open(BytesIO(img_response.content))
                    img_width, img_height = img.size
                    
                    if img_width >= min_width and img_height >= min_height:
                        print(f"Successfully downloaded {img_width}x{img_height} image from Reddit")
                        return img_response.content
                    else:
                        print(f"Image too small ({img_width}x{img_height}), trying next...")
                        
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"Error with r/{subreddit}: {e}, trying next...")
            continue
    
    print("Failed to download image from Reddit")
    return None


def load_local_image(image_path: str) -> Optional[bytes]:
    """
    Loads a local image for testing.
    
    Args:
        image_path: Path to the local file
    
    Returns:
        Image bytes or None in case of error
    """
    script_dir = Path(__file__).parent
    parent_dir = script_dir.parent
    
    # Try to find the file in the parent directory
    local_path = parent_dir / image_path
    if not local_path.exists():
        local_path = script_dir / image_path
    if not local_path.exists():
        local_path = Path(image_path)
    
    if not local_path.exists():
        print(f"Local file not found: {image_path}")
        return None
    
    try:
        with open(local_path, 'rb') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading local file: {e}")
        return None


def process_image(
    image_data: bytes,
    output_dir: str,
    upper_width: int,
    upper_height: int,
    lower_width: int,
    lower_height: int,
    offset_px: int
) -> Tuple[Optional[str], Optional[str]]:
    """
    Processes the image: checks dimensions, scales if necessary,
    crops it for two screens, and saves the files.
    
    Args:
        image_data: Image bytes
        output_dir: Directory for saving cropped images
        upper_width: Upper screen width
        upper_height: Upper screen height
        lower_width: Lower screen width
        lower_height: Lower screen height
        offset_px: Offset between screens in pixels
    
    Returns:
        Tuple (path_to_upper_file, path_to_lower_file) or (None, None) on error
    """
    try:
        # Load the image
        from io import BytesIO
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary (handles palette mode, RGBA, etc.)
        if image.mode != 'RGB':
            print(f"Converting image from {image.mode} mode to RGB...")
            # Handle images with transparency by compositing onto white background
            if image.mode in ('RGBA', 'LA', 'P'):
                # For palette mode, check if it has transparency
                if image.mode == 'P':
                    # Convert palette to RGBA to check for transparency
                    image = image.convert('RGBA')
                
                # If image has alpha channel, composite onto white background
                if image.mode in ('RGBA', 'LA'):
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'LA':
                        # Convert LA to RGBA for proper alpha handling
                        rgba_image = Image.new('RGBA', image.size)
                        rgba_image.paste(image)
                        image = rgba_image
                    rgb_image.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
                    image = rgb_image
            else:
                # Convert other modes (like CMYK, L, etc.) to RGB
                image = image.convert('RGB')
        
        original_width, original_height = image.size
        
        print(f"Original image resolution: {original_width}x{original_height}")
        
        # Calculate required dimensions
        required_width = max(upper_width, lower_width)
        required_height = upper_height + offset_px + lower_height

        # Scale the image in "cover" mode - so it covers the required area
        # Use the minimum coefficient so the image fits exactly
        scale_factor_width = required_width / original_width
        scale_factor_height = required_height / original_height

        # Use the larger coefficient so the image covers the entire area
        scale_factor = max(scale_factor_width, scale_factor_height)

        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)

        if scale_factor != 1.0:
            print(f"Scaling to: {new_width}x{new_height} (coefficient: {scale_factor:.3f})")
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        current_width, current_height = image.size

        # Calculate offset for centering
        horizontal_offset = max(0, (current_width - required_width) // 2)
        vertical_offset = max(0, (current_height - required_height) // 2)

        print(f"Centering: offset ({horizontal_offset}, {vertical_offset})")

        # Crop the upper part (with centering)
        upper_left = horizontal_offset
        upper_top = vertical_offset
        upper_right = upper_left + upper_width
        upper_bottom = upper_top + upper_height

        upper_crop = image.crop((upper_left, upper_top, upper_right, upper_bottom))

        # Crop the lower part (with offset and centering)
        lower_left = horizontal_offset
        lower_top = vertical_offset + upper_height + offset_px
        lower_right = lower_left + lower_width
        lower_bottom = lower_top + lower_height

        lower_crop = image.crop((lower_left, lower_top, lower_right, lower_bottom))
        
        # Create directory for output files
        script_dir = Path(__file__).parent
        output_path = script_dir / output_dir
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save cropped images
        upper_file = output_path / "wallpaper_upper.jpg"
        lower_file = output_path / "wallpaper_lower.jpg"
        
        upper_crop.save(upper_file, "JPEG", quality=95)
        lower_crop.save(lower_file, "JPEG", quality=95)
        
        print(f"Upper screen saved: {upper_file} ({upper_crop.size[0]}x{upper_crop.size[1]})")
        print(f"Lower screen saved: {lower_file} ({lower_crop.size[0]}x{lower_crop.size[1]})")
        
        return str(upper_file), str(lower_file)
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return None, None


def apply_wallpaper(exe_path: str, upper_file: str, lower_file: str) -> bool:
    """
    Applies wallpapers to both monitors via WallpaperChanger.exe.
    
    Args:
        exe_path: Path to WallpaperChanger.exe
        upper_file: Path to file for upper screen
        lower_file: Path to file for lower screen
    
    Returns:
        True if successful, False in case of error
    """
    if not os.path.exists(exe_path):
        print(f"Error: WallpaperChanger.exe not found: {exe_path}")
        return False
    
    if not os.path.exists(upper_file):
        print(f"Error: upper screen file not found: {upper_file}")
        return False
    
    if not os.path.exists(lower_file):
        print(f"Error: lower screen file not found: {lower_file}")
        return False
    
    try:
        # Apply wallpaper to upper screen (monitor 0)
        print(f"Applying wallpaper to upper screen (monitor 0)...")
        result1 = subprocess.run(
            [exe_path, "-m", "0", upper_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result1.returncode != 0:
            print(f"Error applying wallpaper to upper screen: {result1.stderr}")
            return False
        
        # Delay between applying wallpapers
        time.sleep(1)
        
        # Apply wallpaper to lower screen (monitor 1)
        print(f"Applying wallpaper to lower screen (monitor 1)...")
        result2 = subprocess.run(
            [exe_path, "-m", "1", lower_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result2.returncode != 0:
            print(f"Error applying wallpaper to lower screen: {result2.stderr}")
            return False
        
        print("Wallpapers successfully applied to both screens!")
        return True
        
    except subprocess.TimeoutExpired:
        print("Error: timeout while applying wallpapers")
        return False
    except Exception as e:
        print(f"Error applying wallpapers: {e}")
        return False


def main():
    """Main script function."""
    try:
        # Load configuration
        config = load_config()
        
        # Get parameters from configuration
        test_mode = config.get("test_mode", False)
        test_image = config.get("test_image", "")
        source_mode = config.get("source_mode", "pexels").lower()  # "pexels" or "reddit"
        pexels_api_key = config.get("pexels_api_key", "")
        theme = config.get("theme", "black and white minimalist")
        min_width = config.get("min_width", 1920)
        min_height = config.get("min_height", 1695)
        orientation = config.get("orientation", "landscape")
        exe_path = config.get("exe_path", "")
        output_dir = config.get("output_dir", "./temp")
        upper_width = config.get("upper_width", 1920)
        upper_height = config.get("upper_height", 1080)
        lower_width = config.get("lower_width", 1920)
        lower_height = config.get("lower_height", 515)
        offset_px = config.get("offset_px", 100)
        
        # Load image
        image_data = None
        
        if test_mode:
            print("Test mode: loading local image...")
            if not test_image:
                print("Error: test image path not specified")
                return 1
            
            # Try to find the file in the parent directory
            script_dir = Path(__file__).parent
            parent_dir = script_dir.parent
            test_path = parent_dir / test_image
            
            image_data = load_local_image(str(test_path) if test_path.exists() else test_image)
        else:
            if source_mode == "reddit":
                # Direct Reddit mode - no Pexels attempt
                print("Source mode: Reddit")
                image_data = download_wallpaper_from_reddit(theme, min_width, min_height)
            else:
                # Pexels mode: try Pexels first, fallback to Reddit
                print("Source mode: Pexels (with Reddit fallback)")
                image_data = None
                if pexels_api_key:
                    print("Attempting to download from Pexels...")
                    image_data = download_wallpaper_from_pexels(pexels_api_key, theme, min_width, min_height, orientation)
                
                # Fallback to Reddit if Pexels failed or API key not set
                if not image_data:
                    print("Falling back to Reddit...")
                    image_data = download_wallpaper_from_reddit(theme, min_width, min_height)
        
        if not image_data:
            print("Failed to load image from all sources")
            return 1
        
        # Process image
        upper_file, lower_file = process_image(
            image_data,
            output_dir,
            upper_width,
            upper_height,
            lower_width,
            lower_height,
            offset_px
        )
        
        if not upper_file or not lower_file:
            print("Failed to process image")
            return 1
        
        # Apply wallpapers
        if not apply_wallpaper(exe_path, upper_file, lower_file):
            print("Failed to apply wallpapers")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

