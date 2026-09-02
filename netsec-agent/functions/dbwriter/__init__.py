"""Optional PostgreSQL persistence helpers for the netsec Function App."""

from dbwriter.persist import (
    log_activity,
    persist_assessment,
)

__all__ = ["log_activity", "persist_assessment"]
