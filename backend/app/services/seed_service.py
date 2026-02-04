from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import Module, Rate, User


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
    {"role": "Менеджер", "level": "middle", "hourly_rate": 4500},
    {"role": "Проектировщик", "level": "middle", "hourly_rate": 4000},
    {"role": "Дизайнер", "level": "middle", "hourly_rate": 3500},
    {"role": "Бекенд", "level": "middle", "hourly_rate": 6000},
    {"role": "Фронтенд", "level": "middle", "hourly_rate": 5000},
    {"role": "Тестировщик", "level": "middle", "hourly_rate": 3000},
]


def seed_defaults(session: Session) -> None:
    """Seed default modules and rates if missing."""

    _seed_modules(session)
    _seed_rates(session)
    _seed_admin(session)


def _seed_modules(session: Session) -> None:
    existing = session.execute(select(Module.code)).scalars().all()
    existing_set = set(existing)
    for module_data in DEFAULT_MODULES:
        if module_data["code"] in existing_set:
            continue
        session.add(Module(**module_data))
    session.commit()


def _seed_rates(session: Session) -> None:
    existing = session.execute(select(Rate.id)).first()
    if existing:
        return
    for rate_data in DEFAULT_RATES:
        session.add(Rate(**rate_data))
    session.commit()


def _seed_admin(session: Session) -> None:
    existing = session.execute(select(User.id)).first()
    if existing:
        return
    admin = User(
        username=settings.admin_username,
        password_hash=hash_password(settings.admin_password),
        role="admin",
    )
    session.add(admin)
    session.commit()
