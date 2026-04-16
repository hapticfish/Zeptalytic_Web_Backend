from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

from app.db.bootstrap import get_target_metadata
from app.db.session import SessionLocal, engine


def test_parent_db_bootstrap_matches_migrated_postgres_schema() -> None:
    metadata = get_target_metadata()

    with SessionLocal() as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1
        applied_revision = session.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()

    alembic_config = Config("alembic.ini")
    expected_revision = ScriptDirectory.from_config(alembic_config).get_current_head()

    inspector = inspect(engine)
    live_tables = set(inspector.get_table_names())
    expected_tables = set(metadata.tables)
    actual_parent_tables = live_tables - {"alembic_version"}
    missing_tables = expected_tables - actual_parent_tables
    unexpected_tables = actual_parent_tables - expected_tables

    assert "alembic_version" in live_tables
    assert applied_revision == expected_revision
    assert not missing_tables and not unexpected_tables, (
        "Migrated Postgres schema drifted from SQLAlchemy metadata. "
        f"Missing tables: {sorted(missing_tables)}. "
        f"Unexpected tables: {sorted(unexpected_tables)}."
    )


def test_parent_db_bootstrap_exposes_discord_correction_schema() -> None:
    inspector = inspect(engine)

    profile_columns = {
        column["name"]: column for column in inspector.get_columns("profiles")
    }
    discord_history_columns = {
        column["name"]: column
        for column in inspector.get_columns("discord_connection_history")
    }

    assert "discord_user_id" in profile_columns
    assert "discord_username" in profile_columns
    assert "discord_integration_status" in profile_columns
    assert "discord_user_id" in discord_history_columns
    assert "discord_username" in discord_history_columns
    assert "status" in discord_history_columns
