from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request
)
from bson import ObjectId
from datetime import datetime
from app.core.deps import get_current_user
from app.core.mongo import init_mongo
from .schemas import WithdrawRequest
from app.core import stripe as stripe_core
from app.core.config import settings
import stripe

router = APIRouter(
    prefix="/payment/stripe",
    tags=["Payments - Driver"]
)


# ---------------- STRIPE ACCOUNT CREATION ----------------
@router.post("/account")
async def create_or_get_stripe_account(
    current_user=Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(403, "Driver access only")

    db = await init_mongo()

    #  Check existing account
    user = await db.users.find_one({"_id": current_user["_id"]})
    if user.get("stripe_account_id"):
        return {
            "account_id": user["stripe_account_id"],
            "existing": True
        }

    #  Acquire lock
    lock = await db.users.find_one_and_update(
        {
            "_id": current_user["_id"],
            "stripe_account_creating": {"$ne": True}
        },
        {"$set": {"stripe_account_creating": True}},
        return_document=True
    )

    if not lock:
        raise HTTPException(409, "Stripe account creation already in progress")

    try:
        #  Create Stripe account
        account = stripe_core.stripe.Account.create(
            type="express",
            country=settings.STRIPE_COUNTRY,
            capabilities={
                "transfers": {"requested": True}
            },
            metadata={
                "driver_id": str(current_user["_id"])
            }
        )

        #  Save account + release lock
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {
                "$set": {"stripe_account_id": account.id},
                "$unset": {"stripe_account_creating": ""}
            }
        )

        return {
            "account_id": account.id,
            "existing": False
        }

    except Exception:
        #  ALWAYS release lock on failure
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$unset": {"stripe_account_creating": ""}}
        )
        raise

# ---------------- ONBOARDING LINK ----------------
@router.get("/onboard")
async def stripe_onboard(
    current_user=Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(403, "Driver access only")

    db = await init_mongo()
    user = await db.users.find_one({"_id": current_user["_id"]})

    if not user.get("stripe_account_id"):
        raise HTTPException(400, "Stripe account not created")

    link = stripe_core.stripe.AccountLink.create(
        account=user["stripe_account_id"],
        type="account_onboarding",
        refresh_url="https://yourapp.com/stripe/refresh",
        return_url="https://yourapp.com/stripe/success"
    )

    return {"url": link.url}



@router.post("/deposit")
async def deposit(
    payload: WithdrawRequest,
    current_user=Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(403, "Driver access only")

    db = await init_mongo()

    if payload.amount <= 0:
        raise HTTPException(400, "Amount must be greater than 0")

    # Create Stripe PaymentIntent
    intent = stripe_core.stripe.PaymentIntent.create(
        amount=int(payload.amount * 100),
        currency=settings.STRIPE_CURRENCY,
        metadata={
            "driver_id": str(current_user["_id"]),
            "purpose": "wallet_deposit"
        },
        idempotency_key=f"deposit_{current_user['_id']}_{datetime.utcnow().isoformat()}"
    )


    # Save pending deposit (IMPORTANT)
    await db.deposits.insert_one({
        "driver_id": current_user["_id"],
        "payment_intent_id": intent.id,
        "amount": payload.amount,
        "status": "pending",
        "created_at": datetime.utcnow()
    })

    return {
        "client_secret": intent.client_secret,
        "amount": payload.amount,
        "currency": settings.STRIPE_CURRENCY
    }

# ---------------- STRIPE WEBHOOK ----------------
@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(400, "Missing Stripe signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid Stripe signature")
    except Exception as e:
        raise HTTPException(400, str(e))

    db = await init_mongo()
    event_type = event["type"]
    data = event["data"]["object"]

    # --------------------------------------------------
    # DEPOSIT SUCCESS
    # --------------------------------------------------
    if event_type == "payment_intent.succeeded":
        metadata = data.get("metadata", {})

        if metadata.get("purpose") == "wallet_deposit":
            driver_id = ObjectId(metadata["driver_id"])
            amount = round(data["amount"] / 100, 2)

            # Idempotency check
            deposit = await db.deposits.find_one({
                "payment_intent_id": data["id"],
                "status": "completed"
            })

            if not deposit:
                await db.users.update_one(
                    {"_id": driver_id},
                    {"$inc": {"wallet_balance": amount}}
                )

                await db.deposits.update_one(
                    {"payment_intent_id": data["id"]},
                    {
                        "$set": {
                            "status": "completed",
                            "completed_at": datetime.utcnow()
                        }
                    }
                )

    # --------------------------------------------------
    # DEPOSIT FAILED
    # --------------------------------------------------
    elif event_type == "payment_intent.payment_failed":
        await db.deposits.update_one(
            {"payment_intent_id": data["id"]},
            {"$set": {"status": "failed"}}
        )

    # --------------------------------------------------
    # WITHDRAW PAID
    # --------------------------------------------------
    elif event_type == "payout.paid":
        await db.withdrawals.update_one(
            {"payout_id": data["id"]},
            {"$set": {"status": "paid", "paid_at": datetime.utcnow()}}
        )

    # --------------------------------------------------
    # WITHDRAW FAILED → REFUND WALLET
    # --------------------------------------------------
    elif event_type == "payout.failed":
        withdrawal = await db.withdrawals.find_one({
            "payout_id": data["id"]
        })

        if withdrawal and withdrawal["status"] != "failed":
            await db.users.update_one(
                {"_id": withdrawal["driver_id"]},
                {"$inc": {"wallet_balance": withdrawal["amount"]}}
            )

            await db.withdrawals.update_one(
                {"_id": withdrawal["_id"]},
                {"$set": {"status": "failed"}}
            )

    return {"received": True}
