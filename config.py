from pydantic_settings import BaseSettings
from typing import List


class BotSettings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: str = ""
    MINI_APP_URL: str = ""
    API_URL: str = "http://localhost:8000"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    PAYMENT_DETAILS: str = "Card: 0000 0000 0000 0000\nHolder: NOTFALM SHOP"

    @property
    def admin_ids_list(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]

    class Config:
        env_file = ".env"


settings = BotSettings()
