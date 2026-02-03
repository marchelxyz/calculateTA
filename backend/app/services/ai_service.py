from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Module
from app.schemas import (
    AiMindmapConnection,
    AiMindmapNode,
    AiMindmapResponse,
    AiModuleSuggestion,
    AiParseResponse,
    AiWbsTask,
)


@dataclass(frozen=True)
class ModuleCatalogItem:
    """Catalog item for AI input."""

    code: str
    name: str
    description: str


@dataclass(frozen=True)
class ModuleCatalogHours:
    """Catalog item with hour defaults."""

    code: str
    name: str
    description: str
    hours_frontend: float
    hours_backend: float
    hours_qa: float
    role_hours: list[dict[str, float]]


logger = logging.getLogger(__name__)


def parse_prompt_with_ai(session: Session, prompt: str) -> AiParseResponse:
    """Parse prompt into module suggestions using AI or fallback."""

    catalog = _load_catalog(session)
    catalog_index = _build_keyword_index(catalog)
    if settings.openai_api_key:
        return _parse_with_openai(prompt, catalog, catalog_index)
    return _parse_with_heuristics(prompt, catalog, catalog_index)


def parse_prompt_to_mindmap(session: Session, prompt: str) -> AiMindmapResponse:
    """Build mindmap nodes and connections from prompt."""

    response = parse_prompt_with_ai(session, prompt)
    catalog = _load_catalog_with_hours(session)
    catalog_by_code = {item.code: item for item in catalog}
    return _build_mindmap_from_tasks(response.tasks, catalog_by_code, response.rationale)


def _load_catalog(session: Session) -> list[ModuleCatalogItem]:
    """Load module catalog from database."""
    result = session.execute(select(Module))
    items = []
    for module in result.scalars():
        items.append(
            ModuleCatalogItem(
                code=module.code,
                name=module.name,
                description=module.description or "",
            )
        )
    return items


def _load_catalog_with_hours(session: Session) -> list[ModuleCatalogHours]:
    """Load module catalog with hours and role hours."""

    result = session.execute(select(Module))
    items: list[ModuleCatalogHours] = []
    for module in result.scalars():
        items.append(
            ModuleCatalogHours(
                code=module.code,
                name=module.name,
                description=module.description or "",
                hours_frontend=module.hours_frontend,
                hours_backend=module.hours_backend,
                hours_qa=module.hours_qa,
                role_hours=[
                    {"role": item.role, "hours": item.hours}
                    for item in module.role_hours
                ],
            )
        )
    return items


def _parse_with_openai(
    prompt: str,
    catalog: list[ModuleCatalogItem],
    catalog_index: dict[str, set[str]],
) -> AiParseResponse:
    """Request OpenAI WBS decomposition."""
    client = OpenAI(api_key=settings.openai_api_key)
    system_prompt = _build_system_prompt(catalog)
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            timeout=settings.openai_timeout_seconds,
        )
        content = response.choices[0].message.content or ""
        if not content:
            logger.warning("OpenAI returned empty response content.")
        data = _safe_json_loads(content)
        tasks = _parse_tasks(data.get("tasks", []), catalog_index)
        suggestions = _parse_suggestions(data.get("suggestions", []), catalog_index)
        if not suggestions:
            suggestions = _suggest_from_tasks(tasks)
        rationale = data.get("rationale", "AI analysis")
        return AiParseResponse(suggestions=suggestions, tasks=tasks, rationale=rationale)
    except Exception:
        logger.exception("OpenAI request failed. Falling back to heuristics.")
        return _parse_with_heuristics(prompt, catalog, catalog_index)


def _build_system_prompt(catalog: list[ModuleCatalogItem]) -> str:
    """Build system prompt with catalog context."""
    catalog_lines = [
        f"{item.code}: {item.name} — {item.description}".strip()
        for item in catalog
    ]
    catalog_text = "\n".join(catalog_lines)
    return (
        "Ты помощник для декомпозиции продуктовых запросов в технические модули.\n"
        "Сделай WBS: 6-12 задач, каждая привязана к модулю.\n"
        "Верни строго JSON со структурой:\n"
        "{\n"
        '  "tasks": [{"title": "...", "details": "...", "module_code": "...", "confidence": 0.0}],\n'
        '  "suggestions": [{"module_code": "...", "confidence": 0.0, "notes": "..."}],\n'
        '  "rationale": "..."\n'
        "}\n"
        "module_code выбирай только из каталога.\n"
        "Каталог:\n"
        f"{catalog_text}"
    )


def _parse_with_heuristics(
    prompt: str,
    catalog: list[ModuleCatalogItem],
    catalog_index: dict[str, set[str]],
) -> AiParseResponse:
    """Fallback decomposition based on keywords."""
    lowered = prompt.lower()
    tasks: list[AiWbsTask] = []
    for item in catalog:
        if _match_prompt(lowered, item):
            tasks.append(
                AiWbsTask(
                    title=item.name,
                    details=item.description,
                    module_code=item.code,
                    confidence=0.55,
                )
            )
    if not tasks:
        tasks = _fallback_tasks(catalog_index)
    suggestions = _suggest_from_tasks(tasks)
    return AiParseResponse(
        suggestions=suggestions,
        tasks=tasks,
        rationale="Heuristics fallback (no API key configured).",
    )


def _match_prompt(prompt: str, item: ModuleCatalogItem) -> bool:
    """Check if prompt matches catalog item keywords."""
    keywords = {item.code.lower(), item.name.lower()}
    if item.description:
        keywords.update(item.description.lower().split())
    return any(keyword in prompt for keyword in keywords)


def _safe_json_loads(content: str) -> dict:
    """Parse JSON safely with defaults."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"suggestions": [], "tasks": [], "rationale": "Failed to parse AI response"}


def _build_keyword_index(catalog: list[ModuleCatalogItem]) -> dict[str, set[str]]:
    """Build keyword index for module mapping."""
    index: dict[str, set[str]] = {}
    for item in catalog:
        keywords = _extract_keywords(f"{item.code} {item.name} {item.description}")
        index[item.code] = keywords
    return index


def _extract_keywords(text: str) -> set[str]:
    """Extract normalized keywords from text."""
    tokens = {token.strip().lower() for token in text.replace("—", " ").split()}
    return {token for token in tokens if len(token) > 2}


def _parse_tasks(
    raw_tasks: list[dict],
    catalog_index: dict[str, set[str]],
) -> list[AiWbsTask]:
    """Parse and normalize AI task list."""
    tasks: list[AiWbsTask] = []
    for item in raw_tasks:
        title = str(item.get("title", "")).strip() or "Задача"
        details = str(item.get("details", "")).strip()
        module_code = str(item.get("module_code", "")).strip()
        confidence = float(item.get("confidence", 0))
        module_code = _normalize_module_code(module_code, catalog_index)
        if not module_code:
            module_code, confidence = _map_task_to_module(
                title,
                details,
                catalog_index,
                confidence,
            )
        tasks.append(
            AiWbsTask(
                title=title,
                details=details,
                module_code=module_code,
                confidence=confidence,
            )
        )
    return tasks


def _parse_suggestions(
    raw_suggestions: list[dict],
    catalog_index: dict[str, set[str]],
) -> list[AiModuleSuggestion]:
    """Parse and normalize AI suggestions."""
    suggestions: list[AiModuleSuggestion] = []
    for item in raw_suggestions:
        module_code = _normalize_module_code(str(item.get("module_code", "")).strip(), catalog_index)
        if not module_code:
            continue
        suggestions.append(
            AiModuleSuggestion(
                module_code=module_code,
                confidence=float(item.get("confidence", 0)),
                notes=str(item.get("notes", "")),
            )
        )
    return suggestions


def _normalize_module_code(module_code: str, catalog_index: dict[str, set[str]]) -> str:
    """Return module code if it exists in catalog."""
    if module_code in catalog_index:
        return module_code
    return ""


def _map_task_to_module(
    title: str,
    details: str,
    catalog_index: dict[str, set[str]],
    confidence: float,
) -> tuple[str, float]:
    """Map task text to the best matching module."""
    text = f"{title} {details}".lower()
    best_code = ""
    best_score = 0
    for code, keywords in catalog_index.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_score = score
            best_code = code
    if not best_code:
        best_code = _default_module_code(catalog_index)
        confidence = max(confidence, 0.35)
    else:
        confidence = max(confidence, 0.6)
    return best_code, confidence


def _default_module_code(catalog_index: dict[str, set[str]]) -> str:
    """Return fallback module code."""
    if "core" in catalog_index:
        return "core"
    return next(iter(catalog_index.keys()), "")


def _suggest_from_tasks(tasks: list[AiWbsTask]) -> list[AiModuleSuggestion]:
    """Build module suggestions list from WBS tasks."""
    unique: dict[str, AiModuleSuggestion] = {}
    for task in tasks:
        if not task.module_code:
            continue
        existing = unique.get(task.module_code)
        if not existing or task.confidence > existing.confidence:
            unique[task.module_code] = AiModuleSuggestion(
                module_code=task.module_code,
                confidence=task.confidence,
                notes="Выделено из WBS",
            )
    return list(unique.values())


def _fallback_tasks(catalog_index: dict[str, set[str]]) -> list[AiWbsTask]:
    """Return a minimal default WBS."""
    default_module = _default_module_code(catalog_index)
    tasks = [
        AiWbsTask(
            title="Сбор требований и сценариев",
            details="Интервью, пользовательские потоки, KPI",
            module_code=default_module,
            confidence=0.4,
        ),
        AiWbsTask(
            title="Архитектура и интеграции",
            details="Сервисы, контуры безопасности, интеграции",
            module_code=default_module,
            confidence=0.4,
        ),
        AiWbsTask(
            title="UI/UX концепт",
            details="Прототипы, визуальный стиль, ключевые экраны",
            module_code=default_module,
            confidence=0.4,
        ),
    ]
    return tasks


def _build_mindmap_from_tasks(
    tasks: list[AiWbsTask],
    catalog_by_code: dict[str, ModuleCatalogHours],
    rationale: str,
) -> AiMindmapResponse:
    """Convert WBS tasks into mindmap graph."""

    root_key = "root"
    nodes: list[AiMindmapNode] = [
        AiMindmapNode(
            key=root_key,
            title="Проект",
            details="AI-схема по запросу",
            module_code="",
        )
    ]
    connections: list[AiMindmapConnection] = []

    grouped: dict[str, list[AiWbsTask]] = {}
    for task in tasks:
        grouped.setdefault(task.module_code or "core", []).append(task)

    for module_code, grouped_tasks in grouped.items():
        module = catalog_by_code.get(module_code)
        module_key = f"module_{module_code}"
        nodes.append(
            AiMindmapNode(
                key=module_key,
                title=module.name if module else module_code,
                details=module.description if module else "",
                module_code=module_code,
            )
        )
        connections.append(
            AiMindmapConnection(from_key=root_key, to_key=module_key)
        )

        split_hours = _split_hours(module, len(grouped_tasks))
        split_role_hours = _split_role_hours(module, len(grouped_tasks))
        for index, task in enumerate(grouped_tasks):
            node_key = f"task_{module_code}_{index}"
            nodes.append(
                AiMindmapNode(
                    key=node_key,
                    title=task.title,
                    details=task.details,
                    module_code=module_code,
                    hours_frontend=split_hours["frontend"],
                    hours_backend=split_hours["backend"],
                    hours_qa=split_hours["qa"],
                    role_hours=split_role_hours,
                )
            )
            connections.append(
                AiMindmapConnection(from_key=module_key, to_key=node_key)
            )

    return AiMindmapResponse(nodes=nodes, connections=connections, rationale=rationale)


def _split_hours(
    module: ModuleCatalogHours | None,
    count: int,
) -> dict[str, float]:
    """Split module base hours across tasks."""

    if not module or count <= 0:
        return {"frontend": 0.0, "backend": 0.0, "qa": 0.0}
    return {
        "frontend": module.hours_frontend / count,
        "backend": module.hours_backend / count,
        "qa": module.hours_qa / count,
    }


def _split_role_hours(
    module: ModuleCatalogHours | None,
    count: int,
) -> list[dict[str, float]]:
    """Split extra role hours across tasks."""

    if not module or count <= 0:
        return []
    return [
        {"role": item["role"], "hours": item["hours"] / count}
        for item in module.role_hours
    ]
