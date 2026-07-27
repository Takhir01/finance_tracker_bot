# 🤖 Telegram AI Finance Tracker Bot (Gemini 2.5 Flash)

Полнофункциональный Telegram бот для авто-учета расходов и доходов с использованием искусственного интеллекта **Gemini AI** (`google-genai`), графиков `matplotlib` и поддержкой мультимодального анализа (текст + фото чеков).

---

## 🌟 Основные возможности

1. **Распознавание любых трат и доходов (Gemini AI)**:
   - Произвольные сообщения: *"Купил кофе 450р"*, *"Вчера бензин 2000р"*, *"Получил зарплату 100 000 руб"*.
   - **Фотографии чеков**: распознавание сумм, товаров и автоматическая привязка к категориям.
2. **Интерактивные кнопки (Inline Keyboard)**:
   - Изменение категории в 1 клик.
   - Переключение между Расходом и Доходом.
   - Отмена / удаление записи.
3. **Графики и наглядные отчеты**:
   - **Недельный отчет** (статистика за 7 дней + графики).
   - **Месячный отчет** (круговая диаграмма Donut Chart + гистограмма трат по дням).
   - **Экспорт в Excel (.xlsx)** полных данных за всё время.
4. **Система доступа по ссылкам**:
   - Работа с клиентами по ссылкам-приглашениям (реферальная система).
   - Генерация ссылок прямо из бота командами `/genlink` или кнопкой в меню.

---

## 🛠 Быстрый запуск локально (Windows / macOS / Linux)

1. Откройте файл `.env` и вставьте ваш **Telegram Bot Token** от [@BotFather](https://t.me/BotFather):
   ```env
   BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
   GEMINI_API_KEY=AIzaSyCWLEuo-aI0FUmSB9WAesw-3gLNiC8NRCE
   ```

2. Установите зависимости и запустите бота:
   - **Windows**: Двойной клик по `run.bat`
   - **Терминал**:
     ```bash
     pip install -r requirements.txt
     python main.py
     ```

---

## 🚀 Развертывание на сервере (VPS / Google Cloud / Docker)

### Вариант 1: Через Docker Compose (Рекомендуется)
1. Загрузите файлы проекта на ваш сервер.
2. В файле `.env` укажите ваш `BOT_TOKEN`.
3. Запустите одну команду:
   ```bash
   bash deploy.sh
   ```
   Или вручную:
   ```bash
   docker compose up -d --build
   ```

### Вариант 2: Запуск как Systemd служба на Linux VPS
```bash
sudo cp finance_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable finance_bot
sudo systemctl start finance_bot
```

---

## 📁 Структура проекта

```
finance_tracker_bot/
├── .env                  # Конфигурация и API ключи
├── requirements.txt      # Зависимости Python
├── main.py               # Точка входа приложения
├── Dockerfile            # Сборка контейнера Docker
├── docker-compose.yml    # Конфигурация Docker Compose
├── deploy.sh             # Скрипт авторазвертывания на сервере
├── database/             # База данных SQLite (SQLAlchemy Async)
│   ├── models.py
│   ├── db.py
│   └── crud.py
├── services/             # Сервисы ИИ, графиков и отчетов
│   ├── gemini_service.py # Gemini 2.5 Flash API
│   ├── chart_service.py  # Matplotlib диаграммы
│   └── report_service.py # Экспорт Excel и форматирование
└── bot/                  # Обработчики и клавиатуры aiogram 3
    ├── handlers/
    ├── keyboards/
    └── middlewares/
```
