import asyncio
from datetime import UTC, datetime, timedelta
from random import Random

from app.core.mongo import init_mongo
from app.core.security import hash_text


NOW = datetime.now(UTC).replace(tzinfo=None)
RNG = Random(42)
MOCK_TAG = "upso_seed_v1"


def utc_days_ago(days: int, hours: int = 0, minutes: int = 0) -> datetime:
    return NOW - timedelta(days=days, hours=hours, minutes=minutes)


def build_driver(
    name: str,
    phone: str,
    username: str,
    email: str,
    vehicle_type: str,
    license_no: str | None,
    gender: str,
    wallet_balance: float,
    online: bool,
    stripe_account_id: str | None,
    bank_suffix: str,
    city: str,
    lat: float,
    lng: float,
):
    return {
        "name": name,
        "phone": phone,
        "username": username,
        "email": email,
        "role": "driver",
        "vehicle_type": vehicle_type,
        "license_no": license_no,
        "gender": gender,
        "dob": "1996-08-14",
        "address": f"{city}, Tamil Nadu",
        "profile_image": f"https://picsum.photos/seed/{phone}/400/400",
        "bank": {
            "account_no": f"52100456{bank_suffix}",
            "ifsc": "HDFC0001234",
        },
        "wallet_balance": wallet_balance,
        "profile_completed": True,
        "is_online": online,
        "last_online_at": NOW if online else utc_days_ago(1),
        "stripe_account_id": stripe_account_id,
        "created_at": utc_days_ago(RNG.randint(20, 90)),
        "location": {
            "lat": lat,
            "lng": lng,
            "updated_at": NOW,
        },
        "mock_seed": MOCK_TAG,
    }


def build_store(name: str, phone: str, email: str, address: str, approved: bool = True):
    return {
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
        "is_active": True,
        "is_approved": approved,
        "created_at": utc_days_ago(RNG.randint(10, 60)),
        "mock_seed": MOCK_TAG,
    }


def build_order(
    driver_id,
    store_name: str,
    store_address_line: str,
    store_city: str,
    store_postal: str,
    pickup_lat: float,
    pickup_lng: float,
    drop_address: str,
    drop_city: str,
    drop_postal: str,
    drop_lat: float,
    drop_lng: float,
    status: str,
    created_at: datetime,
    total_amount: float,
    payment_method: str,
    cash_to_collect: float,
):
    timeline = []
    status_steps = [
        ("Assigned", created_at + timedelta(minutes=2), str(driver_id)),
        ("PickupReached", created_at + timedelta(minutes=12), "driver"),
        ("ItemsCollected", created_at + timedelta(minutes=20), "driver"),
        ("DeliveryReached", created_at + timedelta(minutes=34), "driver"),
    ]

    if status in {"Assigned", "PickupReached", "ItemsCollected", "DeliveryReached"}:
        allowed = {
            "Assigned": 1,
            "PickupReached": 2,
            "ItemsCollected": 3,
            "DeliveryReached": 4,
        }[status]
        timeline = [
            {"status": step, "at": at, "by": by}
            for step, at, by in status_steps[:allowed]
        ]
        last_status_at = timeline[-1]["at"]
    else:
        timeline = [
            {"status": step, "at": at, "by": by}
            for step, at, by in status_steps
        ]
        delivered_at = created_at + timedelta(minutes=48)
        timeline.append({"status": status, "at": delivered_at, "by": "driver"})
        last_status_at = delivered_at

    return {
        "status": status,
        "assignedDriverId": driver_id,
        "assignedAt": created_at + timedelta(minutes=2),
        "lastStatusAt": last_status_at,
        "createdAt": created_at,
        "totalAmount": total_amount,
        "paymentMethod": payment_method,
        "distanceKm": round(RNG.uniform(2.3, 10.8), 1),
        "etaMin": RNG.randint(14, 38),
        "cashToCollect": cash_to_collect,
        "restaurant": {
            "name": store_name,
            "lat": pickup_lat,
            "lng": pickup_lng,
            "address": {
                "addressLine": store_address_line,
                "city": store_city,
                "postalCode": store_postal,
                "country": "India",
            },
        },
        "address": {
            "addressLine": drop_address,
            "city": drop_city,
            "postalCode": drop_postal,
            "country": "India",
            "lat": drop_lat,
            "lng": drop_lng,
        },
        "timeline": timeline,
        "mock_seed": MOCK_TAG,
    }


async def clear_existing_mock_data(db):
    await db.orders.delete_many({"mock_seed": MOCK_TAG})
    await db.users.delete_many({"mock_seed": MOCK_TAG})
    await db.admins.delete_many({"mock_seed": MOCK_TAG})
    await db.stores.delete_many({"mock_seed": MOCK_TAG})
    await db.deposits.delete_many({"mock_seed": MOCK_TAG})
    await db.withdrawals.delete_many({"mock_seed": MOCK_TAG})
    await db.otps.delete_many({"mock_seed": MOCK_TAG})
    await db.otp_requests.delete_many({"mock_seed": MOCK_TAG})
    await db.refresh_tokens.delete_many({"mock_seed": MOCK_TAG})


async def seed_admin(db):
    admin_doc = {
        "name": "Mock Admin",
        "email": "mock-admin@upso.com",
        "password_hash": hash_text("Admin@123"),
        "is_active": True,
        "created_at": NOW,
        "mock_seed": MOCK_TAG,
    }
    result = await db.admins.insert_one(admin_doc)
    return result.inserted_id


async def seed_drivers(db):
    drivers = [
        build_driver(
            name="Ravi Kumar",
            phone="9876543210",
            username="ravi.kumar",
            email="ravi.kumar@mock.upso",
            vehicle_type="bike",
            license_no=None,
            gender="male",
            wallet_balance=1850.5,
            online=True,
            stripe_account_id="acct_mock_ravi",
            bank_suffix="101",
            city="Anna Nagar, Chennai",
            lat=13.0878,
            lng=80.2087,
        ),
        build_driver(
            name="Priya Sharma",
            phone="9123456780",
            username="priya.sharma",
            email="priya.sharma@mock.upso",
            vehicle_type="car",
            license_no="TN09-2023-123456",
            gender="female",
            wallet_balance=940.0,
            online=False,
            stripe_account_id="acct_mock_priya",
            bank_suffix="202",
            city="Velachery, Chennai",
            lat=12.9791,
            lng=80.2212,
        ),
        build_driver(
            name="Arun Das",
            phone="9000011112",
            username="arun.das",
            email="arun.das@mock.upso",
            vehicle_type="bike",
            license_no=None,
            gender="male",
            wallet_balance=320.75,
            online=True,
            stripe_account_id=None,
            bank_suffix="303",
            city="T Nagar, Chennai",
            lat=13.0418,
            lng=80.2337,
        ),
    ]
    result = await db.users.insert_many(drivers)
    return result.inserted_ids


async def seed_stores(db):
    stores = [
        build_store(
            "Pizza Hub",
            "04440001001",
            "pizza@upso.mock",
            "12 4th Avenue, Anna Nagar, Chennai",
        ),
        build_store(
            "Burger Street",
            "04440001002",
            "burger@upso.mock",
            "88 Phoenix Mall Road, Velachery, Chennai",
        ),
        build_store(
            "Dosa Corner",
            "04440001003",
            "dosa@upso.mock",
            "5 Pondy Bazaar, T Nagar, Chennai",
        ),
    ]
    result = await db.stores.insert_many(stores)
    return result.inserted_ids


async def seed_orders(db, driver_ids):
    orders = [
        build_order(
            driver_id=driver_ids[0],
            store_name="Pizza Hub",
            store_address_line="12 4th Avenue, Anna Nagar",
            store_city="Chennai",
            store_postal="600040",
            pickup_lat=13.0876,
            pickup_lng=80.2083,
            drop_address="221 Shenoy Nagar Main Road",
            drop_city="Chennai",
            drop_postal="600030",
            drop_lat=13.0785,
            drop_lng=80.2215,
            status="Delivered",
            created_at=utc_days_ago(0, hours=2),
            total_amount=245.0,
            payment_method="COD",
            cash_to_collect=245.0,
        ),
        build_order(
            driver_id=driver_ids[0],
            store_name="Burger Street",
            store_address_line="88 Phoenix Mall Road, Velachery",
            store_city="Chennai",
            store_postal="600042",
            pickup_lat=12.9904,
            pickup_lng=80.2181,
            drop_address="14 Gandhi Street, Adambakkam",
            drop_city="Chennai",
            drop_postal="600088",
            drop_lat=12.9806,
            drop_lng=80.2049,
            status="DeliveryReached",
            created_at=utc_days_ago(0, hours=1, minutes=10),
            total_amount=319.0,
            payment_method="UPI",
            cash_to_collect=0.0,
        ),
        build_order(
            driver_id=driver_ids[0],
            store_name="Dosa Corner",
            store_address_line="5 Pondy Bazaar, T Nagar",
            store_city="Chennai",
            store_postal="600017",
            pickup_lat=13.0415,
            pickup_lng=80.2334,
            drop_address="9 CIT Nagar West, Nandanam",
            drop_city="Chennai",
            drop_postal="600035",
            drop_lat=13.0313,
            drop_lng=80.2410,
            status="Delivered",
            created_at=utc_days_ago(3, hours=4),
            total_amount=180.0,
            payment_method="CARD",
            cash_to_collect=0.0,
        ),
        build_order(
            driver_id=driver_ids[1],
            store_name="Pizza Hub",
            store_address_line="12 4th Avenue, Anna Nagar",
            store_city="Chennai",
            store_postal="600040",
            pickup_lat=13.0876,
            pickup_lng=80.2083,
            drop_address="72 Medavakkam Tank Road, Kilpauk",
            drop_city="Chennai",
            drop_postal="600010",
            drop_lat=13.0828,
            drop_lng=80.2409,
            status="NotDelivered",
            created_at=utc_days_ago(6, hours=3),
            total_amount=410.0,
            payment_method="COD",
            cash_to_collect=410.0,
        ),
        build_order(
            driver_id=driver_ids[1],
            store_name="Burger Street",
            store_address_line="88 Phoenix Mall Road, Velachery",
            store_city="Chennai",
            store_postal="600042",
            pickup_lat=12.9904,
            pickup_lng=80.2181,
            drop_address="11 Rajalakshmi Nagar, Pallikaranai",
            drop_city="Chennai",
            drop_postal="600100",
            drop_lat=12.9371,
            drop_lng=80.2056,
            status="Delivered",
            created_at=utc_days_ago(12, hours=2),
            total_amount=289.0,
            payment_method="UPI",
            cash_to_collect=0.0,
        ),
        build_order(
            driver_id=driver_ids[2],
            store_name="Dosa Corner",
            store_address_line="5 Pondy Bazaar, T Nagar",
            store_city="Chennai",
            store_postal="600017",
            pickup_lat=13.0415,
            pickup_lng=80.2334,
            drop_address="30 North Usman Road, Kodambakkam",
            drop_city="Chennai",
            drop_postal="600024",
            drop_lat=13.0524,
            drop_lng=80.2271,
            status="Assigned",
            created_at=utc_days_ago(0, hours=0, minutes=35),
            total_amount=155.0,
            payment_method="COD",
            cash_to_collect=155.0,
        ),
    ]
    result = await db.orders.insert_many(orders)
    return result.inserted_ids


async def seed_financials(db, driver_ids):
    deposits = [
        {
            "driver_id": driver_ids[0],
            "payment_intent_id": "pi_mock_ravi_001",
            "amount": 500.0,
            "status": "completed",
            "created_at": utc_days_ago(7),
            "completed_at": utc_days_ago(7) + timedelta(minutes=5),
            "mock_seed": MOCK_TAG,
        },
        {
            "driver_id": driver_ids[1],
            "payment_intent_id": "pi_mock_priya_001",
            "amount": 750.0,
            "status": "pending",
            "created_at": utc_days_ago(1),
            "mock_seed": MOCK_TAG,
        },
    ]

    withdrawals = [
        {
            "driver_id": driver_ids[0],
            "amount": 300.0,
            "payout_id": "po_mock_ravi_001",
            "status": "paid",
            "created_at": utc_days_ago(4),
            "paid_at": utc_days_ago(4) + timedelta(hours=2),
            "mock_seed": MOCK_TAG,
        },
        {
            "driver_id": driver_ids[1],
            "amount": 150.0,
            "payout_id": "po_mock_priya_001",
            "status": "failed",
            "created_at": utc_days_ago(2),
            "mock_seed": MOCK_TAG,
        },
    ]

    otps = [
        {
            "phone": "9876543210",
            "otp": "111111",
            "purpose": "login",
            "expires_at": NOW + timedelta(minutes=5),
            "attempts": 0,
            "used": False,
            "mock_seed": MOCK_TAG,
        },
        {
            "phone": "9555512345",
            "otp": "111111",
            "purpose": "login",
            "expires_at": NOW + timedelta(minutes=5),
            "attempts": 1,
            "used": False,
            "mock_seed": MOCK_TAG,
        },
    ]

    otp_requests = [
        {
            "phone": "9000099999",
            "purpose": "register",
            "otp_hash": hash_text("111111"),
            "expires_at": NOW + timedelta(minutes=5),
            "created_at": NOW,
            "mock_seed": MOCK_TAG,
        }
    ]

    await db.deposits.insert_many(deposits)
    await db.withdrawals.insert_many(withdrawals)
    await db.otps.insert_many(otps)
    await db.otp_requests.insert_many(otp_requests)


async def main():
    db = await init_mongo()

    await clear_existing_mock_data(db)

    admin_id = await seed_admin(db)
    driver_ids = await seed_drivers(db)
    store_ids = await seed_stores(db)
    order_ids = await seed_orders(db, driver_ids)
    await seed_financials(db, driver_ids)

    print("Mock data seeded successfully")
    print(f"Admins: 1 ({admin_id})")
    print(f"Drivers: {len(driver_ids)}")
    print(f"Stores: {len(store_ids)}")
    print(f"Orders: {len(order_ids)}")
    print("Login OTP for seeded drivers: 111111")
    print("Mock admin email: mock-admin@upso.com")
    print("Mock admin password: Admin@123")


if __name__ == "__main__":
    asyncio.run(main())
