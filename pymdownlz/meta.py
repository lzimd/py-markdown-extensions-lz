"""
Hugo-Pelican Metadata Fixer Extension for Python-Markdown

- Runs AFTER markdown.extensions.meta.
- Converts ``tags: [xx, yy, zz]`` → ``tags: xx, yy, zz``.
- Converts ``categories: [foo]`` → deletes ``categories`` and sets ``category: foo`` (first item if multiple).
- Warns if ``title`` or ``slug`` are missing.
- Warns if ``date`` or ``modified`` are not Hugo-compatible (ISO 8601/RFC 3339).
"""

import logging
import re

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Date validation helpers (Hugo spf13/cast compatible patterns)
# ---------------------------------------------------------------------------
_HUGO_DATE_PATTERNS = [
    # ISO 8601 / RFC 3339
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"),
    re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$"),
    re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"),
    re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$"),
    # Common Hugo formats (US date, etc.)
    re.compile(r"^\d{2} \w+ \d{4}$"),  # 09 May 2026
    re.compile(r"^\d{2} \w+ \d{4} \d{2}:\d{2}$"),  # 09 May 2026 12:30
]


def _is_hugo_date(value: str) -> bool:
    """Return True if *value* is likely to be parsed by Hugo's spf13/cast."""
    if any(p.match(value) for p in _HUGO_DATE_PATTERNS):
        return True
    # Fallback: try dateutil if installed (optional)
    try:
        from dateutil.parser import parse  # type: ignore[import-untyped]

        parse(value)
        return True
    except Exception:
        return False


def _unwrap_bracket_str(value: str) -> str:
    """If *value* is wrapped in ``[...]``, return the inner content, else unchanged."""
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        return v[1:-1].strip()
    return value


class HugoPelicanMetaPreprocessor(Preprocessor):
    """Adjust metadata for Pelican/Hugo dual compatibility."""

    def run(self, lines):
        if not hasattr(self.md, "Meta"):
            return lines

        meta = self.md.Meta  # dict produced by the original Meta extension

        # ---- 1. Fix tags: [xx, yy, zz] → xx, yy, zz -------------------------
        if "tags" in meta:
            raw_list = meta["tags"]
            # Only act when the whole value is still a single bracket‑string
            if len(raw_list) == 1:
                new_val = _unwrap_bracket_str(raw_list[0])
                meta["tags"] = [new_val]

        # ---- 2. Fix categories: [foo] → category = foo ----------------------
        if "categories" in meta:
            raw_list = meta["categories"]
            if raw_list:
                # Get the first category (strip brackets, take first element)
                inner = _unwrap_bracket_str(raw_list[0])
                first_cat = inner.split(",")[0].strip()
            else:
                first_cat = ""
            # Delete categories, set category (as list for Pelican compatibility)
            del meta["categories"]
            # Use a list to match Pelican’s meta structure. The single element
            # will be extracted by Pelican’s _parse_metadata as the value.
            meta["category"] = [first_cat]

        # ---- 3. Check title / slug fields ----
        for field in ("title", "slug"):
            if field not in meta or not any(v.strip() for v in meta[field]):
                logger.warning("Missing or empty metadata field: %s", field)

        # ---- 4. Check date / modified compatibility ----
        for field in ("date", "modified"):
            if field in meta:
                for raw_value in meta[field]:
                    if raw_value.strip() and not _is_hugo_date(raw_value.strip()):
                        logger.warning(
                            "[Title(%s)] "
                            "Metadata field '%s' contains '%s' which may not be "
                            "recognized by Hugo (spf13/cast). "
                            "Use ISO 8601 / RFC 3339 for best compatibility.",
                            meta["title"],
                            field,
                            raw_value,
                        )

        return lines


class HugoPelicanMetaExtension(Extension):
    """
    Meta-Data extension that overrides the built-in meta
    while maintaining full compatibility with Pelican and Hugo.
    """

    def extendMarkdown(self, md):
        md.registerExtension(self)
        self.md = md
        # priority=26 runs AFTER the built-in 'meta' (priority=27)
        md.preprocessors.register(
            HugoPelicanMetaPreprocessor(md), "hugo_pelican_meta_fixer", 26
        )


def makeExtension(**kwargs):
    return HugoPelicanMetaExtension(**kwargs)
