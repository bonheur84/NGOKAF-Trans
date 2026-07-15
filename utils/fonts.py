"""Font loading for Qt."""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase

from config.settings import settings
from resources.theme import FONT_FALLBACK, FONT_FAMILY

logger = logging.getLogger(__name__)


def load_fonts() -> str:
    """Load Inter if present; otherwise fall back to Segoe UI."""
    fonts_dir: Path = settings.FONTS
    loaded = False
    if fonts_dir.exists():
        for pattern in ("Inter*.ttf", "Inter*.otf", "*.ttf"):
            for font_file in fonts_dir.glob(pattern):
                fid = QFontDatabase.addApplicationFont(str(font_file))
                if fid != -1:
                    loaded = True
                    families = QFontDatabase.applicationFontFamilies(fid)
                    logger.info("Loaded font: %s", families)
    if loaded and FONT_FAMILY in QFontDatabase.families():
        return FONT_FAMILY
    # Try system Inter
    if FONT_FAMILY in QFontDatabase.families():
        return FONT_FAMILY
    return FONT_FALLBACK


def app_font(size: int = 14, weight: int = QFont.Weight.Normal) -> QFont:
    family = FONT_FAMILY if FONT_FAMILY in QFontDatabase.families() else FONT_FALLBACK
    font = QFont(family, size)
    font.setWeight(weight)
    return font
