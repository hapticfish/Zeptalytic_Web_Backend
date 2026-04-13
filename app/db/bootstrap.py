from sqlalchemy import MetaData

from app.db.base import Base
from app.db.models import import_models


def get_target_metadata() -> MetaData:
    """Return metadata after importing all ORM model modules."""
    import_models()
    return Base.metadata


target_metadata = get_target_metadata()
