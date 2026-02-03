# calculateTA

Интерактивный «Центр управления полетами» для оценки проектов.

## Стек

- Frontend: Vue 3 + Vite + Pinia
- Backend: FastAPI + SQLAlchemy + Postgres
- AI: OpenAI API (модель задается через переменную окружения)

## Запуск локально

1. Backend:
   - `cd backend`
   - `python -m venv .venv`
   - `source .venv/Scripts/activate`
   - `pip install -r requirements.txt`
   - `cp .env.example .env` и заполнить `DATABASE_URL`
   - `PYTHONPATH=. uvicorn app.main:app --reload`
2. Frontend:
   - `cd frontend`
   - `npm install`
   - `npm run dev`

## Railway

- Используется `DATABASE_URL` от Railway (Postgres).
- Автодеплой на Railway работает через `railway.toml` + `nixpacks.toml`.
- Команда старта: `PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- В Railway задать переменные:
  - `DATABASE_URL`
  - `OPENAI_API_KEY` (опционально)
  - `OPENAI_MODEL` (по умолчанию `gpt-5`)

## Скрипты БД

При старте приложения автоматически выполняется:
- создание таблиц (если их нет);
- проверка наличия всех столбцов;
- сидинг дефолтных модулей и ставок.