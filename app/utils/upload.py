import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status

ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/jpg",
    "application/pdf",
}

MAX_SIZE_MB = 5


# ================= LICENSE FILE UPLOAD =================

async def upload_license_file(file: UploadFile) -> dict:
    if not file:
        return None

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG images or PDF files are allowed",
        )

    # ---- file size check ----
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be under 5MB",
        )

    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="licenses",
            resource_type="auto",  # image + pdf
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed",
        )

    return {
        "url": result.get("secure_url"),
        "public_id": result.get("public_id"),
        "file_type": result.get("resource_type"),  # image | raw
    }


# ================= PROFILE IMAGE UPLOAD =================

async def upload_profile_image(file: UploadFile) -> str:
    if not file:
        return None

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files allowed",
        )

    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder="driver/profile",
            resource_type="image",
            transformation=[
                {"width": 400, "height": 400, "crop": "fill"}
            ],
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image upload failed",
        )

    return result.get("secure_url")
