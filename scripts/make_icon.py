"""Generate Windows .ico and brand raster assets for NGOKAF TRANS."""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    # Brand pipeline: SVG masters + PNG/ICO/PDF + assets/icons/ngokaf.ico + logo.png
    scripts = Path(__file__).resolve().parent
    sys.path.insert(0, str(scripts))
    from export_brand import main as export_main

    return export_main()


if __name__ == "__main__":
    sys.exit(main())
