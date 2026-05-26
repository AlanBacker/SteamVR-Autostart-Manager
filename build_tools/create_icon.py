from __future__ import annotations

import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "app_icon.ico"


def bgra(hex_color: str) -> bytes:
    value = hex_color.lstrip("#")
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    return bytes((b, g, r, 255))


def rect(pixels: list[list[bytes]], x1: int, y1: int, x2: int, y2: int, color: str) -> None:
    value = bgra(color)
    for y in range(max(0, y1), min(32, y2)):
        for x in range(max(0, x1), min(32, x2)):
            pixels[y][x] = value


def make_icon() -> bytes:
    pixels = [[bgra("#0b1220") for _x in range(32)] for _y in range(32)]
    rect(pixels, 2, 2, 30, 30, "#101b2d")
    rect(pixels, 6, 6, 26, 9, "#14b8a6")
    rect(pixels, 6, 9, 10, 26, "#38bdf8")
    rect(pixels, 12, 12, 16, 26, "#e5eef8")
    rect(pixels, 16, 12, 23, 16, "#e5eef8")
    rect(pixels, 20, 16, 24, 26, "#e5eef8")
    rect(pixels, 12, 20, 24, 23, "#14b8a6")
    rect(pixels, 24, 6, 27, 26, "#38bdf8")

    xor_bitmap = b"".join(b"".join(row) for row in reversed(pixels))
    and_mask = b"\x00" * (32 * 4)
    bitmap_info = struct.pack(
        "<IIIHHIIIIII",
        40,
        32,
        64,
        1,
        32,
        0,
        len(xor_bitmap) + len(and_mask),
        0,
        0,
        0,
        0,
    )
    image = bitmap_info + xor_bitmap + and_mask
    header = struct.pack("<HHH", 0, 1, 1)
    directory = struct.pack("<BBBBHHII", 32, 32, 0, 0, 1, 32, len(image), 6 + 16)
    return header + directory + image


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(make_icon())
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
