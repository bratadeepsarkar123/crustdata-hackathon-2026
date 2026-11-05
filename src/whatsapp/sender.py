import time
from typing import Dict, Any, List, Optional
from .config import WhatsAppConfig, WhatsAppMode, WhatsAppSecurityError, WhatsAppConfigError
from .client import MetaWhatsAppCloudClient


class WhatsAppSender:
    """Safe WhatsApp dispatcher with idempotency enforcement and strict safety guards."""

    def __init__(
        self,
        config: Optional[WhatsAppConfig] = None,
        client: Optional[MetaWhatsAppCloudClient] = None
    ):
        self.config = config or WhatsAppConfig()
        self.client = client or MetaWhatsAppCloudClient(config=self.config)
        # In-memory store for idempotency keys -> sent message records
        self._sent_messages: Dict[str, Dict[str, Any]] = {}
        self._message_log: List[Dict[str, Any]] = []

    def send_rfq_request(
        self,
        display_label: Optional[str] = None,
        phone: Optional[str] = None,
        item_description: str = "Industrial Sensors",
        quantity: int = 500,
        idempotency_key: Optional[str] = None,
        is_supplier: bool = True,
        supplier: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Dispatch an RFQ WhatsApp message with idempotency and safety validation.
        
        Can accept explicit fields or a candidate/verified supplier dict from Person 2.
        Note:
        - If is_supplier is True (default for RFQs), mode MUST be SIMULATED.
        - Idempotency key is checked: if key already exists, returns previous result.
        """
        if supplier and isinstance(supplier, dict):
            display_label = display_label or supplier.get("display_label")
            phone = phone or supplier.get("phone", "+910000000000")

        display_label = display_label or "Supplier 1"
        phone = phone or "+910000000000"
        idempotency_key = idempotency_key or f"rfq-wa-{display_label.lower().replace(' ', '-')}"

        # Step 1: Idempotency check before any action
        if idempotency_key in self._sent_messages:
            prior_record = self._sent_messages[idempotency_key]
            return {
                **prior_record,
                "reused_cached_result": True,
                "send_count": prior_record.get("send_count", 1)
            }

        # Step 2: Validate destination against rules and guards
        if is_supplier:
            # All supplier messages are strictly simulated.
            # Even in TEAM_PHONE mode, we cannot send real messages to external suppliers.
            # If the user is running in SIMULATED mode, it logs safely.
            if self.config.mode != WhatsAppMode.SIMULATED:
                raise WhatsAppSecurityError(
                    f"Attempted to send RFQ to supplier '{display_label}' in mode '{self.config.mode.value}'. "
                    "Per rules.md, supplier contact is strictly SIMULATED."
                )
        else:
            # Non-supplier message (e.g. notification to a teammate)
            self.config.validate_destination(phone, is_supplier=False)

        # Step 3: Construct the standard WhatsApp message shape (Section 6)
        text = f"RFQ for {display_label}: Requesting quote for {quantity} units of {item_description}."
        meta_response = None

        if self.config.mode == WhatsAppMode.TEAM_PHONE and not is_supplier:
            # Send real message to approved teammate phone via Meta Cloud API
            meta_response = self.client.send_text_message(phone, text)

        record: Dict[str, Any] = {
            "display_label": display_label,
            "direction": "outbound",
            "text": text,
            "idempotency_key": idempotency_key,
            "mode": self.config.mode.value,
            "label": "SIMULATED" if is_supplier else "REAL_TEAM_MESSAGE",
            "timestamp": time.time(),
            "destination_phone": phone if self.config.mode == WhatsAppMode.TEAM_PHONE else "SIMULATED_CHANNEL",
            "meta_response": meta_response,
            "send_count": 1,
            "reused_cached_result": False
        }

        # Step 4: Record in idempotency registry before returning
        self._sent_messages[idempotency_key] = record
        self._message_log.append(record)
        return record

    def send_team_message(
        self,
        phone: str,
        text: str,
        idempotency_key: str,
        display_label: str = "Teammate"
    ) -> Dict[str, Any]:
        """Dispatch a message to an approved team phone (e.g. notifications for human-in-the-loop).
        
        Requires mode == TEAM_PHONE and recipient in allowlist.
        """
        # Idempotency check
        if idempotency_key in self._sent_messages:
            prior_record = self._sent_messages[idempotency_key]
            return {
                **prior_record,
                "reused_cached_result": True,
                "send_count": prior_record.get("send_count", 1)
            }

        self.config.validate_destination(phone, is_supplier=False)
        meta_resp = None
        if self.config.mode == WhatsAppMode.TEAM_PHONE:
            meta_resp = self.client.send_text_message(phone, text)

        record: Dict[str, Any] = {
            "display_label": display_label,
            "direction": "outbound",
            "text": text,
            "idempotency_key": idempotency_key,
            "mode": self.config.mode.value,
            "label": "REAL_TEAM_MESSAGE" if self.config.mode == WhatsAppMode.TEAM_PHONE else "SIMULATED",
            "timestamp": time.time(),
            "destination_phone": phone if self.config.mode == WhatsAppMode.TEAM_PHONE else "SIMULATED_CHANNEL",
            "meta_response": meta_resp,
            "send_count": 1,
            "reused_cached_result": False
        }
        self._sent_messages[idempotency_key] = record
        self._message_log.append(record)
        return record

    def get_message_log(self) -> List[Dict[str, Any]]:
        """Returns the chronological audit log of all dispatched messages."""
        return list(self._message_log)

    @staticmethod
    def to_contract_message(record: Dict[str, Any]) -> Dict[str, Any]:
        """Projects a message record to Person 1's exact shared contract keys.
        
        Keys: ['display_label', 'direction', 'text', 'idempotency_key', 'mode', 'label']
        """
        return {
            "display_label": record["display_label"],
            "direction": record["direction"],
            "text": record["text"],
            "idempotency_key": record["idempotency_key"],
            "mode": record["mode"],
            "label": record["label"]
        }

    def clear(self):
        """Reset sent cache (used in testing)."""
        self._sent_messages.clear()
        self._message_log.clear()

