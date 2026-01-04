"""Prisma database client."""
from typing import Optional
from prisma import Prisma

from app.utils.logger import get_logger

logger = get_logger(__name__)

prisma_client: Optional[Prisma] = None


async def get_prisma() -> Prisma:
    """Get Prisma client instance.

    Returns:
        Prisma client instance
    """
    global prisma_client

    if prisma_client is None:
        prisma_client = Prisma()
        await prisma_client.connect()
        logger.info("Prisma client connected")

    return prisma_client


async def disconnect_prisma() -> None:
    """Disconnect Prisma client."""
    global prisma_client

    if prisma_client is not None:
        await prisma_client.disconnect()
        prisma_client = None
        logger.info("Prisma client disconnected")
