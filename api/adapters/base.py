"""
Abstract base channel adapter.

All delivery channel implementations (Email, SMS, WhatsApp, etc.)
must inherit from `BaseChannelAdapter` and implement the `send` method.
This enforces the Strategy/Adapter pattern for channel extensibility.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class DeliveryResult:
    """Standardized result from a channel adapter send operation."""
    success: bool
    provider_message_id: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    latency_ms: int = 0


class BaseChannelAdapter(ABC):
    """
    Abstract base class for all channel delivery adapters.

    Each concrete adapter encapsulates the logic for sending messages
    through a specific channel (email, SMS, etc.) and translating
    provider-specific responses into a standardized `DeliveryResult`.

    To add a new channel:
        1. Create a new adapter class inheriting from `BaseChannelAdapter`.
        2. Implement the `send()` method with provider-specific logic.
        3. Register the adapter in `ChannelAdapterFactory`.
    """

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return the canonical channel name (e.g., 'email', 'sms')."""
        ...

    @abstractmethod
    async def send(
        self,
        recipient_address: str,
        subject: Optional[str],
        body: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliveryResult:
        """
        Send a message through this channel.

        Args:
            recipient_address: Target address (email, phone number, etc.)
            subject: Message subject (optional, mainly for email).
            body: Rendered message body.
            metadata: Additional channel-specific parameters.

        Returns:
            DeliveryResult with success/failure status and provider details.
        """
        ...

    async def validate_address(self, address: str) -> bool:
        """
        Validate that the recipient address is well-formed for this channel.
        Override in concrete adapters for channel-specific validation.
        """
        return bool(address and len(address.strip()) > 0)
