import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from .config import WhatsAppConfig, WhatsAppConfigError, WhatsAppAPIError


class MetaWhatsAppCloudClient:
    """Client for Meta WhatsApp Cloud Graph API.
    
    Conforms to Meta Graph API v20.0/v21.0:
    POST https://graph.facebook.com/{version}/{phone_number_id}/messages
    """

    def __init__(self, config: Optional[WhatsAppConfig] = None):
        self.config = config or WhatsAppConfig()

    def send_text_message(self, to_phone: str, message_text: str) -> Dict[str, Any]:
        """Dispatches an outbound text message via Meta WhatsApp Cloud API.
        
        Requires:
        - to_phone: recipient phone number in international format without '+' or spaces.
        - message_text: message body string.
        """
        if not self.config.has_meta_credentials:
            raise WhatsAppConfigError(
                "Missing Meta Cloud API credentials! Set WHATSAPP_ACCESS_TOKEN and "
                "WHATSAPP_PHONE_NUMBER_ID in local environment variables before using live TEAM_PHONE mode."
            )

        # Meta expects phone number without leading '+'
        clean_recipient = to_phone.lstrip("+").strip()

        url = f"https://graph.facebook.com/{self.config.api_version}/{self.config.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_recipient,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text
            }
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Authorization": f"Bearer {self.config.access_token}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                resp_data = resp.read().decode("utf-8")
                return json.loads(resp_data)
        except urllib.error.HTTPError as http_err:
            try:
                err_body = http_err.read().decode("utf-8")
                err_json = json.loads(err_body)
                err_msg = err_json.get("error", {}).get("message", http_err.reason)
            except Exception:
                err_msg = http_err.reason
            raise WhatsAppAPIError(
                f"Meta WhatsApp Cloud API error (HTTP {http_err.code}): {err_msg}"
            )
        except urllib.error.URLError as url_err:
            raise WhatsAppAPIError(
                f"Failed to connect to Meta WhatsApp Cloud API: {url_err.reason}"
            )
        except Exception as exc:
            raise WhatsAppAPIError(f"Unexpected error communicating with Meta API: {str(exc)}")

