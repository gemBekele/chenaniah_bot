import logging
import requests
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, sender_id: Optional[str] = None):
        self.api_key = api_key or Config.AFROMESSAGE_API_KEY
        self.base_url = (base_url or Config.AFROMESSAGE_BASE_URL).rstrip('/')
        self.sender_id = sender_id or Config.AFROMESSAGE_SENDER_ID
        self.provider = "afrosms"  # Default provider

    def is_configured(self) -> bool:
        return bool(self.api_key and self.sender_id)

    def send_sms(self, to_phone: str, message: str) -> bool:
        if not self.is_configured():
            logger.warning("SMS service not configured")
            return False

        try:
            if self.provider == "afrosms":
                return self._send_afrosms_sms(to_phone, message)
            else:
                return self._send_afromessage_sms(to_phone, message)
        except Exception as e:
            logger.exception("Exception while sending SMS: %s", e)
            return False

    def _send_afrosms_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS using AfroMessage API"""
        try:
            # AfroMessage API endpoint
            endpoint = "https://api.afromessage.com/api/send"
            
            headers = {
                'Authorization': f"Bearer {self.api_key}",
                'Content-Type': 'application/json',
            }
            
            # Use the correct payload format for AfroMessage API
            # For beta testing, we can omit 'from' and 'sender' fields
            payload = {
                'to': to_phone,
                'message': message,
            }
            
            logger.info(f"Sending SMS to {to_phone} via AfroMessage")
            logger.info(f"Using endpoint: {endpoint}")
            logger.info(f"Payload: {payload}")
            
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            
            logger.info(f"AfroMessage response: {resp.status_code} - {resp.text}")
            
            if 200 <= resp.status_code < 300:
                # Check if the response contains an error message
                try:
                    response_data = resp.json()
                    if response_data.get('acknowledge') == 'error':
                        logger.error("AfroMessage API error: %s", response_data.get('response', {}).get('errors', []))
                        return False
                    elif response_data.get('acknowledge') == 'success':
                        logger.info("SMS sent successfully to %s via AfroMessage", to_phone)
                        return True
                    else:
                        logger.info("SMS sent successfully to %s via AfroMessage", to_phone)
                        return True
                except (ValueError, KeyError):
                    # If response is not JSON or doesn't have expected structure, assume success
                    logger.info("SMS sent successfully to %s via AfroMessage", to_phone)
                    return True
            else:
                logger.error("Failed to send SMS via AfroMessage (%s): %s", resp.status_code, resp.text)
                return False
                
        except Exception as e:
            logger.exception("Exception while sending SMS via AfroMessage: %s", e)
            return False

    def _send_afromessage_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS using Afromessage API (legacy)"""
        try:
            url = f"{self.base_url}/sms/send"
            headers = {
                'Authorization': f"Bearer {self.api_key}",
                'Content-Type': 'application/json',
            }
            payload = {
                'from': self.sender_id,
                'to': to_phone,
                'message': message,
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            if 200 <= resp.status_code < 300:
                logger.info("SMS sent successfully to %s via Afromessage", to_phone)
                return True
            logger.error("Failed to send SMS via Afromessage (%s): %s", resp.status_code, resp.text)
            return False
        except Exception as e:
            logger.exception("Exception while sending SMS via Afromessage: %s", e)
            return False


