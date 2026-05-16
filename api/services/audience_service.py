"""
Audience Resolution Service — resolves user identifiers to contact profiles.

Contains a `MockContactStore` with pre-seeded contacts and a resolution
engine that maps emails, phone numbers, and usernames to full contact records.
"""

import re
from typing import Dict, List, Optional, Tuple

from api.schemas.schemas import ResolvedContact, AudienceResolveResponse
from api.core.exceptions import AudienceResolutionError
from api.core.logging import get_logger

logger = get_logger(__name__)


class MockContactStore:
    """
    In-memory contact store for POC demonstration.

    In production, this would query the `contact_profiles` table
    via SQLAlchemy. The mock store enables end-to-end testing
    without a live database connection.
    """

    _contacts: Dict[str, Dict] = {
        # ── Pre-seeded contacts ────────────────────────────────────
        "alice@example.com": {
            "id": "contact_01_alice",
            "username": "alice_wonder",
            "email": "alice@example.com",
            "phone": "+1-555-0101",
            "first_name": "Alice",
            "last_name": "Wonderland",
        },
        "bob@example.com": {
            "id": "contact_02_bob",
            "username": "bob_builder",
            "email": "bob@example.com",
            "phone": "+1-555-0102",
            "first_name": "Bob",
            "last_name": "Builder",
        },
        "charlie@example.com": {
            "id": "contact_03_charlie",
            "username": "charlie_choco",
            "email": "charlie@example.com",
            "phone": "+1-555-0103",
            "first_name": "Charlie",
            "last_name": "Bucket",
        },
        "diana@example.com": {
            "id": "contact_04_diana",
            "username": "diana_prince",
            "email": "diana@example.com",
            "phone": "+1-555-0104",
            "first_name": "Diana",
            "last_name": "Prince",
        },
        "eve@example.com": {
            "id": "contact_05_eve",
            "username": "eve_coder",
            "email": "eve@example.com",
            "phone": "+1-555-0105",
            "first_name": "Eve",
            "last_name": "Coder",
        },
        # Phone-keyed entries
        "+1-555-0101": {
            "id": "contact_01_alice",
            "username": "alice_wonder",
            "email": "alice@example.com",
            "phone": "+1-555-0101",
            "first_name": "Alice",
            "last_name": "Wonderland",
        },
        "+1-555-0102": {
            "id": "contact_02_bob",
            "username": "bob_builder",
            "email": "bob@example.com",
            "phone": "+1-555-0102",
            "first_name": "Bob",
            "last_name": "Builder",
        },
        "+1-555-0103": {
            "id": "contact_03_charlie",
            "username": "charlie_choco",
            "email": "charlie@example.com",
            "phone": "+1-555-0103",
            "first_name": "Charlie",
            "last_name": "Bucket",
        },
        # Username-keyed entries
        "alice_wonder": {
            "id": "contact_01_alice",
            "username": "alice_wonder",
            "email": "alice@example.com",
            "phone": "+1-555-0101",
            "first_name": "Alice",
            "last_name": "Wonderland",
        },
        "bob_builder": {
            "id": "contact_02_bob",
            "username": "bob_builder",
            "email": "bob@example.com",
            "phone": "+1-555-0102",
            "first_name": "Bob",
            "last_name": "Builder",
        },
        "charlie_choco": {
            "id": "contact_03_charlie",
            "username": "charlie_choco",
            "email": "charlie@example.com",
            "phone": "+1-555-0103",
            "first_name": "Charlie",
            "last_name": "Bucket",
        },
        "diana_prince": {
            "id": "contact_04_diana",
            "username": "diana_prince",
            "email": "diana@example.com",
            "phone": "+1-555-0104",
            "first_name": "Diana",
            "last_name": "Prince",
        },
        "eve_coder": {
            "id": "contact_05_eve",
            "username": "eve_coder",
            "email": "eve@example.com",
            "phone": "+1-555-0105",
            "first_name": "Eve",
            "last_name": "Coder",
        },
    }

    @classmethod
    def lookup(cls, identifier: str) -> Optional[Dict]:
        """Look up a contact by email, phone, or username."""
        return cls._contacts.get(identifier.lower().strip())

    @classmethod
    def add_contact(cls, key: str, contact: Dict) -> None:
        """Add a new contact to the mock store (used by seed_data.py)."""
        cls._contacts[key.lower().strip()] = contact

    @classmethod
    def all_contacts(cls) -> List[Dict]:
        """Return all unique contacts (deduplicated by ID)."""
        seen_ids = set()
        unique = []
        for contact in cls._contacts.values():
            if contact["id"] not in seen_ids:
                seen_ids.add(contact["id"])
                unique.append(contact)
        return unique


class AudienceService:
    """
    Service for resolving audience identifiers to delivery-ready contacts.

    Accepts mixed lists of emails, phone numbers, and usernames,
    identifies the identifier type, and resolves each to a full
    contact profile via the ContactStore.
    """

    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    PHONE_REGEX = re.compile(r"^\+?[\d\s\-()]{7,20}$")

    @staticmethod
    def _classify_identifier(identifier: str) -> str:
        """Classify an identifier as email, phone, or username."""
        identifier = identifier.strip()
        if AudienceService.EMAIL_REGEX.match(identifier):
            return "email"
        if AudienceService.PHONE_REGEX.match(identifier):
            return "phone"
        return "username"

    @staticmethod
    def resolve(identifiers: List[str]) -> AudienceResolveResponse:
        """
        Resolve a list of identifiers to contact profiles.

        Args:
            identifiers: Mixed list of emails, phones, and usernames.

        Returns:
            AudienceResolveResponse with resolved contacts and unresolved identifiers.
        """
        resolved: List[ResolvedContact] = []
        unresolved: List[str] = []
        seen_ids: set = set()

        for identifier in identifiers:
            identifier = identifier.strip()
            if not identifier:
                continue

            contact = MockContactStore.lookup(identifier)
            if contact and contact["id"] not in seen_ids:
                seen_ids.add(contact["id"])
                resolved.append(
                    ResolvedContact(
                        id=contact["id"],
                        identifier=identifier,
                        email=contact.get("email"),
                        phone=contact.get("phone"),
                        username=contact.get("username"),
                        first_name=contact.get("first_name"),
                        last_name=contact.get("last_name"),
                        resolved=True,
                    )
                )
                logger.info(f"Resolved identifier '{identifier}' → contact {contact['id']}")
            else:
                if contact is None:
                    unresolved.append(identifier)
                    logger.warning(f"Could not resolve identifier: '{identifier}'")

        logger.info(
            f"Audience resolution complete: {len(resolved)} resolved, {len(unresolved)} unresolved"
        )

        return AudienceResolveResponse(
            resolved=resolved,
            unresolved=unresolved,
            total_resolved=len(resolved),
            total_unresolved=len(unresolved),
        )
