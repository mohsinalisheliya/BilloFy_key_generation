# bill_inventry_system/utils.py

from django.core.signing import TimestampSigner
import base64
import time

# MUST match the key in license_manager.py
DESKTOP_APP_SECRET_KEY = "django-insecure-u(jg2i7q%&g7r6q^l-pz*lqi4f!&6(w%*twyfh6!nkr9(4_(=n"

def generate_license(hardware_id, duration_seconds):
    """
    Generates a license key with embedded timestamp.
    Format: HWID | DURATION | TIMESTAMP
    """
    signer = TimestampSigner(key=DESKTOP_APP_SECRET_KEY)
    
    # 1. Get current time
    created_at = int(time.time())
    
    # 2. Create Payload: HWID | Duration | CreatedTime
    # This guarantees the App sees the exact same time the Server used.
    data = f"{hardware_id}|{duration_seconds}|{created_at}"
    
    # 3. Sign it
    signed_value = signer.sign(data)
    
    # 4. Encode to Base32 (Clean looking key)
    key_bytes = base64.b32encode(signed_value.encode())
    key_str = key_bytes.decode().replace('=', '')
    
    return '-'.join(key_str[i:i+4] for i in range(0, len(key_str), 4))