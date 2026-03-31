# ---------------- WITHDRAW ----------------
from fastapi import Depends, HTTPException,Query,APIRouter
from app.api.v1 import router
from app.api.v1.driver.schemas import WithdrawRequest
from app.core.deps import get_current_user
from app.core.mongo import init_mongo

from datetime import datetime
from app.core import stripe as stripe_core
from app.core.config import settings

router = APIRouter(
    prefix="/wallet",
    tags=["Wallet - Driver"]
)


@router.post(
    "/withdraw",
    summary="Withdraw wallet balance",
    description="Initiates a Stripe payout and deducts the amount from driver's wallet atomically.",
    responses={
        200: {
            "description": "Withdrawal successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "amount": 1500,
                        "payout_id": "po_1PZ8R0ABCDEF12345",
                        "status": "pending"
                    }
                }
            }
        },
        400: {
            "description": "Validation or wallet error",
            "content": {
                "application/json": {
                    "examples": {
                        "StripeNotLinked": {
                            "summary": "Stripe account not linked",
                            "value": {
                                "detail": "Stripe account not linked"
                            }
                        },
                        "InvalidAmount": {
                            "summary": "Invalid withdrawal amount",
                            "value": {
                                "detail": "Amount must be greater than 0"
                            }
                        },
                        "InsufficientBalance": {
                            "summary": "Insufficient wallet balance",
                            "value": {
                                "detail": "Insufficient balance"
                            }
                        }
                    }
                }
            }
        }
    }
)

async def withdraw(
    payload: WithdrawRequest,
    current_user=Depends(get_current_user)
):
    db = await init_mongo()

    user = await db.users.find_one({"_id": current_user["_id"]})

    if not user.get("stripe_account_id"):
        raise HTTPException(400, "Stripe account not linked")

    wallet = float(user.get("wallet_balance", 0))

    if payload.amount <= 0:
        raise HTTPException(400, "Amount must be greater than 0")

    if payload.amount > wallet:
        raise HTTPException(400, "Insufficient balance")

    # Stripe payout (convert to smallest unit)
    payout = stripe_core.stripe.Payout.create(
        amount=int(payload.amount * 100),
        currency=settings.STRIPE_CURRENCY,
        stripe_account=user["stripe_account_id"]
    )

    # Atomic balance deduction
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$inc": {"wallet_balance": -payload.amount}}
    )

    # Log withdrawal (VERY IMPORTANT)
    await db.withdrawals.insert_one({
        "driver_id": current_user["_id"],
        "amount": payload.amount,
        "payout_id": payout.id,
        "status": payout.status,
        "created_at": datetime.utcnow()
    })

    return {
        "success": True,
        "amount": payload.amount,
        "payout_id": payout.id,
        "status": payout.status
    }


# ---------------- EARNINGS ----------------
@router.get(
    "/earnings",
    summary="Get driver earnings",
    description="Returns wallet balance and delivered orders with pagination.",
    responses={
        200: {
            "description": "Earnings fetched successfully",
            "content": {
                "application/json": {
                    "example": {
                        "wallet_balance": 3250.75,
                        "page": 1,
                        "limit": 10,
                        "total": 32,
                        "orders": [
                            {
                                "orderId": "65fa1b6e9d13c2a7c1234567",
                                "date": "2026-02-01T12:40:15Z",
                                "amount": 240,
                                "payment": "COD",
                                "pickup": {
                                    "name": "Pizza Hut"
                                },
                                "delivery": {
                                    "address": "Anna Nagar, Chennai"
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
)

async def driver_earnings(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=50),
    current_user=Depends(get_current_user)
):
    db = await init_mongo()
    driver_id = current_user["_id"]

    # ---------------- WALLET ----------------
    user = await db.users.find_one(
        {"_id": driver_id},
        {"wallet_balance": 1}
    )

    wallet_balance = round(float(user.get("wallet_balance", 0)), 2)

    # ---------------- ORDERS ----------------
    skip = (page - 1) * limit

    cursor = (
        db.orders
        .find({
            "assignedDriverId": driver_id,
            "status": "Delivered"
        })
        .sort("createdAt", -1)
        .skip(skip)
        .limit(limit)
    )

    orders = []
    async for order in cursor:
        orders.append({
            "orderId": str(order["_id"]),
            "date": order.get("createdAt"),
            "amount": order.get("totalAmount"),
            "payment": order.get("paymentMethod"),

            "pickup": {
                "name": order.get("restaurant", {}).get("name")
            },
            "delivery": {
                "address": order.get("address", {}).get("addressLine")
            }
        })

    total_orders = await db.orders.count_documents({
        "assignedDriverId": driver_id,
        "status": "Delivered"
    })

    return {
        "wallet_balance": wallet_balance,
        "page": page,
        "limit": limit,
        "total": total_orders,
        "orders": orders
    }
