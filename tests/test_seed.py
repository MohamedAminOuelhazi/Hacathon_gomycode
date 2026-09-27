from app.database.seed import build_seed_data


def test_seed_has_demo_scale_and_required_date_range():
    customers, products, orders, items = build_seed_data()

    assert len(customers) >= 100
    assert len(products) >= 30
    assert len(orders) >= 500
    assert len(items) > len(orders)
    assert {product["category"] for product in products} >= {
        "Electronics", "Furniture", "Office Supplies"
    }
    assert min(order["order_date"] for order in orders).year == 2025
    assert max(order["order_date"] for order in orders).year == 2026
    assert len({customer["country"] for customer in customers}) > 1


def test_seed_is_repeatable_and_foreign_keys_resolve():
    first = build_seed_data()
    second = build_seed_data()
    customers, products, orders, items = first

    assert first == second
    assert {order["customer_id"] for order in orders} <= {row["id"] for row in customers}
    assert {item["order_id"] for item in items} <= {row["id"] for row in orders}
    assert {item["product_id"] for item in items} <= {row["id"] for row in products}
