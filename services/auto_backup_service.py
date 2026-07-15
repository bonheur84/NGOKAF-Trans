"""Automatic daily backup service at 00h00."""
from __future__ import annotations

import logging
from datetime import datetime, time
from pathlib import Path

from PySide6.QtCore import QTimer, QObject

from config.settings import settings
from database.session import get_session
from services import backup_service, notification_service
from services.audit_service import log_audit

logger = logging.getLogger(__name__)


class AutoBackupService(QObject):
    """Service to perform automatic daily backups at midnight."""
    
    def __init__(self):
        super().__init__()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._check_and_backup)
        self._schedule_next_check()
    
    def _schedule_next_check(self) -> None:
        """Schedule next check for midnight."""
        now = datetime.now()
        midnight = datetime.combine(now.date(), time(0, 0, 0))
        
        # If we're past midnight today, schedule for tomorrow
        if now >= midnight:
            from datetime import timedelta
            midnight = midnight + timedelta(days=1)
        
        delay_ms = (midnight - now).total_seconds() * 1000
        self._timer.start(int(delay_ms))
        logger.info("Next auto-backup scheduled for %s", midnight)
    
    def _check_and_backup(self) -> None:
        """Perform backup if it's time (midnight)."""
        try:
            logger.info("Starting automatic daily backup...")
            backup_path = backup_service.backup_database()
            
            # Log to database
            session = get_session()
            try:
                log_audit(
                    session, 
                    "auto_backup", 
                    "database", 
                    None, 
                    None,  # System action, no user
                    {"path": str(backup_path), "type": "automatic"}
                )
                notification_service.notify_backup_success(
                    session, 
                    backup_path.name, 
                    None  # Global notification
                )
                session.commit()
            except Exception as e:
                logger.error("Failed to log auto-backup to database: %s", e)
                session.rollback()
            finally:
                session.close()
            
            logger.info("Automatic backup completed successfully: %s", backup_path)
        except Exception as e:
            logger.error("Automatic backup failed: %s", e)
            # Try to notify even if backup failed
            session = get_session()
            try:
                notification_service.notify_backup_failed(
                    session, 
                    str(e), 
                    None
                )
                session.commit()
            except Exception:
                pass
            finally:
                session.close()
        finally:
            # Schedule next backup
            self._schedule_next_check()
    
    def trigger_manual_backup(self) -> Path:
        """Trigger an immediate manual backup."""
        logger.info("Manual backup triggered...")
        backup_path = backup_service.backup_database()
        logger.info("Manual backup completed: %s", backup_path)
        return backup_path


# Global instance
_auto_backup_service: AutoBackupService | None = None


def get_auto_backup_service() -> AutoBackupService:
    """Get or create the global auto-backup service instance."""
    global _auto_backup_service
    if _auto_backup_service is None:
        _auto_backup_service = AutoBackupService()
    return _auto_backup_service
