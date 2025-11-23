# scripts/seed_projects.py
import textwrap
import yaml
from pathlib import Path

from app.core.storage import init_schema, clear_all, insert_many, get_connection


BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "app" / "config" / "projects.yaml"
DEMO_DATA_DIR = BASE_DIR / "demo_data"
DEMO_REPOS_DIR = DEMO_DATA_DIR / "demo_repos"


def load_projects_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("projects", [])


def seed_db(projects_cfg):
    init_schema()
    clear_all()

    # 1) вставляем проекты
    project_rows = [
        {
            "slug": p["slug"],
            "name": p["name"],
            "description": p.get("description", ""),
        }
        for p in projects_cfg
    ]
    insert_many(
        "INSERT INTO projects",
        project_rows,
    )

    # Получаем их id
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, slug FROM projects;")
    id_by_slug = {row["slug"]: row["id"] for row in cur.fetchall()}

    # 2) репозитории
    repo_rows = []
    space_rows = []

    for p in projects_cfg:
        pid = id_by_slug[p["slug"]]
        repo_rows.append(
            {
                "project_id": pid,
                "name": f"{p['slug']}-mono-repo",
                "path": p["repo_path"],
            }
        )
        space_rows.append(
            {
                "project_id": pid,
                "space_key": p["confluence_space_key"],
                "name": p["confluence_space_name"],
                "base_url": p["confluence_base_url"],
            }
        )

    insert_many("INSERT INTO repos", repo_rows)
    insert_many("INSERT INTO confluence_spaces", space_rows)

    # 3) демо-вопросы для красивых сценариев в UI
    demo_queries = [
        {
            "project_id": id_by_slug["docops-saas"],
            "title": "Архитектура биллинга",
            "question": "Опиши архитектуру биллинга и взаимодействие с сервисом аутентификации.",
            "expected_outline": "Краткий обзор сервиса биллинга, используемые базы данных, взаимодействующие микросервисы, основные сценарии.",
        },
        {
            "project_id": id_by_slug["airport-food"],
            "title": "Процесс доставки в бизнес-зал",
            "question": "Как устроен процесс доставки заказа из ресторана в бизнес-зал аэропорта?",
            "expected_outline": "Шаги от оформления заказа до передачи гостю, интеграции с системами аэропорта, потенциальные точки отказа.",
        },
    ]
    insert_many("INSERT INTO demo_queries", demo_queries)

    conn.close()


def ensure_demo_repo_docops():
    repo_root = DEMO_REPOS_DIR / "docops-saas"
    repo_root.mkdir(parents=True, exist_ok=True)

    # services
    services_dir = repo_root / "services"
    services_dir.mkdir(exist_ok=True)

    (services_dir / "billing").mkdir(exist_ok=True)
    (services_dir / "auth").mkdir(exist_ok=True)
    (services_dir / "notifications").mkdir(exist_ok=True)

    docs_dir = repo_root / "docs"
    docs_dir.mkdir(exist_ok=True)

    # README в корне
    (repo_root / "README.md").write_text(
        textwrap.dedent(
            """
            # DocOps SaaS Platform

            Демонстрационный проект для DocOps MCP Assistant.

            В этом репозитории:
            - Несколько микросервисов (billing, auth, notifications).
            - Документация в каталоге `docs/`.
            - Примеры структурированных описаний сервисов.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    # Документация по биллингу
    (docs_dir / "billing_overview.md").write_text(
        textwrap.dedent(
            """
            # Сервис биллинга

            ## Назначение

            Сервис биллинга отвечает за:
            - учет подписок и тарифных планов;
            - выставление счетов;
            - интеграцию с платежными провайдерами.

            ## Архитектура

            - БД: PostgreSQL (schema: `billing`).
            - Очередь событий: Kafka (топики `billing.invoices`, `billing.payments`).
            - Взаимодействующие сервисы:
              - `auth-service` — проверка идентичности и статуса аккаунта;
              - `notifications-service` — отправка уведомлений о выставленных счетах и просрочках.

            ## Основные сценарии

            1. Создание подписки.
            2. Продление подписки.
            3. Обработка неуспешного списания.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    # Док auth
    (docs_dir / "auth_overview.md").write_text(
        textwrap.dedent(
            """
            # Сервис аутентификации

            ## Назначение

            - Регистрация и аутентификация пользователей.
            - Управление токенами доступа.
            - Поддержка SSO для корпоративных клиентов.

            ## Взаимодействие с биллингом

            - При успешной аутентификации биллингу передается идентификатор клиента.
            - При блокировке аккаунта биллинг прекращает автоматические списания.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    # Просто какой-нибудь код, чтобы MCP Git-сервер мог показать diff/файлы
    (services_dir / "billing" / "main.py").write_text(
        textwrap.dedent(
            """
            def create_invoice(subscription_id: str) -> dict:
                \"\"\"Создает счет по активной подписке.\"\"\"
                # NOTE: упрощенная демо-реализация
                return {
                    "subscription_id": subscription_id,
                    "status": "pending",
                }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def ensure_demo_repo_airport_food():
    repo_root = DEMO_REPOS_DIR / "airport-food"
    repo_root.mkdir(parents=True, exist_ok=True)

    services_dir = repo_root / "services"
    services_dir.mkdir(exist_ok=True)

    (services_dir / "order-service").mkdir(exist_ok=True)
    (services_dir / "courier-service").mkdir(exist_ok=True)

    docs_dir = repo_root / "docs"
    docs_dir.mkdir(exist_ok=True)

    (repo_root / "README.md").write_text(
        textwrap.dedent(
            """
            # Airport Food Delivery

            Демонстрационный проект сервиса доставки блюд из ресторанов в бизнес-залы аэропортов.

            Основные сервисы:
            - order-service: прием и маршрутизация заказов;
            - courier-service: управление курьерами и слотами доставки.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    (docs_dir / "process_overview.md").write_text(
        textwrap.dedent(
            """
            # Процесс доставки в бизнес-зал

            1. Гость оформляет заказ в приложении.
            2. Заказ попадает в `order-service`.
            3. Сервис проверяет:
               - зону аэропорта (общая / стерильная);
               - доступность ресторана;
               - доступность курьера и слота.
            4. `courier-service` назначает курьера.
            5. Курьер забирает заказ в ресторане и передает в бизнес-зал.

            ## Интеграции

            - Система аэропорта для валидации доступа в стерильную зону.
            - Внутренние системы ресторана для статуса готовности блюд.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    (services_dir / "order-service" / "main.py").write_text(
        textwrap.dedent(
            """
            def route_order(order_id: str, lounge_id: str) -> dict:
                \"\"\"Маршрутизирует заказ в нужный ресторан и бизнес-зал.\"\"\"
                return {
                    "order_id": order_id,
                    "lounge_id": lounge_id,
                    "status": "routed",
                }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def main():
    print("Загружаем конфигурацию проектов...")
    projects_cfg = load_projects_config()

    print("Инициализируем базу и наполняем структурами...")
    seed_db(projects_cfg)

    print("Создаем демо-репозитории и документацию...")
    ensure_demo_repo_docops()
    ensure_demo_repo_airport_food()

    print("Готово. База demo_data/demo.db и репо в demo_data/demo_repos/*")


if __name__ == "__main__":
    main()