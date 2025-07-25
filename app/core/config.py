from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str
    SENDGRID_API_KEY: str
    EMAIL_FROM: str


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  

settings = Settings()