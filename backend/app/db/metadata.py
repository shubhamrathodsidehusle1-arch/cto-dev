"""Metadata driven database setup utilities."""
import json
import os
from typing import Any, Dict, List
from app.utils.logger import get_logger
from app.db.prisma import get_prisma

logger = get_logger(__name__)

METADATA_FILE = os.path.join(os.path.dirname(__file__), "metadata.json")

async def load_metadata() -> None:
    """Load metadata from JSON file into the database."""
    if not os.path.exists(METADATA_FILE):
        logger.warning("Metadata file not found", path=METADATA_FILE)
        return

    try:
        with open(METADATA_FILE, "r") as f:
            metadata = json.load(f)
        
        db = await get_prisma()
        
        # Load provider metadata
        providers = metadata.get("providers", [])
        for p_data in providers:
            provider_name = p_data.get("provider")
            await db.providerhealth.upsert(
                where={"provider": provider_name},
                data={
                    "create": {
                        "provider": provider_name,
                        "status": p_data.get("status", "unknown"),
                        "costPerRequest": p_data.get("costPerRequest"),
                        "metadata": p_data.get("metadata", {})
                    },
                    "update": {
                        "costPerRequest": p_data.get("costPerRequest"),
                        "metadata": p_data.get("metadata", {})
                    }
                }
            )
            logger.info("Loaded provider metadata", provider=provider_name)
            
        # Load system metadata
        system_config = metadata.get("system_config", [])
        for config in system_config:
            key = config.get("key")
            await db.systemmetadata.upsert(
                where={"key": key},
                data={
                    "create": {
                        "key": key,
                        "value": config.get("value"),
                        "description": config.get("description")
                    },
                    "update": {
                        "value": config.get("value"),
                        "description": config.get("description")
                    }
                }
            )
            logger.info("Loaded system metadata", key=key)
            
        logger.info("Metadata loading complete")
    except Exception as e:
        logger.error("Failed to load metadata", error=str(e))
        # Don't raise here to allow application to start even if metadata load fails
