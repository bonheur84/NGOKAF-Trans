"""MySQL dump / restore helpers with automatic daily backups."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from config.settings import settings

logger = logging.getLogger(__name__)


def backup_database(dest_dir: Path | None = None) -> Path:
    """Create a MySQL backup with organized folder structure (year/month/day)."""
    now = datetime.now()
    dest_dir = dest_dir or settings.BACKUPS
    
    # Create organized folder structure: backups/YYYY/MM/DD/
    year_month_day = dest_dir / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
    year_month_day.mkdir(parents=True, exist_ok=True)
    
    stamp = now.strftime("%Y%m%d_%H%M%S")
    out = year_month_day / f"ngokaf_trans_{stamp}.sql"
    
    cmd = [
        "mysqldump",
        f"-h{settings.DB_HOST}",
        f"-P{settings.DB_PORT}",
        f"-u{settings.DB_USER}",
        "--ssl-mode=REQUIRED" if settings.DB_SSL_MODE not in {"", "disabled", "false", "off", "none"} else "--skip-ssl",
        "--routines",
        "--triggers",
        settings.DB_NAME,
    ]
    env = {**os.environ, "MYSQL_PWD": settings.DB_PASSWORD}
    if settings.DB_SSL_CA:
        cmd.append(f"--ssl-ca={settings.DB_SSL_CA}")
    with out.open("w", encoding="utf-8") as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, env=env)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise RuntimeError(f"mysqldump failed: {result.stderr}")
    logger.info("Backup written to %s", out)
    
    # Also backup reports folder
    backup_reports(year_month_day, now)
    
    return out


def backup_reports(dest_dir: Path, now: datetime) -> Path:
    """Backup all reports (PDF, Excel, CSV) to the backup folder."""
    reports_dir = settings.REPORTS_DIR
    if not reports_dir.exists():
        logger.warning("Reports directory does not exist: %s", reports_dir)
        return dest_dir
    
    reports_backup = dest_dir / "reports"
    if reports_backup.exists():
        shutil.rmtree(reports_backup)
    shutil.copytree(reports_dir, reports_backup)
    logger.info("Reports backed up to %s", reports_backup)
    return reports_backup


def restore_database(sql_file: Path) -> None:
    """Restore MySQL database from SQL file."""
    cmd = [
        "mysql",
        f"-h{settings.DB_HOST}",
        f"-P{settings.DB_PORT}",
        f"-u{settings.DB_USER}",
        "--ssl-mode=REQUIRED" if settings.DB_SSL_MODE not in {"", "disabled", "false", "off", "none"} else "--skip-ssl",
        settings.DB_NAME,
    ]
    env = {**os.environ, "MYSQL_PWD": settings.DB_PASSWORD}
    if settings.DB_SSL_CA:
        cmd.append(f"--ssl-ca={settings.DB_SSL_CA}")
    with sql_file.open("r", encoding="utf-8") as f:
        result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"mysql restore failed: {result.stderr}")


def list_backups() -> list[Path]:
    """List all backup SQL files, sorted by date (newest first)."""
    if not settings.BACKUPS.exists():
        return []
    backups = list(settings.BACKUPS.rglob("*.sql"))
    backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return backups
