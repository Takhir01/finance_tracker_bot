import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    GEMINI_API_KEY: str = ""
    ADMIN_IDS: str = ""
    DB_PATH: str = "finance_bot.db"
    FREE_ACCESS_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def admin_id_list(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        res = []
        for x in self.ADMIN_IDS.split(","):
            x = x.strip()
            if x.isdigit():
                res.append(int(x))
        return res


settings = Settings()
