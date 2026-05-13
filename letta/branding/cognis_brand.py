"""Cognis Concierge brand constants.

Pulled from env at import time with sensible defaults so a Cognis-flavored
Concierge deploy can override the visible product name / tagline / logo
without forking templates. Consumed by future Letta-UI / template wiring;
this module deliberately does not touch upstream UI code.

Env overrides:
    COGNIS_BRAND_NAME           (default: "Cognis Concierge")
    COGNIS_BRAND_SHORT_NAME     (default: "Cognis")
    COGNIS_BRAND_TAGLINE        (default: "Cognis Concierge — remembers everything, always on.")
    COGNIS_BRAND_LOGO_URL       (default: "/brand-assets/cognis-logo.svg")
    COGNIS_BRAND_SUPPORT_EMAIL  (default: "hello@cognisai.com")
"""

from __future__ import annotations

import os
from typing import Final

COGNIS_BRAND: Final[dict[str, str]] = {
    "name": os.environ.get("COGNIS_BRAND_NAME", "Cognis Concierge"),
    "short_name": os.environ.get("COGNIS_BRAND_SHORT_NAME", "Cognis"),
    "tagline": os.environ.get(
        "COGNIS_BRAND_TAGLINE",
        "Cognis Concierge — remembers everything, always on.",
    ),
    "logo_url": os.environ.get("COGNIS_BRAND_LOGO_URL", "/brand-assets/cognis-logo.svg"),
    "marketing_url": "https://cognisai.com",
    "support_email": os.environ.get("COGNIS_BRAND_SUPPORT_EMAIL", "hello@cognisai.com"),
}

__all__ = ["COGNIS_BRAND"]
