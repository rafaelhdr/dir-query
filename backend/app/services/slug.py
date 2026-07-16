import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    return _NON_ALNUM.sub("-", value.strip().lower()).strip("-")
