from pydantic import BaseModel, Field, root_validator
from typing import Optional
from pydantic import model_validator

class RegisterVerifyOtpSchema(BaseModel):
    name: str
    phone: str
    otp: str
    vehicle_type: str
    license_no: Optional[str] = None

    @model_validator(mode="after")
    def validate_vehicle_requirements(self):
        if self.vehicle_type.lower() == "car" and not self.license_no:
            raise ValueError("license_no is required when vehicle_type is car")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Ravi Kumar",
                "phone": "9876543210",
                "otp": "111111",
                "vehicle_type": "car",
                "license_no": "TN09-2023-123456"
            }
        }
    }



class RegisterSendOtpSchema(BaseModel):
    phone: str = Field(..., example="+12223334444")


class LoginSendOtpSchema(BaseModel):
    phone: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "phone": "9876543210"
            }
        }
    }


class LoginVerifyOtpSchema(BaseModel):
    phone: str
    otp: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "phone": "9876543210",
                "otp": "111111"
            }
        }
    }



class SendOtpSchema(BaseModel):
    phone: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "phone": "9876543210"
            }
        }
    }



class VerifyOtpSchema(BaseModel):
    phone: str
    otp: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "phone": "9876543210",
                "otp": "111111"
            }
        }
    }



class CompleteProfileSchema(BaseModel):
    driver: str
    phone: str
    name: str
    vehicle_type: str
    license_no: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "driver": "65f1c9b7b41234abcd",
                "phone": "9876543210",
                "name": "Ravi Kumar",
                "vehicle_type": "bike",
                "license_no": None
            }
        }
    }

class RefreshTokenSchema(BaseModel):
    refresh_token: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "9f68a2c4-8b1f-4b2e-a9a3-33e9baf03a44"
            }
        }
    }

class RegisterVerifyOtpResponse(BaseModel):
    register_session_id: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "register_session_id": "c8e0a1f7-3a42-4fa4-91aa-9ab123456789"
            }
        }
    }
    
class CompleteProfileResponse(BaseModel):
    access_token: str
    refresh_token: str
    profile_completed: bool