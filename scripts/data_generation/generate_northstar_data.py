"""Generate reproducible, entirely fictional Northstar Retail source data.

Run from the repository root in an activated Python virtual environment:
    python -m scripts.data_generation.generate_northstar_data --scale quick --seed 20260815
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from faker import Faker

from scripts.utilities.logging_utils import configure_logging

LOGGER = logging.getLogger("northstar.generator")

REGIONS = {
    "Northeast": [("NY", "New York"), ("MA", "Boston"), ("PA", "Philadelphia")],
    "Mid-Atlantic": [("VA", "Arlington"), ("MD", "Bethesda"), ("DC", "Washington")],
    "Southeast": [("GA", "Atlanta"), ("NC", "Charlotte"), ("FL", "Orlando")],
    "Midwest": [("IL", "Chicago"), ("OH", "Columbus"), ("MI", "Detroit")],
    "West": [("CA", "San Diego"), ("WA", "Seattle"), ("CO", "Denver")],
}
CATEGORIES = [
    (1, "Electronics"), (2, "Home Office"), (3, "Kitchen"), (4, "Fitness"),
    (5, "Outdoor"), (6, "Personal Care"), (7, "Pet Supplies"), (8, "Travel"),
]
CHANNELS = ["Paid Search", "Social", "Email", "Affiliate", "Organic", "Direct"]
EVENT_SEQUENCE = ["page_view", "product_view", "add_to_cart", "checkout_start", "purchase"]
BRANDS = ["Aurora Works", "Blue Peak", "Cedar & Finch", "Northline", "Orbit & Oak"]
PRODUCT_NOUNS = ["Lamp", "Keyboard", "Bottle", "Backpack", "Blender", "Headphones", "Mat", "Organizer"]


@dataclass(frozen=True)
class GenerationContext:
    seed: int
    scale: str
    output_dir: Path
    counts: dict[str, int]
    issues: dict[str, int]
    batch_id: str
    generated_at: datetime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate fictional Northstar Retail data.")
    parser.add_argument("--scale", choices=["quick", "small", "medium", "portfolio"], default="quick")
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--output-dir", type=Path, default=Path("datasets/sample"))
    parser.add_argument("--config", type=Path, default=Path("config/data_generation.yml"))
    parser.add_argument(
        "--as-of-utc",
        default="2026-08-15T12:00:00+00:00",
        help="Deterministic dataset as-of timestamp; use ISO 8601.",
    )
    return parser.parse_args()


def load_context(args: argparse.Namespace) -> GenerationContext:
    with args.config.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    counts = dict(config["scales"][args.scale])
    issues = dict(config["quality_issues"])
    stamp = datetime.fromisoformat(args.as_of_utc.replace("Z", "+00:00")).astimezone(UTC)
    stable = hashlib.sha256(f"{args.seed}:{args.scale}".encode()).hexdigest()[:12]
    return GenerationContext(
        seed=args.seed,
        scale=args.scale,
        output_dir=args.output_dir,
        counts=counts,
        issues=issues,
        batch_id=f"GEN-{stamp:%Y%m%dT%H%M%SZ}-{stable}",
        generated_at=stamp,
    )


def weighted_choice(rng: random.Random, values: list[Any], weights: list[float]) -> Any:
    return rng.choices(values, weights=weights, k=1)[0]


def write_frame(frame: pd.DataFrame, path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, date_format="%Y-%m-%dT%H:%M:%S")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"file": path.as_posix(), "rows": int(len(frame)), "sha256": digest}


def random_date(rng: random.Random, start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, max(0, (end - start).days)))


def generate_reference_data(ctx: GenerationContext, fake: Faker, rng: random.Random) -> dict[str, pd.DataFrame]:
    now = ctx.generated_at.replace(tzinfo=None)
    categories = pd.DataFrame([
        {"category_id": cid, "category_name": name, "parent_category_id": None,
         "created_at": datetime(2024, 1, 1), "updated_at": now}
        for cid, name in CATEGORIES
    ])

    suppliers_rows = []
    for i in range(ctx.counts["suppliers"]):
        sid = 5001 + i
        suppliers_rows.append({
            "supplier_id": sid,
            "supplier_code": f"SUP-{sid:05d}",
            "supplier_name": f"{fake.unique.company()} Supply",
            "country_code": weighted_choice(rng, ["US", "CA", "MX", "GB"], [0.72, 0.12, 0.10, 0.06]),
            "lead_time_days": weighted_choice(rng, [3, 7, 10, 14, 21, 30], [0.08, 0.20, 0.25, 0.28, 0.14, 0.05]),
            "active_flag": 1 if rng.random() > 0.04 else 0,
            "created_at": datetime(2024, 1, 1),
            "updated_at": now,
        })
    suppliers = pd.DataFrame(suppliers_rows)

    products_rows = []
    for i in range(ctx.counts["products"]):
        pid = 10001 + i
        category_id, category_name = rng.choice(CATEGORIES)
        cost = round(rng.lognormvariate(3.0, 0.65), 2)
        margin = rng.uniform(1.35, 2.8)
        products_rows.append({
            "product_id": pid,
            "sku": f"NRT-{category_name[:3].upper()}-{pid}",
            "product_name": f"{rng.choice(BRANDS)} {rng.choice(PRODUCT_NOUNS)} {i + 1}",
            "category_id": category_id,
            "supplier_id": int(rng.choice(suppliers["supplier_id"].tolist())),
            "brand": rng.choice(BRANDS),
            "unit_cost": cost,
            "list_price": round(cost * margin, 2),
            "currency_code": "USD",
            "active_flag": 1 if rng.random() > 0.03 else 0,
            "created_at": datetime(2024, 1, 1),
            "updated_at": now,
        })
    products = pd.DataFrame(products_rows)

    stores_rows = []
    location_pool = [(region, state, city) for region, values in REGIONS.items() for state, city in values]
    for i in range(ctx.counts["stores"]):
        store_id = 201 + i
        region, state_code, city = location_pool[i % len(location_pool)]
        stores_rows.append({
            "store_id": store_id,
            "store_code": f"{state_code}-{city[:3].upper()}-{i + 1:02d}",
            "store_name": f"Northstar {city} {i // len(location_pool) + 1}",
            "region": region,
            "state_code": state_code,
            "city": city,
            "open_date": random_date(rng, date(2017, 1, 1), date(2024, 12, 31)),
            "active_flag": 1,
            "created_at": datetime(2024, 1, 1),
            "updated_at": now,
        })
    stores = pd.DataFrame(stores_rows)

    employees_rows = []
    for i in range(ctx.counts["employees"]):
        employee_id = 301 + i
        store_id = int(stores.iloc[i % len(stores)]["store_id"])
        employees_rows.append({
            "employee_id": employee_id,
            "employee_number": f"EMP-{employee_id:05d}",
            "store_id": store_id,
            "manager_employee_id": None,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "job_title": weighted_choice(rng, ["Sales Associate", "Store Manager", "Inventory Specialist"], [0.72, 0.10, 0.18]),
            "hire_date": random_date(rng, date(2019, 1, 1), date(2025, 12, 31)),
            "active_flag": 1 if rng.random() > 0.05 else 0,
            "created_at": datetime(2024, 1, 1),
            "updated_at": now,
        })
    employees = pd.DataFrame(employees_rows)
    for store_id, group in employees.groupby("store_id"):
        manager_id = int(group.iloc[0]["employee_id"])
        employees.loc[group.index, "manager_employee_id"] = manager_id
        employees.loc[group.index[0], "job_title"] = "Store Manager"
        employees.loc[group.index[0], "manager_employee_id"] = None

    return {
        "product_categories": categories,
        "suppliers": suppliers,
        "products": products,
        "stores": stores,
        "employees": employees,
    }


def generate_customers(ctx: GenerationContext, fake: Faker, rng: random.Random) -> tuple[pd.DataFrame, pd.DataFrame]:
    today = date(2026, 8, 1)
    rows, addresses = [], []
    for i in range(ctx.counts["customers"]):
        customer_id = 100001 + i
        signup = random_date(rng, date(2023, 1, 1), today - timedelta(days=7))
        first, last = fake.first_name(), fake.last_name()
        customer_number = f"CUS-{customer_id:07d}"
        email = f"{first}.{last}.{customer_id}@example.test".lower().replace("'", "")
        rows.append({
            "customer_id": customer_id,
            "customer_number": customer_number,
            "first_name": first,
            "last_name": last,
            "email": email,
            "phone": fake.numerify("+1-555-####"),
            "signup_date": signup,
            "loyalty_tier": weighted_choice(rng, ["Bronze", "Silver", "Gold", "Platinum"], [0.48, 0.30, 0.17, 0.05]),
            "marketing_opt_in": 1 if rng.random() < 0.68 else 0,
            "created_at": datetime.combine(signup, datetime.min.time()),
            "updated_at": ctx.generated_at.replace(tzinfo=None),
        })
        region, candidates = rng.choice(list(REGIONS.items()))
        state_code, city = rng.choice(candidates)
        addresses.append({
            "address_id": 500001 + i,
            "customer_id": customer_id,
            "address_type": "Shipping",
            "line1": fake.street_address(),
            "line2": None,
            "city": city,
            "state_code": state_code,
            "postal_code": fake.postcode()[:10],
            "country_code": "US",
            "is_default": 1,
            "created_at": datetime.combine(signup, datetime.min.time()),
            "updated_at": ctx.generated_at.replace(tzinfo=None),
        })
    customers = pd.DataFrame(rows)
    address_frame = pd.DataFrame(addresses)

    # Controlled issues. These counts are deterministic and recorded in the fixture.
    for idx in range(min(ctx.issues["null_emails"], len(customers))):
        customers.loc[idx, "email"] = None
    for idx in range(ctx.issues["null_emails"], min(ctx.issues["null_emails"] + ctx.issues["malformed_emails"], len(customers))):
        customers.loc[idx, "email"] = f"bad-email-{idx}"
    start = ctx.issues["null_emails"] + ctx.issues["malformed_emails"]
    for idx in range(start, min(start + ctx.issues["whitespace_and_case"], len(customers))):
        customers.loc[idx, "first_name"] = f"  {str(customers.loc[idx, 'first_name']).upper()}  "
        customers.loc[idx, "loyalty_tier"] = str(customers.loc[idx, "loyalty_tier"]).upper()
    for idx in range(min(ctx.issues["invalid_state_codes"], len(address_frame))):
        address_frame.loc[idx, "state_code"] = ["VIRGINIA", "XX"][idx % 2]
    duplicate_count = min(ctx.issues["duplicate_business_keys"], max(0, len(customers) - 1))
    for idx in range(duplicate_count):
        customers.loc[len(customers) - 1 - idx, "customer_number"] = customers.loc[idx, "customer_number"]
    return customers, address_frame


def generate_orders(
    ctx: GenerationContext,
    refs: dict[str, pd.DataFrame],
    customers: pd.DataFrame,
    rng: random.Random,
) -> dict[str, pd.DataFrame]:
    order_rows, item_rows, payment_rows, shipment_rows = [], [], [], []
    customer_lookup = customers.set_index("customer_id")["signup_date"].to_dict()
    customer_ids = customers["customer_id"].tolist()
    product_ids = refs["products"]["product_id"].tolist()
    product_lookup = refs["products"].set_index("product_id").to_dict("index")
    store_ids = refs["stores"]["store_id"].tolist()
    employee_by_store = refs["employees"].groupby("store_id")["employee_id"].apply(list).to_dict()
    max_order_date = date(2026, 7, 31)

    for i in range(ctx.counts["orders"]):
        order_id = 9_000_001 + i
        customer_id = int(rng.choice(customer_ids))
        signup = customer_lookup[customer_id]
        start = max(signup, date(2024, 1, 1))
        order_date = random_date(rng, start, max_order_date)
        hour = weighted_choice(rng, list(range(8, 23)), [1, 2, 3, 5, 7, 9, 10, 10, 9, 8, 7, 6, 5, 4, 2])
        order_ts = datetime.combine(order_date, datetime.min.time()) + timedelta(hours=hour, minutes=rng.randint(0, 59))
        channel = weighted_choice(rng, ["ONLINE", "STORE"], [0.56, 0.44])
        store_id = int(rng.choice(store_ids))
        employee_id = None if channel == "ONLINE" else int(rng.choice(employee_by_store[store_id]))
        status = weighted_choice(rng, ["COMPLETED", "SHIPPED", "CANCELLED"], [0.72, 0.24, 0.04])
        promo = rng.choice([None, None, None, "WELCOME10", "WEEKEND15", "FREESHIP"])
        order_rows.append({
            "order_id": order_id,
            "order_number": f"ORD-{order_id:09d}",
            "customer_id": customer_id,
            "store_id": store_id,
            "employee_id": employee_id,
            "channel_code": channel,
            "order_timestamp": order_ts,
            "order_status": status,
            "promotion_code": promo,
            "currency_code": "USD",
            "created_at": order_ts,
            "updated_at": ctx.generated_at.replace(tzinfo=None),
        })
        line_count = weighted_choice(rng, [1, 2, 3, 4, 5], [0.43, 0.29, 0.16, 0.08, 0.04])
        subtotal = tax = shipping = 0.0
        chosen = rng.sample(product_ids, k=min(line_count, len(product_ids)))
        for line_no, product_id in enumerate(chosen, start=1):
            product = product_lookup[product_id]
            quantity = weighted_choice(rng, [1, 2, 3, 4], [0.72, 0.20, 0.06, 0.02])
            unit_price = float(product["list_price"])
            discount_rate = 0.0 if promo is None else rng.choice([0.05, 0.10, 0.15])
            discount_amount = round(quantity * unit_price * discount_rate, 2)
            line_subtotal = round(quantity * unit_price - discount_amount, 2)
            line_tax = round(line_subtotal * rng.choice([0.0, 0.05, 0.06, 0.08]), 2)
            item_rows.append({
                "order_item_id": 10_000_001 + len(item_rows),
                "order_id": order_id,
                "line_number": line_no,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "unit_cost": float(product["unit_cost"]),
                "discount_amount": discount_amount,
                "tax_amount": line_tax,
                "created_at": order_ts,
                "updated_at": ctx.generated_at.replace(tzinfo=None),
            })
            subtotal += line_subtotal
            tax += line_tax
        shipping = 0 if channel == "STORE" or subtotal >= 75 else rng.choice([4.99, 7.99, 9.99])
        total = round(subtotal + tax + shipping, 2)
        payment_rows.append({
            "payment_id": 20_000_001 + i,
            "order_id": order_id,
            "payment_timestamp": order_ts + timedelta(minutes=rng.randint(1, 10)),
            "payment_method": weighted_choice(rng, ["CARD", "GIFT_CARD", "DIGITAL_WALLET"], [0.73, 0.10, 0.17]),
            "payment_status": "REFUNDED" if status == "CANCELLED" else "CAPTURED",
            "amount": total,
            "currency_code": "USD",
            "transaction_reference": f"PAY-{uuid.UUID(int=rng.getrandbits(128)).hex[:16].upper()}",
            "created_at": order_ts,
            "updated_at": ctx.generated_at.replace(tzinfo=None),
        })
        if channel == "ONLINE" and status != "CANCELLED":
            promised = order_date + timedelta(days=rng.choice([2, 3, 4, 5]))
            shipped = order_date + timedelta(days=rng.choice([0, 1, 1, 2]))
            delivered = shipped + timedelta(days=rng.choice([1, 2, 3, 4, 6]))
            shipment_rows.append({
                "shipment_id": 30_000_001 + len(shipment_rows),
                "order_id": order_id,
                "carrier": rng.choice(["ParcelOne", "SwiftShip", "National Ground"]),
                "tracking_number": f"NST{order_id}{rng.randint(100, 999)}",
                "ship_date": shipped,
                "promised_delivery_date": promised,
                "actual_delivery_date": delivered,
                "shipment_status": "DELIVERED",
                "shipping_cost": shipping,
                "created_at": datetime.combine(shipped, datetime.min.time()),
                "updated_at": ctx.generated_at.replace(tzinfo=None),
            })

    orders = pd.DataFrame(order_rows)
    items = pd.DataFrame(item_rows)
    payments = pd.DataFrame(payment_rows)
    shipments = pd.DataFrame(shipment_rows)
    for idx in range(min(ctx.issues["impossible_quantities"], len(items))):
        items.loc[idx, "quantity"] = [-2, 0][idx % 2]
    for idx in range(min(ctx.issues["currency_inconsistencies"], len(payments))):
        payments.loc[idx, "currency_code"] = ["usd", "EUR"][idx % 2]
    return {"orders": orders, "order_items": items, "payments": payments, "shipments": shipments}


def generate_inventory(ctx: GenerationContext, refs: dict[str, pd.DataFrame], rng: random.Random) -> dict[str, pd.DataFrame]:
    transactions, snapshots = [], []
    snapshot_date = date(2026, 7, 31)
    for store_id in refs["stores"]["store_id"].tolist():
        sample_size = min(len(refs["products"]), max(10, len(refs["products"]) // 3))
        for product_id in rng.sample(refs["products"]["product_id"].tolist(), sample_size):
            starting = rng.randint(5, 120)
            received = rng.randint(0, 60)
            sold = rng.randint(0, min(50, starting + received))
            adjusted = rng.choice([-2, -1, 0, 0, 0, 1, 2])
            on_hand = starting + received - sold + adjusted
            base_id = 40_000_001 + len(transactions)
            for movement_type, qty, days_back in [
                ("OPENING", starting, 30), ("RECEIPT", received, 18), ("SALE", -sold, 5), ("ADJUSTMENT", adjusted, 1)
            ]:
                if qty == 0:
                    continue
                transactions.append({
                    "inventory_transaction_id": base_id + len(transactions),
                    "store_id": store_id,
                    "product_id": product_id,
                    "transaction_timestamp": datetime.combine(snapshot_date - timedelta(days=days_back), datetime.min.time()),
                    "transaction_type": movement_type,
                    "quantity_change": qty,
                    "reference_type": "SYNTHETIC",
                    "reference_id": None,
                    "created_at": ctx.generated_at.replace(tzinfo=None),
                })
            snapshots.append({
                "inventory_snapshot_id": 50_000_001 + len(snapshots),
                "snapshot_date": snapshot_date,
                "store_id": store_id,
                "product_id": product_id,
                "quantity_on_hand": on_hand,
                "quantity_reserved": min(max(0, on_hand), rng.randint(0, 8)),
                "reorder_point": rng.randint(5, 20),
                "created_at": ctx.generated_at.replace(tzinfo=None),
            })
    return {
        "inventory_transactions": pd.DataFrame(transactions),
        "inventory_snapshots": pd.DataFrame(snapshots),
    }


def generate_digital(
    ctx: GenerationContext,
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    fake: Faker,
    rng: random.Random,
) -> dict[str, pd.DataFrame]:
    web_users = []
    linked_customer_ids = customers["customer_id"].sample(
        n=min(ctx.counts["web_users"], len(customers)), random_state=ctx.seed
    ).tolist()
    for i in range(ctx.counts["web_users"]):
        user_id = 700001 + i
        customer_id = linked_customer_ids[i] if i < len(linked_customer_ids) and rng.random() < 0.75 else None
        created = random_date(rng, date(2023, 1, 1), date(2026, 7, 1))
        web_users.append({
            "web_user_id": user_id,
            "customer_id": customer_id,
            "anonymous_cookie_id": uuid.UUID(int=rng.getrandbits(128)).hex,
            "email_hash": hashlib.sha256(f"web-{user_id}@example.test".encode()).hexdigest(),
            "created_at": datetime.combine(created, datetime.min.time()),
            "updated_at": ctx.generated_at.replace(tzinfo=None),
        })
    web_users_df = pd.DataFrame(web_users)

    campaigns = []
    for i in range(ctx.counts["campaigns"]):
        campaign_id = 8001 + i
        start = random_date(rng, date(2025, 1, 1), date(2026, 6, 30))
        campaigns.append({
            "campaign_id": campaign_id,
            "campaign_code": f"CMP-{campaign_id:05d}",
            "campaign_name": f"{rng.choice(['Launch', 'Seasonal', 'Retention', 'Awareness'])} Campaign {i + 1}",
            "channel": rng.choice(CHANNELS[:-2]),
            "start_date": start,
            "end_date": start + timedelta(days=rng.choice([14, 30, 45, 60])),
            "budget_amount": round(rng.uniform(500, 25000), 2),
            "currency_code": "USD",
            "created_at": datetime.combine(start, datetime.min.time()),
            "updated_at": ctx.generated_at.replace(tzinfo=None),
        })
    campaigns_df = pd.DataFrame(campaigns)

    sessions, events, touchpoints = [], [], []
    order_choices = orders[orders["channel_code"] == "ONLINE"]["order_id"].tolist()
    for i in range(ctx.counts["web_sessions"]):
        session_id = 1_000_001 + i
        web_user_id = int(rng.choice(web_users_df["web_user_id"].tolist()))
        start_date = random_date(rng, date(2025, 1, 1), date(2026, 7, 31))
        started = datetime.combine(start_date, datetime.min.time()) + timedelta(
            hours=rng.randint(0, 23), minutes=rng.randint(0, 59), seconds=rng.randint(0, 59)
        )
        duration = max(5, int(rng.lognormvariate(4.2, 0.8)))
        ended = started + timedelta(seconds=duration)
        channel = weighted_choice(rng, CHANNELS, [0.24, 0.19, 0.11, 0.07, 0.25, 0.14])
        campaign_id = None
        if channel in {"Paid Search", "Social", "Email", "Affiliate"} and rng.random() < 0.75:
            campaign_id = int(rng.choice(campaigns_df["campaign_id"].tolist()))
        converted = rng.random() < (0.08 if channel in {"Email", "Paid Search"} else 0.035)
        order_id = int(rng.choice(order_choices)) if converted and order_choices else None
        sessions.append({
            "session_id": session_id,
            "web_user_id": web_user_id,
            "session_start_utc": started.isoformat() + "+00:00",
            "session_end_utc": ended.isoformat() + "+00:00",
            "source_channel": channel,
            "campaign_id": campaign_id,
            "device_type": weighted_choice(rng, ["mobile", "desktop", "tablet"], [0.61, 0.34, 0.05]),
            "country_code": "US",
            "converted_order_id": order_id,
            "created_at": ctx.generated_at.isoformat(),
        })
        event_types = EVENT_SEQUENCE if converted else EVENT_SEQUENCE[: rng.randint(1, 4)]
        current = started
        for event_type in event_types:
            current += timedelta(seconds=rng.randint(2, 80))
            events.append({
                "event_id": 2_000_001 + len(events),
                "session_id": session_id,
                "event_timestamp": current.isoformat() + "+00:00",
                "event_type": event_type,
                "page_url": f"https://northstar.example/{event_type.replace('_', '-')}",
                "product_id": None,
                "order_id": order_id if event_type == "purchase" else None,
                "event_properties": json.dumps({"synthetic": True, "sequence": len(events)}),
                "created_at": ctx.generated_at.isoformat(),
            })
        if campaign_id is not None:
            touchpoints.append({
                "touchpoint_id": 3_000_001 + len(touchpoints),
                "web_user_id": web_user_id,
                "session_id": session_id,
                "campaign_id": campaign_id,
                "touchpoint_timestamp": started.isoformat() + "+00:00",
                "touchpoint_type": "click",
                "attribution_weight": 1.0,
                "created_at": ctx.generated_at.isoformat(),
            })

    sessions_df = pd.DataFrame(sessions)
    events_df = pd.DataFrame(events)
    for idx in range(min(ctx.issues["out_of_order_events"], len(events_df))):
        events_df.loc[idx, "event_timestamp"] = "2020-01-01T00:00:00+00:00"
    for idx in range(min(ctx.issues["timezone_differences"], len(sessions_df))):
        value = pd.Timestamp(sessions_df.loc[idx, "session_start_utc"])
        sessions_df.loc[idx, "session_start_utc"] = value.tz_convert("America/New_York").isoformat()

    spend = []
    for _, campaign in campaigns_df.iterrows():
        current = campaign["start_date"]
        while current <= campaign["end_date"]:
            spend.append({
                "spend_id": 4_000_001 + len(spend),
                "spend_date": current,
                "campaign_id": int(campaign["campaign_id"]),
                "channel": campaign["channel"],
                "spend_amount": round(rng.uniform(10, max(20, float(campaign["budget_amount"]) / 20)), 2),
                "impressions": rng.randint(100, 50000),
                "clicks": rng.randint(5, 2000),
                "currency_code": "USD",
                "created_at": ctx.generated_at.isoformat(),
            })
            current += timedelta(days=1)
    return {
        "web_users": web_users_df,
        "web_sessions": sessions_df,
        "web_events": events_df,
        "campaigns": campaigns_df,
        "campaign_touchpoints": pd.DataFrame(touchpoints),
        "marketing_spend": pd.DataFrame(spend),
    }


def generate_file_feeds(
    ctx: GenerationContext,
    refs: dict[str, pd.DataFrame],
    orders: dict[str, pd.DataFrame],
    rng: random.Random,
) -> dict[str, Any]:
    items = orders["order_items"]
    candidates = items[items["quantity"] > 0].sample(
        n=min(max(1, len(items) // 12), 10000), random_state=ctx.seed
    )
    returns = []
    order_dates = orders["orders"].set_index("order_id")["order_timestamp"].to_dict()
    for _, item in candidates.iterrows():
        purchase_dt = pd.Timestamp(order_dates[item["order_id"]]).to_pydatetime()
        return_dt = purchase_dt + timedelta(days=rng.randint(1, 45))
        returns.append({
            "return_id": f"RET-{len(returns)+1:08d}",
            "order_id": int(item["order_id"]),
            "order_item_id": int(item["order_item_id"]),
            "product_id": int(item["product_id"]),
            "customer_id": int(orders["orders"].loc[orders["orders"]["order_id"] == item["order_id"], "customer_id"].iloc[0]),
            "return_date": return_dt.date().isoformat(),
            "return_quantity": 1,
            "return_reason": rng.choice(["Damaged", "Wrong size", "Changed mind", "Late delivery", "Not as described"]),
            "refund_amount": round(float(item["unit_price"]) - float(item["discount_amount"]) / max(1, int(item["quantity"])), 2),
            "currency_code": "USD",
            "source_file_date": ctx.generated_at.date().isoformat(),
        })
    returns_df = pd.DataFrame(returns)
    for idx in range(min(ctx.issues["unknown_file_references"], len(returns_df))):
        returns_df.loc[idx, "product_id"] = 99999999 + idx
    for idx in range(min(ctx.issues["mixed_date_formats"], len(returns_df))):
        parsed = pd.Timestamp(returns_df.loc[idx, "return_date"])
        formats = ["%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d"]
        returns_df.loc[idx, "return_date"] = parsed.strftime(formats[idx % len(formats)])
    for idx in range(min(ctx.issues["late_arriving_records"], len(returns_df))):
        returns_df.loc[idx, "source_file_date"] = "2025-01-01"

    cost_updates = []
    for _, product in refs["products"].sample(n=min(len(refs["products"]), 1000), random_state=ctx.seed).iterrows():
        effective = random_date(rng, date(2026, 1, 1), date(2026, 7, 31))
        cost_updates.append({
            "supplier_cost_update_id": f"SCU-{len(cost_updates)+1:08d}",
            "supplier_code": refs["suppliers"].loc[
                refs["suppliers"]["supplier_id"] == product["supplier_id"], "supplier_code"
            ].iloc[0],
            "sku": product["sku"],
            "effective_date": effective.isoformat(),
            "new_unit_cost": round(float(product["unit_cost"]) * rng.uniform(0.92, 1.12), 2),
            "currency_code": "USD",
        })
    cost_df = pd.DataFrame(cost_updates)

    promotions = pd.DataFrame([
        {"promotion_code": "WELCOME10", "promotion_name": "New Customer Welcome", "start_date": "2025-01-01", "end_date": "2026-12-31", "discount_type": "PERCENT", "discount_value": 10, "channel_code": "ONLINE"},
        {"promotion_code": "WEEKEND15", "promotion_name": "Weekend Event", "start_date": "2026-01-01", "end_date": "2026-12-31", "discount_type": "PERCENT", "discount_value": 15, "channel_code": "ALL"},
        {"promotion_code": "FREESHIP", "promotion_name": "Free Shipping", "start_date": "2026-01-01", "end_date": "2026-12-31", "discount_type": "SHIPPING", "discount_value": 100, "channel_code": "ONLINE"},
    ])

    tracking = []
    for _, shipment in orders["shipments"].iterrows():
        shipped = pd.Timestamp(shipment["ship_date"])
        delivered = pd.Timestamp(shipment["actual_delivery_date"])
        tracking.append({
            "tracking_number": shipment["tracking_number"],
            "order_id": int(shipment["order_id"]),
            "carrier": shipment["carrier"],
            "events": [
                {"event_type": "LABEL_CREATED", "event_timestamp": shipped.isoformat(), "location": {"city": "Origin", "country": "US"}},
                {"event_type": "IN_TRANSIT", "event_timestamp": (shipped + timedelta(days=1)).isoformat(), "location": {"city": "Hub", "country": "US"}},
                {"event_type": "DELIVERED", "event_timestamp": delivered.isoformat(), "location": {"city": "Destination", "country": "US"}},
            ],
        })
    return {
        "returns.csv": returns_df,
        "supplier_cost_updates.csv": cost_df,
        "promotion_calendar.csv": promotions,
        "shipment_tracking_events.jsonl": tracking,
    }


def validate(frames: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    tests = []
    def check(name: str, passed: bool, details: str) -> None:
        tests.append({"test": name, "status": "PASS" if passed else "FAIL", "details": details})
    check("customers_not_empty", len(frames["customers"]) > 0, f"rows={len(frames['customers'])}")
    check("orders_not_empty", len(frames["orders"]) > 0, f"rows={len(frames['orders'])}")
    normal_orders = set(frames["orders"]["customer_id"]) - set(frames["customers"]["customer_id"])
    check("orders_customer_fk", len(normal_orders) == 0, f"orphans={len(normal_orders)}")
    order_items_orphans = set(frames["order_items"]["order_id"]) - set(frames["orders"]["order_id"])
    check("items_order_fk", len(order_items_orphans) == 0, f"orphans={len(order_items_orphans)}")
    signup = frames["customers"].set_index("customer_id")["signup_date"].to_dict()
    invalid_dates = sum(pd.Timestamp(row.order_timestamp).date() < signup[row.customer_id] for row in frames["orders"].itertuples())
    check("signup_before_order", invalid_dates == 0, f"invalid={invalid_dates}")
    return tests


def write_outputs(
    ctx: GenerationContext,
    sqlserver: dict[str, pd.DataFrame],
    postgres: dict[str, pd.DataFrame],
    files: dict[str, Any],
) -> None:
    output = ctx.output_dir
    if output.exists():
        # Only remove generated subfolders, never the repository or arbitrary parent folder.
        for child in ["sqlserver", "postgres", "files", "metadata"]:
            target = output / child
            if target.exists():
                import shutil
                shutil.rmtree(target)
    manifests = []
    for name, frame in sqlserver.items():
        manifests.append({"source_system": "sqlserver", **write_frame(frame, output / "sqlserver" / f"{name}.csv")})
    for name, frame in postgres.items():
        manifests.append({"source_system": "postgres", **write_frame(frame, output / "postgres" / f"{name}.csv")})
    for filename, value in files.items():
        path = output / "files" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        if filename.endswith(".jsonl"):
            with path.open("w", encoding="utf-8") as handle:
                for record in value:
                    handle.write(json.dumps(record) + "\n")
            rows = len(value)
            manifests.append({"source_system": "files", "file": path.as_posix(), "rows": rows, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        else:
            manifests.append({"source_system": "files", **write_frame(value, path)})

    # Store paths relative to the generated dataset root so manifests are portable and
    # deterministic whether --output-dir is relative or absolute.
    for item in manifests:
        item["file"] = Path(item["file"]).relative_to(output).as_posix()

    all_frames = {**sqlserver, **postgres}
    tests = validate(all_frames)
    metadata = output / "metadata"
    metadata.mkdir(parents=True, exist_ok=True)
    (metadata / "batch_manifest.json").write_text(json.dumps({
        "batch_id": ctx.batch_id,
        "generated_at_utc": ctx.generated_at.isoformat(),
        "seed": ctx.seed,
        "scale": ctx.scale,
        "files": manifests,
    }, indent=2), encoding="utf-8")
    (metadata / "validation_results.json").write_text(json.dumps(tests, indent=2), encoding="utf-8")
    expected = {
        "fixture_purpose": "Expected controlled issues for teaching Silver data-quality handling.",
        "seed": ctx.seed,
        "scale": ctx.scale,
        "configured_issue_counts": ctx.issues,
        "notes": [
            "A configured issue can affect more than one column.",
            "The fixture records injections, while validation code measures observed rows by rule.",
            "All names, contacts, companies, and identifiers are fictional.",
        ],
    }
    (metadata / "expected_quality_issues.json").write_text(json.dumps(expected, indent=2), encoding="utf-8")
    summary = pd.DataFrame([{"source_system": item["source_system"], "file": Path(item["file"]).name, "rows": item["rows"]} for item in manifests])
    summary.to_csv(metadata / "generation_summary.csv", index=False)
    failed = [test for test in tests if test["status"] != "PASS"]
    if failed:
        raise RuntimeError(f"Generation validation failed: {failed}")
    LOGGER.info("Generated %s files for batch %s", len(manifests), ctx.batch_id)
    LOGGER.info("Output folder: %s", output.resolve())


def main() -> int:
    configure_logging()
    args = parse_args()
    ctx = load_context(args)
    rng = random.Random(ctx.seed)
    Faker.seed(ctx.seed)
    fake = Faker("en_US")
    fake.seed_instance(ctx.seed)
    LOGGER.info("Generating scale=%s seed=%s", ctx.scale, ctx.seed)
    refs = generate_reference_data(ctx, fake, rng)
    customers, addresses = generate_customers(ctx, fake, rng)
    orders = generate_orders(ctx, refs, customers, rng)
    inventory = generate_inventory(ctx, refs, rng)
    sqlserver = {**refs, "customers": customers, "addresses": addresses, **orders, **inventory}
    postgres = generate_digital(ctx, customers, orders["orders"], fake, rng)
    file_feeds = generate_file_feeds(ctx, refs, orders, rng)
    write_outputs(ctx, sqlserver, postgres, file_feeds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
