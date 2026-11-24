from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "assets" / "icon.ico"
    output.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (256, 256), "#0f172a")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((25, 25, 231, 231), radius=48, fill="#2563eb")
    draw.line((64, 95, 192, 95), fill="white", width=18)
    draw.line((64, 128, 192, 128), fill="white", width=18)
    draw.line((64, 161, 150, 161), fill="white", width=18)
    draw.ellipse((174, 151, 198, 175), fill="#93c5fd")
    image.save(output, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


if __name__ == "__main__":
    main()
