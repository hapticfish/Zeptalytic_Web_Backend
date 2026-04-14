from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEV_COMPOSE_PATH = REPO_ROOT / "docker-compose.yml"
TEST_COMPOSE_PATH = REPO_ROOT / "docker-compose.test.yml"


def _read_compose_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_compose_topology_files_exist() -> None:
    assert DEV_COMPOSE_PATH.exists()
    assert TEST_COMPOSE_PATH.exists()


def test_dev_compose_exposes_expected_services_and_migration_command() -> None:
    compose_text = _read_compose_file(DEV_COMPOSE_PATH)

    assert "services:" in compose_text
    assert "\n  db:\n" in compose_text
    assert "\n  api:\n" in compose_text
    assert "\n  migrate:\n" in compose_text
    assert 'command: ["alembic", "upgrade", "head"]' in compose_text


def test_test_compose_requires_db_then_migrate_then_test() -> None:
    compose_text = _read_compose_file(TEST_COMPOSE_PATH)

    assert "services:" in compose_text
    assert "\n  db:\n" in compose_text
    assert "\n  migrate:\n" in compose_text
    assert "\n  test:\n" in compose_text

    assert (
        "  migrate:\n"
        "    build:\n"
        "      context: .\n"
        "    depends_on:\n"
        "      db:\n"
        "        condition: service_healthy\n"
    ) in compose_text

    assert (
        "  test:\n"
        "    build:\n"
        "      context: .\n"
        "    depends_on:\n"
        "      db:\n"
        "        condition: service_healthy\n"
        "      migrate:\n"
        "        condition: service_healthy\n"
    ) in compose_text


def test_test_compose_locks_healthchecks_and_runtime_commands() -> None:
    compose_text = _read_compose_file(TEST_COMPOSE_PATH)

    assert (
        'test: ["CMD-SHELL", "pg_isready -U postgres -d zeptalytic_web_backend_test"]'
        in compose_text
    )
    assert 'test: ["CMD-SHELL", "test -f /tmp/migrate-ready"]' in compose_text
    assert "alembic upgrade head && touch /tmp/migrate-ready && tail -f /dev/null" in compose_text
    assert 'command: ["pytest", "-q"]' in compose_text
