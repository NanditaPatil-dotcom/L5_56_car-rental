"""A small in-memory car rental booking demonstration."""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import tempfile
from datetime import datetime
from typing import Any

fleet: dict[str, dict[str, Any]] = {}
bookings: list[dict[str, Any]] = []
conn = sqlite3.connect(":memory:")
conn.execute(
    "CREATE TABLE customers (name TEXT, licence TEXT, phone TEXT)"
)


def add_car(
    plate: str,
    model: str = "Unknown",
    daily_rate: int = 0,
    features: list[str] | None = None,
) -> dict[str, Any]:
    """Add a car to the fleet and return its record."""
    if not is_valid_plate(plate):
        raise ValueError("Invalid number plate")
    if daily_rate < 0:
        raise ValueError("Daily rate cannot be negative")
    car = {
        "model": model,
        "rate": daily_rate,
        "available": True,
        "features": list(features) if features is not None else [],
    }
    fleet[plate] = car
    return car


def register_customer(name: str, licence: str, phone: str) -> None:
    """Save a customer using a parameterized SQL statement."""
    conn.execute(
        "INSERT INTO customers VALUES (?, ?, ?)", (name, licence, phone)
    )


def find_customer(name: str) -> list[tuple[str, str, str]]:
    """Return customer records matching a name."""
    return conn.execute(
        "SELECT * FROM customers WHERE name = ?", (name,)
    ).fetchall()


def rent_car(plate: str, customer: str, start: str, end: str) -> int:
    """Book an available car for a registered customer."""
    if not find_customer(customer):
        raise ValueError("Customer not registered")
    if plate not in fleet:
        raise ValueError("Car not found")
    car = fleet[plate]
    if not car["available"]:
        raise ValueError("Car is not available")
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    days = (end_date - start_date).days
    if days <= 0:
        raise ValueError("Rental end date must be after start date")
    cost = days * car["rate"]
    bookings.append(
        {
            "code": booking_code(),
            "plate": plate,
            "customer": customer,
            "days": days,
            "cost": cost,
        }
    )
    car["available"] = False
    return cost


def return_car(plate: str, km_driven: int) -> int:
    """Return a rented car and calculate any extra kilometre charge."""
    if plate not in fleet:
        raise ValueError("Car not found")
    if km_driven < 0:
        raise ValueError("Kilometres driven cannot be negative")
    fleet[plate]["available"] = True
    return max(0, km_driven - 300) * 5


def booking_code() -> str:
    """Create a hard-to-predict booking identifier."""
    return f"BK-{secrets.randbelow(90000) + 10000}"


def licence_hash(licence: str) -> str:
    """Return a SHA-256 digest of a licence number."""
    return hashlib.sha256(licence.encode("utf-8")).hexdigest()


def apply_promo(rule: str, amount: float) -> float:
    """Apply a supported percentage multiplier without evaluating code."""
    match = re.fullmatch(
        r"\s*amount\s*=\s*amount\s*\*\s*(0(?:\.\d+)?|1(?:\.0+)?)\s*",
        rule,
    )
    if match is None:
        raise ValueError("Promo must be a multiplier between 0 and 1")
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    return amount * float(match.group(1))


def is_valid_plate(plate: str) -> bool:
    """Check whether a plate matches the expected registration format."""
    pattern = r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}"
    return re.fullmatch(pattern, plate) is not None


def write_receipt(booking: dict[str, Any]) -> str:
    """Write a private receipt to a uniquely created temporary file."""
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".txt", delete=False
    ) as receipt:
        receipt.write(
            f"Booking {booking['code']}: {booking['plate']} for "
            f"{booking['days']} days = Rs.{booking['cost']}\n"
        )
        return receipt.name


def admin_login(user: str, password: str) -> bool:
    """Check admin credentials supplied through the environment."""
    expected_password = os.environ.get("CAR_RENTAL_ADMIN_PASSWORD", "")
    return user == "admin" and bool(expected_password) and hmac.compare_digest(
        password, expected_password
    )


def available_cars() -> list[str]:
    """Return the plates of all available cars."""
    return [plate for plate, car in fleet.items() if car["available"]]


def main() -> None:
    """Run a short demonstration of the rental system."""
    add_car("KA01AB1234", "Swift", 1500)
    add_car("KA02CD5678", "Innova", 3000)
    add_car("KA03EF9999", "Nexon", 500)
    register_customer("Ravi", "DL-0420110012345", "9845012345")
    register_customer("Meera", "DL-0420110099999", "9845099999")
    swift_cost = rent_car(
        "KA01AB1234", "Ravi", "2026-11-01", "2026-11-04"
    )
    print("Rent Swift:", swift_cost)
    print("Lookup injection:", find_customer("x' OR '1'='1"))
    print("Extra km charge:", return_car("KA01AB1234", 420))
    print("Promo price:", apply_promo("amount = amount * 0.9", 4500))
    print("Plate valid?", is_valid_plate("KA01AB1234"))
    print("Licence hash:", licence_hash("DL-0420110012345"))
    password = os.environ.get("CAR_RENTAL_ADMIN_PASSWORD", "")
    print("Admin:", admin_login("admin", password))
    print("Available:", available_cars())
    print("Receipt saved to:", write_receipt(bookings[0]))


if __name__ == "__main__":
    main()
