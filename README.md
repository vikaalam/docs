# workspace-ops — documentation site

The published documentation for **`workspace-ops`**, built on [Mintlify](https://mintlify.com).

This site is a **rendering** of the design spike in the parent folder. It is never a source: if a
page here disagrees with `../ARCHITECTURE.md`, the page is the defect.

## Audiences

Six tabs, three audiences. Each tab has exactly one reader in mind, and they differ in vocabulary
and depth — never in facts.

| Tab | Written for |
|---|---|
| **Overview** | Everyone, first |
| **For Operations** | Ops analysts and their leads. No architecture |
| **For Compliance** | Compliance, MLRO, legal, internal audit. No architecture |
| **Engineering** | Senior engineers and reviewers |
| **API reference** | Implementers and publishing-service owners |
| **Design** | Anyone evaluating the interface |

`overview/how-to-read-this.mdx` states the rule that keeps the tabs from drifting into three
inconsistent products, and it is the page to update if that rule changes.

## Contracts — a copy, and it must stay one

`contracts/` here is a **derived copy of `../contracts/`**, produced by `sync-contracts.py`. Never
edit it by hand.

```bash
python3 sync-contracts.py          # copy + transform + regenerate the API nav
python3 sync-contracts.py --check  # exit 1 if the copy has drifted
```

Run it after any upstream contract change. Three things it does, and each exists for a measured
reason:

1. **Copies the envelope schema verbatim.**
2. **Resolves the one external `$ref`.** The source spec references the schema externally and its own
   comment explains why — that reasoning is correct and the source keeps it. But **Mintlify rejects
   external `$ref`s and does not fail on the page that uses them: it refuses to build the navigation
   and every route on the site returns 404.** An entire docs site disappears over one line.
3. **Regenerates the API reference navigation in `docs.json`** — one group per tag, each with an
   explicit `pages` list. A group carrying `openapi` with **no** `pages` renders the group and
   generates nothing, silently; tab-level `openapi` alongside groups does the same. Group-level plus
   an explicit list is the shape that works. 92 hand-maintained entries would drift, so they are
   derived.

The four MDX pages under `api/` are hand-written and describe the contracts' provenance; they are not
generated.

## Screens

`images/screens/*.webp` — **47 screens, exported from `../workspace.pen`** in the current `cu/`
light design language.

They are **read-only exports**. To regenerate, use the `pencil` MCP `export_nodes` tool with
`format: "webp"`, `scale: 2`, `quality: 88`, writing into `images/screens/`.

Two things learned doing it, worth not rediscovering:

- **The output directory must already exist** — the tool reports "you are probably referencing the
  wrong .pen file" if it does not, which is misleading.
- **Export in batches of 3–5.** Larger batches fail with that same misleading message. The two tall
  explainer frames need `scale: 1.5`.

Filenames on disk are readable names rather than node ids; the mapping is one `mv` per frame.

## Diagrams and custom styling

- `custom.css` — the product's own `cu/` design tokens as CSS custom properties, light and dark.
  Mintlify applies a repository CSS file site-wide.
- `snippets/*.jsx` — hand-built diagram components, imported into MDX with
  `import { X } from "/snippets/x.jsx"`.

Structural diagrams are components; sequence diagrams stay Mermaid. Every `var()` inside a component
carries an inline light-mode fallback, so a figure still renders if the stylesheet is ever not picked
up. See `AGENTS.md` for the full rule.

## Development

```bash
npm i -g mint
mint dev          # run from this directory, where docs.json lives
```

Preview at `http://localhost:3000`.

## Deployment

This folder has **its own `.git`, wired to GitHub, and Mintlify deploys from that remote.** Do not
delete the nested repository.

It is excluded from the parent folder's `design-sync.py` link checks — its content is `.mdx` while
the checker walks `.md`. Adoption is recorded in `../ARCHITECTURE.md`'s document index; the exclusion
is about what a script can usefully police. Two questions, two answers.

## The standing rule

**Never commit.** Every change in this workspace is left in the working tree for review and committed
by hand.
