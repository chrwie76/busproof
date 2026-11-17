"""Each template for .env stays a template: documented, prefixed, and without a secret in it.

The plant and the test project have one each: where the plant listens is the plant's business,
where the system is and how to log in is the test project's.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
TEMPLATES = [ROOT / "plant" / ".env.example", ROOT / "test-project" / ".env.example"]
SECRET_WORDS = ("PASSWORD", "TOKEN", "SECRET", "KEY")


@pytest.fixture(params=TEMPLATES, ids=lambda path: path.parent.name)
def template(request: pytest.FixtureRequest) -> Path:
    return request.param


def blocks(template: Path) -> list[list[str]]:
    """The template's lines, grouped into blocks separated by blank lines."""
    groups: list[list[str]] = [[]]
    for line in template.read_text().splitlines():
        if line.strip():
            groups[-1].append(line)
        elif groups[-1]:
            groups.append([])
    return [group for group in groups if group]


def variables(template: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1)
        for group in blocks(template)
        for line in group
        if not line.startswith("#")
    )


def test_every_variable_is_explained_by_a_comment_in_its_block(template: Path):
    for group in blocks(template):
        if any(not line.startswith("#") for line in group):
            assert any(line.startswith("#") for line in group), f"undocumented: {group}"


def test_every_variable_belongs_to_busproof(template: Path):
    assert variables(template)
    for name in variables(template):
        assert name.startswith("BUSPROOF_"), name


def test_no_secret_has_a_value_in_the_template(template: Path):
    for name, value in variables(template).items():
        if any(word in name for word in SECRET_WORDS):
            assert value == "", f"{name} must stay empty in .env.example"


def test_no_variable_is_in_both_templates():
    plant, project = (set(variables(path)) for path in TEMPLATES)
    assert not plant & project
