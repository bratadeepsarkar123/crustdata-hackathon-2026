import os
import re
from enum import Enum
from typing import Set


class WhatsAppMode(str, Enum):
    SIMULATED = "SIMULATED"
    TEAM_PHONE = "TEAM_PHONE"


class WhatsAppSecurityError(Exception):
    """Raised when an outreach attempts to violate safety rules or contact unapproved numbers."""
    pass


class WhatsAppConfigError(Exception):
    """Raised when required Meta WhatsApp configuration or credentials are missing."""
    pass


class WhatsAppAPIError(Exception):
    """Raised when the Meta WhatsApp Cloud API returns an error."""
    pass


class WhatsAppConfig:
    """Configuration and guard rail validator for WhatsApp messaging.
    
    Hard Rules from MASTER-HANDOFF-supplier.md (Section 3, 5, 12):
    - Default mode is always SIMULATED.
    - Only SIMULATED or TEAM_PHONE modes are permitted.
    - In TEAM_PHONE mode, only explicitly allowlisted team phones may be contacted.
    - Zero messaging to real suppliers, buyers, or any external phone numbers.
    - Never expose credentials or log auth tokens.
    """

    def __init__(self, mode: str = None, allowlist: Set[str] = None):
        raw_mode = mode or os.getenv("WHATSAPP_MODE", WhatsAppMode.SIMULATED.value)
        raw_mode_upper = raw_mode.upper().strip()
        
        if raw_mode_upper not in (WhatsAppMode.SIMULATED.value, WhatsAppMode.TEAM_PHONE.value):
            raise WhatsAppSecurityError(
                f"Invalid WhatsApp mode: '{raw_mode}'. "
                f"Permitted modes are strictly {WhatsAppMode.SIMULATED.value} or {WhatsAppMode.TEAM_PHONE.value}."
            )
        
        self.mode = WhatsAppMode(raw_mode_upper)
        
        # Load allowlist from param or environment
        self._allowlist: Set[str] = set()
        if allowlist:
            for p in allowlist:
                self._allowlist.add(self._normalize_phone(p))
        else:
            env_allowlist = os.getenv("TEAM_PHONE_ALLOWLIST", "")
            if env_allowlist.strip():
                for p in env_allowlist.split(","):
                    p_clean = p.strip()
                    if p_clean:
                        self._allowlist.add(self._normalize_phone(p_clean))
            else:
                # Default authorized team test phone numbers for local simulation
                self._allowlist = {
                    "+919876543210",  # Team phone 1 (Person 1 - Integrator)
                    "+919876543211",  # Team phone 2 (Person 2 - Discovery)
                    "+919876543212",  # Team phone 3 (Person 3 - Quotes/Policy)
                }

        # Meta Cloud API configuration (read from environment, never logged)
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", os.getenv("META_WHATSAPP_TOKEN", "")).strip()
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
        self.api_version = os.getenv("META_GRAPH_API_VERSION", "v20.0").strip()

    @property
    def has_meta_credentials(self) -> bool:
        """Returns True if Meta Cloud API token and phone number ID are present."""
        return bool(self.access_token and self.phone_number_id)

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Strip spaces, hyphens, parentheses; ensure standard e164-like formatting."""
        cleaned = re.sub(r"[\s\-\(\)]", "", str(phone))
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        return cleaned

    def is_phone_allowed(self, phone: str) -> bool:
        """Returns True if and only if the phone is in the team allowlist."""
        normalized = self._normalize_phone(phone)
        return normalized in self._allowlist

    def validate_destination(self, phone: str, is_supplier: bool = False):
        """Enforce strict guardrails on destination."""
        if is_supplier:
            raise WhatsAppSecurityError(
                "Real supplier outreach is STRICTLY PROHIBITED by ContextCon 04 rules. "
                "Supplier interactions must be SIMULATED only."
            )
        
        if self.mode == WhatsAppMode.SIMULATED:
            # In simulated mode, outbound calls never contact the real cellular network.
            return True
        
        if self.mode == WhatsAppMode.TEAM_PHONE:
            if not self.is_phone_allowed(phone):
                raise WhatsAppSecurityError(
                    f"Outbound message blocked! Phone {phone} is not in the approved team allowlist. "
                    "External calls are forbidden."
                )
            return True

        raise WhatsAppSecurityError(f"Unsupported WhatsApp operating mode: {self.mode}")

