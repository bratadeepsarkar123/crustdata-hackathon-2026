"""WhatsApp communication module for ContextCon 04 Hackathon.
Enforces strict SIMULATED (default) and TEAM_PHONE modes only.
"""
from .config import WhatsAppConfig, WhatsAppMode, WhatsAppSecurityError, WhatsAppConfigError, WhatsAppAPIError
from .sender import WhatsAppSender
from .client import MetaWhatsAppCloudClient

__all__ = [
    "WhatsAppConfig",
    "WhatsAppMode",
    "WhatsAppSecurityError",
    "WhatsAppConfigError",
    "WhatsAppAPIError",
    "WhatsAppSender",
    "MetaWhatsAppCloudClient"
]

