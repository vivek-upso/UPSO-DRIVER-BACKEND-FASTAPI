from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
)

from app.core.deps import get_current_user
from app.core.mongo import init_mongo
from .schemas import DriverProfileResponse, DriverProfileUpdate
from .service import calculate_profile_completion
from app.utils.upload import upload_profile_image

router = APIRouter(
    prefix="/profile",
    tags=["Profile - Driver"]
)

# ---------------- PROFILE GET ----------------
@router.get("", response_model=DriverProfileResponse)
async def get_driver_profile(current_user=Depends(get_current_user)):
    # current_user already comes from DB
    user = current_user

    completion = calculate_profile_completion(user)

    return {
        "profile_image": user.get("profile_image"),
        "name": user.get("name"),
        "phone": user.get("phone"),
        "gender": user.get("gender"),
        "dob": user.get("dob"),
        "address": user.get("address"),

        # DRIVER DETAILS
        "driving_license_no": user.get("license_no"),
        "vehicle_type": user.get("vehicle_type"),

        # BANK
        "account_no": user.get("bank", {}).get("account_no"),
        "ifsc": user.get("bank", {}).get("ifsc"),

        "profile_completed": user.get("profile_completed", False),
        "profile_completion": completion,
        "online_status": user.get("is_online", False),
    }

# ---------------- PROFILE UPDATE ----------------
@router.put("")
async def update_driver_profile(
    payload: DriverProfileUpdate,
    current_user=Depends(get_current_user)
):
    update_data = {
        k: v for k, v in payload.dict().items()
        if v is not None
    }

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided to update"
        )

    db = await init_mongo()

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_data}
    )

    return {"message": "Profile updated successfully"}

# ---------------- PROFILE IMAGE UPLOAD ----------------
@router.post("/image")
async def upload_profile_image_api(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Invalid image file")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files allowed")

    image_url = await upload_profile_image(file.file)

    db = await init_mongo()
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"profile_image": image_url}}
    )

    return {
        "success": True,
        "profile_image": image_url
    }
