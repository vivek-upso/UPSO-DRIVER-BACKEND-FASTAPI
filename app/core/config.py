from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ---------------- DATABASE ----------------
    MONGO_URI: str

    # Redis (optional)
    REDIS_URL: str | None = None

    # ---------------- AUTH ----------------
    JWT_SECRET: str
    JWT_EXPIRE_MIN: int = 1440  # 1 day

    # ---------------- OTP ----------------
    USE_DUMMY_OTP: bool = True
    DUMMY_OTP: str = "111111"

    # ---------------- SMS ----------------
    TWILIO_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_FROM: str | None = None

    # ---------------- GOOGLE ----------------
    GCP_GEOCODING_API_KEY: str | None = None

    # ---------------- STRIPE (MANDATORY FOR WITHDRAW) ----------------
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str | None = None

    STRIPE_COUNTRY: str = "IN"
    STRIPE_CURRENCY: str = "inr"

    ORDER_SOCKET_URL: str = "http://localhost:8080"
    ORDER_SOCKET_TOKEN: str | None = None 
    
    
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
