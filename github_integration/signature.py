"""
HMAC Signature Verification for GitHub Webhooks

Provides secure webhook signature verification using HMAC SHA-256
to prevent unauthorized requests and replay attacks.
"""

import hmac
import hashlib
from typing import Optional


def verify_webhook_signature(
    body: bytes,
    signature: str,
    secret: str
) -> bool:
    """
    Verify GitHub webhook signature using HMAC SHA-256.
    
    GitHub sends signatures in the format: sha256=<hex_digest>
    We compute HMAC-SHA256(secret, body) and compare securely.
    
    Args:
        body: Raw request body as bytes
        signature: X-Hub-Signature-256 header value
        secret: Webhook secret from environment
        
    Returns:
        True if signature is valid, False otherwise
        
    Example:
        >>> body = b'{"action": "opened"}'
        >>> signature = "sha256=abc123..."
        >>> secret = "my_webhook_secret"
        >>> verify_webhook_signature(body, signature, secret)
        True
    """
    # Validate inputs
    if not signature or not secret:
        return False
    
    # GitHub format: "sha256=<hex_digest>"
    if not signature.startswith("sha256="):
        return False
    
    # Extract hex digest from signature
    try:
        received_digest = signature.split("=", 1)[1]
    except IndexError:
        return False
    
    # Compute expected HMAC
    expected_digest = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Timing-safe comparison to prevent timing attacks
    return hmac.compare_digest(expected_digest, received_digest)


def generate_webhook_signature(body: bytes, secret: str) -> str:
    """
    Generate webhook signature for testing.
    
    Args:
        body: Request body as bytes
        secret: Webhook secret
        
    Returns:
        Signature in GitHub format: sha256=<hex_digest>
    """
    digest = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return f"sha256={digest}"


def verify_timestamp(timestamp: Optional[int], max_age_seconds: int = 300) -> bool:
    """
    Verify webhook timestamp to prevent replay attacks.
    
    Args:
        timestamp: Unix timestamp from webhook payload
        max_age_seconds: Maximum age in seconds (default: 5 minutes)
        
    Returns:
        True if timestamp is recent, False otherwise
    """
    if timestamp is None:
        return False
    
    import time
    current_time = int(time.time())
    age = current_time - timestamp
    
    # Check if timestamp is not too old and not in the future
    return 0 <= age <= max_age_seconds
