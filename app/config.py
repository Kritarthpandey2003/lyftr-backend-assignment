import os

class Settings:
    # Use absolute path for sqlite to avoid errors in Docker
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////data/app.db")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "testsecret") 
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()