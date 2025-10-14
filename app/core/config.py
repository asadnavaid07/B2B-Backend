from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL")
    SENDGRID_API_KEY: str
    EMAIL_FROM: str
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET")


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  

settings = Settings()