"""Cognis Concierge brand constants.

Pulled from env at import time with sensible defaults so a Cognis-flavored
Concierge deploy can override the visible product name / tagline / logo
without forking templates. Consumed by FastAPI app metadata + future
Letta-UI / template wiring; this module is the single source of truth
for customer-facing brand strings on the Concierge fork.

Env overrides:
    COGNIS_BRAND_NAME           (default: "Cognis Concierge")
    COGNIS_BRAND_SHORT_NAME     (default: "Cognis")
    COGNIS_BRAND_TAGLINE        (default: "Cognis Concierge — remembers everything, always on.")
    COGNIS_BRAND_DESCRIPTION    (long-form, used in OpenAPI summary etc.)
    COGNIS_BRAND_API_TITLE      (OpenAPI title; default: "Cognis Concierge API")
    COGNIS_BRAND_LOGO_URL       (default: "/brand-assets/cognis-logo.svg")
    COGNIS_BRAND_DOCS_URL       (customer docs site; default: marketing URL)
    COGNIS_BRAND_SUPPORT_EMAIL  (default: "hello@cognisai.com")
    COGNIS_BRAND_DASHBOARD_URL  (optional Bridge dashboard URL surfaced
                                  in the server startup banner; unset =
                                  no upstream-product pointer is shown).
"""

from __future__ import annotations

import os
from typing import Final, Optional

_DEFAULT_TAGLINE = "Cognis Concierge — remembers everything, always on."
_DEFAULT_DESCRIPTION = (
    "Cognis Concierge is the personal-AI / stateful-memory product from "
    "Cognis AI. Build agents that remember everything across sessions, "
    "tools, and conversations."
)

COGNIS_BRAND: Final[dict[str, str]] = {
    "name": os.environ.get("COGNIS_BRAND_NAME", "Cognis Concierge"),
    "short_name": os.environ.get("COGNIS_BRAND_SHORT_NAME", "Cognis"),
    "tagline": os.environ.get("COGNIS_BRAND_TAGLINE", _DEFAULT_TAGLINE),
    "description": os.environ.get("COGNIS_BRAND_DESCRIPTION", _DEFAULT_DESCRIPTION),
    "api_title": os.environ.get("COGNIS_BRAND_API_TITLE", "Cognis Concierge API"),
    "logo_url": os.environ.get("COGNIS_BRAND_LOGO_URL", "/brand-assets/cognis-logo.svg"),
    "marketing_url": "https://cognisai.com",
    "docs_url": os.environ.get("COGNIS_BRAND_DOCS_URL", "https://cognisai.com"),
    "support_email": os.environ.get("COGNIS_BRAND_SUPPORT_EMAIL", "hello@cognisai.com"),
}

# Optional pointer at the Bridge / portal dashboard. Left unset by default
# so Concierge in local-dev mode does not advertise any URL it cannot
# guarantee exists — and so we never silently steer users at upstream's
# hosted product.
COGNIS_DASHBOARD_URL: Final[Optional[str]] = os.environ.get("COGNIS_BRAND_DASHBOARD_URL")

__all__ = ["COGNIS_BRAND", "COGNIS_DASHBOARD_URL"]
