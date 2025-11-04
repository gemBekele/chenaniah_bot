# SMS Configuration Issues Analysis

## Issues Found

### 1. Missing Environment Variables in `env.example`
The `env.example` file does not include SMS configuration variables:
- `AFROMESSAGE_API_KEY`
- `AFROMESSAGE_SENDER_ID`
- `AFROMESSAGE_BASE_URL`

### 2. Hardcoded API Endpoint
In `sms_service.py` line 37, the AfroMessage endpoint is hardcoded:
```python
endpoint = "https://api.afromessage.com/api/send"
```
This doesn't use the configurable `base_url` from Config.

### 3. Sender ID Requirement
The `is_configured()` method requires both `api_key` and `sender_id` (line 17):
```python
return bool(self.api_key and self.sender_id)
```
However, for some SMS providers like AfroMessage in beta, the sender_id might not be required.

### 4. Potential Phone Number Format Issues
The SMS service doesn't validate or normalize phone numbers before sending. Ethiopian phone numbers might need the '+' prefix or country code format.

## Recommendations

1. **Update `env.example`** to include SMS configuration:
```env
# SMS Configuration (Optional)
AFROMESSAGE_API_KEY=your_api_key_here
AFROMESSAGE_SENDER_ID=your_sender_id_here
AFROMESSAGE_BASE_URL=https://api.afromessage.com
```

2. **Use Configurable Base URL** in `sms_service.py`:
```python
endpoint = f"{self.base_url}/api/send"
```

3. **Make sender_id optional** for providers that don't require it:
```python
def is_configured(self) -> bool:
    return bool(self.api_key)  # Only require API key
```

4. **Add phone number validation/normalization**:
```python
def normalize_phone(self, phone: str) -> str:
    # Remove spaces, dashes
    phone = phone.replace(' ', '').replace('-', '')
    # Add country code if missing
    if not phone.startswith('+'):
        if phone.startswith('0'):
            phone = '+251' + phone[1:]  # Ethiopian number
        else:
            phone = '+251' + phone
    return phone
```

