"""Edit the title screen's logo. graphics/title/README.md is the guide.

usage, from the repository root:
    python3 graphics/tools/title_screen.py export LOGO.png [--source TITLE]
    python3 graphics/tools/title_screen.py import LOGO.png OUTPUT.bin [--source TITLE]
    python3 graphics/tools/title_screen.py info [TITLE]
    python3 graphics/tools/title_screen.py unpack DATA.dat [--source TITLE]
    python3 graphics/tools/title_screen.py pack DATA.dat OUTPUT.bin

TITLE is a title data file (graphics/title/*.bin) or an unheadered rom, by default the title data
Worlds Collide uses. export and import need Pillow (pip install pillow)."""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import graphics.title_screen as title_screen
from graphics.title_screen import TitleScreenError

DEFAULT_SOURCE = os.path.join(ROOT, "graphics", "title", "WC Spartan Title Data-CDude.bin")

def image_module():
    try:
        from PIL import Image
    except ImportError:
        raise TitleScreenError("this needs Pillow: pip install pillow")
    return Image

def export_logo(source, png_path):
    Image = image_module()
    logo = title_screen.read_logo(title_screen.unpack(title_screen.read_block(source)))

    image = Image.new("P", (title_screen.LOGO_WIDTH, title_screen.LOGO_HEIGHT))
    image.putpalette([channel for color in title_screen.PALETTE for channel in color])
    image.putdata([color for row in logo for color in row])
    image.save(png_path)
    print(f"{png_path}: the logo of {source}")

def image_logo(png_path):
    # the logo in an image: each pixel is the logo color which looks most like it
    Image = image_module()
    image = Image.open(png_path).convert("RGB")
    if image.size != (title_screen.LOGO_WIDTH, title_screen.LOGO_HEIGHT):
        raise TitleScreenError(f"{png_path} is {image.size[0]}x{image.size[1]} pixels, the logo is "
                               f"{title_screen.LOGO_WIDTH}x{title_screen.LOGO_HEIGHT}")
    nearest, inexact = {}, 0
    logo = []
    channels = image.tobytes()
    pixels = [tuple(channels[index : index + 3]) for index in range(0, len(channels), 3)]
    for y in range(title_screen.LOGO_HEIGHT):
        row = []
        for rgb in pixels[y * title_screen.LOGO_WIDTH : (y + 1) * title_screen.LOGO_WIDTH]:
            if rgb not in nearest:
                nearest[rgb] = min(range(title_screen.COLORS), key = lambda color:
                                   sum((a - b) ** 2 for a, b in zip(rgb, title_screen.PALETTE[color])))
            inexact += rgb != title_screen.PALETTE[nearest[rgb]]
            row.append(nearest[rgb])
        logo.append(row)
    if inexact:
        print(f"note: {inexact} pixels are not one of the logo's colors, they became the nearest one")
    return logo

def import_logo(source, png_path, output):
    data = title_screen.unpack(title_screen.read_block(source))
    tiles = title_screen.write_logo(data, image_logo(png_path))
    block = title_screen.pack(data)
    with open(output, "wb") as file:
        file.write(bytes(block))
    size = int.from_bytes(bytes(block[:2]), "little")
    print(f"{output}: {tiles} of {title_screen.LOGO_MAX_TILES} tiles, {size} of {title_screen.BLOCK_SIZE} bytes")

def info(source):
    block = title_screen.read_block(source)
    data = title_screen.unpack(block)
    logo = title_screen.read_logo(data)
    colors = sorted(set(color for row in logo for color in row))
    print(source)
    print(f"    {int.from_bytes(bytes(block[:2]), 'little')} of {title_screen.BLOCK_SIZE} bytes, {len(data)} decompressed")
    print(f"    the logo uses {title_screen.logo_tile_count(data)} of {title_screen.LOGO_MAX_TILES} tiles, colors {colors}")

def unpack(source, data_path):
    with open(data_path, "wb") as file:
        file.write(bytes(title_screen.unpack(title_screen.read_block(source))))
    print(f"{data_path}: the decompressed title screen data of {source}")

def pack(data_path, output):
    with open(data_path, "rb") as file:
        block = title_screen.pack(list(file.read()))
    with open(output, "wb") as file:
        file.write(bytes(block))
    print(f"{output}: {int.from_bytes(bytes(block[:2]), 'little')} of {title_screen.BLOCK_SIZE} bytes")

def main():
    parser = argparse.ArgumentParser(description = "Edit the title screen's logo (see graphics/title/README.md)")
    commands = parser.add_subparsers(dest = "command", required = True)

    command = commands.add_parser("export", help = "write the logo to a png")
    command.add_argument("png")
    command.add_argument("--source", default = DEFAULT_SOURCE, help = "title data file or rom to take the logo from")

    command = commands.add_parser("import", help = "make title data with the logo in a png")
    command.add_argument("png")
    command.add_argument("output", help = "the title data file to write")
    command.add_argument("--source", default = DEFAULT_SOURCE, help = "title data file or rom the rest of the title is from")

    command = commands.add_parser("info", help = "describe title data")
    command.add_argument("source", nargs = "?", default = DEFAULT_SOURCE)

    command = commands.add_parser("unpack", help = "write the decompressed title screen data to a file")
    command.add_argument("data")
    command.add_argument("--source", default = DEFAULT_SOURCE)

    command = commands.add_parser("pack", help = "make title data from decompressed title screen data")
    command.add_argument("data")
    command.add_argument("output")

    args = parser.parse_args()
    try:
        if args.command == "export":
            export_logo(args.source, args.png)
        elif args.command == "import":
            import_logo(args.source, args.png, args.output)
        elif args.command == "info":
            info(args.source)
        elif args.command == "unpack":
            unpack(args.source, args.data)
        elif args.command == "pack":
            pack(args.data, args.output)
    except (TitleScreenError, OSError) as error:
        sys.exit(f"error: {error}")

if __name__ == "__main__":
    main()
