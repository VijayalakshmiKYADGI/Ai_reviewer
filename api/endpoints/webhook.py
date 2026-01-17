"""
GitHub Webhook Endpoint

Receives real-time PR events from GitHub and triggers automated code reviews.
"""

import os
import json
from typing import Optional
from fastapi import APIRouter, Request, Header, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import structlog

from github_integration import WebhookHandler, verify_webhook_signature

logger = structlog.get_logger()

router = APIRouter(prefix="/webhook", tags=["webhooks"])


# In-memory deduplication cache (Phase 10 will use Redis)
_processed_deliveries = set()


async def process_webhook_background(payload: dict, delivery_id: str):
    """
    Background task to process webhook event.
    
    Args:
        payload: GitHub webhook payload
        delivery_id: Unique delivery ID
    """
    try:
        handler = WebhookHandler()
        result = await handler.process_pr_event(payload, delivery_id)
        
        logger.info(
            "webhook_processed",
            delivery_id=delivery_id,
            result=result
        )
    
    except Exception as e:
        logger.error(
            "webhook_background_failed",
            delivery_id=delivery_id,
            error=str(e),
            exc_info=True
        )


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: Optional[str] = Header(None),
    x_github_delivery: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None),
):
    """
    GitHub webhook endpoint.
    
    Receives real-time events from GitHub and triggers code reviews.
    
    Headers:
        X-GitHub-Event: Event type (pull_request, issues, etc.)
        X-GitHub-Delivery: Unique delivery ID
        X-Hub-Signature-256: HMAC SHA-256 signature
        
    Returns:
        202 Accepted: Event queued for processing
        200 OK: Event ignored (unsupported type)
        403 Forbidden: Invalid signature
        400 Bad Request: Malformed payload
    """
    # Read raw body for signature verification
    try:
        body = await request.body()
    except Exception as e:
        logger.error("failed_to_read_body", error=str(e))
        raise HTTPException(status_code=400, detail="Failed to read request body")
    
    # Get webhook secret from environment
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not webhook_secret:
        logger.error("webhook_secret_not_configured")
        raise HTTPException(
            status_code=500,
            detail="Webhook secret not configured"
        )
    
    # Verify signature
    if not x_hub_signature_256:
        logger.warning("missing_signature", delivery_id=x_github_delivery)
        raise HTTPException(status_code=403, detail="Missing signature")
    
    if not verify_webhook_signature(body, x_hub_signature_256, webhook_secret):
        logger.warning(
            "invalid_signature",
            delivery_id=x_github_delivery,
            event=x_github_event
        )
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse JSON payload
    try:
        payload = json.loads(body.decode('utf-8'))
    except json.JSONDecodeError as e:
        logger.error("malformed_json", error=str(e), delivery_id=x_github_delivery)
        raise HTTPException(status_code=400, detail="Malformed JSON payload")
    
    # Log webhook receipt
    logger.info(
        "webhook_received",
        github_event=x_github_event,
        delivery_id=x_github_delivery,
        action=payload.get("action", "")
    )
    
    # Check for duplicate delivery (simple deduplication)
    if x_github_delivery in _processed_deliveries:
        logger.info(
            "duplicate_delivery",
            delivery_id=x_github_delivery
        )
        return JSONResponse(
            status_code=200,
            content={
                "status": "duplicate",
                "delivery_id": x_github_delivery,
                "message": "Already processed"
            }
        )
    
    # Mark as processed
    _processed_deliveries.add(x_github_delivery)
    
    # Keep cache size manageable (last 1000 deliveries)
    if len(_processed_deliveries) > 1000:
        _processed_deliveries.clear()
    
    # Filter events - only handle pull_request events
    if x_github_event != "pull_request":
        logger.info(
            "unsupported_event",
            github_event=x_github_event,
            delivery_id=x_github_delivery
        )
        return JSONResponse(
            status_code=200,
            content={
                "status": "ignored",
                "event": x_github_event,
                "message": "Event type not supported"
            }
        )
    
    # Check action
    action = payload.get("action", "")
    supported_actions = ["opened", "synchronize", "reopened"]
    
    if action not in supported_actions:
        logger.info(
            "unsupported_action",
            action=action,
            delivery_id=x_github_delivery
        )
        return JSONResponse(
            status_code=200,
            content={
                "status": "ignored",
                "action": action,
                "message": f"Action not supported. Supported: {supported_actions}"
            }
        )
    
    # Queue background task for processing
    # This ensures we respond to GitHub within 3 seconds
    background_tasks.add_task(
        process_webhook_background,
        payload,
        x_github_delivery
    )
    
    # Extract PR details for response
    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})
    
    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "event": x_github_event,
            "action": action,
            "delivery_id": x_github_delivery,
            "repository": repo_data.get("full_name", ""),
            "pr_number": pr_data.get("number", 0),
            "message": "Webhook queued for processing"
        }
    )


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoint."""
    return {
        "status": "healthy",
        "endpoint": "/webhook/github",
        "supported_events": ["pull_request"],
        "supported_actions": ["opened", "synchronize", "reopened"]
    }
