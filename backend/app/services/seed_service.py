from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Module, Rate


DEFAULT_MODULES = [
    {
        "code": "core",
        "name": "Базовая платформа",
        "description": "Проектирование, инфраструктура, базовые сущности",
        "hours_frontend": 6,
        "hours_backend": 10,
        "hours_qa": 3,
    },
    {
        "code": "auth",
        "name": "Аутентификация",
        "description": "Регистрация, логин, восстановление пароля, сессии",
        "hours_frontend": 8,
        "hours_backend": 10,
        "hours_qa": 3,
    },
    {
        "code": "profile",
        "name": "Профили пользователей",
        "description": "Личные данные, настройки, роли",
        "hours_frontend": 6,
        "hours_backend": 8,
        "hours_qa": 2,
    },
    {
        "code": "catalog",
        "name": "Каталог",
        "description": "Каталог товаров/услуг, фильтры, карточки",
        "hours_frontend": 12,
        "hours_backend": 14,
        "hours_qa": 4,
    },
    {
        "code": "search",
        "name": "Поиск",
        "description": "Полнотекстовый поиск, фильтрация, ранжирование",
        "hours_frontend": 8,
        "hours_backend": 12,
        "hours_qa": 3,
    },
    {
        "code": "geo",
        "name": "Гео-сервис",
        "description": "Карта, гео-поиск, зоны доставки, маршруты",
        "hours_frontend": 10,
        "hours_backend": 14,
        "hours_qa": 4,
    },
    {
        "code": "cart",
        "name": "Корзина",
        "description": "Добавление, пересчет, скидки, промокоды",
        "hours_frontend": 8,
        "hours_backend": 10,
        "hours_qa": 3,
    },
    {
        "code": "orders",
        "name": "Заказы",
        "description": "Оформление, статусы, история, возвраты",
        "hours_frontend": 10,
        "hours_backend": 14,
        "hours_qa": 4,
    },
    {
        "code": "payments",
        "name": "Платежи",
        "description": "Эквайринг, счета, статусы, webhooks",
        "hours_frontend": 6,
        "hours_backend": 12,
        "hours_qa": 3,
    },
    {
        "code": "notifications",
        "name": "Уведомления",
        "description": "Email, SMS, push, шаблоны сообщений",
        "hours_frontend": 6,
        "hours_backend": 8,
        "hours_qa": 2,
    },
    {
        "code": "chat",
        "name": "Чат и поддержка",
        "description": "Онлайн-чат, тикеты, SLA",
        "hours_frontend": 8,
        "hours_backend": 12,
        "hours_qa": 3,
    },
    {
        "code": "admin",
        "name": "Админка",
        "description": "Админ-панель, права доступа, модерация",
        "hours_frontend": 14,
        "hours_backend": 16,
        "hours_qa": 5,
    },
    {
        "code": "analytics",
        "name": "Аналитика",
        "description": "Дашборды, метрики, выгрузки",
        "hours_frontend": 8,
        "hours_backend": 10,
        "hours_qa": 3,
    },
    {
        "code": "integrations",
        "name": "Интеграции",
        "description": "CRM/ERP, внешние API, webhooks",
        "hours_frontend": 4,
        "hours_backend": 12,
        "hours_qa": 3,
    },
    {
        "code": "cms",
        "name": "Контент и CMS",
        "description": "Страницы, баннеры, контентные блоки",
        "hours_frontend": 8,
        "hours_backend": 10,
        "hours_qa": 3,
    },
]

DEFAULT_RATES = [
    {"role": "frontend", "level": "junior", "hourly_rate": 25},
    {"role": "frontend", "level": "middle", "hourly_rate": 40},
    {"role": "frontend", "level": "senior", "hourly_rate": 60},
    {"role": "backend", "level": "junior", "hourly_rate": 28},
    {"role": "backend", "level": "middle", "hourly_rate": 45},
    {"role": "backend", "level": "senior", "hourly_rate": 70},
    {"role": "qa", "level": "junior", "hourly_rate": 18},
    {"role": "qa", "level": "middle", "hourly_rate": 30},
    {"role": "qa", "level": "senior", "hourly_rate": 45},
]


def seed_defaults(session: Session) -> None:
    """Seed default modules and rates if missing."""

    _seed_modules(session)
    _seed_rates(session)


def _seed_modules(session: Session) -> None:
    existing = session.execute(select(Module.code)).scalars().all()
    existing_set = set(existing)
    for module_data in DEFAULT_MODULES:
        if module_data["code"] in existing_set:
            continue
        session.add(Module(**module_data))
    session.commit()


def _seed_rates(session: Session) -> None:
    existing = session.execute(select(Rate.role, Rate.level)).all()
    existing_set = {(role, level) for role, level in existing}
    for rate_data in DEFAULT_RATES:
        if (rate_data["role"], rate_data["level"]) in existing_set:
            continue
        session.add(Rate(**rate_data))
    session.commit()
