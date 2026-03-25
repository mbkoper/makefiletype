import argparse
import io
import math
import os
import random
import string
import sys

SUPPORTED_TYPES = ["pdf", "tiff", "jpg", "html", "txt", "xml"]


def generate_pdf(target_size: int) -> bytes:
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    for _ in range(20):
        r, g, b = random.random(), random.random(), random.random()
        c.setFillColorRGB(r, g, b)
        x = random.randint(0, 500)
        y = random.randint(0, 800)
        c.rect(x, y, 20, 20, fill=1, stroke=0)
    c.save()
    pdf_data = buffer.getvalue()

    if len(pdf_data) > target_size:
        # Fallback: minimal PDF
        buf2 = io.BytesIO()
        c2 = canvas.Canvas(buf2)
        c2.save()
        pdf_data = buf2.getvalue()

    if len(pdf_data) > target_size:
        raise ValueError(
            f"Target size {target_size} is too small for a valid PDF "
            f"(minimum ~{len(pdf_data)} bytes)."
        )

    shortfall = target_size - len(pdf_data)
    if shortfall >= 2:
        padding = b"\n%" + os.urandom(shortfall - 2)
    else:
        padding = b" " * shortfall
    return pdf_data + padding


def generate_tiff(target_size: int) -> bytes:
    from PIL import Image

    # Scale image dimensions with target size; TIFF is uncompressed (~3 bytes/pixel).
    side = max(8, int(math.sqrt(target_size / 3)))
    while True:
        img = Image.frombytes("RGB", (side, side), os.urandom(side * side * 3))
        buf = io.BytesIO()
        img.save(buf, format="TIFF")
        tiff_data = buf.getvalue()
        if len(tiff_data) <= target_size:
            break
        if side <= 8:
            raise ValueError(
                f"Target size {target_size} is too small for a valid TIFF "
                f"(minimum ~{len(tiff_data)} bytes)."
            )
        side = max(8, side - max(1, side // 10))

    shortfall = target_size - len(tiff_data)
    return tiff_data + os.urandom(shortfall)


def generate_jpg(target_size: int) -> bytes:
    from PIL import Image

    # Scale image dimensions with target size; random-noise JPEG at quality=85
    # compresses poorly, so estimate ~5 bytes/pixel and iterate down if needed.
    side = max(8, int(math.sqrt(target_size / 5)))
    while True:
        img = Image.frombytes("RGB", (side, side), os.urandom(side * side * 3))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        jpg_data = buf.getvalue()
        if len(jpg_data) <= target_size:
            break
        if side <= 8:
            raise ValueError(
                f"Target size {target_size} is too small for a valid JPEG "
                f"(minimum ~{len(jpg_data)} bytes)."
            )
        side = max(8, side - max(1, side // 10))

    # Append padding after the EOI marker (0xFFD9)
    shortfall = target_size - len(jpg_data)
    return jpg_data + os.urandom(shortfall)


def generate_html(target_size: int) -> bytes:
    base = (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head><title>Generated</title></head>\n"
        "<body>\n"
        "<p>Generated file.</p>\n"
        "</body>\n"
        "</html>"
    )
    base_bytes = base.encode("utf-8")

    if len(base_bytes) > target_size:
        raise ValueError(
            f"Target size {target_size} is too small for a valid HTML document "
            f"(minimum {len(base_bytes)} bytes)."
        )

    shortfall = target_size - len(base_bytes)
    if shortfall == 0:
        return base_bytes

    # Pad using HTML comments: <!-- ... -->
    # Overhead: "<!-- " (5 bytes) + " -->" (4 bytes) = 9 bytes; content fills the rest.
    OPEN = b"<!-- "
    CLOSE = b" -->"
    overhead = len(OPEN) + len(CLOSE)  # 9

    # Insert comment block just before </body>
    insert_point = base_bytes.rfind(b"</body>")
    prefix = base_bytes[:insert_point]
    suffix = base_bytes[insert_point:]

    if shortfall < overhead + 1:
        # Not enough room for a comment; pad with spaces before </body>
        return prefix + b" " * shortfall + suffix

    comment_content_len = shortfall - overhead
    comment_content = _random_printable_bytes(comment_content_len)
    return prefix + OPEN + comment_content + CLOSE + suffix


def generate_txt(target_size: int) -> bytes:
    chars = string.ascii_letters + string.digits + string.punctuation + " "
    content = "".join(random.choices(chars, k=target_size))
    return content.encode("utf-8")


def generate_xml(target_size: int) -> bytes:
    base = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<root>\n"
        "  <item>Generated</item>\n"
        "</root>"
    )
    base_bytes = base.encode("utf-8")

    if len(base_bytes) > target_size:
        raise ValueError(
            f"Target size {target_size} is too small for a valid XML document "
            f"(minimum {len(base_bytes)} bytes)."
        )

    shortfall = target_size - len(base_bytes)
    if shortfall == 0:
        return base_bytes

    OPEN = b"<!-- "
    CLOSE = b" -->"
    overhead = len(OPEN) + len(CLOSE)  # 9

    insert_point = base_bytes.rfind(b"</root>")
    prefix = base_bytes[:insert_point]
    suffix = base_bytes[insert_point:]

    if shortfall < overhead + 1:
        # Pad with spaces
        return prefix + b" " * shortfall + suffix

    comment_content_len = shortfall - overhead
    comment_content = _random_printable_bytes(comment_content_len)
    return prefix + OPEN + comment_content + CLOSE + suffix


def _random_printable_bytes(length: int) -> bytes:
    # Printable ASCII excluding '--' sequences to keep XML/HTML comments valid
    chars = (string.ascii_letters + string.digits + " ").encode("ascii")
    return bytes(random.choices(chars, k=length))


def parse_size(value: str) -> int:
    """Parse a size string with optional suffix into bytes.

    Supported suffixes (case-insensitive): k/K (kibibytes), m/M (mebibytes),
    g/G (gibibytes). A bare integer is treated as bytes.

    Examples: '100k', '100K', '1m', '1g', '1024'
    """
    value = value.strip()
    suffixes = {"k": 1024, "m": 1024 ** 2, "g": 1024 ** 3}
    if value and value[-1].lower() in suffixes:
        multiplier = suffixes[value[-1].lower()]
        number_part = value[:-1]
    else:
        multiplier = 1
        number_part = value
    try:
        return int(number_part) * multiplier
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid size '{value}'. Use an integer optionally followed by "
            "k/K (kibibytes), m/M (mebibytes), or g/G (gibibytes). "
            "Examples: 1024, 100k, 5m, 1g"
        )


def _format_size(n: int) -> str:
    """Return a compact size label: e.g. 5120 → '5k', 5242880 → '5m', 999 → '999'."""
    if n >= 1024 * 1024 and n % (1024 * 1024) == 0:
        return f"{n // (1024 * 1024)}m"
    if n >= 1024 and n % 1024 == 0:
        return f"{n // 1024}k"
    return str(n)


GENERATORS = {
    "pdf": generate_pdf,
    "tiff": generate_tiff,
    "jpg": generate_jpg,
    "html": generate_html,
    "txt": generate_txt,
    "xml": generate_xml,
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate a file of a specified type and exact size."
    )
    parser.add_argument(
        "--type", "-t",
        required=True,
        choices=SUPPORTED_TYPES,
        help="File type to generate: " + ", ".join(SUPPORTED_TYPES),
    )
    parser.add_argument(
        "--size", "-s",
        required=True,
        type=parse_size,
        help=(
            "Desired file size. Accepts a plain integer (bytes) or an integer "
            "with a suffix: k/K (kibibytes), m/M (mebibytes), g/G (gibibytes). "
            "Examples: 1024, 100k, 5m, 1g"
        ),
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output filename (default: <size>.<ext>, e.g. 250k.pdf).",
    )

    args = parser.parse_args()

    if args.size <= 0:
        print(f"Error: --size must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    file_type = args.type
    target_size = args.size
    output_file = args.output if args.output else f"{_format_size(target_size)}.{file_type}"

    try:
        data = GENERATORS[file_type](target_size)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if len(data) != target_size:
        print(
            f"Error: generated {len(data)} bytes but expected {target_size}.",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(output_file, "wb") as f:
        f.write(data)

    print(f"Saved: {output_file} | Size: {len(data)} bytes")


if __name__ == "__main__":
    main()
