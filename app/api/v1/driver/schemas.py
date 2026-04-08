from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime


class DriverStatusUpdateSchema(BaseModel):
    status: Literal["online", "offline"]


# ---------------- LOCATION ----------------
class DriverLocation(BaseModel):
    lat: float
    lng: float
    updated_at: Optional[datetime] = None



# ---------------- PROFILE RESPONSE ----------------
# class DriverProfileResponse(BaseModel):
#     id: str
#     name: str
#     phone: str

#     profile_image: Optional[str]

#     gender: Optional[str]
#     dob: Optional[datetime]
#     address: Optional[str]

#     driving_license_no: Optional[str]
#     vehicle_type: Optional[str]

#     account_no: Optional[str]
#     ifsc: Optional[str]

#     location: Optional[DriverLocation]

#     wallet_balance: float
#     currency: str

#     stripe_account_linked: bool
#     stripe_onboarded: bool

#     profile_completed: bool
#     profile_completion: int

#     online_status: bool
#     last_active_at: Optional[datetime]


# ---------------- PROFILE UPDATE ----------------
# class DriverProfileUpdate(BaseModel):
#     name: Optional[str] = None
#     address: Optional[str] = None
#     gender: Optional[str] = None
#     dob: Optional[datetime] = None

#     driving_license_no: Optional[str] = None
#     vehicle_type: Optional[str] = None

#     account_no: Optional[str] = None
#     ifsc: Optional[str] = None


# ---------------- WALLET ----------------
class WithdrawRequest(BaseModel):
    amount: float
    currency: Optional[str] = "CAD"



# ---------------- ORDER SUB OBJECTS ----------------

class PickupInfo(BaseModel):
    name: Optional[str]
    address: Optional[str] = None


class DeliveryInfo(BaseModel):
    address: Optional[str]


OrderStatus = Literal[
    "Assigned",
    "PickupReached",
    "ItemsCollected",
    "DeliveryReached",
    "Delivered",
    "NotDelivered"
]

class OrderHistoryItem(BaseModel):
    orderId: str
    date: datetime
    amount: Optional[float]
    payment: Optional[str]
    status: OrderStatus
    pickup: PickupInfo
    delivery: DeliveryInfo

class OrderHistoryResponse(BaseModel):
    page: int
    limit: int
    total: int
    orders: List[OrderHistoryItem]


class LatestOrdersResponse(BaseModel):
    today: dict
    lifetime: dict
    latest_orders: List[OrderHistoryItem]


# ---------------- ORDER ACTION RESPONSES ----------------

class OrderAcceptResponse(BaseModel):
    success: bool
    orderId: str
    assigned: bool


class OrderStatusResponse(BaseModel):
    status: str

from pydantic import BaseModel
from typing import Optional


class DriverProfileResponse(BaseModel):
    profile_image: Optional[str]
    name: Optional[str]
    phone: str
    gender: Optional[str]
    dob: Optional[str]
    address: Optional[str]

    driving_license_no: Optional[str]
    vehicle_type: Optional[str]

    account_no: Optional[str]
    ifsc: Optional[str]

    profile_completed: bool
    profile_completion: int
    online_status: bool


class DriverProfileUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    address: Optional[str] = None
    vehicle_type: Optional[str] = None
    license_no: Optional[str] = None
