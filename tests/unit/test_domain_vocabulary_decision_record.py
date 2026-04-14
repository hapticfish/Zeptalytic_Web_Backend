from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VOCABULARY_RECORD_PATH = REPO_ROOT / "docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md"
CONTROL_DOC_PATHS = (
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "IMPLEMENTATION_PLAN.md",
    REPO_ROOT / "docs/architecture/Zeptalytic_Website_Implementation_Control_Plan.md",
)


def test_vocabulary_decision_record_contains_locked_parent_vocabularies() -> None:
    content = VOCABULARY_RECORD_PATH.read_text(encoding="utf-8")

    assert "Zeptalytic Domain Vocabulary Decision Record" in content
    assert "## 1. Account status" in content
    assert "## 19. Attachment scan status" in content
    assert "Do not invent alternate values during implementation." in content
    assert "Mirror the Pay payment-status vocabulary exactly." in content


def test_control_docs_reference_vocabulary_decision_record_as_canonical_source() -> None:
    for path in CONTROL_DOC_PATHS:
        content = path.read_text(encoding="utf-8")

        assert "docs/architecture/Zeptalytic_Domain_Vocabulary_Decision_Record.md" in content
        assert "canonical source" in content.lower()
