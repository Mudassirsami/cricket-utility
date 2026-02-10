"""
Utility to generate bcrypt-hashed PINs for Manager and Scorer roles.
Run: python generate_pin.py
Copy the output hashes into your .env file.
"""
import bcrypt
import sys


def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


if __name__ == "__main__":
    print("=== Cricket Club PIN Generator ===\n")

    manager_pin = input("Enter Manager PIN: ").strip()
    if not manager_pin:
        print("Manager PIN cannot be empty.")
        sys.exit(1)

    scorer_pin = input("Enter Scorer PIN: ").strip()
    if not scorer_pin:
        print("Scorer PIN cannot be empty.")
        sys.exit(1)

    manager_hash = hash_pin(manager_pin)
    scorer_hash = hash_pin(scorer_pin)

    print(f"\n--- Add these to your .env file ---\n")
    print(f"MANAGER_PIN_HASH={manager_hash}")
    print(f"SCORER_PIN_HASH={scorer_hash}")
    print()
