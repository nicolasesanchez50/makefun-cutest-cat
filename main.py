#!/usr/bin/env python3
"""Writes one picture of a cat to the run's output directory.

The picture is the 1024px kitten shipped beside this program as cat.png.
The program checks that the file is a whole PNG inside the competition's
limits and then copies its bytes unchanged, so every run writes the same
bytes and the judge sees exactly the file the repository holds.
"""

import os
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGE = HERE / "cat.png"

MAX_BYTES = 1024 * 1024
MAX_SIDE = 1024


def output_dir() -> Path:
    """The writable directory the harness gives the run (/output by default)."""
    return Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")


def read_png(path: Path) -> bytes:
    """Return the file's bytes after checking it starts like a PNG."""
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SystemExit(f"{path.name}: not a PNG")
    return data


def image_size(data: bytes) -> tuple[int, int]:
    """Width and height from the IHDR chunk, which a PNG header always holds."""
    if len(data) < 24 or data[12:16] != b"IHDR":
        raise SystemExit("cat.png: no IHDR chunk")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def check_whole(data: bytes) -> None:
    """Walk every chunk, checking its CRC, and insist the stream ends with IEND.

    A truncated or corrupted PNG is refused here rather than by the gate, so a
    broken file never reaches the judge as a blank entry.
    """
    import binascii

    pos = 8
    seen_iend = False
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        crc = data[pos + 8 + length:pos + 12 + length]
        if len(crc) != 4:
            raise SystemExit("cat.png: a chunk is cut short")
        want = binascii.crc32(kind + body) & 0xFFFFFFFF
        if want != struct.unpack(">I", crc)[0]:
            raise SystemExit(f"cat.png: chunk {kind!r} fails its checksum")
        pos += 12 + length
        if kind == b"IEND":
            seen_iend = True
            break
    if not seen_iend or pos != len(data):
        raise SystemExit("cat.png: the image is not whole")


def main() -> int:
    data = read_png(IMAGE)
    if len(data) > MAX_BYTES:
        raise SystemExit(f"cat.png: {len(data)} bytes, over the {MAX_BYTES}-byte limit")
    width, height = image_size(data)
    if width > MAX_SIDE or height > MAX_SIDE:
        raise SystemExit(f"cat.png: {width}x{height}, over {MAX_SIDE}px")
    check_whole(data)

    out = output_dir()
    out.mkdir(parents=True, exist_ok=True)
    target = out / "entry.png"
    target.write_bytes(data)
    print(f"wrote {target} ({width}x{height}, {len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
