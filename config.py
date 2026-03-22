import os

from dotenv import load_dotenv


load_dotenv()

def _get_required_env(name: str) -> str:
    """Возвращает обязательную переменную окружения или бросает ошибку"""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(
            f"Не задана переменная {name}. "
            "Заполните файл .env на основе .env.example."
        )
    return value


def get_settings() -> tuple[str, str]:
    """Возвращает TELEGRAM_BOT_TOKEN и WEATHER_API_KEY"""
    telegram_bot_token = _get_required_env("TELEGRAM_BOT_TOKEN")
    weather_api_key = _get_required_env("WEATHER_API_KEY")
    return telegram_bot_token, weather_api_key
