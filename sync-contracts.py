#!/usr/bin/env python3
"""
Copy ../contracts/ into ./contracts/ for Mintlify, resolving the one external $ref.

WHY THIS SCRIPT EXISTS
----------------------
Mintlify deploys from this folder's own git remote, so it cannot read a file outside
it — the contracts have to be copied in. That much is just plumbing.

The transform is the interesting part. `../contracts/openapi.yaml` references the
envelope schema with an EXTERNAL $ref, and its own comment says why:

    "Authored separately as contracts/event-envelope.schema.json and authoritative
     there — deliberately not restated inline, because two representations of one
     contract is the defect §7.1 forbids arriving through the back door."

That reasoning is correct and the source keeps it. **Mintlify rejects external $refs
outright** — and it does not fail loudly on the page that uses them: it refuses to
build the navigation, and *every route on the site returns 404*. A whole documentation
site disappears because of one line in a spec.

So the ref is resolved HERE, in the derived copy, at copy time. The source keeps its
single representation; the published copy is generated and never hand-edited, so no
human ever maintains a second one.

USAGE
-----
    python3 sync-contracts.py          # copy + transform
    python3 sync-contracts.py --check  # verify the copy is in step; exit 1 if not
"""

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE.parent / "contracts"
DST = HERE / "contracts"

SCHEMA = "event-envelope.schema.json"
SPEC = "openapi.yaml"

# Meaningless inside components.schemas, and dropped rather than carried across.
STRIP_TOP_LEVEL = {"$schema", "$id", "description"}

REF_LINE = "      $ref: './event-envelope.schema.json'"


def to_yaml(value, indent):
    """Emit the JSON-Schema subset we actually use as block-style YAML.

    Deliberately not pyyaml: this runs in CI and in a docs repo that has no Python
    dependencies, and the subset here is small enough to be obviously correct.
    """
    pad = " " * indent
    if isinstance(value, dict):
        if not value:
            return " {}"
        out = []
        for k, v in value.items():
            key = k if k.replace("$", "").replace("_", "").isalnum() else json.dumps(k, ensure_ascii=False)
            out.append(f"\n{pad}{key}:{to_yaml(v, indent + 2)}")
        return "".join(out)
    if isinstance(value, list):
        if not value:
            return " []"
        return "".join(f"\n{pad}- {json.dumps(v, ensure_ascii=False)}" for v in value)
    if isinstance(value, bool):
        return " true" if value else " false"
    if value is None:
        return " null"
    if isinstance(value, (int, float)):
        return f" {value}"
    # JSON string literals are valid YAML double-quoted scalars, escaping included.
    return f" {json.dumps(value, ensure_ascii=False)}"


def build():
    schema = json.loads((SRC / SCHEMA).read_text())
    inlined = {k: v for k, v in schema.items() if k not in STRIP_TOP_LEVEL}

    spec = (SRC / SPEC).read_text()
    if REF_LINE not in spec:
        sys.exit(
            f"FAIL: expected external $ref line not found in {SRC / SPEC}.\n"
            f"      The source spec changed shape — re-read it before trusting this script."
        )

    body = to_yaml(inlined, 6).lstrip("\n")
    replacement = (
        "      # ---- INLINED BY sync-contracts.py — DO NOT EDIT ----\n"
        "      # Source of truth: contracts/event-envelope.schema.json.\n"
        "      # Mintlify rejects external $refs and answers 404 on EVERY route when it\n"
        "      # finds one, so the ref is resolved in this derived copy only.\n"
        f"{body}"
    )
    return spec.replace(REF_LINE, replacement, 1)



# ---------------------------------------------------------------------------
# Navigation for the API reference tab.
#
# Mintlify only auto-populates endpoint pages in some navigation shapes, and a
# group carrying `openapi` with no `pages` is NOT one of them — it renders the
# group and generates nothing, silently. The shape that works is a group with
# `openapi` AND an explicit `pages` list of "METHOD /path" entries.
#
# 88 hand-maintained entries would drift from the spec within a release, so they
# are generated here instead and rewritten into docs.json on every sync.
# ---------------------------------------------------------------------------

METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
SPEC_REF = "/contracts/openapi.yaml"
MDX_GROUP = "The contracts"


def operations_by_tag(spec_text):
    """Minimal walk of the paths section: path -> method -> tag."""
    by_tag, path, method = {}, None, None
    for line in spec_text.split("\n"):
        if line.startswith("  /"):
            path, method = line[2:].split(":", 1)[0].strip(), None
        elif path and line.startswith("    ") and not line.startswith("     "):
            head = line.strip().split(":", 1)[0]
            method = head if head in METHODS else None
        elif method and line.strip().startswith("tags:"):
            tag = line.split("[", 1)[1].split("]", 1)[0].strip() if "[" in line else None
            if tag:
                by_tag.setdefault(tag, []).append(f"{method.upper()} {path}")
            method = None
    return by_tag


def write_nav(spec_text):
    import collections
    cfg_path = HERE / "docs.json"
    cfg = json.loads(cfg_path.read_text())
    by_tag = operations_by_tag(spec_text)
    if not by_tag:
        sys.exit("FAIL: parsed zero operations out of the spec — the nav would silently empty.")

    groups = [{"group": MDX_GROUP,
               "pages": ["api/index", "api/event-envelope", "api/conventions", "api/what-is-missing"]}]
    for tag in sorted(by_tag, key=lambda t: (-len(by_tag[t]), t)):
        groups.append({"group": tag, "openapi": SPEC_REF, "pages": by_tag[tag]})

    for tab in cfg["navigation"]["tabs"]:
        if tab["tab"] == "API reference":
            tab.pop("openapi", None)      # tab-level does not auto-populate; group-level + pages does
            tab["groups"] = groups
            break
    else:
        sys.exit("FAIL: no 'API reference' tab in docs.json")

    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    total = sum(len(v) for v in by_tag.values())
    print(f"docs.json: {total} operations across {len(by_tag)} tags written into the API reference tab")
    return total


def main():
    check = "--check" in sys.argv
    DST.mkdir(exist_ok=True)

    want_spec = build()
    want_schema = (SRC / SCHEMA).read_text()

    if check:
        have_spec = (DST / SPEC).read_text() if (DST / SPEC).exists() else ""
        have_schema = (DST / SCHEMA).read_text() if (DST / SCHEMA).exists() else ""
        drift = []
        if have_spec != want_spec:
            drift.append(SPEC)
        if have_schema != want_schema:
            drift.append(SCHEMA)
        if drift:
            print("DRIFT: " + ", ".join(drift) + " — run `python3 sync-contracts.py`")
            return 1
        print("contracts/ is in step with ../contracts/")
        return 0

    (DST / SPEC).write_text(want_spec)
    shutil.copyfile(SRC / SCHEMA, DST / SCHEMA)
    write_nav(want_spec)
    print(f"wrote {DST / SPEC} (external $ref resolved inline)")
    print(f"wrote {DST / SCHEMA} (verbatim)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
