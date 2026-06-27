from __future__ import annotations


def missing_runtime_dependencies() -> tuple[str, ...]:
    missing: list[str] = []
    try:
        import bs4  # noqa: F401
    except ImportError:
        missing.append("beautifulsoup4")
    return tuple(missing)
