"""Generate a simple tray icon for PaintedDesktop."""

from PIL import Image, ImageDraw
from pathlib import Path

def create_tray_icon(output_path: str, size: int = 64):
    """
    Create an art-themed tray icon (palette and paintbrush).
    
    Args:
        output_path: Path to save the icon
        size: Icon size (64x64 pixels)
    """
    # Create a new transparent image
    img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw Wooden Palette (bean shape / tilted oval)
    palette_color = (210, 150, 90) # Wood color
    draw.ellipse([8, 16, 56, 52], fill=palette_color, outline=(150, 100, 50), width=2)
    
    # Thumb hole
    draw.ellipse([42, 28, 50, 40], fill=(0, 0, 0, 0), outline=(150, 100, 50), width=2)
    
    # Paint dabs
    colors = [
        ((220, 50, 50), [16, 26, 26, 36]),  # Red
        ((50, 100, 200), [20, 40, 30, 50]), # Blue
        ((250, 200, 50), [28, 20, 38, 30]), # Yellow
        ((50, 180, 80), [34, 42, 44, 52])   # Green
    ]
    
    for color, bbox in colors:
        draw.ellipse(bbox, fill=color)
        
    # Paintbrush handle
    brush_color = (120, 50, 20)
    draw.line([2, 58, 22, 38], fill=brush_color, width=4)
    # Paintbrush ferrule (metal part)
    draw.line([22, 38, 26, 34], fill=(192, 192, 192), width=5)
    # Paintbrush bristles
    draw.polygon([25, 35, 34, 26, 32, 24, 24, 32], fill=(80, 80, 80))
    # Paint on tip (blue)
    draw.ellipse([30, 22, 36, 28], fill=(50, 100, 200))
    
    # Save the icon
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_file, 'PNG')
    print(f"Icon created: {output_file}")


if __name__ == '__main__':
    create_tray_icon('PaintedDesktop/assets/tray_icon.png')
