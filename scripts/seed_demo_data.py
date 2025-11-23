# scripts/seed_demo_data.py

from pathlib import Path


def ensure_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content.strip() + "\n", encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    demo_repos = root / "demo_data" / "demo_repos"

    # ------------------------------------------------------------------------------------
    # DOCOPS-SAAS — документация сервисов, API, CI/CD, архитектура
    # ------------------------------------------------------------------------------------
    ensure_file(
        demo_repos / "docops-saas" / "README.md",
        """
# DocOps SaaS Platform

Тестовый проект для демонстрации возможностей DocOps MCP Assistant.  
Содержит упрощенные материалы по архитектуре, API, DevOps и внутренним сервисам.
        """
    )

    ensure_file(
        demo_repos / "docops-saas" / "docs" / "billing_overview.md",
        """
# Сервис биллинга

Сервис биллинга выполняет:
- расчет стоимости подписки,
- генерацию счетов,
- управление циклом оплаты,
- обработку веб-хуков платежных систем.

Используется в платной части платформы.
        """
    )

    ensure_file(
        demo_repos / "docops-saas" / "docs" / "auth_service.md",
        """
# Auth-Service (Single Sign-On)

Auth-Service обеспечивает:
- SSO для всех внутренних компонентов,
- OIDC-авторизацию,
- выпуск короткоживущих токенов,
- валидацию JWT.

Сервис написан на FastAPI и использует Redis для хранения сессий.
        """
    )

    ensure_file(
        demo_repos / "docops-saas" / "docs" / "architecture.md",
        """
# Архитектура DocOps-SaaS

Основные компоненты:
- Web Frontend — Next.js.
- API Gateway — FastAPI.
- Billing — отдельное Python-микросервис.
- DocOps ML Engine — сервис генерации документации.
- Event Bus — Redis Streams.

Документы и код распределены по нескольким сервисам.
        """
    )

    ensure_file(
        demo_repos / "docops-saas" / "docs" / "api_gateway.md",
        """
# API Gateway

Функции:
- маршрутизация запросов,
- rate limiting,
- валидация схем,
- выдача токенов для внутренних сервисов.

OpenAPI-спецификация доступна по `/openapi.json`.
        """
    )

    ensure_file(
        demo_repos / "docops-saas" / "docs" / "ci_cd.md",
        """
# CI/CD Pipeline

Конвейер включает стадии:
1. Lint & Tests
2. Build Docker Image
3. Security Scan
4. Deploy to Staging
5. Manual Approval
6. Deploy to Production

Используется GitHub Actions и ArgoCD.
        """
    )

    ensure_file(
        demo_repos / "docops-saas" / "docs" / "ml_engine.md",
        """
# DocOps ML Engine

ML-ядро используется для:
- генерации технической документации,
- автосводок для релизов,
- анализа покрытия документацией,
- поиска по исходным кодам и Confluence.

Внутри — Faiss + OpenAI Embeddings.
        """
    )

    ensure_file(
        demo_repos / "docops-saas" / "docs" / "troubleshooting.md",
        """
# Troubleshooting

Типовые проблемы:
- `JWT expired` → обновить токен.
- `429 too many requests` → увеличить квоту rate limit.
- `Billing webhook signature mismatch` → проверить секрет.
        """
    )

    # ------------------------------------------------------------------------------------
    # AIRPORT-FOOD — документация процессов доставки в бизнес-залы
    # ------------------------------------------------------------------------------------
    ensure_file(
        demo_repos / "airport-food" / "README.md",
        """
# Airport Food Delivery

Сервис доставки блюд из ресторанов в бизнес-залы аэропортов.  
Использует DocOps для управления процессами и документацией.
        """
    )

    ensure_file(
        demo_repos / "airport-food" / "docs" / "process_overview.md",
        """
# Общая схема процесса доставки

1. Гость делает заказ в ресторане.
2. Оператор подтверждает готовность кухни.
3. Курьер доставляет блюдо в бизнес-зал.
4. Менеджер зала получает заказ и проверяет соответствие.

Нормативное время доставки: **15–22 минуты**.
        """
    )

    ensure_file(
        demo_repos / "airport-food" / "docs" / "restaurant_integration.md",
        """
# Интеграция с ресторанами

Компоненты:
- POS API — получение заказа,
- Kitchen Display System — мониторинг готовности,
- Loyalty API — начисление бонусов.

Рестораны используют разные POS, поэтому API унифицирован адаптером.
        """
    )

    ensure_file(
        demo_repos / "airport-food" / "docs" / "courier_flow.md",
        """
# Курьерский процесс

Этапы:
- принятие задания,
- маршрут внутри аэропорта,
- контроль допуска в стерильную зону,
- сдача заказа менеджеру зоны.

Каждый шаг логируется.
        """
    )

    ensure_file(
        demo_repos / "airport-food" / "docs" / "quality_requirements.md",
        """
# Стандарты качества

- блюдо не должно терять температуру более чем на 15%,
- упаковка — фирменная, устойчивая к перемещению,
- курьер обязан иметь чистую форму,
- блюдо доставляется без вскрытия и следов повреждений.
        """
    )

    ensure_file(
        demo_repos / "airport-food" / "docs" / "incident_management.md",
        """
# Управление инцидентами

Типичные инциденты:
- длительная доставка,
- потеря заказа,
- несоответствие блюда,
- гость не найден.

Для каждого инцидента формируется отчет и автоматическое уведомление в Slack.
        """
    )

    print(f"Demo repos seeded under: {demo_repos}")


if __name__ == "__main__":
    main()