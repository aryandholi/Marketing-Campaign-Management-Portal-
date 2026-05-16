"""
Channel Adapter Factory — registry-based factory for delivery adapters.

Implements the Factory Pattern to decouple the orchestration layer
from concrete channel implementations. Adding a new channel requires
only creating the adapter class and registering it here.
"""

from typing import Dict, Type

from api.adapters.base import BaseChannelAdapter
from api.adapters.email_adapter import EmailAdapter
from api.adapters.sms_adapter import SMSAdapter
from api.core.exceptions import ChannelNotSupportedError
from api.core.logging import get_logger

logger = get_logger(__name__)


class ChannelAdapterFactory:
    """
    Factory for creating channel-specific delivery adapters.

    Usage:
        adapter = ChannelAdapterFactory.get_adapter("email")
        result = await adapter.send(...)

    To add a new channel (e.g., WhatsApp):
        1. Create `WhatsAppAdapter(BaseChannelAdapter)` in `api/adapters/whatsapp_adapter.py`.
        2. Add `"whatsapp": WhatsAppAdapter` to the `_registry`.
        3. Update `ChannelType` enum in the Campaign model.
    """

    _registry: Dict[str, Type[BaseChannelAdapter]] = {
        "email": EmailAdapter,
        "sms": SMSAdapter,
        # Future channels:
        # "whatsapp": WhatsAppAdapter,
        # "push": PushNotificationAdapter,
        # "in_app_chat": InAppChatAdapter,
    }

    @classmethod
    def get_adapter(cls, channel: str) -> BaseChannelAdapter:
        """
        Retrieve and instantiate the adapter for the given channel.

        Args:
            channel: Channel name (must match a registered adapter).

        Returns:
            An instance of the appropriate BaseChannelAdapter subclass.

        Raises:
            ChannelNotSupportedError: If the channel is not registered.
        """
        adapter_class = cls._registry.get(channel.lower())
        if adapter_class is None:
            logger.error(f"Unsupported channel requested: {channel}")
            raise ChannelNotSupportedError(channel)

        logger.info(f"Factory: created {adapter_class.__name__} for channel '{channel}'")
        return adapter_class()

    @classmethod
    def register_adapter(cls, channel: str, adapter_class: Type[BaseChannelAdapter]) -> None:
        """
        Dynamically register a new channel adapter at runtime.

        Useful for plugin-based architectures or testing.
        """
        cls._registry[channel.lower()] = adapter_class
        logger.info(f"Factory: registered adapter {adapter_class.__name__} for channel '{channel}'")

    @classmethod
    def supported_channels(cls) -> list:
        """Return a list of all currently registered channel names."""
        return list(cls._registry.keys())
