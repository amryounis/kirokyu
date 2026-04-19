"""Placeholder test module.

Will be removed or replaced when Phase 1 introduces real domain tests.
Its purpose is to give pytest at least one test to discover, so pre-commit's
pytest hook passes during the scaffolding phase.
"""


def test_sanity() -> None:
    """Trivial passing test — keeps pytest exit code 0 until real tests arrive."""
    assert True
