from __future__ import annotations

import io
import textwrap
from pathlib import Path
from typing import Iterable

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "share_cards"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try common CJK-capable fonts first, then fall back to Latin fonts.

    On Windows this should pick Microsoft JhengHei, so Chinese restaurant names can
    render correctly in generated PNG cards.
    """
    candidates = [
        # Windows
        "C:/Windows/Fonts/msjh.ttc" if not bold else "C:/Windows/Fonts/msjhbd.ttc",
        "C:/Windows/Fonts/mingliu.ttc",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        # Linux CJK candidates
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" if not bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc" if not bold else "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        # Latin fallback
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    font: ImageFont.ImageFont,
    fill: str,
    width_chars: int,
    line_gap: int = 8,
    max_lines: int | None = None,
) -> int:
    x, y = xy
    lines: list[str] = []
    for paragraph in str(text).split("\n"):
        lines.extend(textwrap.wrap(paragraph, width=width_chars) or [""])
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .") + "..."
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line, font=font)
        y += (bbox[3] - bbox[1]) + line_gap
    return y


def _items(value: object, limit: int = 5) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out = [str(x).strip() for x in value if str(x).strip()]
    else:
        out = [x.strip() for x in str(value).split("|") if x.strip()]
    return out[:limit]


def _tags_to_text(tags: Iterable[str], limit: int = 5) -> str:
    items = list(tags)[:limit]
    return "  •  ".join(items) if items else "Not enough repeated signal yet"


def _open_photo(photo_url: str | None, size: tuple[int, int]) -> Image.Image:
    W, H = size
    if photo_url:
        try:
            if str(photo_url).startswith("http"):
                response = requests.get(str(photo_url), timeout=8)
                response.raise_for_status()
                source = Image.open(io.BytesIO(response.content)).convert("RGB")
            else:
                source = Image.open(ROOT / str(photo_url)).convert("RGB")
            # cover crop
            src_w, src_h = source.size
            scale = max(W / src_w, H / src_h)
            resized = source.resize((int(src_w * scale), int(src_h * scale)))
            left = (resized.width - W) // 2
            top = (resized.height - H) // 2
            return resized.crop((left, top, left + W, top + H))
        except Exception:
            pass

    # Warm gradient fallback, so share cards still look designed.
    img = Image.new("RGB", (W, H), "#fed7aa")
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / max(1, H - 1)
        r = int(254 * (1 - t) + 253 * t)
        g = int(215 * (1 - t) + 186 * t)
        b = int(170 * (1 - t) + 116 * t)
        draw.line((0, y, W, y), fill=(r, g, b))
    return img.filter(ImageFilter.GaussianBlur(0.2))


def _rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def _paste_rounded(base: Image.Image, image: Image.Image, box: tuple[int, int], radius: int) -> None:
    mask = _rounded_mask(image.size, radius)
    base.paste(image, box, mask)


def generate_restaurant_card(row: dict, output_path: Path | None = None, photo_url: str | None = None) -> Path:
    """Generate a polished vertical social-share style PNG card."""
    rid = str(row.get("restaurant_id", "restaurant")).replace("/", "_")
    output_path = output_path or OUTPUT_DIR / f"share_card_{rid}.png"

    W, H = 1080, 1720
    img = Image.new("RGB", (W, H), "#fff7ed")
    draw = ImageDraw.Draw(img)

    # Background
    for y in range(H):
        t = y / max(1, H - 1)
        r = int(255 * (1 - t) + 255 * t)
        g = int(247 * (1 - t) + 250 * t)
        b = int(237 * (1 - t) + 242 * t)
        draw.line((0, y, W, y), fill=(r, g, b))
    draw.ellipse((-180, -160, 420, 420), fill="#ffedd5")
    draw.ellipse((760, 80, 1240, 560), fill="#dcfce7")
    draw.ellipse((700, 1050, 1250, 1600), fill="#dbeafe")

    title_font = _font(66, bold=True)
    sub_font = _font(36, bold=True)
    body_font = _font(31)
    small_font = _font(25)
    badge_font = _font(30, bold=True)
    micro_font = _font(22)

    # Main white card
    draw.rounded_rectangle((54, 54, W - 54, H - 54), radius=46, fill="#ffffff", outline="#f3e8d7", width=2)

    # Photo hero
    hero = _open_photo(photo_url, (972, 430))
    _paste_rounded(img, hero, (54, 54), 46)
    overlay = Image.new("RGBA", (972, 430), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for yy in range(430):
        alpha = int(10 + 125 * (yy / 430))
        od.line((0, yy, 972, yy), fill=(17, 24, 39, alpha))
    img.paste(overlay, (54, 54), overlay)

    name = str(row.get("name", "Restaurant"))
    area = str(row.get("area", "Area"))
    cuisine = str(row.get("primary_cuisine", "Food"))
    personality = str(row.get("personality_type", "Restaurant Personality"))
    summary = str(row.get("one_line_summary", "No summary yet."))
    price_min = int(float(row.get("price_min", 0)))
    price_max = int(float(row.get("price_max", 0)))
    rating = float(row.get("rating", 0))
    distance = int(float(row.get("distance_min", 0)))
    score = float(row.get("group_match_score", rating * 20))

    draw.rounded_rectangle((92, 96, 430, 146), radius=25, fill="#f97316")
    draw.text((116, 108), "BiteRadar Pick", font=small_font, fill="#ffffff")
    draw.rounded_rectangle((800, 96, 990, 156), radius=26, fill="#10b981")
    draw.text((826, 111), f"{score:.0f}% match", font=small_font, fill="#ffffff")

    # Text on hero
    y = 255
    draw.text((92, y), name, font=title_font, fill="#ffffff")
    y += 78
    draw.text((96, y), f"{area} · {cuisine} · NT${price_min}-{price_max} · {distance} min walk", font=small_font, fill="#f3f4f6")

    # Body content
    y = 535
    draw.rounded_rectangle((92, y, 92 + min(820, 245 + len(personality) * 18), y + 58), radius=29, fill="#111827")
    draw.text((122, y + 13), f"✨ {personality}", font=badge_font, fill="#ffffff")
    y += 90

    draw.text((92, y), "One-line personality", font=sub_font, fill="#111827")
    y += 50
    y = _draw_wrapped(draw, summary, (92, y), body_font, "#374151", 43, line_gap=10, max_lines=3)
    y += 24

    # Best for
    draw.rounded_rectangle((92, y, 988, y + 118), radius=28, fill="#eff6ff")
    draw.text((122, y + 18), "Best for", font=small_font, fill="#1e40af")
    draw.text((122, y + 58), _tags_to_text(_items(row.get("occasion_tags"), 4)), font=body_font, fill="#1e3a8a")
    y += 144

    # Positive and watch-outs in two boxes
    box_h = 170
    draw.rounded_rectangle((92, y, 525, y + box_h), radius=28, fill="#dcfce7")
    draw.text((122, y + 20), "People like", font=small_font, fill="#166534")
    _draw_wrapped(draw, _tags_to_text(_items(row.get("positive_tags"), 4)), (122, y + 62), body_font, "#14532d", 25, max_lines=3)

    draw.rounded_rectangle((555, y, 988, y + box_h), radius=28, fill="#fee2e2")
    draw.text((585, y + 20), "Watch out", font=small_font, fill="#991b1b")
    _draw_wrapped(draw, _tags_to_text(_items(row.get("negative_tags"), 3)), (585, y + 62), body_font, "#7f1d1d", 24, max_lines=3)
    y += box_h + 34

    draw.text((92, y), "Recommended dishes", font=sub_font, fill="#111827")
    y += 48
    y = _draw_wrapped(draw, _tags_to_text(_items(row.get("recommended_dishes"), 4)), (92, y), body_font, "#374151", 44, max_lines=2)
    y += 20

    # Mini metrics
    metrics = [
        ("Food", row.get("food_score", 0)),
        ("Vibe", row.get("vibe_score", 0)),
        ("Value", row.get("value_score", 0)),
        ("Group", row.get("group_score", 0)),
    ]
    col_w = 204
    for i, (label, value) in enumerate(metrics):
        x = 92 + i * (col_w + 26)
        draw.rounded_rectangle((x, y, x + col_w, y + 94), radius=25, fill="#f9fafb", outline="#e5e7eb", width=1)
        draw.text((x + 24, y + 18), label, font=micro_font, fill="#6b7280")
        draw.text((x + 24, y + 46), f"{float(value):.1f}/5", font=badge_font, fill="#111827")
    y += 140

    # Footer
    # Footer: keep it clearly separated from the metric cards.
    # The original 1500px canvas could overlap when recommended dishes wrapped to 2 lines.
    footer_top = max(y + 48, H - 178)
    footer_bottom = footer_top + 64
    if footer_bottom > H - 70:
        footer_top = H - 178
        footer_bottom = H - 114

    draw.rounded_rectangle((92, footer_top, 988, footer_bottom), radius=30, fill="#111827")
    draw.text((122, footer_top + 18), "Generated by BiteRadar · Restaurant Personality Card", font=small_font, fill="#ffffff")
    draw.text((122, H - 82), "Prototype uses placeholder/self-owned/licensed images unless official API display is enabled.", font=micro_font, fill="#6b7280")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path
