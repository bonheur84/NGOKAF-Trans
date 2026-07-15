"""Create writable runtime dirs and seed .env / config.ini on first launch."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path


RUNTIME_DIRS = ("logs", "backups", "reports", "temp", "config")


def ensure_runtime(root: Path, resource_root: Path) -> list[str]:
    """
    Ensure runtime folders exist and seed missing config files.
    Returns a list of human-readable warnings (empty if all OK).
    """
    warnings: list[str] = []

    for name in RUNTIME_DIRS:
        try:
            (root / name).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            warnings.append(f"Impossible de créer le dossier « {name} » : {e}")

    # Optional local assets for user overrides (logo drop-in)
    try:
        (root / "assets").mkdir(parents=True, exist_ok=True)
    except OSError as e:
        warnings.append(f"Impossible de créer assets : {e}")

    env_dst = root / ".env"
    if not env_dst.exists():
        for candidate in (
            resource_root / ".env.example",
            root / ".env.example",
            resource_root / "_internal" / ".env.example",
        ):
            if candidate.exists():
                try:
                    shutil.copy2(candidate, env_dst)
                    break
                except OSError as e:
                    warnings.append(f"Impossible de créer .env : {e}")
                    break
        else:
            warnings.append(
                "Fichier .env introuvable et aucun modèle .env.example disponible."
            )

    cfg_dst = root / "config.ini"
    if not cfg_dst.exists():
        for candidate in (
            resource_root / "config.ini.example",
            root / "config.ini.example",
            resource_root / "config.ini",
        ):
            if candidate.exists():
                try:
                    shutil.copy2(candidate, cfg_dst)
                    break
                except OSError as e:
                    warnings.append(f"Impossible de créer config.ini : {e}")
                    break
        else:
            warnings.append(
                "Fichier config.ini introuvable et aucun modèle disponible."
            )

    return warnings


def show_bootstrap_errors(messages: list[str]) -> None:
    """Display critical bootstrap messages (Qt if available, else stderr)."""
    if not messages:
        return
    text = "\n\n".join(messages)
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance()
        created = False
        if app is None:
            app = QApplication(sys.argv)
            created = True
        QMessageBox.warning(
            None,
            "NGOKAF TRANS — Configuration",
            "Certains fichiers ou dossiers sont manquants :\n\n" + text,
        )
        if created:
            # Do not quit; caller continues
            pass
    except Exception:
        print("NGOKAF TRANS — Configuration:", text, file=sys.stderr)


def verify_critical_resources(resource_root: Path) -> list[str]:
    """Return warnings if critical bundled resources are missing."""
    issues: list[str] = []
    logo_jpg = resource_root / "assets" / "images" / "logo.jpg"
    logo_png = resource_root / "assets" / "images" / "logo.png"
    if not logo_jpg.exists() and not logo_png.exists():
        issues.append(
            "Logo introuvable (assets/images/logo.png ou logo.jpg).\n"
            "L'application fonctionnera mais sans logo sur les tickets."
        )
    return issues
