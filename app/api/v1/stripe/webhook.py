import stripe
from fastapi import APIRouter, Request, HTTPException
from bson import ObjectId
from datetime import datetime

from app.core.config import settings
from app.core.mongo import init_mongo

router = APIRouter(prefix="/stripe", tags=["Stripe"])

stripe.api_key = settings.STRIPE_SECRET_KEY
