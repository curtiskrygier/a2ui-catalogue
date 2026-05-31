"""Generate the surface compatibility table for the README from atoms/schema.yaml.

Usage:
    python tests/generate_compat_table.py

Prints the markdown table to stdout. Redirect to update the README section.
"""

import sys
from pathlib import Path
import yaml

CATALOGUE_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = CATALOGUE_ROOT / "atoms" / "schema.yaml"
SURFACES = ["web", "meet-stage", "googlechat", "email", "pdf"]

SYMBOLS = {
    "works":        "✅",
    "degraded":     "⚠️",
    "incompatible": "❌",
    "unknown":      "—",
}


def surface_status(atom: dict, surface: str) -> str:
    s = atom.get("surfaces", {})
    works_on      = s.get("works_on", [])
    degraded_on   = [e["surface"] for e in s.get("degraded_on", [])]
    incompatible  = [e["surface"] for e in s.get("incompatible_on", [])]

    if surface in incompatible:
        return SYMBOLS["incompatible"]
    if surface in degraded_on:
        return SYMBOLS["degraded"]
    if surface in works_on:
        return SYMBOLS["works"]
    return SYMBOLS["unknown"]


def generate_table(schema: dict) -> str:
    atoms = schema["blocks"]
    header = "| Atom | " + " | ".join(SURFACES) + " |"
    sep    = "|---|" + "---|" * len(SURFACES)
    rows   = []
    for atom in atoms:
        name   = f"`{atom['type']}`"
        cells  = [surface_status(atom, s) for s in SURFACES]
        rows.append(f"| {name} | " + " | ".join(cells) + " |")

    legend = (
        "\n\n"
        f"{SYMBOLS['works']} works fully  "
        f"{SYMBOLS['degraded']} degraded — renders with caveats  "
        f"{SYMBOLS['incompatible']} incompatible — do not use  "
        f"— not declared\n"
    )

    return "\n".join([header, sep] + rows) + legend


if __name__ == "__main__":
    with open(SCHEMA_PATH) as f:
        schema = yaml.safe_load(f)
    print(generate_table(schema))
