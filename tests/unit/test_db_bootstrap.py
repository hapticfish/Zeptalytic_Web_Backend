from sqlalchemy import MetaData

import app.db.bootstrap as bootstrap


def test_get_target_metadata_imports_models(monkeypatch) -> None:
    called = False

    def fake_import_models() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(bootstrap, "import_models", fake_import_models)

    metadata = bootstrap.get_target_metadata()

    assert called is True
    assert isinstance(metadata, MetaData)
    assert metadata is bootstrap.Base.metadata
