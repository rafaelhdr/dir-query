from app.services.slug import slugify


def test_slugifies_simple_name() -> None:
    assert slugify("Company X") == "company-x"


def test_collapses_non_alphanumeric_runs() -> None:
    assert slugify("Foo & Bar / Baz!!") == "foo-bar-baz"


def test_trims_leading_and_trailing_hyphens() -> None:
    assert slugify("  -- Acme -- ") == "acme"


def test_all_punctuation_slugifies_to_empty() -> None:
    assert slugify("!!!") == ""
