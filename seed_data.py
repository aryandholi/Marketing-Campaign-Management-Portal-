"""
Seed Data Script — populates the MockContactStore with sample data.

Run this script to pre-load the contact store for demonstration purposes.
In a production environment, this would be replaced by database migrations
and a proper data seeding process.

Usage:
    python seed_data.py
"""

from api.services.audience_service import MockContactStore


def seed_contacts() -> None:
    """Add additional contacts to the MockContactStore beyond the defaults."""

    additional_contacts = [
        {
            "id": "contact_06_frank",
            "username": "frank_castle",
            "email": "frank@example.com",
            "phone": "+1-555-0106",
            "first_name": "Frank",
            "last_name": "Castle",
        },
        {
            "id": "contact_07_grace",
            "username": "grace_hopper",
            "email": "grace@example.com",
            "phone": "+1-555-0107",
            "first_name": "Grace",
            "last_name": "Hopper",
        },
        {
            "id": "contact_08_henry",
            "username": "henry_ford",
            "email": "henry@example.com",
            "phone": "+1-555-0108",
            "first_name": "Henry",
            "last_name": "Ford",
        },
        {
            "id": "contact_09_iris",
            "username": "iris_west",
            "email": "iris@example.com",
            "phone": "+1-555-0109",
            "first_name": "Iris",
            "last_name": "West",
        },
        {
            "id": "contact_10_jack",
            "username": "jack_sparrow",
            "email": "jack@example.com",
            "phone": "+1-555-0110",
            "first_name": "Jack",
            "last_name": "Sparrow",
        },
    ]

    for contact in additional_contacts:
        # Index by email
        MockContactStore.add_contact(contact["email"], contact)
        # Index by phone
        MockContactStore.add_contact(contact["phone"], contact)
        # Index by username
        MockContactStore.add_contact(contact["username"], contact)

    print("=" * 60)
    print("  SEED DATA - Mock Contact Store Populated")
    print("=" * 60)
    print()

    all_contacts = MockContactStore.all_contacts()
    print(f"  Total unique contacts: {len(all_contacts)}")
    print()

    for c in all_contacts:
        print(f"  [Email] {c['email']:<25} [Phone] {c['phone']:<15} [User] {c['username']}")

    print()
    print("  You can resolve these contacts via:")
    print("    - Email:    alice@example.com, bob@example.com, ...")
    print("    - Phone:    +1-555-0101, +1-555-0102, ...")
    print("    - Username: alice_wonder, bob_builder, ...")
    print("=" * 60)


if __name__ == "__main__":
    seed_contacts()
