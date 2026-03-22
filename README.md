# Telegram Weather Pet Bot

Python-бот показывает погоду в выбранном городе и присылает картинку попугая по погоде

## Что умеет бот

- Принимает город от пользователя
- Получает погоду через OpenWeatherMap API
- Определяет тип погоды: Clear, Clouds, Rain/Drizzle, Snow, Thunderstorm, Mist/Fog
- Отправляет:
  - температуру
  - описание
  - ощущаемую температуру
  - влажность и скорость ветра
  - короткий совет, что надеть
- Показывает изображение попугая по текущей погоде

## Технологии

- Python 3.10+
- aiogram
- requests
- python-dotenv

## Быстрый запуск

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Создайте `.env` и заполните ключи:

- `TELEGRAM_BOT_TOKEN` — токен бота из BotFather
- `WEATHER_API_KEY` — ключ OpenWeatherMap

Пример файла `.env`:

```env
TELEGRAM_BOT_TOKEN=1234567890:your-telegram-bot-token
WEATHER_API_KEY=your-openweather-api-key
```

3. Добавьте картинки в папки `assets/`:

- `assets/sunny/`
- `assets/rainy/`
- `assets/snowy/`
- `assets/cloudy/`

Правило для имен файлов:

- в имени файла должна быть часть `parrot` (например, `parrot_sunny_1.jpg`)

4. Запустите бота:

```bash
python bot.py
```


## Структура

- `bot.py` — вся основная логика (команды, кнопки, погода, текст, картинки)
- `config.py` — загрузка токенов из `.env`
- `assets/` — локальные изображения по типам погоды
