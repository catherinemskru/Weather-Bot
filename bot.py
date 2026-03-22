"""Телеграм-бот с погодой и картинками попугаев"""

import asyncio
from dataclasses import dataclass
import logging
from pathlib import Path
import random

import requests
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import get_settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
router = Router()
TELEGRAM_BOT_TOKEN = ""
WEATHER_API_KEY = ""


class CityNotFoundError(Exception):
    """Город не найден"""

    pass


class WeatherAPIError(Exception):
    """Проблема с API погоды"""

    pass


@dataclass
class WeatherData:
    """Данные о погоде в удобном виде"""

    city: str
    temperature: float
    feels_like: float
    description: str
    humidity: int
    wind_speed: float
    weather_type: str


def normalize_weather(weather_main: str) -> str:
    """Сводит погоду к нашим категориям"""

    value = (weather_main or "").strip()
    if value in {"Rain", "Drizzle"}:
        return "Rain"
    if value in {"Mist", "Fog", "Haze", "Smoke"}:
        return "Mist"
    if value in {
        "Clear",
        "Clouds",
        "Rain",
        "Snow",
        "Thunderstorm",
        "Mist",
    }:
        return value
    return "Clouds"


def get_weather(city: str) -> WeatherData:
    """Запрашивает погоду по названию города"""

    if not city.strip():
        raise CityNotFoundError

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city.strip(),
                "appid": WEATHER_API_KEY,
                "units": "metric",
                "lang": "ru",
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        logger.exception("Ошибка сети: %s", exc)
        raise WeatherAPIError from exc

    if response.status_code == 404:
        raise CityNotFoundError
    if response.status_code != 200:
        raise WeatherAPIError

    data = response.json()
    return WeatherData(
        city=data["name"],
        temperature=float(data["main"]["temp"]),
        feels_like=float(data["main"]["feels_like"]),
        description=str(data["weather"][0]["description"]),
        humidity=int(data["main"]["humidity"]),
        wind_speed=float(data["wind"]["speed"]),
        weather_type=normalize_weather(data["weather"][0]["main"]),
    )


def clothes_advice(weather_type: str, temperature: float) -> str:
    """Совет по одежде"""

    if temperature <= 0:
        return "Теплее оденьтесь. 🧥"
    if temperature >= 28:
        return "Лёгкая одежда и вода. 🥤"
    if weather_type == "Rain":
        return "Не забудьте зонт. ☔"
    if weather_type == "Snow":
        return "Нужна тёплая обувь. ❄️"
    if weather_type == "Thunderstorm":
        return "Лучше переждать грозу в помещении. ⚡"
    return "Погода комфортная. 🙂"


def weather_text(weather: WeatherData) -> str:
    """Собирает текст ответа для пользователя"""

    return (
        f"🦜 Погода в городе {weather.city}\n\n"
        f"🌡 Температура: {weather.temperature:.1f}°C\n"
        f"🤗 Ощущается как: {weather.feels_like:.1f}°C\n"
        f"☁️ Описание: {weather.description.capitalize()}\n"
        f"💧 Влажность: {weather.humidity}%\n"
        f"💨 Ветер: {weather.wind_speed:.1f} м/с\n\n"
        f"👕 Совет: {clothes_advice(weather.weather_type, weather.temperature)}"
    )


def weather_folder(weather_type: str) -> str:
    """Выбирает папку с картинками по погоде"""

    if weather_type == "Clear":
        return "sunny"
    if weather_type in {"Rain", "Thunderstorm"}:
        return "rainy"
    if weather_type == "Snow":
        return "snowy"
    return "cloudy"


def pick_image(weather_type: str) -> Path | None:
    """Берет случайную картинку попугая"""

    folder = (
        Path(__file__).resolve().parent
        / "assets"
        / weather_folder(weather_type)
    )
    if not folder.exists():
        return None
    images = [
        p for p in folder.iterdir()
        if p.is_file() and "parrot" in p.stem.lower()
    ]
    return random.choice(images) if images else None


def action_keyboard() -> InlineKeyboardMarkup:
    """Кнопки под ответом"""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Другой город",
                    callback_data="action:new_city",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Обновить",
                    callback_data="action:refresh",
                )
            ],
        ]
    )


async def send_weather(message: Message, state: FSMContext, city: str) -> None:
    """Получает погоду и отправляет ответ"""

    weather = get_weather(city)
    await state.update_data(last_city=weather.city)

    text = weather_text(weather)
    image = pick_image(weather.weather_type)
    keyboard = action_keyboard()

    if image:
        await message.answer_photo(
            FSInputFile(str(image)),
            caption=text,
            reply_markup=keyboard,
        )
    else:
        await message.answer(
            text + "\n\n📷 Картинка пока не добавлена.",
            reply_markup=keyboard,
        )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Стартовое сообщение"""

    await state.clear()
    await state.update_data(last_city="")
    await message.answer(
        "Привет! 👋\n"
        "Я показываю погоду и присылаю попугая под неё\n\n"
        "Напиши город, например: Москва"
    )


@router.message(F.text & ~F.text.startswith("/"))
async def on_city(message: Message, state: FSMContext) -> None:
    """Город от пользователя"""

    try:
        await send_weather(message, state, message.text.strip())
    except CityNotFoundError:
        await message.answer("Не нашел такой город, проверь написание 🙏")
    except WeatherAPIError:
        await message.answer(
            "Сервис погоды временно недоступен, попробуй позже"
        )


@router.callback_query(lambda c: c.data == "action:new_city")
async def on_new_city(callback: CallbackQuery, state: FSMContext) -> None:
    """Кнопка Другой город"""

    await state.update_data(last_city="")
    await callback.message.answer("Введите новый город. 🌍")
    await callback.answer()


@router.callback_query(lambda c: c.data == "action:refresh")
async def on_refresh(callback: CallbackQuery, state: FSMContext) -> None:
    """Кнопка Обновить"""

    city = (await state.get_data()).get("last_city", "").strip()
    if not city:
        await callback.message.answer("Сначала введите город. 🏙️")
        await callback.answer()
        return

    try:
        await send_weather(callback.message, state, city)
    except (CityNotFoundError, WeatherAPIError):
        await callback.message.answer("Не получилось обновить погоду.")
    await callback.answer()


async def main() -> None:
    """Запуск бота"""
    global TELEGRAM_BOT_TOKEN, WEATHER_API_KEY

    try:
        TELEGRAM_BOT_TOKEN, WEATHER_API_KEY = get_settings()
    except ValueError as exc:
        logger.error(str(exc))
        return

    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)
    logger.info("Бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
