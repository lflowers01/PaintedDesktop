"""Generate a simple tray icon for Daily Art Wallpaper."""

from PIL import Image, ImageDraw
from pathlib import Path

def create_tray_icon(output_path: str, size: int = 64):
    """
    Create a simple tray icon.
    
    Args:
        output_path: Path to save the icon
        size: Icon size (64x64 pixels)
    """
    # Create a new image with a blue background
    img = Image.new('RGB', (size, size), color=(70, 130, 180))  # Steel blue
    draw = ImageDraw.Draw(img)
    
    # Draw a paintbrush-like icon
    # Draw a circle in the center (palette)
    center = size // 2
    radius = size // 4
    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        fill=(255, 200, 100),  # Light orange
        outline=(200, 150, 50),
        width=2
    )
    
    # Add some color spots
    spot_color = (200, 100, 100)  # Red
    draw.ellipse([center - 15, center - 15, center - 8, center - 8], fill=spot_color)
    
    spot_color = (100, 150, 100)  # Green
    draw.ellipse([center + 8, center - 15, center + 15, center - 8], fill=spot_color)
    
    spot_color = (100, 100, 200)  # Blue
    draw.ellipse([center - 8, center + 8, center + 15, center + 15], fill=spot_color)
    
    # Save the icon
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_file, 'PNG')
    print(f"Icon created: {output_file}")


if __name__ == '__main__':
    create_tray_icon('DailyArtWallpaper/assets/tray_icon.png')
