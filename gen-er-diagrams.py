#!/usr/bin/env python3
"""
Generate Mermaid erDiagram blocks from ../migrations/<schema>/001-init.sql.

WHY GENERATED
-------------
The migrations are output of the module data models. An ER diagram drawn by hand
is a third representation of the same schema, and it drifts silently — nothing
would ever fail. Generating it means the diagram cannot disagree with the SQL that
was actually applied to PostgreSQL.

WHY ONE DIAGRAM PER SCHEMA, AND NEVER ONE BIG ONE
-------------------------------------------------
**No foreign key leaves a schema.** The migrations say so in their own comments,
and it is a boundary rule, not an accident: cross-module relations are bare uuids
resolved by a client/ call or not resolved at all.

So a single 65-table diagram would be nine disconnected islands — or, worse,
somebody would join them by hand and draw relationships the database does not
enforce and the architecture forbids. A per-schema diagram is the only honest one.

Bare cross-schema columns are listed in the notes below each diagram instead, so
the reference is visible without being drawn as a relationship.

USAGE
-----
    python3 gen-er-diagrams.py <schema>     # print one mermaid block
    python3 gen-er-diagrams.py --list       # schemas and table counts
"""

import re
import sys
from pathlib import Path

MIGRATIONS = Path(__file__).parent.parent / "migrations"

# Columns whose name says they point into another schema. They are NOT foreign keys.
CROSS = re.compile(r"^(task|invocation|report_run|artifact|subject_key|person|process_instance)_id$")


def parse(schema):
    sql = (MIGRATIONS / schema / "001-init.sql").read_text()
    tables = {}
    for m in re.finditer(
        r"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?([a-z_]+)\.([a-z_0-9]+)\s*\((.*?)\n\)\s*(PARTITION BY[^;]*)?;", sql, re.S | re.I
    ):
        name, body, part = m.group(2), m.group(3), m.group(4)
        if "PARTITION OF" in body.upper()[:120]:
            continue
        cols, fks, bare = [], [], []
        for line in body.split("\n"):
            raw = line.split("--")[0].strip().rstrip(",")
            if not raw or raw.upper().startswith(
                ("PRIMARY KEY", "UNIQUE", "CHECK", "CONSTRAINT", "FOREIGN KEY", "EXCLUDE")
            ):
                continue
            parts = raw.split()
            if len(parts) < 2 or not re.match(r"^[a-z_][a-z_0-9]*$", parts[0]):
                continue
            col, typ = parts[0], parts[1].split("(")[0]
            ref = re.search(r"REFERENCES\s+[a-z_]+\.([a-z_0-9]+)", raw, re.I)
            if ref:
                fks.append((col, ref.group(1)))
            elif CROSS.match(col):
                bare.append(col)
            cols.append((col, typ, "PRIMARY KEY" in raw.upper(), bool(ref)))
        tables[name] = {"cols": cols, "fks": fks, "bare": bare, "partitioned": bool(part)}
    return tables


def diagram(schema, max_cols=8):
    t = parse(schema)
    out = ["erDiagram"]
    for name, d in t.items():
        out.append(f"    {name} {{")
        for col, typ, pk, fk in d["cols"][:max_cols]:
            out.append(f"        {typ} {col}{' PK' if pk else (' FK' if fk else '')}")
        if len(d["cols"]) > max_cols:
            out.append(f"        more {len(d['cols']) - max_cols}_further_columns")
        out.append("    }")
    for name, d in t.items():
        for col, target in d["fks"]:
            out.append(f'    {target} ||--o{{ {name} : "{col}"')
    return "\n".join(out), t


def main():
    if "--list" in sys.argv:
        for p in sorted(MIGRATIONS.glob("*/001-init.sql")):
            s = p.parent.name
            t = parse(s)
            fks = sum(len(d["fks"]) for d in t.values())
            bare = sum(len(d["bare"]) for d in t.values())
            print(f"{s:<14} {len(t):>2} tables  {fks:>2} in-schema FKs  {bare:>2} bare cross-schema refs")
        return 0
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    block, t = diagram(sys.argv[1])
    print(block)
    bare = {n: d["bare"] for n, d in t.items() if d["bare"]}
    if bare:
        print("\n<!-- bare cross-schema references, deliberately NOT drawn as relationships:")
        for n, cols in bare.items():
            print(f"     {n}: {', '.join(cols)}")
        print("-->")
    return 0


if __name__ == "__main__":
    sys.exit(main())
