"""Central model-registration path for SQLAlchemy metadata discovery."""


def import_models() -> None:
    """Import concrete model modules here as they are added."""
    from app.db.models import auth  # noqa: F401
