"""Central model-registration path for SQLAlchemy metadata discovery."""


def import_models() -> None:
    """Import concrete model modules here as they are added."""
    from app.db.models import account_security_settings  # noqa: F401
    from app.db.models import accounts  # noqa: F401
    from app.db.models import auth_events  # noqa: F401
    from app.db.models import auth_sessions  # noqa: F401
    from app.db.models import auth  # noqa: F401
    from app.db.models import email_verification_tokens  # noqa: F401
    from app.db.models import mfa_recovery_codes  # noqa: F401
    from app.db.models import password_reset_tokens  # noqa: F401
