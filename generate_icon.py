"""Generate the app icon (palette and paintbrush): tray PNG and multi-size Windows ICO."""

from pathlib import Path

from PIL import Image, ImageDraw


def draw_icon(size: int = 256) -> Image.Image:
    """Draw on a 64-unit grid scaled up to size, so downsampling gives smooth edges."""
    s = size / 64
    box = lambda *xy: [v * s for v in xy]
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Wooden palette with thumb hole
    draw.ellipse(box(8, 16, 56, 52), fill=(210, 150, 90), outline=(150, 100, 50), width=round(2 * s))
    draw.ellipse(box(42, 28, 50, 40), fill=(0, 0, 0, 0), outline=(150, 100, 50), width=round(2 * s))

    # Paint dabs
    for color, bbox in [((220, 50, 50), (16, 26, 26, 36)), ((50, 100, 200), (20, 40, 30, 50)),
                        ((250, 200, 50), (28, 20, 38, 30)), ((50, 180, 80), (34, 42, 44, 52))]:
        draw.ellipse(box(*bbox), fill=color)

    # Paintbrush: handle, ferrule, bristles, paint on the tip
    draw.line(box(2, 58, 22, 38), fill=(120, 50, 20), width=round(4 * s))
    draw.line(box(22, 38, 26, 34), fill=(192, 192, 192), width=round(5 * s))
    draw.polygon(box(25, 35, 34, 26, 32, 24, 24, 32), fill=(80, 80, 80))
    draw.ellipse(box(30, 22, 36, 28), fill=(50, 100, 200))
    return img


if __name__ == "__main__":
    assets = Path(__file__).parent / "PaintedDesktop" / "assets"
    icon = draw_icon(256)
    icon.resize((64, 64), Image.LANCZOS).save(assets / "tray_icon.png")
    icon.save(assets / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Icons written to {assets}")
