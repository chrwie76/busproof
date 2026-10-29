"""The template for .env stays a template: documented, prefixed, and without a secret in it."""

from pathlib import Path

TEMPLATE = Path(__file__).parent.parent / ".env.example"
SECRET_WORDS = ("PASSWORD", "TOKEN", "SECRET", "KEY")


def blocks() -> list[list[str]]:
    """The template's lines, grouped into blocks separated by blank lines."""
    groups: list[list[str]] = [[]]
    for line in TEMPLATE.read_text().splitlines():
        if line.strip():
            groups[-1].append(line)
        elif groups[-1]:
            groups.append([])
    return [group for group in groups if group]


def variables() -> dict[str, str]:
    return dict(
        line.split("=", 1) for group in blocks() for line in group if not line.startswith("#")
    )


def test_every_variable_is_explained_by_a_comment_in_its_block():
    for group in blocks():
        if any(not line.startswith("#") for line in group):
            assert any(line.startswith("#") for line in group), f"undocumented: {group}"


def test_every_variable_belongs_to_busproof():
    assert variables()
    for name in variables():
        assert name.startswith("BUSPROOF_"), name


def test_no_secret_has_a_value_in_the_template():
    for name, value in variables().items():
        if any(word in name for word in SECRET_WORDS):
            assert value == "", f"{name} must stay empty in .env.example"
