import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database.connection import create_database_engine
from app.database.schema import Base, Customer, Order, OrderItem, Product

CUSTOMER_COUNT = 120
PRODUCTS = (
    ("Electronics", ("Wireless Headphones", "Smart Speaker", "4K Monitor", "Webcam", "USB-C Hub", "Mechanical Keyboard")),
    ("Furniture", ("Standing Desk", "Ergonomic Chair", "Bookshelf", "Desk Lamp", "Filing Cabinet", "Meeting Table")),
    ("Office Supplies", ("Notebook Set", "Printer Paper", "Whiteboard", "Ink Cartridge", "Stapler", "Storage Box")),
    ("Software", ("Analytics License", "Team Suite", "Security Bundle", "Design Toolkit", "Backup Plan", "CRM License")),
    ("Appliances", ("Coffee Machine", "Air Purifier", "Mini Fridge", "Water Dispenser", "Microwave", "Floor Fan")),
)
COUNTRIES = ("Tunisia", "France", "Germany", "United States", "Morocco", "Italy", "Spain", "United Kingdom")
STATUSES = ("completed", "completed", "completed", "completed", "refunded", "cancelled")


def build_seed_data(seed: int = 42) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Return customers, products, orders, and items using a repeatable data set."""
    rng = random.Random(seed)
    customers = [
        {
            "id": customer_id,
            "name": f"{rng.choice(('Amira', 'Youssef', 'Sami', 'Nour', 'Lina', 'Karim', 'Maya', 'Adam'))} {rng.choice(('Ben Ali', 'Trabelsi', 'Mansour', 'Haddad', 'Gharbi', 'Saidi'))}",
            "email": f"customer{customer_id}@example.com",
            "country": rng.choice(COUNTRIES),
        }
        for customer_id in range(1, CUSTOMER_COUNT + 1)
    ]

    products = []
    product_id = 1
    for category, names in PRODUCTS:
        for name in names:
            products.append({
                "id": product_id,
                "name": name,
                "category": category,
                "price": Decimal(rng.randrange(800, 250_000)) / 100,
            })
            product_id += 1

    start = date(2025, 1, 1)
    days = (date(2026, 12, 31) - start).days
    orders = []
    items = []
    for order_id in range(1, 651):
        orders.append({
            "id": order_id,
            "customer_id": rng.randint(1, CUSTOMER_COUNT),
            "order_date": start + timedelta(days=rng.randint(0, days)),
            "status": rng.choice(STATUSES),
        })
        for _ in range(rng.randint(1, 4)):
            product = rng.choice(products)
            items.append({
                "order_id": order_id,
                "product_id": product["id"],
                "quantity": rng.randint(1, 8),
                "unit_price": product["price"],
            })
    return customers, products, orders, items


def seed_database(database_url: str | None = None) -> None:
    engine = create_database_engine(database_url)
    try:
        Base.metadata.create_all(engine)
        customers, products, orders, items = build_seed_data()

        with Session(engine) as session, session.begin():
            session.execute(delete(OrderItem))
            session.execute(delete(Order))
            session.execute(delete(Product))
            session.execute(delete(Customer))
            session.add_all([Customer(**row) for row in customers])
            session.add_all([Product(**row) for row in products])
            session.add_all([Order(**row) for row in orders])
            session.add_all([OrderItem(**row) for row in items])
    except OperationalError as error:
        raise SystemExit(_seed_connection_hint(error)) from None
    finally:
        engine.dispose()
    print(f"Seeded {len(customers)} customers, {len(products)} products, {len(orders)} orders, and {len(items)} order items.")


def _seed_connection_hint(error: OperationalError) -> str:
    detail = str(error.orig).lower()
    if "password authentication failed" in detail:
        return (
            "PostgreSQL rejected the configured username or password. Check DATABASE_URL in .env. "
            "If DATABASE_URL is set in this PowerShell session, it overrides .env; run "
            "Remove-Item Env:DATABASE_URL before retrying."
        )
    return (
        "Could not connect to PostgreSQL using DATABASE_URL. Check that PostgreSQL is running "
        "and that the database, username, password, host, and port are correct."
    )


if __name__ == "__main__":
    seed_database()
