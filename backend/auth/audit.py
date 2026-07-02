"""
AEGIS-OS Audit Logger.
Every significant action is recorded for compliance and forensic integrity.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("aegis.audit")


class AuditLogger:
    """
    Writes audit records to the audit_logs table.
    Used as a FastAPI dependency or standalone.
    """

    async def log(
        self,
        db,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
    ) -> None:
        """Persist an audit record."""
        try:
            from database.models import AuditLog
            entry = AuditLog(
                user_id=user_id,
                user_email=user_email,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                success=success,
                timestamp=datetime.now(timezone.utc),
            )
            db.add(entry)
            # Intentionally not awaiting commit here — let the request handler commit
            logger.info(
                f"AUDIT | {action} | {resource_type}/{resource_id} | "
                f"user={user_email} | ok={success}"
            )
        except Exception as e:
            # Audit log failure should never crash the main request
            logger.error(f"Audit log write failed: {e}")

    def log_sync(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Synchronous audit log (stdout only — for use in agents/functions)."""
        logger.info(
            f"AUDIT | {action} | {resource_type}/{resource_id} | "
            f"user={user_email} | details={details}"
        )


audit_logger = AuditLogger()
