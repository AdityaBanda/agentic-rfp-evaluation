from __future__ import annotations

import random
import string
from datetime import datetime, timezone


def generate_rfp_run_id() -> str:
    """Generate a unique run id such as RFP-20260928-AB12CD."""
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"RFP-{date_part}-{suffix}"
