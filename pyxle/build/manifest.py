"""Page manifest loading for production builds."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def load_manifest(path: Path | str) -> Dict[str, Any]:
    """Load and validate a page-manifest.json file.

    Returns the parsed manifest dictionary. Raises ``ValueError`` when the
    file does not contain a valid JSON object.
    """
    manifest_path = Path(path)
    with manifest_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, dict):
        raise ValueError(
            f"page-manifest.json at '{manifest_path}' must be a JSON object, "
            f"got {type(data).__name__}"
        )

    return data
