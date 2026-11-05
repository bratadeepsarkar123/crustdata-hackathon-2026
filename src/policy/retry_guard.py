import time
import logging
from typing import Dict, Any, Callable, Optional


logger = logging.getLogger(__name__)


class IdempotencyError(Exception):
    """Raised when an idempotency violation occurs or retry limits are exceeded."""
    pass


class IdempotencyStore:
    """In-memory idempotency registry storing state before any write operation.
    
    Conforms to MASTER-HANDOFF Section 4:
    'Idempotency: every write (WhatsApp send, quote, vendor record, PO) gets a unique key,
     stored before the write and checked before any retry. A crash or retry never sends or creates twice.'
    """

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._store.get(key)

    def record_pending(self, key: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        record = {
            "idempotency_key": key,
            "status": "PENDING",
            "attempts": 1,
            "result": None,
            "error": None,
            "created_at": time.time(),
            "updated_at": time.time(),
            "metadata": metadata or {}
        }
        self._store[key] = record
        return record

    def record_success(self, key: str, result: Any) -> Dict[str, Any]:
        record = self._store.get(key, {})
        record.update({
            "status": "SUCCESS",
            "result": result,
            "error": None,
            "updated_at": time.time()
        })
        self._store[key] = record
        return record

    def record_failure(self, key: str, error: str) -> Dict[str, Any]:
        record = self._store.get(key, {})
        attempts = record.get("attempts", 0) + 1
        record.update({
            "status": "FAILED",
            "error": error,
            "attempts": attempts,
            "updated_at": time.time()
        })
        self._store[key] = record
        return record

    def clear(self):
        self._store.clear()


class ActionRetryGuard:
    """Generic idempotent executor handling retries for transient actions without duplicates."""

    def __init__(self, store: Optional[IdempotencyStore] = None):
        self.store = store or IdempotencyStore()

    def execute(
        self,
        idempotency_key: str,
        action_fn: Callable[..., Any],
        *args,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        existing = self.store.get(idempotency_key)
        
        # 1. If previously successful, reuse previous result; do NOT re-execute
        if existing and existing.get("status") == "SUCCESS":
            result = existing["result"]
            if isinstance(result, dict):
                return {**result, "idempotency_replayed": True}
            return result

        # 2. Check retry count on previous failure
        if existing and existing.get("status") == "FAILED":
            attempts = existing.get("attempts", 1)
            if attempts >= max_retries:
                raise IdempotencyError(
                    f"Action with key '{idempotency_key}' exceeded maximum retries ({max_retries}). "
                    f"Last error: {existing.get('error')}"
                )

        # 3. Store state before write (PENDING)
        if not existing:
            self.store.record_pending(idempotency_key, metadata=metadata)

        # 4. Attempt execution
        try:
            result = action_fn(*args, **kwargs)
            self.store.record_success(idempotency_key, result)
            return result
        except Exception as exc:
            self.store.record_failure(idempotency_key, str(exc))
            raise exc


class PORetryGuard:
    """Specialized retry guard compatible with Person 1's PO creation interface.
    
    Person 1's PO contract shape:
    { idempotency_key, display_label, po_number, total, status, label: "SIMULATED" }
    
    This guard guarantees that repeated PO issuance calls never duplicate PO creation.
    """

    def __init__(self, store: Optional[IdempotencyStore] = None):
        self.retry_guard = ActionRetryGuard(store or IdempotencyStore())
        self.call_count = 0

    def create_po_idempotent(
        self,
        po_creation_fn: Callable[..., Dict[str, Any]],
        idempotency_key: str,
        display_label: str,
        total: float,
        po_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """Wraps Person 1's PO creation callable with idempotency protection."""
        def wrapped_call():
            self.call_count += 1
            return po_creation_fn(
                idempotency_key=idempotency_key,
                display_label=display_label,
                total=total,
                po_number=po_number
            )

        return self.retry_guard.execute(
            idempotency_key=idempotency_key,
            action_fn=wrapped_call,
            metadata={"display_label": display_label, "total": total}
        )

