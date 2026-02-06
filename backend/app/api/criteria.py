"""Criteria management API endpoints."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.config import criteria_config
from app.models import CriteriaUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["criteria"])


@router.get("/criteria")
async def get_criteria() -> Dict[str, Any]:
    """Get current criteria configuration.

    Returns:
        Full criteria configuration
    """
    try:
        return criteria_config.to_dict()
    except Exception as e:
        logger.error(f"Failed to get criteria: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get criteria: {str(e)}")


@router.put("/criteria")
async def update_criteria(request: CriteriaUpdateRequest) -> Dict[str, str]:
    """Update criteria configuration.

    Note: This is a simplified version that reloads from file.
    In a production app, you might want to persist changes to the YAML file.

    Args:
        request: Criteria update request

    Returns:
        Success message
    """
    try:
        # For now, just reload from file
        # In a full implementation, you would update the YAML file
        criteria_config.reload()

        return {"message": "Criteria configuration reloaded"}

    except Exception as e:
        logger.error(f"Failed to update criteria: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update criteria: {str(e)}")
