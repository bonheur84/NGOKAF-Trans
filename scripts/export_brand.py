"""Export NGOKAF TRANS brand assets: PNG, ICO, PDF (SVG masters + Pillow renderer)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "assets" / "brand"
PNG_DIR = BRAND / "png"
PDF_DIR = BRAND / "pdf"
ICONS = ROOT / "assets" / "icons"
IMAGES = ROOT / "assets" / "images"

GOLD = (140, 106, 0, 255)
GOLD_LT = (165, 124, 0, 255)
GOLD_HI = (201, 162, 39, 255)
BROWN = (47, 42, 36, 255)
BROWN_DK = (26, 23, 20, 255)
BEIGE = (248, 242, 233, 255)
WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)

SIZES = [16, 32, 48, 64, 128, 256, 512, 1024]
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def _font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_mark(size: int = 1024, *, detail: bool = True) -> Image.Image:
    """Transparent symbol: route + bus + NG (+ ticket if detail)."""
    img = Image.new("RGBA", (size, size), TRANSPARENT)
    d = ImageDraw.Draw(img)
    s = size / 512.0

    def P(x: float, y: float) -> tuple[float, float]:
        return (x * s, y * s)

    def R(v: float) -> int:
        return max(1, int(v * s))

    # Route curves
    d.line(
        [P(70, 395), P(150, 355), P(230, 425), P(330, 365), P(450, 320)],
        fill=GOLD_LT,
        width=R(12),
        joint="curve",
    )
    d.line(
        [P(85, 415), P(165, 375), P(245, 445), P(345, 385), P(455, 350)],
        fill=GOLD,
        width=R(7),
        joint="curve",
    )
    d.ellipse([P(60, 385), P(80, 405)], fill=GOLD)
    d.ellipse([P(440, 310), P(460, 330)], fill=GOLD_LT)

    # Ticket
    if detail and size >= 64:
        tb = Image.new("RGBA", (R(100), R(120)), TRANSPARENT)
        tbd = ImageDraw.Draw(tb)
        tbd.rounded_rectangle(
            [R(4), R(4), R(76), R(100)],
            radius=R(8),
            fill=BEIGE,
            outline=GOLD,
            width=R(3),
        )
        tbd.ellipse([R(-6), R(42), R(10), R(58)], fill=WHITE)
        tbd.ellipse([R(70), R(42), R(86), R(58)], fill=WHITE)
        tbd.rounded_rectangle([R(16), R(20), R(60), R(28)], radius=R(2), fill=GOLD)
        tbd.rounded_rectangle([R(16), R(38), R(50), R(44)], radius=R(2), fill=(*BROWN[:3], 55))
        tbd.rounded_rectangle([R(20), R(70), R(56), R(86)], radius=R(3), fill=GOLD)
        rotated = tb.rotate(-12, expand=True, resample=Image.Resampling.BICUBIC)
        layer = Image.new("RGBA", (size, size), TRANSPARENT)
        layer.paste(rotated, (int(355 * s), int(110 * s)), rotated)
        img = Image.alpha_composite(img, layer)
        d = ImageDraw.Draw(img)

    # Ground shadow
    d.ellipse([P(140, 340), P(370, 370)], fill=(*BROWN[:3], 45))

    # Bus body
    d.rounded_rectangle([P(120, 175), P(360, 290)], radius=R(28), fill=GOLD)
    # Cabin extension / nose
    d.rounded_rectangle([P(330, 195), P(400, 275)], radius=R(22), fill=GOLD_LT)
    # Roof highlight
    d.rounded_rectangle([P(130, 182), P(345, 225)], radius=R(18), fill=(*GOLD_HI[:3], 150))
    # Windshield
    d.rounded_rectangle([P(338, 205), P(388, 255)], radius=R(10), fill=BROWN_DK)
    d.rounded_rectangle([P(345, 212), P(372, 245)], radius=R(6), fill=(*BEIGE[:3], 70))
    # Side windows
    for wx in (145, 195, 245, 295):
        d.rounded_rectangle([P(wx, 200), P(wx + 38, 235)], radius=R(6), fill=BROWN_DK)
    # Bumper
    d.rounded_rectangle([P(125, 272), P(395, 288)], radius=R(6), fill=(*BROWN_DK[:3], 200))
    # Wheels
    for wx in (175, 320):
        d.ellipse([P(wx - 26, 278), P(wx + 26, 330)], fill=BROWN_DK)
        d.ellipse([P(wx - 11, 293), P(wx + 11, 315)], fill=GOLD_LT)
    # Headlight
    d.ellipse([P(385, 235), P(403, 253)], fill=BEIGE)
    d.ellipse([P(389, 239), P(399, 249)], fill=GOLD_LT)
    # NG badge
    d.rounded_rectangle([P(148, 245), P(210, 275)], radius=R(7), fill=BROWN_DK)
    font = _font(max(9, R(18)))
    bbox = d.textbbox((0, 0), "NG", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((179 * s - tw / 2, 260 * s - th / 2), "NG", font=font, fill=GOLD_LT)

    return img


def draw_app_icon(size: int = 1024) -> Image.Image:
    img = Image.new("RGBA", (size, size), TRANSPARENT)
    d = ImageDraw.Draw(img)
    pad = int(size * 0.03)
    radius = int(size * 0.21)
    d.rounded_rectangle([pad, pad, size - pad - 1, size - pad - 1], radius=radius, fill=BROWN)
    gloss = Image.new("RGBA", (size, size), TRANSPARENT)
    ImageDraw.Draw(gloss).rounded_rectangle(
        [pad, pad, size - pad - 1, int(size * 0.36)],
        radius=radius,
        fill=(255, 255, 255, 16),
    )
    img = Image.alpha_composite(img, gloss)
    mark = draw_mark(size, detail=size >= 64)
    inset = int(size * 0.05)
    mark_s = mark.resize((size - 2 * inset, size - 2 * inset), Image.Resampling.LANCZOS)
    layer = Image.new("RGBA", (size, size), TRANSPARENT)
    layer.paste(mark_s, (inset, inset), mark_s)
    return Image.alpha_composite(img, layer)


def draw_circle_icon(size: int = 1024) -> Image.Image:
    img = Image.new("RGBA", (size, size), TRANSPARENT)
    d = ImageDraw.Draw(img)
    m = int(size * 0.03)
    d.ellipse([m, m, size - m - 1, size - m - 1], fill=BROWN)
    gloss = Image.new("RGBA", (size, size), TRANSPARENT)
    ImageDraw.Draw(gloss).ellipse(
        [int(size * 0.14), int(size * 0.07), int(size * 0.52), int(size * 0.4)],
        fill=(255, 255, 255, 14),
    )
    img = Image.alpha_composite(img, gloss)
    mark = draw_mark(size, detail=size >= 64)
    inset = int(size * 0.07)
    mark_s = mark.resize((size - 2 * inset, size - 2 * inset), Image.Resampling.LANCZOS)
    layer = Image.new("RGBA", (size, size), TRANSPARENT)
    layer.paste(mark_s, (inset, inset), mark_s)
    return Image.alpha_composite(img, layer)


def draw_lockup(width: int = 2048, height: int = 768) -> Image.Image:
    img = Image.new("RGBA", (width, height), TRANSPARENT)
    mark_h = int(height * 0.92)
    mark = draw_mark(mark_h, detail=True).resize((mark_h, mark_h), Image.Resampling.LANCZOS)
    img.paste(mark, (int(width * 0.02), (height - mark_h) // 2), mark)
    d = ImageDraw.Draw(img)
    text_x = int(width * 0.42)
    d.text((text_x, int(height * 0.28)), "NGOKAF", font=_font(max(28, int(height * 0.22))), fill=BROWN)
    d.text((text_x, int(height * 0.52)), "TRANS", font=_font(max(20, int(height * 0.14))), fill=GOLD)
    bar_y = int(height * 0.72)
    d.rounded_rectangle(
        [text_x, bar_y, text_x + int(width * 0.12), bar_y + max(4, height // 80)],
        radius=3,
        fill=GOLD_LT,
    )
    return img


def try_cairo_raster(svg_path: Path, out_png: Path, size: int) -> bool:
    try:
        import cairosvg  # type: ignore
    except Exception:
        return False
    try:
        kwargs = {"url": str(svg_path), "write_to": str(out_png), "output_width": size}
        if "lockup" in svg_path.name:
            kwargs["output_height"] = int(size * 0.375)
        else:
            kwargs["output_height"] = size
        cairosvg.svg2png(**kwargs)
        return out_png.exists()
    except Exception:
        return False


def export_png_set(name: str, image: Image.Image) -> Path:
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    master = PNG_DIR / f"{name}_1024.png"
    if name == "lockup":
        image.resize((2048, 768), Image.Resampling.LANCZOS).save(
            PNG_DIR / f"{name}_2048x768.png", "PNG"
        )
        image.resize((1024, 384), Image.Resampling.LANCZOS).save(master, "PNG")
    else:
        base = image.resize((1024, 1024), Image.Resampling.LANCZOS)
        base.save(master, "PNG")
        for sz in SIZES:
            if sz == 1024:
                continue
            base.resize((sz, sz), Image.Resampling.LANCZOS).save(
                PNG_DIR / f"{name}_{sz}.png", "PNG"
            )
    return master


def build_ico(app_icon: Image.Image) -> Path:
    """Write multi-resolution Windows ICO (16…256) from the rounded app icon."""
    ICONS.mkdir(parents=True, exist_ok=True)
    brand_ico = BRAND / "ngokaf.ico"
    icons_path = ICONS / "ngokaf.ico"

    frames: list[Image.Image] = []
    for w, h in ICO_SIZES:
        # Redraw at higher res then downsample for cleaner small sizes
        src = draw_app_icon(256 if w <= 48 else max(w, 256))
        frames.append(src.resize((w, h), Image.Resampling.LANCZOS).convert("RGBA"))

    _write_ico_manual(brand_ico, frames)
    shutil.copy2(brand_ico, icons_path)
    return icons_path


def _write_ico_manual(path: Path, frames: list[Image.Image]) -> None:
    """Minimal ICO writer (PNG-compressed entries) when Pillow collapses frames."""
    import struct
    import io

    entries = []
    images_data = []
    for im in frames:
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        data = buf.getvalue()
        w, h = im.size
        entries.append((w if w < 256 else 0, h if h < 256 else 0, len(data), data))
        images_data.append(data)

    # ICONDIR + ICONDIRENTRY * n + payloads
    offset = 6 + 16 * len(entries)
    parts = [struct.pack("<HHH", 0, 1, len(entries))]
    for w, h, size, _ in entries:
        parts.append(struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, size, offset))
        offset += size
    for _, _, _, data in entries:
        parts.append(data)
    path.write_bytes(b"".join(parts))


def export_pdfs(png_map: dict[str, Path]) -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    for name, png in png_map.items():
        if not png.exists():
            continue
        out = PDF_DIR / f"ngokaf_{name}.pdf"
        c = pdf_canvas.Canvas(str(out), pagesize=A4)
        w, h = A4
        c.setFont("Helvetica-Bold", 16)
        c.setFillColorRGB(47 / 255, 42 / 255, 36 / 255)
        c.drawString(40, h - 40, f"NGOKAF TRANS — {name}")
        im = Image.open(png)
        max_w = 120 * mm
        ratio = im.height / max(im.width, 1)
        draw_w = max_w
        draw_h = max_w * ratio
        if draw_h > 160 * mm:
            draw_h = 160 * mm
            draw_w = draw_h / ratio
        c.drawImage(
            ImageReader(im),
            (w - draw_w) / 2,
            h - 60 - draw_h,
            width=draw_w,
            height=draw_h,
            mask="auto",
        )
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.45, 0.45, 0.45)
        c.drawString(40, 40, "Identité visuelle — billets, factures, rapports, favicon, raccourcis")
        c.save()


def install_ui_logo(symbol_png: Path) -> Path:
    IMAGES.mkdir(parents=True, exist_ok=True)
    dest = IMAGES / "logo.png"
    shutil.copy2(symbol_png, dest)
    return dest


def main() -> int:
    BRAND.mkdir(parents=True, exist_ok=True)
    print("Génération PNG (Pillow)…")
    symbol = draw_mark(1024, detail=True)
    app_icon = draw_app_icon(1024)
    circle = draw_circle_icon(1024)
    lockup = draw_lockup(2048, 768)

    masters = {
        "symbol": export_png_set("symbol", symbol),
        "app_icon": export_png_set("app_icon", app_icon),
        "circle": export_png_set("circle", circle),
        "lockup": export_png_set("lockup", lockup),
    }

    for name, svg in {
        "symbol": BRAND / "ngokaf_symbol.svg",
        "app_icon": BRAND / "ngokaf_app_icon.svg",
        "circle": BRAND / "ngokaf_circle.svg",
        "lockup": BRAND / "ngokaf_lockup.svg",
    }.items():
        if svg.exists() and try_cairo_raster(svg, PNG_DIR / f"{name}_1024.png", 1024):
            print(f"  SVG→PNG cairo: {name}")
            if name != "lockup":
                master_img = Image.open(PNG_DIR / f"{name}_1024.png").convert("RGBA")
                for sz in SIZES:
                    if sz == 1024:
                        continue
                    master_img.resize((sz, sz), Image.Resampling.LANCZOS).save(
                        PNG_DIR / f"{name}_{sz}.png", "PNG"
                    )
                if name == "app_icon":
                    app_icon = master_img
                if name == "symbol":
                    masters["symbol"] = PNG_DIR / "symbol_1024.png"

    ico = build_ico(app_icon)
    print(f"ICO: {ico}")
    export_pdfs(masters)
    print(f"PDF -> {PDF_DIR}")
    logo = install_ui_logo(masters["symbol"])
    print(f"UI logo: {logo}")
    app_icon.resize((256, 256), Image.Resampling.LANCZOS).save(BRAND / "ngokaf_app_icon_256.png")
    print("Export brand termine.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
